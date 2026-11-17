#!/usr/bin/env node
/* test_salon_rules.js — the training salon's booking engine, exercised without Vercel, Upstash,
   Stripe or Resend.

       node --test scripts/test_salon_rules.js

   No dependencies: Node's built-in test runner (Node 18+). The REAL handlers run against a store
   in memory, a fixed clock and a fake fetch that captures what would have gone to Stripe and
   Resend; nothing leaves the machine.

   Two disciplines, both taken from the engine this one was modelled on:
     - every rule has a case that PASSES and a case that FAILS, so a rule that has switched
       itself off cannot hide behind a green run;
     - EVERY OFFERED SLOT PASSES THE SAVE-TIME CHECK — the offer engine and the save path call
       one function, and this file proves it by booking what was offered.

   The people here are invented. Names say what the case is about; phone numbers are from
   Ofcom's reserved drama range; emails are example.com.
*/
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const LIB = path.join(__dirname, "..", "site", "api", "_lib", "salon");
const RAW = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "_data", "salon", "policy.json"), "utf8"));
const { compile, unconfirmed, resolve } = require(path.join(LIB, "policy.js"));
const T = require(path.join(LIB, "time.js"));
const { quote, depositFor } = require(path.join(LIB, "quote.js"));
const { feasible, blocks } = require(path.join(LIB, "feasible.js"));
const A = require(path.join(LIB, "availability.js"));
const { MemoryStore, transact, Refused, K, usable, storeFromEnv } = require(path.join(LIB, "store.js"));
const S = require(path.join(LIB, "seal.js"));
const stripe = require(path.join(LIB, "stripe.js"));
const mail = require(path.join(LIB, "email.js"));
const H = require(path.join(LIB, "handlers.js"));

const P = compile(RAW);
/** A policy with some values changed, for the capacity cases. */
function policyWith(change) { const raw = JSON.parse(JSON.stringify(RAW)); change(resolveInPlace(raw)); return compile(raw); }
function resolveInPlace(raw) { return raw; }
const setv = (obj, key, value) => { obj[key] = value; };

// A Monday in the first week of the placeholder spring term; the clock is the Monday before.
const MON = "2027-01-18", WED = "2027-01-20", TUE = "2027-01-19";
const NOW = Date.parse("2027-01-11T09:00:00Z");
const at = (h, m) => h * 60 + (m || 0);

const STUDENTS = [
  { id: "st_000000a1", name: "Learner One",   level: "l1", days: ["mon", "wed"], active: true },
  { id: "st_000000a2", name: "Learner Two",   level: "l2", days: ["mon", "wed"], active: true },
  { id: "st_000000a3", name: "Learner Three", level: "l3", days: ["mon", "wed"], active: true },
  { id: "st_000000a4", name: "Graduate Four", level: "graduate", days: ["mon"], active: true },
];
const ctxFor = (over) => Object.assign({ policy: P, students: STUDENTS, patch: [], now: NOW }, over || {});

/** A candidate the way the engine builds one. */
function cand(serviceId, level, studentId, date, start, extra) {
  const q = quote(P, { serviceId, level });
  assert.equal(q.ok, true, "fixture quote " + serviceId + "/" + level);
  return A.candidateFrom(q, Object.assign({ date, start, studentId, under16: false, guardianConsent: false }, extra || {}));
}
/** A stored booking occupying a slot. */
function stored(id, serviceId, level, studentId, date, start, extra) {
  const q = quote(P, { serviceId, level });
  return Object.assign({ id, v: 1, date, start, segments: q.segments, minutes: q.minutes, serviceId, level, studentId,
    status: "confirmed", payments: [], log: [] }, extra || {});
}
const codeOf = (r) => (r === null ? null : r.code);

// =================================================================================================
// The policy file
// =================================================================================================
test("policy: the engine's copy is the data file, byte for byte", () => {
  const copy = path.join(LIB, "policy.json");
  assert.ok(fs.existsSync(copy), "site/api/_lib/salon/policy.json is missing — run website/_src/build.py");
  assert.equal(fs.readFileSync(copy, "utf8"), fs.readFileSync(path.join(__dirname, "..", "_data", "salon", "policy.json"), "utf8"),
    "the engine's policy.json differs from _data/salon/policy.json — rebuild");
});

test("policy: the contact address is the one in _data/site.json", () => {
  const site = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "_data", "site.json"), "utf8"));
  assert.equal(mail.CONTACT, site.email);
});

test("policy: placeholders are listed, and resolve() strips the wrapper", () => {
  const raw = { a: { todo_pm: true, value: 2 }, b: 3, list: [{ id: "x", c: { todo_pm: true, value: [1] } }], _note: "ignored" };
  assert.deepEqual(unconfirmed(raw), ["a", "list.x.c"]);
  assert.deepEqual(resolve(raw), { a: 2, b: 3, list: [{ id: "x", c: [1] }] });
  assert.deepEqual(unconfirmed({ a: 2, b: { c: 3 } }), []);
});

test("policy: the placeholder level factors are the ones in the brief", () => {
  assert.deepEqual(P.levelIds.map((l) => P.levels[l].duration_factor), [2.0, 1.6, 1.3, 1.0]);
  assert.equal(P.deposit.percent, 20);
  assert.equal(P.cancel_window_hours, 48);
  assert.equal(P.patch_test.min_hours, 48);
  assert.equal(P.patch_test.max_months, 12);
});

// =================================================================================================
// Quote: level durations, prices per tier, deposit
// =================================================================================================
test("quote: a learner's factor stretches work and basin time, not developing time or the check", () => {
  const svc = P.serviceById.get("root-colour");
  const g = quote(P, { serviceId: "root-colour", level: "graduate" });
  const l2 = quote(P, { serviceId: "root-colour", level: "l2" });
  svc.timings.forEach((seg, i) => {
    assert.equal(g.segments[i].minutes, seg.minutes, "graduate is the base timing");
    if (seg.kind === "process" || seg.kind === "check") assert.equal(l2.segments[i].minutes, seg.minutes, seg.kind + " must not stretch");
    else assert.equal(l2.segments[i].minutes, T.roundUp5(seg.minutes * 1.6), seg.kind + " stretches by the level factor");
  });
  assert.ok(l2.minutes > g.minutes);
  assert.equal(l2.qualifiedMinutes, g.minutes, "the page can say honestly how much longer a learner takes");
});

test("quote: Level 1 takes longest and costs least; each tier has its own price", () => {
  const all = ["l1", "l2", "l3", "graduate"].map((level) => quote(P, { serviceId: "cut-finish", level }));
  for (let i = 1; i < all.length; i += 1) {
    assert.ok(all[i].minutes < all[i - 1].minutes, "higher level is quicker");
    assert.ok(all[i].price > all[i - 1].price, "higher level costs more");
  }
  assert.equal(all[0].price, P.serviceById.get("cut-finish").prices.l1);
});

test("quote: deposit is the percentage, capped, and nothing on a free service", () => {
  assert.equal(depositFor(P, 30), 6);                    // 20%
  assert.equal(depositFor(P, 200), P.deposit.cap_pounds); // capped
  assert.equal(depositFor(P, 0), 0);                     // a free patch test takes no deposit
  assert.equal(depositFor(P, 2), 1);                     // never rounds a real price down to nothing
  assert.equal(quote(P, { serviceId: "patch-test", level: "l1" }).deposit, 0);
});

test("quote: refuses an unknown service, an unknown level, and a level below the service's minimum", () => {
  assert.equal(quote(P, { serviceId: "nope", level: "l1" }).code, "unknown-service");
  assert.equal(quote(P, { serviceId: "cut-finish", level: "l9" }).code, "unknown-level");
  assert.equal(quote(P, { serviceId: "foils", level: "l2" }).code, "skill-level");     // fail
  assert.equal(quote(P, { serviceId: "foils", level: "l3" }).ok, true);                // pass
});

// =================================================================================================
// feasible(): every rule, a pass and a fail
// =================================================================================================
test("rule: a plain appointment in term, in hours, with notice, is feasible", () => {
  assert.equal(feasible(cand("cut-finish", "l2", "st_000000a2", MON, at(10)), [], ctxFor()), null);
});

test("rule: term time only", () => {
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", "2027-04-05", at(10)), [], ctxFor({ now: Date.parse("2027-03-29T09:00:00Z") }))), "out-of-term");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", "2027-04-12", at(10)), [], ctxFor({ now: Date.parse("2027-04-05T09:00:00Z") }))), null);
});

test("rule: a closure date inside term is closed", () => {
  const now = Date.parse("2027-02-08T09:00:00Z");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", "2027-02-15", at(10)), [], ctxFor({ now }))), "closed-date");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", "2027-02-22", at(10)), [], ctxFor({ now: now + 7 * 86400000 }))), null);
});

test("rule: only on the days the salon opens", () => {
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", TUE, at(10)), [], ctxFor())), "closed-day");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", WED, at(10)), [], ctxFor())), null);
});

