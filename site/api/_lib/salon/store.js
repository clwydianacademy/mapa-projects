/* Clwydian Academy training salon — where bookings live.
 *
 * Upstash Redis over its REST API, with plain fetch: no package. The database is the academy's
 * own (KV_REST_API_URL / KV_REST_API_TOKEN in the academy's Vercel project) and every key starts
 * "salon:".
 *
 * There is NO file fallback. A serverless function's disk does not survive, so a booking
 * written to it would be confirmed to the client and then lost. With no store the endpoints
 * say "email us" instead — see handlers.js.
 *
 * TRANSACTIONS. transact(keys, fn) takes a short lock on every key (in sorted order, so two
 * writers cannot deadlock), reads them, runs fn — synchronous, so the feasibility rule runs on
 * exactly what was read — and commits. Two things make it safe:
 *   - the commit is ONE script that checks this writer still holds every lock, writes, and
 *     releases. A writer that overran its lock writes nothing.
 *   - a lock is only ever deleted by the writer whose token is in it.
 */
"use strict";
const crypto = require("node:crypto");

const LOCK_MS = 8000;
const TRIES = 60;
const WAIT_MS = 50;

const COMMIT = [
  "local n = tonumber(ARGV[2])",
  "for i = 1, n do if redis.call('GET', KEYS[i]) ~= ARGV[1] then return 0 end end",
  "for i = n + 1, #KEYS do redis.call('SET', KEYS[i], ARGV[2 + i - n]) end",
  "for i = 1, n do redis.call('DEL', KEYS[i]) end",
  "return 1",
].join("\n");
const RELEASE = "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end";

