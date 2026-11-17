/* Clwydian Academy training salon — what a visit takes and costs.
 *
 * quote() turns a service, a learner level, the client's answers about their hair and any
 * extras into the SEGMENTS of the appointment, its length, its price and its deposit. It decides
 * nothing about whether the appointment can be kept: that is feasible.js, and only feasible.js.
 *
 * LENGTH. base minutes (what a qualified stylist takes) x the level's factor for the service's
 * category, rounded up to five minutes, plus the educator's minutes — a consultation check at
 * the start and a final check at the end, on every booking.
 *
 * PRICE. The level's price for the service, plus what each answer adds at that level, plus each
 * extra. Additive, never multiplied. A concession takes a percentage off cutting and styling
 * (never colour) on the listed weekdays.
 *
 * A segment is { kind, minutes }:
 *   check   the educator is with the learner and the client
 *   work    the learner is working on the client in the chair
 *   basin   the learner and the client are at a basin
 * The learner and the chair are taken for the whole appointment.
 */
"use strict";
const { roundUp5, dayKey } = require("./time");
const { rank } = require("./policy");

const total = (segments) => segments.reduce((n, s) => n + s.minutes, 0);

function segmentsFor(p, service, level, extraBase) {
  const factor = p.levels[level].factors[service.category];
  const work = roundUp5((service.base_minutes + (extraBase || 0)) * factor);
  const out = [{ kind: "check", minutes: p.educator.consultation_minutes }];
  const basin = service.basin;
  if (basin) {
    const before = Math.min(work - 5, Math.floor((basin.from * factor) / 5) * 5);
    const at = Math.min(work - before, roundUp5(basin.minutes * factor));
    if (before > 0) out.push({ kind: "work", minutes: before });
    out.push({ kind: "basin", minutes: at });
    if (work - before - at > 0) out.push({ kind: "work", minutes: work - before - at });
  } else {
    out.push({ kind: "work", minutes: work });
  }
  out.push({ kind: "check", minutes: p.educator.final_check_minutes });
  return out;
}

/** Flat deposit by category; never more than the price; nothing on a free service. */
function depositFor(p, service, price) {
  if (!(price > 0)) return 0;
  return Math.min(p.deposit[service.category], price);
}

/** Is the concession in force on this date for this service? */
function concessionOn(p, service, date) {
  return service.concession === true && typeof date === "string" && p.concession.days.includes(dayKey(date));
}

const lowestLevelWith = (p, table) => p.levelIds.find((l) => table[l] !== undefined) || null;

/**
 * @param {object} p      compiled policy
 * @param {object} input  { serviceId, level, answers?, addons?, concession?, date? }
 * @returns {{ok:true, ...}|{ok:false, code:string, ...}}
 */
function quote(p, input) {
  const service = p.serviceById.get(input && input.serviceId);
  if (!service) return { ok: false, code: "unknown-service" };
  const level = input.level;
  if (!p.levels[level] || !p.levelIds.includes(level)) return { ok: false, code: "unknown-level" };
  if (!service.levels.includes(level)) return { ok: false, code: "skill-level", needs: service.levels[0] || null };
  if (service.quote_only) return { ok: false, code: "quote-only" };

  let price = service.prices[level];
  const answers = input.answers || {};
  const missing = [];
  const chosen = {};
  for (const qid of service.questions || []) {
    const option = p.questions[qid].options.find((o) => o.id === answers[qid]);
    if (!option) { missing.push(qid); continue; }
    // an answer with no figure at this level is not offered at this level: it routes upward
    if (option.add[level] === undefined) return { ok: false, code: "needs-higher-level", needs: lowestLevelWith(p, option.add), question: qid };
    price += option.add[level];
    chosen[qid] = option.id;
  }
  if (missing.length) return { ok: false, code: "answers-missing", missing };

  let extraBase = 0;
  const addons = [];
  for (const id of [...new Set(input.addons || [])]) {
    const addon = p.addons[id];
    if (!addon || !addon.for.includes(service.id)) return { ok: false, code: "unknown-addon" };
    if (addon.prices[level] === undefined) return { ok: false, code: "needs-higher-level", needs: lowestLevelWith(p, addon.prices), addon: id };
    price += addon.prices[level];
    extraBase += addon.base_minutes;
    addons.push(id);
  }

  // the lowest level at which everything chosen is offered — feasible() holds the learner to it
  let needsLevel = service.levels[0];
  const raise = (table) => { const l = lowestLevelWith(p, table); if (l && rank(p, l) > rank(p, needsLevel)) needsLevel = l; };
  for (const qid of Object.keys(chosen)) raise(p.questions[qid].options.find((o) => o.id === chosen[qid]).add);
  for (const id of addons) raise(p.addons[id].prices);

  const fullPrice = price;
  const concession = input.concession === true && concessionOn(p, service, input.date);
  if (concession) price = Math.round((price * (100 - p.concession.percent)) / 100 / p.concession.round_to) * p.concession.round_to;

  const segments = segmentsFor(p, service, level, extraBase);
  const top = p.levelIds[p.levelIds.length - 1];
  return {
    ok: true,
    serviceId: service.id,
    level,
    answers: chosen,
    addons,
    segments,
    minutes: total(segments),
    // what a qualified stylist would take, so the page can say honestly how much longer this is
    qualifiedMinutes: roundUp5(service.base_minutes + extraBase) + p.educator.consultation_minutes + p.educator.final_check_minutes,
    price,
    fullPrice,
    concession,
    deposit: depositFor(p, service, price),
    chemical: service.chemical || null,
    patchProduct: service.patch_test_product || null,
    consultFirst: service.consultation_first === true,
    needsLevel,
    isPatchTest: service.is_patch_test === true,
    isConsultation: service.is_consultation === true,
    top,
  };
}

/** The levels allowed to perform a service, lowest first. */
function levelsFor(p, service) { return service.levels.slice(); }

module.exports = { quote, segmentsFor, depositFor, levelsFor, concessionOn, total, rank };
