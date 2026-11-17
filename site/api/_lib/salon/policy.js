/* Clwydian Academy training salon — the policy, as the engine reads it.
 *
 * The numbers live in _data/salon/policy.json. A serverless function cannot read that folder at
 * run time, so website/_src/build.py copies it to ./policy.json beside this file, and
 * scripts/test_salon_rules.js fails if the two differ.
 *
 * Two kinds of unconfirmed value: a PLACEHOLDER { "todo_pm": true, "value": X } and the PM's
 * DRAFT { "pm_draft": "central scenario", "value": X }. resolve() strips both wrappers so the
 * engine reads plain values; unconfirmed() lists every one still in the file. While any remain
 * the engine will not take a booking in production — see openState() in handlers.js.
 */
"use strict";

let cached = null;

const isTodo = (o) => o !== null && typeof o === "object" && !Array.isArray(o) && o.todo_pm === true;
const isDraft = (o) => o !== null && typeof o === "object" && !Array.isArray(o) && typeof o.pm_draft === "string";
const isWrapped = (o) => isTodo(o) || isDraft(o);

function resolve(node) {
  if (isWrapped(node)) return resolve(node.value);
  if (Array.isArray(node)) return node.map(resolve);
  if (node !== null && typeof node === "object") {
    const out = {};
    for (const k of Object.keys(node)) if (k[0] !== "_") out[k] = resolve(node[k]);
    return out;
  }
  return node;
}

/** Every unconfirmed path still in the raw policy, e.g. "levels.l2.factors". `kind` is
 *  "todo" (a placeholder), "draft" (the PM's draft) or undefined for both. A draft may hold
 *  placeholders inside it, so the walk goes on down through a wrapper's value. */
function unconfirmed(raw, kind, path) {
  const here = path || "";
  const out = [];
  if (isWrapped(raw)) {
    if (!kind || (kind === "todo" ? isTodo(raw) : isDraft(raw))) out.push(here);
    return out.concat(unconfirmed(raw.value, kind, here));
  }
  if (Array.isArray(raw)) {
    raw.forEach((v, i) => out.push(...unconfirmed(v, kind, here + "." + (v && v.id ? v.id : i))));
  } else if (raw !== null && typeof raw === "object") {
    for (const k of Object.keys(raw)) out.push(...unconfirmed(raw[k], kind, here ? here + "." + k : k));
  }
  return out;
}

/** Build the engine's view of a raw policy object. */
function compile(raw) {
  const p = resolve(raw);
  p.todo = unconfirmed(raw, "todo");
  p.draft = unconfirmed(raw, "draft");
  p.unconfirmed = p.todo.length + p.draft.length;
  // Only levels that are switched on exist as far as the engine is concerned.
  p.levelIds = Object.keys(p.levels).filter((l) => p.levels[l].enabled !== false).sort((a, b) => p.levels[a].rank - p.levels[b].rank);
  for (const s of p.services) {
    // the levels a service is offered at: those with a price, that are switched on
    s.levels = p.levelIds.filter((l) => s.prices[l] !== undefined && !(l === "l2" && s.l2_allowed === false));
  }
  p.serviceById = new Map(p.services.map((s) => [s.id, s]));
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
