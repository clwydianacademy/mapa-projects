/* Clwydian Academy training salon — can this appointment be kept?
 *
 * THE ONE RULE. feasible() is called in exactly two situations and gives the same answer in both:
 *
 *   - when working out which slots to OFFER (availability.js), and
 *   - again, inside the write lock, when a booking is SAVED or MOVED (handlers.js).
 *
 * The second call is the one that counts: what a client was offered may be minutes old, two
 * people may press the same slot, something may post to the API directly. If you add a
 * scheduling or safety rule it goes HERE, never in a caller — scripts/test_salon_rules.js
 * asserts that every slot the offer engine produces passes this function on the save path.
 *
 * Deliberately synchronous and pure: everything it needs (the day's bookings, the learners, the
 * client's patch-test records, the clock) is handed in, so it can run inside a lock without
 * awaiting anything.
 *
 * Returns null when the appointment can be kept, or { code, ...detail } saying why not. The
 * words shown to a person are in messages.js, in both languages.
 */
"use strict";
const T = require("./time");
const { rank } = require("./policy");

/** Does this booking still occupy its place? A cancelled one does not. A HELD one (somebody is
 *  on the payment page) does until its hold runs out, and then simply stops — decided when
 *  read, never by a scheduled job, so a failed job can never wedge the diary. */
function blocks(booking, now) {
  if (!booking || booking.status === "cancelled") return false;
  if (booking.status === "held") return typeof booking.heldUntil !== "number" || booking.heldUntil > now;
  return true;
}

/** [{kind, from, to}] in minutes past midnight. */
function spans(booking) {
  const out = [];
  let t = booking.start;
  for (const s of booking.segments) { out.push({ kind: s.kind, from: t, to: t + s.minutes }); t += s.minutes; }
  return out;
}
const endOf = (b) => b.start + b.segments.reduce((n, s) => n + s.minutes, 0);
const overlap = (aFrom, aTo, bFrom, bTo) => aFrom < bTo && aTo > bFrom;

/** The session (opening period) a span sits wholly inside, or null. */
function sessionFor(p, date, start, end) {
  const list = p.opening.sessions[T.dayKey(date)] || [];
  return list.find((s) => start >= T.parseClock(s.open) && end <= T.parseClock(s.close)) || null;
}
const inTerm = (p, date) => p.opening.terms.some((t) => date >= t.from && date <= t.to);

/**
 * @param {object} c    the candidate: { id?, date, start, segments, studentId, serviceId, level,
 *                       age ("u12" | "u16" | "adult"), guardianConsent, chemical, patchProduct,
 *                       consultFirst }
 * @param {object[]} day   every booking stored for that date (any status)
 * @param {object} ctx  { policy, students, patch, now, actor? }   actor "staff" lifts the notice rule only
 *                       students: [{ id, level, active, days?, skills? }]
 *                       patch:    [{ product, testedAt }] for THIS client (testedAt epoch ms)
 */