test("rule: the whole appointment sits inside the session", () => {
  const q = quote(P, { serviceId: "cut-finish", level: "l2" });
  const close = T.parseClock(P.opening.sessions.mon[0].close), open = T.parseClock(P.opening.sessions.mon[0].open);
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, close - q.minutes), [], ctxFor())), null, "finishing exactly at closing is fine");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, close - q.minutes + 5), [], ctxFor())), "outside-hours");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, open - 5), [], ctxFor())), "outside-hours");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, open), [], ctxFor())), null);
});

test("rule: minimum notice, measured in real hours — and staff alone may go under it", () => {
  const start = at(10), instant = T.instantOf(MON, start);
  const notice = P.booking.min_notice_hours * 3600000;
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, start), [], ctxFor({ now: instant - notice }))), null);
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, start), [], ctxFor({ now: instant - notice + 60000 }))), "too-soon");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, start), [], ctxFor({ now: instant - 60000, actor: "staff" }))), null);
});

test("rule: not beyond the booking horizon", () => {
  const far = Date.parse("2026-11-01T09:00:00Z");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, at(10)), [], ctxFor({ now: far }))), "too-far");
});

test("rule: the age question must be answered — it fails closed", () => {
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, at(10), { under16: undefined }), [], ctxFor())), "age-missing");
});

test("rule: under 16 — no permanent or quasi colour, bleach or relaxer, and consent does not unlock it", () => {
  const tested = [{ product: "colour", testedAt: NOW - 5 * 86400000 }, { product: "lightener", testedAt: NOW - 5 * 86400000 }, { product: "relaxer", testedAt: NOW - 5 * 86400000 }];
  for (const [svc, level, who] of [["root-colour", "l2", "st_000000a2"], ["full-colour", "l2", "st_000000a2"], ["foils", "l3", "st_000000a3"], ["relaxer", "l2", "st_000000a2"]]) {
    assert.ok(P.age.restricted_chemicals.includes(P.serviceById.get(svc).chemical), svc + " is a restricted chemical service");
    assert.equal(codeOf(feasible(cand(svc, level, who, MON, at(10), { under16: true, guardianConsent: true }), [], ctxFor({ patch: tested }))), "under16-chemical", svc);
    assert.equal(codeOf(feasible(cand(svc, level, who, MON, at(10), { under16: false }), [], ctxFor({ patch: tested }))), null, svc + " for an adult");
  }
});

test("rule: under 16, any other service — only with a guardian's consent", () => {
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, at(10), { under16: true, guardianConsent: false }), [], ctxFor())), "guardian-consent");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, at(10), { under16: true, guardianConsent: true }), [], ctxFor())), null);
});

test("rule: patch test — none on record is refused", () => {
  assert.equal(codeOf(feasible(cand("root-colour", "l2", "st_000000a2", MON, at(10)), [], ctxFor({ patch: [] }))), "patch-none");
});

test("rule: patch test — at least 48 hours before the appointment, to the minute", () => {
  const appt = T.instantOf(MON, at(10));
  const c = cand("root-colour", "l2", "st_000000a2", MON, at(10));
  assert.equal(codeOf(feasible(c, [], ctxFor({ patch: [{ product: "colour", testedAt: appt - 48 * 3600000 }] }))), null, "exactly 48h");
  assert.equal(codeOf(feasible(c, [], ctxFor({ patch: [{ product: "colour", testedAt: appt - 48 * 3600000 + 60000 }] }))), "patch-too-recent", "47h59");
});

test("rule: patch test — no more than 12 months old", () => {
  const appt = T.instantOf(MON, at(10));
  const c = cand("root-colour", "l2", "st_000000a2", MON, at(10));
  const twelve = T.monthsBefore(appt, 12);
  assert.equal(codeOf(feasible(c, [], ctxFor({ patch: [{ product: "colour", testedAt: twelve }] }))), null, "exactly 12 months");
  assert.equal(codeOf(feasible(c, [], ctxFor({ patch: [{ product: "colour", testedAt: twelve - 86400000 }] }))), "patch-expired", "12 months and a day");
});

test("rule: patch test — the SAME product; a test for another product does not count", () => {
  const good = NOW - 5 * 86400000;
  const c = cand("foils", "l3", "st_000000a3", MON, at(10));                     // uses the lightener
  assert.equal(codeOf(feasible(c, [], ctxFor({ patch: [{ product: "colour", testedAt: good }] }))), "patch-none");
  assert.equal(codeOf(feasible(c, [], ctxFor({ patch: [{ product: "lightener", testedAt: good }] }))), null);
});

test("rule: an expired test plus a valid one for the same product passes", () => {
  const appt = T.instantOf(MON, at(10));
  const c = cand("root-colour", "l2", "st_000000a2", MON, at(10));
  assert.equal(codeOf(feasible(c, [], ctxFor({ patch: [{ product: "colour", testedAt: appt - 500 * 86400000 }, { product: "colour", testedAt: appt - 10 * 86400000 }] }))), null);
});

test("rule: skill gating by level", () => {
  // a Level 2 learner offered a Level 3 service — built by hand, because quote() refuses it too
  const q3 = quote(P, { serviceId: "foils", level: "l3" });
  const sneaky = A.candidateFrom(q3, { date: MON, start: at(10), studentId: "st_000000a2", under16: false, level: "l2" });
  const patch = [{ product: "lightener", testedAt: NOW - 5 * 86400000 }];
  assert.equal(codeOf(feasible(Object.assign(sneaky, { level: "l2" }), [], ctxFor({ patch }))), "skill-level");
  assert.equal(codeOf(feasible(cand("foils", "l3", "st_000000a3", MON, at(10)), [], ctxFor({ patch }))), null);
});

test("rule: skill gating by sign-off, where a learner has a sign-off list", () => {
  const students = STUDENTS.map((s) => (s.id === "st_000000a2" ? Object.assign({}, s, { skills: ["blow-dry"] }) : s));
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, at(10)), [], ctxFor({ students }))), "skill-not-signed-off");
  assert.equal(codeOf(feasible(cand("blow-dry", "l2", "st_000000a2", MON, at(10)), [], ctxFor({ students }))), null);
});

test("rule: the learner must exist, be active, be at the quoted level, and be in that day", () => {
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_ffffffff", MON, at(10)), [], ctxFor())), "student-unknown");
  const inactive = STUDENTS.map((s) => (s.id === "st_000000a2" ? Object.assign({}, s, { active: false }) : s));
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a2", MON, at(10)), [], ctxFor({ students: inactive }))), "student-unknown");
  assert.equal(codeOf(feasible(cand("cut-finish", "l2", "st_000000a3", MON, at(10)), [], ctxFor())), "student-level-changed");
  assert.equal(codeOf(feasible(cand("cut-finish", "graduate", "st_000000a4", WED, at(10)), [], ctxFor())), "student-not-in");
  assert.equal(codeOf(feasible(cand("cut-finish", "graduate", "st_000000a4", MON, at(10)), [], ctxFor())), null);
});

test("rule: a learner cannot be with two clients at once — but back-to-back is fine", () => {
  const first = stored("CAS-0000000A", "cut-finish", "l2", "st_000000a2", MON, at(10));
  const end = first.start + first.minutes;
  assert.equal(codeOf(feasible(cand("blow-dry", "l2", "st_000000a2", MON, end - 5), [first], ctxFor())), "student-busy");
  assert.equal(codeOf(feasible(cand("blow-dry", "l2", "st_000000a2", MON, end), [first], ctxFor())), null);
});

test("rule: chairs — one more appointment than chairs is refused", () => {
  const two = policyWith((r) => setv(r.resources, "chairs", 2));
  const day = [stored("CAS-0000000A", "cut-finish", "l1", "st_000000a1", MON, at(10)), stored("CAS-0000000B", "cut-finish", "l2", "st_000000a2", MON, at(10))];
  const c = cand("barber-cut", "l3", "st_000000a3", MON, at(10));
  assert.equal(codeOf(feasible(c, day, ctxFor({ policy: two }))), "no-chair");
  assert.equal(codeOf(feasible(c, day.slice(0, 1), ctxFor({ policy: two }))), null);
});

test("rule: basins — counted only while a client is AT the basin", () => {
  const one = policyWith((r) => setv(r.resources, "basins", 1));
  // blow-dry starts at the basin: two starting together need two basins
  const a = stored("CAS-0000000A", "blow-dry", "l1", "st_000000a1", MON, at(10));
  assert.equal(codeOf(feasible(cand("blow-dry", "l2", "st_000000a2", MON, at(10)), [a], ctxFor({ policy: one }))), "no-basin");
  // once the first has left the basin, the second may start there
  const basinEnds = a.start + a.segments[0].minutes;
  assert.equal(a.segments[0].kind, "basin");
  assert.equal(codeOf(feasible(cand("blow-dry", "l2", "st_000000a2", MON, basinEnds), [a], ctxFor({ policy: one }))), null);
});