class LockError extends Error {}
/** Thrown by a transaction's fn to refuse the write; carries what to tell the caller. */
class Refused extends Error {
  constructor(detail) { super(detail && detail.code ? detail.code : "refused"); this.detail = detail || {}; }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class UpstashStore {
  constructor(url, token, fetchImpl) {
    this.url = String(url).replace(/\/+$/, "");
    this.token = token;
    this.fetch = fetchImpl || ((...a) => globalThis.fetch(...a));
  }
  async cmd(command) {
    const r = await this.fetch(this.url, {
      method: "POST",
      headers: { Authorization: "Bearer " + this.token, "Content-Type": "application/json" },
      body: JSON.stringify(command),
    });
    if (!r.ok) throw new Error("store " + r.status);
    const j = await r.json();
    if (j.error) throw new Error("store: " + String(j.error).slice(0, 120));
    return j.result;
  }
  async get(key) { const raw = await this.cmd(["GET", key]); return raw ? JSON.parse(raw) : null; }
  async set(key, value, ttlSeconds) {
    const c = ["SET", key, JSON.stringify(value)];
    if (ttlSeconds) c.push("EX", String(Math.max(1, Math.ceil(ttlSeconds))));
    await this.cmd(c);
  }
  /** Set only if absent. True if this call created it. */
  async setIfAbsent(key, value, ttlSeconds) {
    return (await this.cmd(["SET", key, JSON.stringify(value), "NX", "EX", String(Math.ceil(ttlSeconds))])) === "OK";
  }
  /** A counter that expires `windowSeconds` after its first increment. */
  async bump(key, windowSeconds) {
    const n = await this.cmd(["INCR", key]);
    if (n === 1) await this.cmd(["EXPIRE", key, String(windowSeconds)]);
    return n;
  }
  async lock(key, token) { return (await this.cmd(["SET", key + ":lock", token, "NX", "PX", String(LOCK_MS)])) === "OK"; }
  async release(key, token) { await this.cmd(["EVAL", RELEASE, "1", key + ":lock", token]); }
  async commit(lockedKeys, token, writes) {
    const keys = Object.keys(writes);
    const ok = await this.cmd(["EVAL", COMMIT, String(lockedKeys.length + keys.length),
      ...lockedKeys.map((k) => k + ":lock"), ...keys, token, String(lockedKeys.length),
      ...keys.map((k) => JSON.stringify(writes[k]))]);
    return ok === 1;
  }
}

/** The same contract in memory — for the tests, and nothing else. */
class MemoryStore {
  constructor(now) { this.data = new Map(); this.expiry = new Map(); this.locks = new Map(); this.now = now || (() => Date.now()); }
  live(key) {
    const e = this.expiry.get(key);
    if (e !== undefined && e <= this.now()) { this.data.delete(key); this.expiry.delete(key); }
    return this.data.has(key);
  }
  async get(key) { return this.live(key) ? JSON.parse(this.data.get(key)) : null; }
  async set(key, value, ttlSeconds) {
    this.data.set(key, JSON.stringify(value));
    if (ttlSeconds) this.expiry.set(key, this.now() + ttlSeconds * 1000); else this.expiry.delete(key);
  }
  async setIfAbsent(key, value, ttlSeconds) { if (this.live(key)) return false; await this.set(key, value, ttlSeconds); return true; }
  async bump(key, windowSeconds) {
    const n = ((await this.get(key)) || 0) + 1;
    const keep = this.expiry.get(key);
    this.data.set(key, JSON.stringify(n));
    this.expiry.set(key, n === 1 || keep === undefined ? this.now() + windowSeconds * 1000 : keep);
    return n;
  }
  async lock(key, token) {
    const held = this.locks.get(key);
    if (held && held.until > Date.now()) return false;
    this.locks.set(key, { token, until: Date.now() + LOCK_MS });
    return true;
  }
  async release(key, token) { const h = this.locks.get(key); if (h && h.token === token) this.locks.delete(key); }
  async commit(lockedKeys, token, writes) {
    for (const k of lockedKeys) { const h = this.locks.get(k); if (!h || h.token !== token || h.until <= Date.now()) return false; }
    for (const k of Object.keys(writes)) { this.data.set(k, JSON.stringify(writes[k])); this.expiry.delete(k); }
    for (const k of lockedKeys) this.locks.delete(k);
    return true;
  }
}

/**
 * Read-check-write under lock.
 * @param {string[]} keys  the keys to lock and read
 * @param {(current: object) => ({writes?: object, result?: any})} fn  SYNCHRONOUS. Throw Refused to
 *        write nothing. `writes` may name keys outside `keys` (a new reference, say).
 */
async function transact(store, keys, fn) {
  const sorted = [...new Set(keys)].sort();
  const token = crypto.randomUUID();
  for (let attempt = 0; attempt < TRIES; attempt += 1) {
    const got = [];
    let all = true;
    for (const k of sorted) {
      if (await store.lock(k, token)) got.push(k); else { all = false; break; }
    }
    if (!all) {
      for (const k of got) await store.release(k, token);
      await sleep(WAIT_MS);
      continue;
    }
    try {
      const current = {};
      for (const k of sorted) current[k] = await store.get(k);
      const out = fn(current) || {};
      if (out.writes && Object.keys(out.writes).length) {
        if (!(await store.commit(sorted, token, out.writes))) throw new LockError("lost the lock before writing");
        return out.result;
      }
      for (const k of sorted) await store.release(k, token);
      return out.result;
    } catch (e) {
      for (const k of sorted) await store.release(k, token).catch(() => {});
      throw e;
    }
  }
  throw new LockError("could not get a lock");
}

/** Is a value somebody put in an environment variable usable, or does it only look set?
 *  Vercel writes the literal "[SENSITIVE]" for a sensitive variable pulled to a file. */
function usable(value, { min = 8, prefixes = null } = {}) {
  const v = String(value || "").trim();
  if (v.length < min || /^\[.*\]$/.test(v) || /^(todo|changeme|xxx+|your[-_ ])/i.test(v)) return false;
  return !prefixes || prefixes.some((p) => v.startsWith(p));
}

function storeFromEnv(env) {
  const url = String(env.KV_REST_API_URL || "").trim();
  const token = String(env.KV_REST_API_TOKEN || "").trim();
  if (!usable(url) || !usable(token)) return null;
  try { if (new URL(url).protocol !== "https:") return null; } catch { return null; }
  return new UpstashStore(url, token);
}

const K = {
  day: (date) => "salon:day:" + date,
  ref: (id) => "salon:ref:" + id,
  students: "salon:students",
  patch: (clientKey) => "salon:patch:" + clientKey,
  evt: (id) => "salon:evt:" + id,
  models: "salon:models",
  unreconciled: "salon:unreconciled",
  rl: (k) => "salon:rl:" + k,
};

module.exports = { UpstashStore, MemoryStore, transact, Refused, LockError, storeFromEnv, usable, K };
