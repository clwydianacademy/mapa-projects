/* Clwydian Academy training salon — which appointments can be offered.
 *
 * Walks days and start times and keeps what feasible() passes. It has NO rule of its own: if a
 * slot is offered it is because feasible() said yes, and the save path asks feasible() again.
 */
"use strict";
const T = require("./time");
const { quote, levelsFor } = require("./quote");
const { feasible } = require("./feasible");
const { rank } = require("./policy");

/** Learners who could be asked for this service at this level choice, cheapest level first
 *  (the lower levels need the practice most), then by id so the order is stable. */
function candidatesFor(p, service, who, students) {
  const levels = who === "any" ? levelsFor(p, service) : [who];
  return (students || [])
    .filter((s) => s.active !== false && levels.includes(s.level))
    .sort((a, b) => rank(p, a.level) - rank(p, b.level) || String(a.id).localeCompare(String(b.id)));
}

/**
 * Slots on one date.
 * @param {object} req  { serviceId, who ("any" | level id), under16, guardianConsent }
 * @param {object} ctx  { policy, students, patch, now }
 * @returns {Array<{date,start,end,level,studentId,minutes,price,deposit,period}>}
 */
function slotsForDate(req, date, dayBookings, ctx) {
  const p = ctx.policy;
  const service = p.serviceById.get(req.serviceId);
  if (!service) return [];
  const sessions = p.opening.sessions[T.dayKey(date)] || [];
  const people = candidatesFor(p, service, req.who, ctx.students);
  const afternoon = T.parseClock(p.booking.afternoon_from);
  const out = [];
  for (const session of sessions) {
    const open = T.parseClock(session.open), close = T.parseClock(session.close);
    for (let start = open; start < close; start += p.booking.slot_step_minutes) {
      for (const student of people) {
        const q = quote(p, { serviceId: service.id, level: student.level });
        if (!q.ok) continue;
        const candidate = candidateFrom(q, { date, start, studentId: student.id,
          under16: req.under16, guardianConsent: req.guardianConsent });
        if (feasible(candidate, dayBookings, ctx) === null) {
          out.push({ date, start, end: start + q.minutes, level: student.level, studentId: student.id,
            minutes: q.minutes, price: q.price, deposit: q.deposit,
            period: start < afternoon ? "morning" : "afternoon" });
          break;                                   // one offer per start time
        }
      }
    }
  }
  return out;
}

/** The one place a quote becomes a candidate for feasible(), so the offer path and the save
 *  path cannot build it differently. */
function candidateFrom(q, extra) {
  return Object.assign({
    serviceId: q.serviceId, level: q.level, segments: q.segments,
    chemical: q.chemical, patchProduct: q.patchProduct,
  }, extra);
}

/** "Lots" / "A few" / "Full" — always a word, never a colour alone. */
function fullness(count) {
  if (count === 0) return "full";
  return count <= 3 ? "few" : "lots";
}

/** If nothing can be offered at all, the first reason feasible() gives that is about the CLIENT
 *  (age, patch test) rather than about the day — so the page can say what to do next. */
function clientBlock(req, ctx) {
  const p = ctx.policy;
  const service = p.serviceById.get(req.serviceId);
  if (!service) return { code: "unknown-service" };
  if (req.under16 === true) {
    if (service.chemical && p.age.restricted_chemicals.includes(service.chemical)) return { code: "under16-chemical" };
    if (req.guardianConsent !== true) return { code: "guardian-consent" };
  }
  if (service.patch_test_product && !(ctx.patch || []).some((r) => r.product === service.patch_test_product)) {
    return { code: "patch-none", product: service.patch_test_product };
  }
  return null;
}

module.exports = { slotsForDate, candidateFrom, candidatesFor, fullness, clientBlock };