test("rule: the supervisor can check one learner's work at a time", () => {
  // barber-cut has no basin and ends on a check; two identical ones started together clash on the check only
  const a = stored("CAS-0000000A", "barber-cut", "l2", "st_000000a2", MON, at(10));
  const g = quote(P, { serviceId: "barber-cut", level: "l3" });
  const clash = a.start + a.minutes - g.minutes;                     // ends at the same minute, so the checks coincide
  assert.equal(codeOf(feasible(cand("barber-cut", "l3", "st_000000a3", MON, clash), [a], ctxFor())), "no-supervisor");
  assert.equal(codeOf(feasible(cand("barber-cut", "l3", "st_000000a3", MON, clash - 5), [a], ctxFor())), null, "five minutes apart, the checks do not overlap");
  const two = policyWith((r) => setv(r.resources, "supervisors_on_floor", 2));
  assert.equal(codeOf(feasible(cand("barber-cut", "l3", "st_000000a3", MON, clash), [a], ctxFor({ policy: two }))), null, "a second supervisor lifts it");
});

test("rule: supervisor ratio — learners working at once, per supervisor", () => {
  const tight = policyWith((r) => setv(r.resources, "supervisor_ratio", 2));
  const day = [stored("CAS-0000000A", "cut-finish", "l1", "st_000000a1", MON, at(10)), stored("CAS-0000000B", "cut-finish", "l2", "st_000000a2", MON, at(10))];
  const c = cand("hair-up", "l3", "st_000000a3", MON, at(10, 5));
  assert.equal(codeOf(feasible(c, day, ctxFor({ policy: tight }))), "supervisor-ratio");
  assert.equal(codeOf(feasible(c, day, ctxFor())), null, "at the placeholder ratio it fits");
});

test("rule: a hold blocks its slot until it lapses, then stops — no sweep needed", () => {
  const held = stored("CAS-0000000A", "cut-finish", "l2", "st_000000a2", MON, at(10), { status: "held", heldUntil: NOW + 30 * 60000 });
  const c = cand("blow-dry", "l2", "st_000000a2", MON, at(10));
  assert.equal(codeOf(feasible(c, [held], ctxFor({ now: NOW + 29 * 60000 }))), "student-busy");
  assert.equal(codeOf(feasible(c, [held], ctxFor({ now: NOW + 30 * 60000 }))), null);
  assert.equal(blocks({ status: "held" }, NOW), true, "a hold with no expiry blocks rather than silently freeing a slot");
  assert.equal(codeOf(feasible(c, [Object.assign({}, held, { status: "cancelled" })], ctxFor())), null);
});

test("rule: moving a booking does not collide with itself", () => {
  const a = stored("CAS-0000000A", "cut-finish", "l2", "st_000000a2", MON, at(10));
  const same = Object.assign(cand("cut-finish", "l2", "st_000000a2", MON, at(10, 15)), { id: a.id });
  assert.equal(codeOf(feasible(same, [a], ctxFor())), null);
  assert.equal(codeOf(feasible(Object.assign({}, same, { id: "CAS-0000000Z" }), [a], ctxFor())), "student-busy");
});

test("time: 09:30 in St Asaph is 09:30 either side of the clock change", () => {
  assert.equal(new Date(T.instantOf("2027-01-18", 570)).toISOString(), "2027-01-18T09:30:00.000Z");   // GMT
  assert.equal(new Date(T.instantOf("2027-06-14", 570)).toISOString(), "2027-06-14T08:30:00.000Z");   // BST
  assert.equal(T.isoDate(Date.parse("2027-06-13T23:30:00Z")), "2027-06-14");
  assert.equal(new Date(T.monthsBefore(Date.parse("2028-02-29T10:00:00Z"), 12)).toISOString().slice(0, 10), "2027-02-28");
});

// =================================================================================================
// The handlers, on a store in memory
// =================================================================================================
const HOST = "www.clwydianacademy.co.uk";
const REQ = (ip) => ({ headers: { host: HOST, origin: "https://" + HOST, "x-forwarded-for": ip || "10.1.0.1" } });
const DATA_KEY = crypto.randomBytes(32).toString("base64");
const WHSEC = "whsec_test_" + "a".repeat(24);
const FULL_ENV = { SALON_BOOKING_OPEN: "1", SALON_ALLOW_PLACEHOLDERS: "1", STRIPE_SECRET_KEY: "sk_test_" + "b".repeat(24),
  STRIPE_WEBHOOK_SECRET: WHSEC, SALON_DATA_KEY: DATA_KEY, RESEND_API_KEY: "re_test_" + "c".repeat(16), STAFF_PASSWORD: "correct horse battery" };

/** A world: store, clock, captured outgoing requests. */
async function world(over) {
  const w = { now: NOW, sent: [], sessions: [], stripeFails: false };
  w.store = over && over.noStore ? null : new MemoryStore(() => w.now);
  w.fetch = async (url, init) => {
    if (String(url).includes("api.stripe.com")) {
      if (w.stripeFails) return { ok: false, status: 500, json: async () => ({}) };
      const form = new URLSearchParams(init.body);
      const s = { id: "cs_test_" + (w.sessions.length + 1), url: "https://checkout.stripe.test/pay/" + (w.sessions.length + 1), form, key: init.headers["Idempotency-Key"] };
      w.sessions.push(s);
      return { ok: true, status: 200, json: async () => ({ id: s.id, url: s.url }) };
    }
    if (String(url).includes("api.resend.com")) { w.sent.push(JSON.parse(init.body)); return { ok: true, status: 200, text: async () => "" }; }
    throw new Error("unexpected fetch: " + url);
  };
  w.ctx = (envOver) => H.context({ env: Object.assign({}, FULL_ENV, (over && over.env) || {}, envOver || {}), store: w.store, now: () => w.now, fetch: w.fetch, policy: (over && over.policy) || P });
  if (w.store) await w.store.set(K.students, { v: 1, list: STUDENTS });
  return w;
}
let ipN = 0;
const freshReq = () => REQ("10.2." + Math.floor(ipN / 250) + "." + (ipN++ % 250));
const CLIENT = { name: "Mrs Ten Fifteen", email: "ten.fifteen@example.com", phone: "07700 900115" };
function order(over) {
  return Object.assign({ serviceId: "cut-finish", who: "l2", date: MON, start: at(10, 15), under16: false, lang: "en",
    client: CLIENT, consent: { terms: true } }, over || {});
}
async function bookingsOn(w, date) { return ((await w.store.get(K.day(date))) || { bookings: [] }).bookings; }
function signed(event, secret, tsMs) {
  const raw = Buffer.from(JSON.stringify(event));
  const t = Math.floor(tsMs / 1000);
  const v1 = crypto.createHmac("sha256", secret).update(t + "." + raw.toString("utf8")).digest("hex");
  return { raw, header: "t=" + t + ",v1=" + v1 };
}
const paidEvent = (id, ref, intent) => ({ id, type: "checkout.session.completed", data: { object: { id: "cs_test_1", client_reference_id: ref,
  payment_status: "paid", amount_total: 200, payment_intent: intent || "pi_test_1", metadata: { booking_id: ref } } } });

test("EVERY OFFERED SLOT PASSES THE SAVE-TIME CHECK — each one is booked, on a busy day", async () => {
  // A deliberately awkward day: a tight salon with appointments already in it.
  const tight = policyWith((r) => { setv(r.resources, "chairs", 2); setv(r.resources, "basins", 1); });
  const seed = [
    stored("CAS-0000000A", "cut-finish", "l1", "st_000000a1", MON, at(9, 30)),
    stored("CAS-0000000B", "root-colour", "l2", "st_000000a2", MON, at(11)),
    stored("CAS-0000000C", "blow-dry", "l3", "st_000000a3", MON, at(13)),
    stored("CAS-0000000D", "barber-cut", "graduate", "st_000000a4", MON, at(14), { status: "held", heldUntil: NOW + 600000 }),
  ];
  let offered = 0, checked = 0;
  for (const serviceId of ["cut-finish", "blow-dry", "barber-cut", "root-colour", "conditioning"]) {
    for (const who of ["any", "l1", "l2", "l3", "graduate"]) {
      const w = await world({ policy: tight });
      await w.store.set(K.day(MON), { v: 4, bookings: seed });
      const key = S.clientKey(S.keyFrom(FULL_ENV), CLIENT.email);
      await w.store.set(K.patch(key), { records: [{ product: "colour", testedAt: NOW - 5 * 86400000 }] });
      const svc = tight.serviceById.get(serviceId);
      const extra = svc.chemical ? { consultation: { reaction: false, notes: "" }, consent: { terms: true, health: true } } : {};
      const r = await H.availability(w.ctx(), { serviceId, who, under16: "false", from: MON, email: CLIENT.email }, freshReq());
      if (r.status !== 200) { assert.ok(["skill-level", "student-unknown"].includes(r.body.code) || r.status === 409, serviceId + "/" + who + " " + JSON.stringify(r.body)); continue; }
      const day = r.body.days.find((d) => d.date === MON);
      for (const slot of day.slots) {
        offered += 1;
        // the rule itself, on exactly what the save path will read
        const q = quote(tight, { serviceId, level: slot.level });
        const c = A.candidateFrom(q, { date: MON, start: slot.start, studentId: slot.s, under16: false, guardianConsent: false });
        assert.equal(feasible(c, seed, { policy: tight, students: STUDENTS, patch: [{ product: "colour", testedAt: NOW - 5 * 86400000 }], now: NOW }), null,
          `offered ${serviceId}/${who} at ${T.formatClock(slot.start)} must pass feasible()`);
        // and the save path end to end, each on a fresh copy of the day
        const w2 = await world({ policy: tight });
        await w2.store.set(K.day(MON), { v: 4, bookings: seed });
        await w2.store.set(K.patch(key), { records: [{ product: "colour", testedAt: NOW - 5 * 86400000 }] });
        const saved = await H.book(w2.ctx(), order(Object.assign({ serviceId, who, start: slot.start, s: slot.s }, extra)), freshReq());
        assert.equal(saved.status, 200, `offered ${serviceId}/${who} at ${T.formatClock(slot.start)} was refused on save: ${JSON.stringify(saved.body)}`);
        checked += 1;
      }
    }
  }
  assert.ok(offered > 40, "the fixture must actually offer slots (offered " + offered + ")");
  assert.equal(checked, offered);
});