function feasible(c, day, ctx) {
  const p = ctx.policy;
  const now = ctx.now;
  if (!T.isDate(c.date) || !Number.isInteger(c.start) || !Array.isArray(c.segments) || !c.segments.length) {
    return { code: "bad-request" };
  }
  const start = c.start;
  const end = endOf(c);

  // ---- when the salon is open -------------------------------------------------------------
  if (!inTerm(p, c.date)) return { code: "out-of-term" };
  if (p.opening.closures.includes(c.date)) return { code: "closed-date" };
  if (!(p.opening.sessions[T.dayKey(c.date)] || []).length) return { code: "closed-day" };
  if (!sessionFor(p, c.date, start, end)) return { code: "outside-hours" };
  if (start % 5 !== 0) return { code: "bad-request" };

  // ---- notice and horizon ------------------------------------------------------------------
  // The one thing staff may do that a client may not: place an appointment at short notice or
  // far ahead (moving somebody on the day). Every other rule below applies to staff as well.
  const hours = T.hoursUntil(c.date, start, now);
  if (ctx.actor === "staff") { /* no notice or horizon rule */ } else
  if (hours < p.booking.min_notice_hours) return { code: "too-soon", hours: p.booking.min_notice_hours };
  if (hours > (p.booking.horizon_days + 1) * 24) return { code: "too-far", days: p.booking.horizon_days };

  // ---- age ---------------------------------------------------------------------------------
  // Under 16: no permanent or quasi-permanent colour, bleach or relaxer — no consent unlocks it.
  // Anything else for an under-16 needs a parent or guardian's consent.
  // 12 to 15: the listed services only. Under 12: the children's cut only. Both: a parent or
  // guardian must consent and be present. A children-only service is not sold to an adult.
  if (c.age === "u12" || c.age === "u16") {
    if (c.chemical && p.age.restricted_chemicals.includes(c.chemical)) return { code: "under16-chemical" };
    const allowed = c.age === "u12" ? p.age.under12_services : p.age.under16_services;
    if (!allowed.includes(c.serviceId)) return { code: c.age === "u12" ? "under12-service" : "under16-service" };
    if (c.guardianConsent !== true) return { code: "guardian-consent" };
  } else if (c.age === "adult") {
    const svc = p.serviceById.get(c.serviceId);
    if (svc && svc.children_only) return { code: "children-only" };
  } else {
    return { code: "age-missing" };          // fails closed: an unanswered age question is not "adult"
  }

  // ---- patch test: at least 48 hours before, no more than 12 months old, SAME product --------
  if (c.patchProduct) {
    const at = T.instantOf(c.date, start);
    const tests = (ctx.patch || []).filter((r) => r.product === c.patchProduct && typeof r.testedAt === "number");
    if (!tests.length) return { code: "patch-none", product: c.patchProduct };
    const earliestOk = T.monthsBefore(at, p.patch_test.max_months);
    const latestOk = at - p.patch_test.min_hours * 3600000;
    if (!tests.some((r) => r.testedAt <= latestOk && r.testedAt >= earliestOk)) {
      return tests.some((r) => r.testedAt > latestOk)
        ? { code: "patch-too-recent", hours: p.patch_test.min_hours, product: c.patchProduct }
        : { code: "patch-expired", months: p.patch_test.max_months, product: c.patchProduct };
    }
  }

  // ---- a free consultation first, where the service needs one --------------------------------
  // Recorded when staff complete the consultation appointment; good for as long as a patch test.
  if (c.consultFirst) {
    const at = T.instantOf(c.date, start);
    const oldest = T.monthsBefore(at, p.patch_test.max_months);
    const seen = (ctx.patch || []).some((r) => r.product === "consult:" + c.serviceId && r.testedAt <= at && r.testedAt >= oldest);
    if (!seen) return { code: "consultation-first" };
  }

  // ---- the learner: exists, is in that day, and is allowed to do this ------------------------
  const service = p.serviceById.get(c.serviceId);
  if (!service) return { code: "unknown-service" };
  const student = (ctx.students || []).find((s) => s.id === c.studentId);
  if (!student || student.active === false) return { code: "student-unknown" };
  if (student.level !== c.level) return { code: "student-level-changed" };
  if (Array.isArray(student.days) && !student.days.includes(T.dayKey(c.date))) return { code: "student-not-in" };
  // the level must be switched on, the service offered at it, and high enough for what the
  // client's answers call for (bleach history or a big lift route a colour to Level 3)
  if (!service.levels.includes(student.level)) return { code: "skill-level", needs: service.levels[0] || null };
  if (c.needsLevel && rank(p, student.level) < rank(p, c.needsLevel)) return { code: "skill-level", needs: c.needsLevel };
  if (Array.isArray(student.skills) && !student.skills.includes(service.id)) return { code: "skill-not-signed-off" };

  // ---- resources, segment by segment ----------------------------------------------------------
  const others = day.filter((b) => b.id !== c.id && blocks(b, now));
  for (const b of others) {
    if (b.studentId === c.studentId && overlap(start, end, b.start, endOf(b))) return { code: "student-busy" };
  }
  const supervisors = p.resources.supervisors_on_floor;
  const mine = spans(c);
  const theirs = others.map((b) => ({ from: b.start, to: endOf(b), spans: spans(b) }));
  // Every time is a multiple of five minutes, so walking in fives sees every change.
  for (let t = start; t < end; t += 5) {
    const here = theirs.filter((b) => t >= b.from && t < b.to);
    if (here.length + 1 > p.resources.chairs) return { code: "no-chair" };
    if (here.length + 1 > p.resources.supervisor_ratio * supervisors) return { code: "supervisor-ratio" };
    const kind = mine.find((s) => t >= s.from && t < s.to).kind;
    if (kind === "basin" || kind === "check") {
      const same = here.filter((b) => b.spans.some((s) => s.kind === kind && t >= s.from && t < s.to)).length;
      if (kind === "basin" && same + 1 > p.resources.basins) return { code: "no-basin" };
      if (kind === "check" && same + 1 > supervisors) return { code: "no-supervisor" };
    }
  }
  return null;
}

module.exports = { feasible, blocks, spans, endOf, sessionFor, inTerm };
