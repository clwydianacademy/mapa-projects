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
 * @param {object} req  { serviceId, who ("any" | level id), age, guardianConsent, answers, addons, concession }
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
        const q = quote(p, { serviceId: service.id, level: student.level, answers: req.answers, addons: req.addons, concession: req.concession, date });
        if (!q.ok) continue;                       // not offered at this learner's level, for these answers
        const candidate = candidateFrom(q, { date, start, studentId: student.id,
          age: req.age, guardianConsent: req.guardianConsent });
        if (feasible(candidate, dayBookings, ctx) === null) {
          out.push({ date, start, end: start + q.minutes, level: student.level, studentId: student.id,
            minutes: q.minutes, qualifiedMinutes: q.qualifiedMinutes, price: q.price, fullPrice: q.fullPrice,
            concession: q.concession, deposit: q.deposit,
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
    chemical: q.chemical, patchProduct: q.patchProduct, consultFirst: q.consultFirst, needsLevel: q.needsLevel,
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
  if (req.age === "u12" || req.age === "u16") {
    if (service.chemical && p.age.restricted_chemicals.includes(service.chemical)) return { code: "under16-chemical" };
    const allowed = req.age === "u12" ? p.age.under12_services : p.age.under16_services;
    if (!allowed.includes(service.id)) return { code: req.age === "u12" ? "under12-service" : "under16-service" };
    if (req.guardianConsent !== true) return { code: "guardian-consent" };
  } else if (req.age === "adult") {
    if (service.children_only) return { code: "children-only" };
  } else return { code: "age-missing" };
  if (service.quote_only) return { code: "quote-only" };
  if (service.consultation_first && !(ctx.patch || []).some((r) => r.product === "consult:" + service.id)) return { code: "consultation-first" };
  if (service.patch_test_product && !(ctx.patch || []).some((r) => r.product === service.patch_test_product)) {
    return { code: "patch-none", product: service.patch_test_product };
  }
  // no level at all can do this for these answers (asked for one level; the answers need a higher one)
  const levels = req.who === "any" ? service.levels : [req.who];
  const tries = levels.map((level) => quote(p, { serviceId: service.id, level, answers: req.answers, addons: req.addons }));
  if (!tries.some((q) => q.ok)) return tries[tries.length - 1] || { code: "skill-level" };
  return null;
}

module.exports = { slotsForDate, candidateFrom, candidatesFor, fullness, clientBlock };