test("offer: nothing offered collides with what is already booked, and a booked slot is no longer offered", async () => {
  const w = await world();
  const first = await H.availability(w.ctx(), { serviceId: "cut-finish", who: "l2", under16: "false", from: MON }, freshReq());
  const slot = first.body.days.find((d) => d.date === MON).slots[0];
  assert.ok(slot, "there is a slot to take");
  assert.equal((await H.book(w.ctx(), order({ start: slot.start, s: slot.s }), freshReq())).status, 200);
  const again = await H.availability(w.ctx(), { serviceId: "cut-finish", who: "l2", under16: "false", from: MON }, freshReq());
  assert.ok(!again.body.days.find((d) => d.date === MON).slots.some((s) => s.start === slot.start), "the only Level 2 learner is now busy then");
});

test("offer: fullness is a word; closed days are marked closed; next available is found", async () => {
  const w = await world();
  const r = await H.availability(w.ctx(), { serviceId: "cut-finish", who: "any", under16: "false", from: MON }, freshReq());
  assert.equal(r.body.days.length, P.booking.strip_days);
  for (const d of r.body.days) assert.ok(["lots", "few", "full", "closed"].includes(d.fullness));
  assert.equal(r.body.days.find((d) => d.date === TUE).fullness, "closed");
  assert.deepEqual(r.body.next.date, MON);
  assert.equal(A.fullness(0), "full"); assert.equal(A.fullness(3), "few"); assert.equal(A.fullness(4), "lots");
  for (const s of r.body.days[0].slots) assert.ok(["morning", "afternoon"].includes(s.period));
});

test("offer: 'any learner' offers the lowest level that can do it, and says which", async () => {
  const w = await world();
  const r = await H.availability(w.ctx(), { serviceId: "cut-finish", who: "any", under16: "false", from: MON }, freshReq());
  assert.equal(r.body.days[0].slots[0].level, "l1");
  const r3 = await H.availability(w.ctx(), { serviceId: "restyle", who: "any", under16: "false", from: MON }, freshReq());
  assert.equal(r3.body.days[0].slots[0].level, "l2", "restyle is not offered at Level 1");
});

test("offer: the client-side blocks are named before any slot is searched", async () => {
  const w = await world();
  const kid = await H.availability(w.ctx(), { serviceId: "root-colour", who: "l2", under16: "true", guardianConsent: "true" }, freshReq());
  assert.equal(kid.status, 409); assert.equal(kid.body.code, "under16-chemical");
  const noTest = await H.availability(w.ctx(), { serviceId: "root-colour", who: "l2", under16: "false", email: CLIENT.email }, freshReq());
  assert.equal(noTest.body.code, "patch-none");
  const noAge = await H.availability(w.ctx(), { serviceId: "cut-finish", who: "l2" }, freshReq());
  assert.equal(noAge.body.code, "age-missing");
});

// ---- degrade, never fail silently ---------------------------------------------------------------
test("degrade: unconfirmed placeholders close booking in production, whatever the switches say", async () => {
  const w = await world();
  const env = { VERCEL_ENV: "production" };
  assert.equal(H.openState(w.ctx(env)).reason, "not-confirmed");
  for (const r of [await H.availability(w.ctx(env), { serviceId: "cut-finish", who: "l2", under16: "false" }, freshReq()),
                   await H.book(w.ctx(env), order(), freshReq())]) {
    assert.equal(r.status, 503); assert.equal(r.body.code, "unavailable"); assert.equal(r.body.reason, "not-confirmed");
    assert.equal(r.body.contact, "hello@clwydianacademy.co.uk"); assert.match(r.body.message, /hello@clwydianacademy\.co\.uk/);
  }
  const cfg = H.config(w.ctx(env));
  assert.equal(cfg.body.state.open, false);
  assert.deepEqual(cfg.body.services, [], "no placeholder price reaches a browser");
  assert.equal((await bookingsOn(w, MON)).length, 0);
});

test("degrade: a fully confirmed policy opens in production", async () => {
  const confirmed = compile(resolve(RAW));
  assert.deepEqual(confirmed.todo, []);
  const w = await world({ policy: confirmed });
  assert.equal(H.openState(w.ctx({ VERCEL_ENV: "production", SALON_ALLOW_PLACEHOLDERS: "" })).open, true);
  assert.equal(H.openState(w.ctx({ VERCEL_ENV: "production", SALON_BOOKING_OPEN: "" })).reason, "not-open");
});

test("degrade: no database — every endpoint says so and gives the email address", async () => {
  const w = await world({ noStore: true });
  for (const r of [await H.availability(w.ctx(), { serviceId: "cut-finish", who: "l2", under16: "false" }, freshReq()),
                   await H.book(w.ctx(), order(), freshReq()),
                   await H.bookingStatus(w.ctx(), { ref: "CAS-0000000A" }, freshReq()),
                   await H.staff(w.ctx(), { action: "day" }, freshReq())]) {
    assert.equal(r.status, 503); assert.equal(r.body.code, "unavailable"); assert.equal(r.body.contact, "hello@clwydianacademy.co.uk");
  }
  assert.equal((await H.webhook(w.ctx(), Buffer.from("{}"), "t=1,v1=00")).status, 503, "Stripe is told to retry");
  assert.equal(storeFromEnv({ KV_REST_API_URL: "[SENSITIVE]", KV_REST_API_TOKEN: "x".repeat(30) }), null, "a placeholder is not a credential");
  assert.equal(usable("[SENSITIVE]"), false); assert.equal(usable("sk_test_" + "x".repeat(20), { prefixes: ["sk_"] }), true);
});

test("degrade: no Stripe keys — a paid service is refused with the email address, a free patch test still books", async () => {
  const w = await world();
  const env = { STRIPE_SECRET_KEY: "", STRIPE_WEBHOOK_SECRET: "" };
  const paid = await H.book(w.ctx(env), order(), freshReq());
  assert.equal(paid.status, 503); assert.equal(paid.body.reason, "no-payments");
  assert.equal((await bookingsOn(w, MON)).length, 0, "no slot is held for a payment that cannot be taken");
  const free = await H.book(w.ctx(env), order({ serviceId: "patch-test", who: "l1", forProduct: "colour" }), freshReq());
  assert.equal(free.status, 200); assert.equal(free.body.status, "confirmed");
  // a secret key alone is not enough: without the webhook secret nothing could ever be confirmed
  assert.equal((await H.book(w.ctx({ STRIPE_WEBHOOK_SECRET: "" }), order({ start: at(12) }), freshReq())).body.reason, "no-payments");
});

test("degrade: Stripe refusing — the hold is released and the client is told", async () => {
  const w = await world(); w.stripeFails = true;
  const r = await H.book(w.ctx(), order(), freshReq());
  assert.equal(r.status, 503); assert.equal(r.body.reason, "payments-error");
  const [bk] = await bookingsOn(w, MON);
  assert.equal(bk.status, "cancelled");
  w.stripeFails = false;
  assert.equal((await H.book(w.ctx(), order(), freshReq())).status, 200, "the slot is free again");
});

test("degrade: no encryption key — a service with a consultation is refused, never stored in clear", async () => {
  const w = await world();
  const key = S.clientKey(S.keyFrom(FULL_ENV), CLIENT.email);
  await w.store.set(K.patch(key), { records: [{ product: "colour", testedAt: NOW - 5 * 86400000 }] });
  const r = await H.book(w.ctx({ SALON_DATA_KEY: "" }), order({ serviceId: "root-colour", consultation: { reaction: false, notes: "none" }, consent: { terms: true, health: true } }), freshReq());
  assert.equal(r.status, 503); assert.equal(r.body.reason, "no-encryption");
  assert.equal((await bookingsOn(w, MON)).length, 0);
  assert.equal(S.keyFrom({ SALON_DATA_KEY: "short" }), null);
});

test("degrade: no Resend key — the booking still stands, and the record says the email did not go", async () => {
  const w = await world();
  const r = await H.book(w.ctx({ RESEND_API_KEY: "" }), order({ serviceId: "patch-test", who: "l1", forProduct: "colour" }), freshReq());
  assert.equal(r.status, 200);
  assert.equal((await bookingsOn(w, MON))[0].confirmationEmail, "not-configured");
  assert.equal(w.sent.length, 0);
});

