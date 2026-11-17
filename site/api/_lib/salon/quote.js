/* Clwydian Academy training salon — what a visit takes and costs.
 *
 * quote() turns a service and a learner level into the SEGMENTS of the appointment, its length,
 * its price and its deposit. It decides nothing about whether the appointment can be kept: that
 * is feasible.js, and only feasible.js.
 *
 * A segment is { kind, minutes }:
 *   work     the learner is working on the client in the chair      (scaled by the level factor)
 *   basin    the learner and the client are at a basin              (scaled by the level factor)
 *   process  colour or lotion is developing; chemistry does not slow down for a learner (not scaled)
 *   check    the supervisor is checking the work                    (not scaled)
 * The learner and the chair are taken for the whole appointment.
 */
"use strict";
const { roundUp5 } = require("./time");
const { rank } = require("./policy");

const SCALED = new Set(["work", "basin"]);

function segmentsFor(p, service, level) {
  const factor = p.levels[level].duration_factor;
  return service.timings.map((s) => ({
    kind: s.kind,
    minutes: SCALED.has(s.kind) ? roundUp5(s.minutes * factor) : roundUp5(s.minutes),
  }));
}
const total = (segments) => segments.reduce((n, s) => n + s.minutes, 0);

/** Deposit in whole pounds: a percentage of the price, never more than the cap, never more than
 *  the price. A free service has no deposit. */
function depositFor(p, price) {
  if (!(price > 0)) return 0;
  return Math.min(Math.max(1, Math.round(price * p.deposit.percent / 100)), p.deposit.cap_pounds, price);
}

/**
 * @param {object} p        compiled policy
 * @param {object} input    { serviceId, level }
 * @returns {{ok:true, ...}|{ok:false, code:string}}
 */
function quote(p, input) {
  const service = p.serviceById.get(input && input.serviceId);
  if (!service) return { ok: false, code: "unknown-service" };
  const level = input.level;
  if (!p.levels[level]) return { ok: false, code: "unknown-level" };
  if (rank(p, level) < rank(p, service.min_level)) return { ok: false, code: "skill-level" };
  const segments = segmentsFor(p, service, level);
  const minutes = total(segments);
  const price = service.prices[level];
  return {
    ok: true,
    serviceId: service.id,
    level,
    segments,
    minutes,
    // what a qualified stylist would take, so the page can say honestly how much longer this is
    qualifiedMinutes: total(segmentsFor(p, service, "graduate")),
    price,
    deposit: depositFor(p, price),
    chemical: service.chemical || null,
    patchProduct: service.patch_test_product || null,
    isPatchTest: service.is_patch_test === true,
  };
}

/** The levels allowed to perform a service, lowest first. */
function levelsFor(p, service) {
  return p.levelIds.filter((l) => rank(p, l) >= rank(p, service.min_level));
}

module.exports = { quote, segmentsFor, depositFor, levelsFor, total };
