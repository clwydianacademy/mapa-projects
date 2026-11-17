/* Clwydian Academy training salon — the policy, as the engine reads it.
 *
 * The numbers live in _data/salon/policy.json. A serverless function cannot read that folder at
 * run time, so website/_src/build.py copies it to ./policy.json beside this file, and
 * scripts/test_salon_rules.js fails if the two differ.
 *
 * A PLACEHOLDER is { "todo_pm": true, "value": X }. resolve() strips the wrappers so the engine
 * reads plain values; unconfirmed() lists every placeholder still in the file. While that list
 * is not empty the engine will not take a booking in production — see openState().
 */
"use strict";

let cached = null;

function isTodo(o) { return o !== null && typeof o === "object" && !Array.isArray(o) && o.todo_pm === true; }

function resolve(node) {
  if (isTodo(node)) return resolve(node.value);
  if (Array.isArray(node)) return node.map(resolve);
  if (node !== null && typeof node === "object") {
    const out = {};
    for (const k of Object.keys(node)) if (k[0] !== "_") out[k] = resolve(node[k]);
    return out;
  }
  return node;
}

/** Every placeholder path still in the raw policy, e.g. "levels.l1.duration_factor". */
function unconfirmed(raw, path) {
  const here = path || "";
  if (isTodo(raw)) return [here];
  const out = [];
  if (Array.isArray(raw)) {
    raw.forEach((v, i) => out.push(...unconfirmed(v, here + "." + (v && v.id ? v.id : i))));
  } else if (raw !== null && typeof raw === "object") {
    for (const k of Object.keys(raw)) out.push(...unconfirmed(raw[k], here ? here + "." + k : k));
  }
  return out;
}

/** Build the engine's view of a raw policy object. */
function compile(raw) {
  const p = resolve(raw);
  p.todo = unconfirmed(raw);
  p.serviceById = new Map(p.services.map((s) => [s.id, s]));
  p.levelIds = Object.keys(p.levels).sort((a, b) => p.levels[a].rank - p.levels[b].rank);
  return p;
}

function policy() {
  if (!cached) cached = compile(require("./policy.json"));
  return cached;
}
/** Tests only: run the engine on a given raw policy. */
function usePolicy(raw) { cached = raw ? compile(raw) : null; return cached; }

const rank = (p, level) => (p.levels[level] ? p.levels[level].rank : 0);

module.exports = { policy, usePolicy, compile, resolve, unconfirmed, rank };