// ---- booking ------------------------------------------------------------------------------------
test("book: a paid service is HELD, with a checkout matched to the hold — not confirmed", async () => {
  const w = await world();
  const r = await H.book(w.ctx(), order(), freshReq());
  assert.equal(r.status, 200); assert.equal(r.body.status, "held"); assert.match(r.body.ref, /^CAS-[0-9A-F]{8}$/);
  assert.equal(r.body.checkout, "https://checkout.stripe.test/pay/1");
  const [bk] = await bookingsOn(w, MON);
  assert.equal(bk.status, "held"); assert.equal(bk.heldUntil, NOW + P.hold_minutes * 60000);
  assert.deepEqual(bk.payments, []);
  const s = w.sessions[0].form;
  assert.equal(s.get("line_items[0][price_data][unit_amount]"), String(bk.deposit * 100));
  assert.equal(s.get("expires_at"), String(Math.floor(bk.heldUntil / 1000)));
  assert.equal(s.get("client_reference_id"), bk.id);
  assert.equal(s.get("success_url"), "https://www.clwydianacademy.co.uk/salon/book/?ref=" + bk.id + "&back=paid");
  assert.equal(w.sessions[0].key, "salon-" + bk.id + "-deposit");
  assert.equal(w.sent.length, 0, "no confirmation before the money is real");
});

test("book: the return address is allow-listed — a forged Host cannot redirect a paying client", () => {
  assert.equal(stripe.returnBase({ host: "evil.example" }), "https://www.clwydianacademy.co.uk");
  assert.equal(stripe.returnBase({ host: "evil.example/www.clwydianacademy.co.uk" }), "https://www.clwydianacademy.co.uk");
  assert.equal(stripe.returnBase({ host: "mapa-projects-abc123.vercel.app" }), "https://mapa-projects-abc123.vercel.app");
  assert.equal(stripe.returnBase({ host: "clwydianacademy.co.uk" }), "https://clwydianacademy.co.uk");
});

test("book: two people pressing the same slot — exactly one gets it", async () => {
  const w = await world();
  const both = await Promise.all([
    H.book(w.ctx(), order({ client: { name: "Mr First Press", email: "first@example.com" } }), freshReq()),
    H.book(w.ctx(), order({ client: { name: "Ms Second Press", email: "second@example.com" } }), freshReq()),
  ]);
  assert.deepEqual(both.map((r) => r.status).sort(), [200, 409]);
  assert.equal(both.find((r) => r.status === 409).body.code, "student-busy");
  assert.equal((await bookingsOn(w, MON)).length, 1);
  assert.equal((await w.store.get(K.day(MON))).v, 1, "the day's version moved once");
});

test("book: a slot the page never offered is refused on save — the API cannot be used to skip the rule", async () => {
  const w = await world();
  assert.equal((await H.book(w.ctx(), order({ date: TUE }), freshReq())).body.code, "closed-day");
  assert.equal((await H.book(w.ctx(), order({ start: at(15, 55) }), freshReq())).body.code, "outside-hours");
  assert.equal((await H.book(w.ctx(), order({ serviceId: "root-colour", consultation: { reaction: false }, consent: { terms: true, health: true } }), freshReq())).body.code, "patch-none");
  assert.equal((await H.book(w.ctx(), order({ under16: true }), freshReq())).body.code, "guardian-consent");
  const below = await H.book(w.ctx(), order({ serviceId: "foils", who: "l2", consultation: { reaction: false }, consent: { terms: true, health: true } }), freshReq());
  assert.equal(below.status, 409); assert.equal(below.body.code, "skill-level");
  assert.equal((await bookingsOn(w, MON)).length, 0);
});

test("book: if the offered learner has gone, another at the same level is tried under the lock", async () => {
  const students = STUDENTS.concat([{ id: "st_000000b2", name: "Learner Two-B", level: "l2", days: ["mon"], active: true }]);
  const w = await world(); await w.store.set(K.students, { v: 2, list: students });
  await w.store.set(K.day(MON), { v: 1, bookings: [stored("CAS-0000000A", "cut-finish", "l2", "st_000000a2", MON, at(10))] });
  // five minutes later, so the two supervisor checks do not coincide — that is a different rule
  const r = await H.book(w.ctx(), order({ start: at(10, 5), s: "st_000000a2" }), freshReq());
  assert.equal(r.status, 200, JSON.stringify(r.body));
  assert.equal((await bookingsOn(w, MON))[1].studentId, "st_000000b2");
});

test("book: details and consent are required; a honeypot hit writes nothing; cross-site posts are refused", async () => {
  const w = await world();
  assert.equal((await H.book(w.ctx(), order({ client: { name: "", email: "x@example.com" } }), freshReq())).body.code, "details");
  assert.equal((await H.book(w.ctx(), order({ client: { name: "Mx No Email", email: "nope" } }), freshReq())).body.code, "details");
  assert.equal((await H.book(w.ctx(), order({ consent: {} }), freshReq())).body.code, "consent-terms");
  assert.equal((await H.book(w.ctx(), order({ website: "http://spam" }), freshReq())).status, 200);
  assert.equal((await H.book(w.ctx(), order(), { headers: { host: HOST, origin: "https://evil.example" } })).status, 403);
  assert.equal((await H.book(w.ctx(), order(), { headers: { host: HOST } })).status, 403);
  assert.equal((await bookingsOn(w, MON)).length, 0);
});

test("book: under 16 with a guardian's name and consent is booked, and the consent is recorded", async () => {
  const w = await world();
  assert.equal((await H.book(w.ctx(), order({ under16: true, guardian: { name: "Guardian Of Ten Fifteen", confirmed: false } }), freshReq())).body.code, "guardian-consent");
  const r = await H.book(w.ctx(), order({ under16: true, guardian: { name: "Guardian Of Ten Fifteen", confirmed: true } }), freshReq());
  assert.equal(r.status, 200);
  const [bk] = await bookingsOn(w, MON);
  assert.equal(bk.under16, true); assert.equal(bk.guardian.name, "Guardian Of Ten Fifteen"); assert.ok(bk.guardian.at);
});

// ---- consultation data --------------------------------------------------------------------------
test("consultation: stored only with explicit consent, and only encrypted", async () => {
  const w = await world();
  const key = S.clientKey(S.keyFrom(FULL_ENV), CLIENT.email);
  await w.store.set(K.patch(key), { records: [{ product: "colour", testedAt: NOW - 5 * 86400000 }] });
  const colour = (over) => order(Object.assign({ serviceId: "root-colour", consultation: { reaction: false, notes: "Allergic to plasters ZEBRA-MARKER", history: "box-colour" }, consent: { terms: true, health: true } }, over || {}));
  assert.equal((await H.book(w.ctx(), colour({ consent: { terms: true } }), freshReq())).body.code, "consent-health");
  assert.equal((await H.book(w.ctx(), colour({ consultation: { notes: "x" } }), freshReq())).body.code, "details", "the reaction question must be answered");
  const gate = await H.book(w.ctx(), colour({ consultation: { reaction: true } }), freshReq());
  assert.equal(gate.status, 409); assert.equal(gate.body.code, "consultation-needed");
  assert.equal((await bookingsOn(w, MON)).length, 0);

  assert.equal((await H.book(w.ctx(), colour(), freshReq())).status, 200);
  const everything = JSON.stringify([...w.store.data.entries()]);
  assert.ok(!everything.includes("ZEBRA-MARKER"), "the answer is nowhere in the database in clear");
  assert.ok(!everything.includes(CLIENT.email + '"]') && !everything.includes("salon:patch:" + CLIENT.email), "patch records are not filed under an email address");
  const [bk] = await bookingsOn(w, MON);
  assert.equal(bk.consultation.alg, "A256GCM");
  assert.equal(bk.consent.health.version, H.CONSENT_VERSION);
  assert.equal(S.open(S.keyFrom(FULL_ENV), bk.id, bk.consultation).notes, "Allergic to plasters ZEBRA-MARKER");
});

test("seal: a wrong key, an altered byte, or another booking's reference will not open", () => {
  const k = crypto.randomBytes(32), sealed = S.seal(k, "CAS-0000000A", { a: 1 });
  assert.deepEqual(S.open(k, "CAS-0000000A", sealed), { a: 1 });
  assert.throws(() => S.open(crypto.randomBytes(32), "CAS-0000000A", sealed));
  assert.throws(() => S.open(k, "CAS-0000000B", sealed));
  const bent = Object.assign({}, sealed, { ct: Buffer.from("x" + Buffer.from(sealed.ct, "base64").toString("latin1").slice(1), "latin1").toString("base64") });
  assert.throws(() => S.open(k, "CAS-0000000A", bent));
  assert.notEqual(S.seal(k, "CAS-0000000A", { a: 1 }).iv, sealed.iv, "a fresh nonce every time");
});

// ---- money --------------------------------------------------------------------------------------
test("money: the success page does not make a booking paid", async () => {
  const w = await world();
  const { body } = await H.book(w.ctx(), order(), freshReq());
  const seen = await H.bookingStatus(w.ctx(), { ref: body.ref, back: "paid" }, freshReq());
  assert.equal(seen.body.status, "held"); assert.equal(seen.body.depositPaid, false);
  assert.equal(seen.body.client, undefined, "a reference shows no name");
  assert.equal((await H.bookingStatus(w.ctx(), { ref: "CAS-FFFFFFFF" }, freshReq())).status, 404);
});

test("money: an unsigned, wrongly signed or stale webhook marks nothing paid", async () => {
  const w = await world();
  const { body } = await H.book(w.ctx(), order(), freshReq());
  const ev = paidEvent("evt_1", body.ref);
  const good = signed(ev, WHSEC, w.now);
  for (const [raw, header] of [
    [good.raw, ""], [good.raw, "t=" + Math.floor(w.now / 1000) + ",v1=abcd"],                    // wrong length must not throw
    [good.raw, signed(ev, "whsec_other_" + "z".repeat(24), w.now).header],
    [good.raw, signed(ev, WHSEC, w.now - 301000).header],                                          // too old
    [Buffer.from(good.raw.toString().replace("paid", "paid ")), good.header],                      // body altered after signing
  ]) {
    const r = await H.webhook(w.ctx(), raw, header);
    assert.equal(r.status, 400);
  }
  const [bk] = await bookingsOn(w, MON);
  assert.equal(bk.status, "held"); assert.deepEqual(bk.payments, []);
  assert.equal((await H.webhook(w.ctx({ STRIPE_WEBHOOK_SECRET: "" }), good.raw, good.header)).status, 503);
});

test("money: a verified webhook confirms the booking, once, and sends one confirmation", async () => {
  const w = await world();
  const { body } = await H.book(w.ctx(), order({ lang: "cy" }), freshReq());
  const ev = signed(paidEvent("evt_1", body.ref), WHSEC, w.now);
  const r = await H.webhook(w.ctx(), ev.raw, ev.header);
  assert.equal(r.status, 200); assert.equal(r.body.outcome, "paid");
  let [bk] = await bookingsOn(w, MON);
  assert.equal(bk.status, "confirmed"); assert.equal(bk.heldUntil, null);
  assert.equal(bk.payments.length, 1); assert.equal(bk.payments[0].amountPence, 200);
  assert.equal(w.sent.length, 1);
  assert.deepEqual(w.sent[0].to, [CLIENT.email]); assert.equal(w.sent[0].from, "Clwydian Academy <hello@clwydianacademy.co.uk>");
  assert.match(w.sent[0].text, /wedi'i gadarnhau/); assert.match(w.sent[0].text, new RegExp(body.ref));
  assert.equal(bk.confirmationEmail, "sent");
  // the same event again, and the same payment under a new event id
  assert.equal((await H.webhook(w.ctx(), ev.raw, ev.header)).body.duplicate, true);
  const again = signed(paidEvent("evt_2", body.ref), WHSEC, w.now);
  await H.webhook(w.ctx(), again.raw, again.header);
  [bk] = await bookingsOn(w, MON);
  assert.equal(bk.payments.length, 1); assert.equal(w.sent.length, 1);
  assert.equal((await H.bookingStatus(w.ctx(), { ref: body.ref }, freshReq())).body.depositPaid, true);
});

test("money: an unpaid session event does not confirm", async () => {
  const w = await world();
  const { body } = await H.book(w.ctx(), order(), freshReq());
  const e = paidEvent("evt_1", body.ref); e.data.object.payment_status = "unpaid";
  const ev = signed(e, WHSEC, w.now);
  assert.equal((await H.webhook(w.ctx(), ev.raw, ev.header)).body.outcome, "ignored");
  assert.equal((await bookingsOn(w, MON))[0].status, "held");
});

test("money: an expired checkout releases the hold", async () => {
  const w = await world();
  const { body } = await H.book(w.ctx(), order(), freshReq());
  const ev = signed({ id: "evt_x", type: "checkout.session.expired", data: { object: { id: "cs_test_1", client_reference_id: body.ref } } }, WHSEC, w.now);
  assert.equal((await H.webhook(w.ctx(), ev.raw, ev.header)).body.outcome, "released");
  assert.equal((await bookingsOn(w, MON))[0].cancelReason, "hold-expired");
  assert.equal((await H.book(w.ctx(), order(), freshReq())).status, 200, "the slot can be taken again");
});

test("money: paid after the hold lapsed — confirmed if the slot is still free, flagged for refund if it has gone", async () => {
  // still free
  let w = await world();
  let { body } = await H.book(w.ctx(), order(), freshReq());
  w.now += 45 * 60000;
  let ev = signed(paidEvent("evt_1", body.ref), WHSEC, w.now);
  assert.equal((await H.webhook(w.ctx(), ev.raw, ev.header)).body.outcome, "paid");
  assert.equal((await bookingsOn(w, MON))[0].status, "confirmed");

  // gone: somebody else took it in between
  w = await world();
  ({ body } = await H.book(w.ctx(), order(), freshReq()));
  w.now += 45 * 60000;
  const other = await H.book(w.ctx(), order({ client: { name: "Ms Took It After", email: "after@example.com" } }), freshReq());
  assert.equal(other.status, 200, "the lapsed hold no longer blocks");
  ev = signed(paidEvent("evt_1", body.ref), WHSEC, w.now);
  assert.equal((await H.webhook(w.ctx(), ev.raw, ev.header)).body.outcome, "needs-refund");
  const day = await bookingsOn(w, MON);
  const late = day.find((x) => x.id === body.ref);
  assert.equal(late.status, "cancelled"); assert.equal(late.needsRefund, true); assert.equal(late.payments.length, 1);
  assert.equal(day.filter((x) => blocks(x, w.now)).length, 1, "never two people in one slot");
  assert.equal((await w.store.get(K.unreconciled)).length, 1);
  assert.equal(w.sent.length, 0, "no confirmation for an appointment that is not happening");
});

test("money: a payment for a booking that does not exist is kept for a human, not dropped", async () => {
  const w = await world();
  const ev = signed(paidEvent("evt_1", "CAS-DEADBEEF"), WHSEC, w.now);
  const r = await H.webhook(w.ctx(), ev.raw, ev.header);
  assert.equal(r.status, 200); assert.equal(r.body.outcome, "unreconciled");
  assert.equal((await w.store.get(K.unreconciled))[0].bookingId, "CAS-DEADBEEF");
});

test("money: the webhook function reads the raw stream and never req.body", async () => {
  const src = fs.readFileSync(path.join(__dirname, "..", "site", "api", "salon", "stripe-webhook.js"), "utf8");
  const code = src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
  assert.ok(!/req\.body/.test(code), "touching req.body makes Vercel parse the body");
  const { rawBody } = require(path.join(__dirname, "..", "site", "api", "salon", "stripe-webhook.js"));
  const { Readable } = require("node:stream");
  const bytes = Buffer.from('{"a": 1 ,  "b":"£"}');
  assert.deepEqual(await rawBody(Readable.from([bytes.subarray(0, 5), bytes.subarray(5)])), bytes);
});

test("money: only the webhook path writes a paid payment", () => {
  const src = fs.readFileSync(path.join(LIB, "handlers.js"), "utf8");
  const writers = src.split("\n").filter((line) => /status:\s*"paid"/.test(line) && /push|=/.test(line) && !/some\(|find\(/.test(line));
  assert.equal(writers.length, 1, "exactly one line may record a paid payment:\n" + writers.join("\n"));
  const fn = src.slice(src.indexOf("async function markPaid"), src.indexOf("async function release"));
  assert.ok(fn.includes(writers[0].trim()), "and it is inside markPaid, which only the verified webhook calls");
  assert.equal((src.match(/markPaid\(/g) || []).length, 2, "markPaid: one definition, one call");
});

// ---- the store ----------------------------------------------------------------------------------
test("store: a writer that lost its lock writes nothing; a lock is released only by its owner", async () => {
  const s = new MemoryStore();
  await s.set("k", { n: 1 });
  assert.equal(await s.lock("k", "mine"), true);
  assert.equal(await s.lock("k", "theirs"), false);
  await s.release("k", "theirs");                                   // not the owner: no effect
  assert.equal(await s.lock("k", "theirs"), false);
  assert.equal(await s.commit(["k"], "theirs", { k: { n: 99 } }), false);
  assert.deepEqual(await s.get("k"), { n: 1 });
  assert.equal(await s.commit(["k"], "mine", { k: { n: 2 } }), true);
  assert.deepEqual(await s.get("k"), { n: 2 });
  assert.equal(await s.lock("k", "theirs"), true, "committing released it");
});

test("store: transactions on the same key run one at a time, and a refusal writes nothing", async () => {
  const s = new MemoryStore();
  await Promise.all(Array.from({ length: 12 }, () => transact(s, ["n"], (cur) => ({ writes: { n: (cur.n || 0) + 1 } }))));
  assert.equal(await s.get("n"), 12);
  await assert.rejects(transact(s, ["n"], () => { throw new Refused({ code: "student-busy" }); }), (e) => e.detail.code === "student-busy");
  assert.equal(await s.get("n"), 12);
  assert.equal(await transact(s, ["n"], () => ({ result: "read only" })), "read only");
  assert.equal(await s.lock("n", "next"), true, "the lock was released after a refusal and after a read");
});

test("store: every key is prefixed salon:", () => {
  for (const k of [K.day(MON), K.ref("CAS-1"), K.students, K.patch("abc"), K.evt("evt_1"), K.models, K.unreconciled, K.rl("x")]) assert.match(k, /^salon:/);
});

// ---- staff day sheet ----------------------------------------------------------------------------
async function signIn(w) {
  const r = await H.staff(w.ctx(), { action: "login", password: FULL_ENV.STAFF_PASSWORD }, freshReq());
  assert.equal(r.status, 200);
  const cookie = r.headers["Set-Cookie"].split(";")[0];
  return () => { const q = freshReq(); q.headers.cookie = cookie; return q; };
}

test("staff: no password set — refused; wrong password — refused; nothing readable without the cookie", async () => {
  const w = await world();
  assert.equal((await H.staff(w.ctx({ STAFF_PASSWORD: "" }), { action: "login", password: "" }, freshReq())).status, 503);
  assert.equal((await H.staff(w.ctx({ STAFF_PASSWORD: "short" }), { action: "login", password: "short" }, freshReq())).status, 503, "a weak placeholder is not a password");
  assert.equal((await H.staff(w.ctx(), { action: "login", password: "wrong" }, freshReq())).status, 401);
  assert.equal((await H.staff(w.ctx(), { action: "day", date: MON }, freshReq())).status, 401);
  const forged = freshReq(); forged.headers.cookie = "ca_salon_staff=eyJyb2xlIjoic3RhZmYiLCJleHAiOjk5OTk5OTk5OTl9.AAAA";
  assert.equal((await H.staff(w.ctx(), { action: "day", date: MON }, forged)).status, 401);
});

test("staff: sign-in sets an HttpOnly cookie that expires; repeated wrong passwords are throttled", async () => {
  const w = await world();
  const r = await H.staff(w.ctx(), { action: "login", password: FULL_ENV.STAFF_PASSWORD }, freshReq());
  assert.match(r.headers["Set-Cookie"], /HttpOnly; Secure; SameSite=Strict/);
  const req = await signIn(w);
  assert.equal((await H.staff(w.ctx(), { action: "day", date: MON }, req())).status, 200);
  w.now += 13 * 3600000;
  assert.equal((await H.staff(w.ctx(), { action: "day", date: MON }, req())).status, 401, "twelve hours, then sign in again");
  const one = REQ("10.9.9.9");
  for (let i = 0; i < 10; i += 1) assert.equal((await H.staff(w.ctx(), { action: "login", password: "guess" + i }, one)).status, 401);
  assert.equal((await H.staff(w.ctx(), { action: "login", password: FULL_ENV.STAFF_PASSWORD }, one)).status, 429);
});

test("staff: the day lists bookings with the learners; status moves forward only, on the current version", async () => {
  const w = await world(); const req = await signIn(w);
  const { body } = await H.book(w.ctx(), order({ serviceId: "patch-test", who: "l1", forProduct: "colour" }), freshReq());
  let day = (await H.staff(w.ctx(), { action: "day", date: MON }, req())).body;
  assert.equal(day.bookings.length, 1); assert.equal(day.students.length, 4);
  const b = day.bookings[0];
  assert.equal(b.client.name, CLIENT.name); assert.deepEqual(b.next, ["arrived", "no_show", "cancelled"]);
  assert.equal((await H.staff(w.ctx(), { action: "status", id: body.ref, v: b.v, status: "completed" }, req())).body.code, "bad-transition");
  assert.equal((await H.staff(w.ctx(), { action: "status", id: body.ref, v: b.v + 5, status: "arrived" }, req())).body.code, "stale");
  const ok1 = await H.staff(w.ctx(), { action: "status", id: body.ref, v: b.v, status: "arrived" }, req());
  assert.equal(ok1.status, 200); assert.equal(ok1.body.booking.status, "arrived");
  assert.equal((await H.staff(w.ctx(), { action: "status", id: body.ref, v: b.v, status: "in_progress" }, req())).body.code, "stale", "a second screen on the old version is refused");
});

test("staff: completing a patch-test appointment creates the record that unlocks colour 48 hours later", async () => {
  const w = await world();
  const colour = (start, date) => order({ serviceId: "root-colour", date: date || WED, start, consultation: { reaction: false }, consent: { terms: true, health: true } });
  assert.equal((await H.book(w.ctx(), colour(at(11)), freshReq())).body.code, "patch-none");
  const { body } = await H.book(w.ctx(), order({ serviceId: "patch-test", who: "l1", forProduct: "colour", start: at(10) }), freshReq());
  w.now = T.instantOf(MON, at(10));                                    // the day of the test
  const req = await signIn(w);
  let v = (await bookingsOn(w, MON))[0].v;
  for (const status of ["arrived", "in_progress", "completed"]) {
    const r = await H.staff(w.ctx(), { action: "status", id: body.ref, v, status }, req());
    assert.equal(r.status, 200, status); v = r.body.booking.v;
  }
  // Wednesday 09:30 is 47.5 hours after Monday 10:00; Wednesday 10:00 is exactly 48
  assert.equal((await H.book(w.ctx(), colour(at(9, 30)), freshReq())).body.code, "patch-too-recent");
  const offered = await H.availability(w.ctx(), { serviceId: "root-colour", who: "l2", under16: "false", from: MON, email: CLIENT.email }, freshReq());
  assert.equal(offered.status, 200);
  const first = offered.body.days.flatMap((d) => d.slots.map((s) => ({ date: d.date, start: s.start })))[0];
  assert.ok(T.instantOf(first.date, first.start) - w.now >= 48 * 3600000, "nothing is offered inside 48 hours of the test");
  assert.equal((await H.book(w.ctx(), colour(first.start, first.date), freshReq())).status, 200);
});

test("staff: a patch test done elsewhere in the salon can be recorded by hand — never in the future", async () => {
  const w = await world(); const req = await signIn(w);
  assert.equal((await H.staff(w.ctx(), { action: "patch-add", email: CLIENT.email, product: "colour", testedOn: "2027-02-01" }, req())).body.code, "details");
  assert.equal((await H.staff(w.ctx(), { action: "patch-add", email: CLIENT.email, product: "glitter", testedOn: "2027-01-05" }, req())).body.code, "details");
  assert.equal((await H.staff(w.ctx(), { action: "patch-add", email: CLIENT.email, product: "colour", testedOn: "2027-01-05" }, req())).status, 200);
  const r = await H.book(w.ctx(), order({ serviceId: "root-colour", consultation: { reaction: false }, consent: { terms: true, health: true } }), freshReq());
  assert.equal(r.status, 200);
});

test("staff: a move is re-checked by the same rule — a clash is refused, a free time is taken", async () => {
  const w = await world(); const req = await signIn(w);
  const a = (await H.book(w.ctx(), order({ start: at(10) }), freshReq())).body.ref;
  const b = (await H.book(w.ctx(), order({ start: at(13), client: { name: "Mr One O'Clock", email: "one@example.com" } }), freshReq())).body.ref;
  const vb = (await bookingsOn(w, MON)).find((x) => x.id === b).v;
  const clash = await H.staff(w.ctx(), { action: "move", id: b, v: vb, toDate: MON, toStart: at(10, 30) }, req());
  assert.equal(clash.status, 409); assert.equal(clash.body.code, "student-busy");
  assert.equal((await H.staff(w.ctx(), { action: "move", id: b, v: vb, toDate: TUE, toStart: at(10) }, req())).body.code, "closed-day");
  const moved = await H.staff(w.ctx(), { action: "move", id: b, v: vb, toDate: WED, toStart: at(10) }, req());
  assert.equal(moved.status, 200);
  assert.equal((await bookingsOn(w, MON)).length, 1); assert.equal((await bookingsOn(w, WED))[0].id, b);
  assert.equal((await w.store.get(K.ref(b))).date, WED);
  assert.equal((await H.staff(w.ctx(), { action: "move", id: b, v: vb, toDate: MON, toStart: at(14) }, req())).body.code, "stale");
  assert.ok(a);
});

test("staff: a resize is re-checked too — it cannot run into the learner's next client or past closing", async () => {
  const w = await world(); const req = await signIn(w);
  const a = (await H.book(w.ctx(), order({ start: at(10) }), freshReq())).body.ref;
  const first = (await bookingsOn(w, MON))[0];
  await H.book(w.ctx(), order({ start: first.start + first.minutes + 10, client: { name: "Ms Straight After", email: "after@example.com" } }), freshReq());
  const longer = await H.staff(w.ctx(), { action: "resize", id: a, v: first.v, minutes: first.minutes + 15 }, req());
  assert.equal(longer.body.code, "student-busy");
  const ok10 = await H.staff(w.ctx(), { action: "resize", id: a, v: first.v, minutes: first.minutes + 10 }, req());
  assert.equal(ok10.status, 200); assert.equal(ok10.body.booking.minutes, first.minutes + 10);
  assert.equal((await H.staff(w.ctx(), { action: "resize", id: a, v: ok10.body.booking.v, minutes: 7 }, req())).body.code, "bad-request");
});

test("staff: the learner list is saved on the current version, with levels the policy knows", async () => {
  const w = await world(); const req = await signIn(w);
  const list = [{ name: "Learner Five", level: "l2", days: ["mon"] }];
  assert.equal((await H.staff(w.ctx(), { action: "students-save", v: 0, list }, req())).body.code, "stale");
  assert.equal((await H.staff(w.ctx(), { action: "students-save", v: 1, list: [{ name: "Learner Six", level: "l7" }] }, req())).body.code, "details");
  const r = await H.staff(w.ctx(), { action: "students-save", v: 1, list }, req());
  assert.equal(r.status, 200); assert.match(r.body.students[0].id, /^st_[0-9a-f]{8}$/); assert.equal(r.body.studentsV, 2);
});

test("staff: consultation answers are opened only on request, and the look is logged", async () => {
  const w = await world(); const req = await signIn(w);
  await H.staff(w.ctx(), { action: "patch-add", email: CLIENT.email, product: "colour", testedOn: "2027-01-05" }, req());
  const { body } = await H.book(w.ctx(), order({ serviceId: "root-colour", consultation: { reaction: false, notes: "Sensitive scalp" }, consent: { terms: true, health: true } }), freshReq());
  const day = (await H.staff(w.ctx(), { action: "day", date: MON }, req())).body;
  assert.equal(day.bookings[0].hasConsultation, true);
  assert.ok(!JSON.stringify(day).includes("Sensitive scalp"), "the day list does not carry the answers");
  assert.equal((await H.staff(w.ctx(), { action: "consultation", id: body.ref }, freshReq())).status, 401);
  const seen = await H.staff(w.ctx(), { action: "consultation", id: body.ref }, req());
  assert.equal(seen.body.consultation.notes, "Sensitive scalp");
  assert.ok((await bookingsOn(w, MON))[0].log.some((x) => x.what === "consultation viewed" && x.by === "staff"));
});

// ---- model register -----------------------------------------------------------------------------
test("models: a name is stored and the academy is emailed; with nowhere to put it, the visitor is told", async () => {
  const w = await world();
  const entry = { name: "Mx Model Volunteer", email: "model@example.com", interests: ["colour", "nonsense"], days: "Mondays", consent: true, lang: "en" };
  const r = await H.models(w.ctx(), entry, freshReq());
  assert.equal(r.status, 200);
  const saved = await w.store.get(K.models);
  assert.equal(saved.length, 1); assert.deepEqual(saved[0].interests, ["colour"]);
  assert.deepEqual(w.sent[0].to, ["hello@clwydianacademy.co.uk"]);
  assert.equal((await H.models(w.ctx(), Object.assign({}, entry, { consent: false }), freshReq())).body.code, "consent-terms");
  assert.equal((await H.models(w.ctx(), Object.assign({}, entry, { email: "x" }), freshReq())).body.code, "details");
  const dead = await world({ noStore: true });
  const none = await H.models(dead.ctx({ RESEND_API_KEY: "" }), entry, freshReq());
  assert.equal(none.status, 503); assert.equal(none.body.contact, "hello@clwydianacademy.co.uk");
  assert.equal((await H.models(dead.ctx(), entry, freshReq())).status, 200, "no database, but the email went: accepted");
});

// =================================================================================================
// The built pages
// =================================================================================================
const SITE_DIR = path.join(__dirname, "..", "site");
const SALON_PAGES = ["salon", "salon/prices", "salon/book", "salon/models", "salon/terms", "cy/salon", "cy/salon/prisiau", "cy/salon/archebu", "cy/salon/modelau", "cy/salon/telerau", "staff"];
const pageHtml = (p) => fs.readFileSync(path.join(SITE_DIR, p, "index.html"), "utf8");
/** What a reader sees: the body, without scripts (the journey's strings legitimately hold {tokens}). */
const visible = (html) => html.slice(html.indexOf("<body")).replace(/<script[\s\S]*?<\/script>/g, " ").replace(/<[^>]+>/g, " ");

test("pages: every salon page is built, and nothing the generator left unfinished is visible", () => {
  for (const p of SALON_PAGES) {
    const text = visible(pageHtml(p));
    assert.ok(!/\{[a-z_]+\}/.test(text), p + ": an unfilled {token} is visible: " + (text.match(/\{[a-z_]+\}/) || [""])[0]);
    assert.ok(!/\[\('|'\)\]|\bNone\b|\bundefined\b|<function/.test(text), p + ": generator debris is visible: " + (text.match(/\[\('.{0,40}|'\)\]|\bNone\b|\bundefined\b/) || [""])[0]);
  }
});

test("pages: while any policy value is a placeholder, salon pages are noindex, absent from the sitemap, and print no price", () => {
  const sitemap = fs.readFileSync(path.join(SITE_DIR, "sitemap.xml"), "utf8");
  const placeholders = unconfirmed(RAW).length > 0;
  for (const p of SALON_PAGES.filter((x) => x !== "staff")) {
    const html = pageHtml(p), inMap = sitemap.includes("<loc>https://www.clwydianacademy.co.uk/" + p + "/</loc>");
    assert.equal(/<meta name="robots" content="noindex/.test(html), placeholders, p + " robots");
    assert.equal(inMap, !placeholders, p + " sitemap");
    if (placeholders) assert.ok(!/£|&pound;/.test(visible(html)), p + ": a placeholder price is printed");
  }
  assert.match(pageHtml("staff"), /<meta name="robots" content="noindex, nofollow">/, "the day sheet is never indexed");
  assert.ok(!sitemap.includes("/staff/"));
});

test("pages: robots.txt and vercel.json keep /staff/ and /api/ out of search", () => {
  const robots = fs.readFileSync(path.join(SITE_DIR, "robots.txt"), "utf8");
  assert.match(robots, /^Disallow: \/staff\/$/m); assert.match(robots, /^Disallow: \/api\/$/m);
  const v = JSON.parse(fs.readFileSync(path.join(SITE_DIR, "vercel.json"), "utf8"));
  for (const src of ["/staff/(.*)", "/api/(.*)"]) assert.ok(v.headers.some((h) => h.source === src && h.headers.some((x) => x.key === "X-Robots-Tag" && /noindex/.test(x.value))), src);
});

test("pages: HairSalon structured data is tied to the academy's own Organization, with no parent and no phone", () => {
  for (const p of ["salon", "cy/salon"]) {
    const blocks = [...pageHtml(p).matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map((m) => JSON.parse(m[1]));
    const org = blocks.find((b) => b["@id"] === "https://www.clwydianacademy.co.uk/#organization" && b.name);
    const salon = blocks.find((b) => b["@type"] === "HairSalon");
    const link = blocks.find((b) => b.department);
    assert.ok(org && salon && link, p + ": Organization, HairSalon and the department link are all present");
    assert.equal(link["@id"], org["@id"]); assert.equal(link.department["@id"], salon["@id"]);
    assert.equal(salon.address.addressLocality, "St Asaph"); assert.equal(salon.address.streetAddress, undefined, "no street address until the premises are confirmed");
    assert.equal(salon.email, "hello@clwydianacademy.co.uk");
    const flat = JSON.stringify(blocks);
    assert.ok(!/parentOrganization|"telephone"|"founder"|"Person"/.test(flat));
    if (unconfirmed(RAW).some((x) => x.startsWith("opening"))) assert.equal(salon.openingHoursSpecification, undefined, "no opening hours until they are confirmed");
  }
});

test("pages: the journey has no words of its own, and both languages carry the same strings", () => {
  const keys = (p) => { const d = JSON.parse(pageHtml(p).match(/<script type="application\/json" id="salon-data">([\s\S]*?)<\/script>/)[1]); return [d, Object.keys(d.t).sort()]; };
  const [en, enKeys] = keys("salon/book"), [cy, cyKeys] = keys("cy/salon/archebu");
  assert.deepEqual(enKeys, cyKeys); assert.equal(en.lang, "en"); assert.equal(cy.lang, "cy");
  const js = fs.readFileSync(path.join(SITE_DIR, "assets", "js", "salon-book.js"), "utf8");
  for (const used of new Set([...js.matchAll(/\bS\.([a-z_0-9]+)/g)].map((m) => m[1]))) assert.ok(enKeys.includes(used), "salon-book.js uses S." + used + ", which the page does not supply");
  const [men, menKeys] = keys("salon/models"), [, mcyKeys] = keys("cy/salon/modelau");
  assert.deepEqual(menKeys, mcyKeys); assert.ok(men.groups.colour);
});

test("pages: the page arithmetic and the engine agree on the length of every service at every level", () => {
  const { execFileSync } = require("node:child_process");
  const out = execFileSync("python3", ["-c", [
    "import json, sys", "sys.path.insert(0, sys.argv[1])", "import salon", "p = salon.raw()",
    "print(json.dumps({s['id'] + '/' + l: salon.minutes_for(p, s, l) for s in p['services'] for l in salon.LEVELS if salon.offered(p, s, l)}))",
  ].join("\n"), path.join(__dirname, "..", "website", "_src")], { encoding: "utf8" });
  const py = JSON.parse(out);
  let n = 0;
  for (const s of P.services) for (const l of P.levelIds) {
    const q = quote(P, { serviceId: s.id, level: l });
    if (!q.ok) { assert.equal(py[s.id + "/" + l], undefined, s.id + "/" + l + " is offered on the page but not by the engine"); continue; }
    assert.equal(py[s.id + "/" + l], q.minutes, s.id + "/" + l); n += 1;
  }
  assert.equal(n, Object.keys(py).length); assert.ok(n > 30);
});
