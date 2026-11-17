/* Clwydian Academy training salon — the request handlers.
 *
 * All the logic is here; site/api/salon/*.js are thin shells that hand a request to one of
 * these and write the answer. Each handler takes a context — { env, store, now, fetch, policy }
 * — so scripts/test_salon_rules.js can run the real code against a store in memory, a fixed
 * clock and a fake Stripe, with nothing leaving the machine.
 *
 * DEGRADE, NEVER FAIL SILENTLY. If something this needs is missing (the database, a Stripe key,
 * the encryption key, an unconfirmed policy value), the answer is a plain 503 with
 * code "unavailable", the reason, and the academy's email address — and the page shows it.
 */
"use strict";
const crypto = require("node:crypto");
const T = require("./time");
const { policy: loadPolicy } = require("./policy");
const { quote, segmentsFor, total } = require("./quote");
const { feasible, blocks, endOf } = require("./feasible");
const A = require("./availability");
const { transact, Refused, storeFromEnv, K } = require("./store");
const S = require("./seal");
const stripe = require("./stripe");
const auth = require("./auth");
const mail = require("./email");
const M = require("./messages");

const CONSENT_VERSION = "2026-11";
const EVENT_MEMORY_SECONDS = 7 * 24 * 60 * 60;
const EMAIL_RE = /^[^\s@<>"']{1,64}@[^\s@<>"']{1,190}\.[^\s@<>"']{2,}$/;

function context(over) {
  const env = (over && over.env) || process.env;
  return Object.assign({
    env,
    store: storeFromEnv(env),
    now: () => Date.now(),
    fetch: (...a) => globalThis.fetch(...a),
    policy: (over && over.policy) || loadPolicy(),
  }, over || {});
}

const ok = (body, headers) => ({ status: 200, body: Object.assign({ ok: true }, body), headers });
const lang = (v) => (v === "cy" ? "cy" : "en");
function fail(status, code, l, detail) {
  return { status, body: Object.assign({ ok: false, code, message: M.say(code, l, detail), contact: mail.CONTACT }, detail && detail.reason ? { reason: detail.reason } : {}) };
}
const unavailable = (l, reason) => fail(503, "unavailable", l, { reason });

function refusal(ctx, r, l) {
  const p = ctx.policy;
  const detail = Object.assign({ hours: p.patch_test.min_hours, months: p.patch_test.max_months }, r);
  return { status: 409, body: { ok: false, code: r.code, message: M.say(r.code, l, detail), contact: mail.CONTACT } };
}

/** Whether the salon can take bookings at all, and why not. */
function openState(ctx) {
  const env = ctx.env, p = ctx.policy;
  const placeholders = p.unconfirmed > 0;          // placeholders and PM drafts alike: neither is confirmed
  // Placeholders can be exercised on a preview deployment, with test keys. Never in production.
  const allowed = env.SALON_ALLOW_PLACEHOLDERS === "1" && env.VERCEL_ENV !== "production";
  let reason = null;
  if (placeholders && !allowed) reason = "not-confirmed";
  else if (env.SALON_BOOKING_OPEN !== "1") reason = "not-open";
  else if (!ctx.store) reason = "no-store";
  const key = stripe.secretKey(env);
  const payments = Boolean(key && stripe.webhookSecret(env)) && !(placeholders && stripe.isLiveKey(key));
  return { open: reason === null, reason, placeholders, payments, encryption: Boolean(S.keyFrom(env)) };
}

function ipOf(req) {
  const h = (req && req.headers) || {};
  return String(h["x-forwarded-for"] || h["x-real-ip"] || "unknown").split(",")[0].trim().slice(0, 64);
}
async function limited(ctx, name, req, limit, windowSeconds) {
  if (!ctx.store) return false;
  try { return (await ctx.store.bump(K.rl(name + ":" + ipOf(req)), windowSeconds)) > limit; }
  catch { return false; }                       // a counter that cannot be read must not block a booking
}
const SITE_HOST = /^(?:(?:www\.)?clwydianacademy\.co\.uk|[a-z0-9-]+\.vercel\.app|localhost(?::\d+)?)$/i;
/** Same-origin only, for anything that writes. */
function sameOrigin(req) {
  const h = (req && req.headers) || {};
  const from = h.origin || h.referer;
  if (!from) return false;
  try { const host = new URL(from).host; return SITE_HOST.test(host) && host === String(h["x-forwarded-host"] || h.host || "").split(",")[0].trim(); }
  catch { return false; }
}
const text = (v, max) => String(v === undefined || v === null ? "" : v).replace(/[\u0000-\u001f\u007f]+/g, " ").trim().slice(0, max);
const bool = (v) => (v === true || v === "true" || v === "1" ? true : v === false || v === "false" || v === "0" ? false : null);
const ageOf = (v) => (v === "u12" || v === "u16" || v === "adult" ? v : null);
/** The client's answers and extras, from a query string or a JSON body. Only known ids survive. */
function choicesOf(p, service, src) {
  let answers = src.answers;
  if (typeof answers === "string") { try { answers = JSON.parse(answers); } catch { answers = {}; } }
  const clean = {};
  for (const q of service.questions || []) if (answers && typeof answers[q] === "string") clean[q] = answers[q].slice(0, 30);
  let addons = src.addons;
  if (typeof addons === "string") addons = addons.split(",");
  addons = (Array.isArray(addons) ? addons : []).map((x) => String(x).slice(0, 30)).filter((x) => p.addons[x]);
  return { answers: clean, addons, concession: bool(src.concession) === true };
}
/** The record a free test or consultation appointment creates when staff complete it. */
function recordFor(p, service, raw) {
  const v = text(raw, 60);
  if (service.is_patch_test) return p.patch_test.products[v] ? v : null;
  if (service.is_consultation) { const m = /^consult:(.+)$/.exec(v); const t = m && p.serviceById.get(m[1]); return t && t.consultation_first ? v : null; }
  return null;
}

async function studentsOf(ctx) { return ((await ctx.store.get(K.students)) || { v: 0, list: [] }); }
async function patchFor(ctx, email) {
  const key = S.keyFrom(ctx.env);
  if (!key || !EMAIL_RE.test(String(email || ""))) return { clientKey: null, records: [] };
  const clientKey = S.clientKey(key, email);
  return { clientKey, records: ((await ctx.store.get(K.patch(clientKey))) || { records: [] }).records };
}
const dayDoc = (doc) => doc || { v: 0, bookings: [] };
/** A booking as it stands now, read without a lock — for deciding what else to read. */
async function peek(ctx, id) {
  const ref = id ? await ctx.store.get(K.ref(id)) : null;
  return ref ? dayDoc(await ctx.store.get(K.day(ref.date))).bookings.find((x) => x.id === id) || null : null;
}
/** The patch-test records of the client a booking belongs to. */
async function patchOfBooking(ctx, bk) {
  return bk && bk.clientKey ? ((await ctx.store.get(K.patch(bk.clientKey))) || { records: [] }).records : [];
}
/** A stored booking, as a candidate for the one rule. */
const asCandidate = (bk) => Object.assign({}, bk, { guardianConsent: Boolean(bk.guardian) });

// ---------------------------------------------------------------------------------------------
// GET /api/salon/quote — what the journey needs to draw itself
// ---------------------------------------------------------------------------------------------
function config(ctx) {
  const p = ctx.policy, state = openState(ctx);
  const body = { state: { open: state.open, reason: state.reason, payments: state.payments, placeholders: state.placeholders },
    contact: mail.CONTACT, services: [], levels: [], groups: p.groups, products: {},
    rules: { cancelHours: p.cancel_window_hours, patchMinHours: p.patch_test.min_hours, patchMaxMonths: p.patch_test.max_months,
      stripDays: p.booking.strip_days, noticeHours: p.booking.min_notice_hours } };
  if (!state.open) return ok(body);            // nothing unconfirmed is ever sent to a browser
  body.levels = p.levelIds.map((id) => ({ id, name: p.levels[id].name }));
  for (const id of Object.keys(p.patch_test.products)) body.products[id] = p.patch_test.products[id].name;
  body.questions = {};
  for (const id of Object.keys(p.questions)) body.questions[id] = { ask: p.questions[id].ask, options: p.questions[id].options.map((o) => ({ id: o.id, label: o.label, levels: p.levelIds.filter((l) => o.add[l] !== undefined) })) };
  body.concession = { percent: p.concession.percent, days: p.concession.days, who: p.concession.who };
  body.age = { under12: p.age.under12_services, under16: p.age.under16_services };
  body.services = p.services.map((s) => ({
    id: s.id, group: s.group, name: s.name, note: s.note || null, chemical: s.chemical || null, patchProduct: s.patch_test_product || null,
    isPatchTest: s.is_patch_test === true, isConsultation: s.is_consultation === true, consultFirst: s.consultation_first === true,
    quoteOnly: s.quote_only === true, childrenOnly: s.children_only === true, concession: s.concession === true,
    restricted: Boolean(s.chemical && p.age.restricted_chemicals.includes(s.chemical)),
    questions: s.questions || [],
    addons: Object.keys(p.addons).filter((a) => p.addons[a].for.includes(s.id)).map((a) => ({ id: a, name: p.addons[a].name, prices: p.addons[a].prices })),
    // "from" figures: the service with no extras and the cheapest answers
    levels: s.levels.map((l) => ({ id: l, from: s.prices[l], minutes: total(segmentsFor(p, s, l, 0)),
      qualifiedMinutes: total(segmentsFor(p, s, p.levelIds[p.levelIds.length - 1], 0)) })),
  }));
  return ok(body);
}

// POST /api/salon/quote
function quoteHandler(ctx, body) {
  const l = lang(body && body.lang);
  if (!openState(ctx).open) return unavailable(l, openState(ctx).reason);
  const p = ctx.policy, service = p.serviceById.get(body && body.serviceId);
  if (!service) return fail(400, "unknown-service", l);
  const c = choicesOf(p, service, body);
  // one answer per level the service is offered at: the price and length there, or why not
  const levels = service.levels.map((level) => {
    const q = quote(p, { serviceId: service.id, level, answers: c.answers, addons: c.addons });
    return q.ok ? { level, ok: true, minutes: q.minutes, qualifiedMinutes: q.qualifiedMinutes, price: q.price, deposit: q.deposit }
      : { level, ok: false, code: q.code, needs: q.needs || null, missing: q.missing || null };
  });
  return ok({ serviceId: service.id, levels });
}

// ---------------------------------------------------------------------------------------------
// GET /api/salon/availability
// ---------------------------------------------------------------------------------------------
async function availability(ctx, query, req) {
  const l = lang(query.lang), p = ctx.policy, state = openState(ctx);
  if (!state.open) return unavailable(l, state.reason);
  if (await limited(ctx, "avail", req, 120, 600)) return fail(429, "rate", l);
  const service = p.serviceById.get(query.serviceId);
  if (!service) return fail(400, "unknown-service", l);
  const who = query.who === "any" || p.levels[query.who] ? query.who : null;
  if (!who) return fail(400, "unknown-level", l);
  const age = ageOf(query.age);
  if (!age) return fail(400, "age-missing", l);
  const request = Object.assign({ serviceId: service.id, who, age, guardianConsent: bool(query.guardianConsent) === true }, choicesOf(p, service, query));
  const now = ctx.now();
  try {
    const students = (await studentsOf(ctx)).list;
    const patch = service.patch_test_product || service.consultation_first ? (await patchFor(ctx, query.email)).records : [];
    const fctx = { policy: p, students, patch, now };
    const blocked = A.clientBlock(request, fctx);
    if (blocked) return refusal(ctx, blocked, l);
    const today = T.isoDate(now);
    const from = T.isDate(query.from) && query.from > today ? query.from : today;
    const last = T.addDays(today, p.booking.horizon_days);
    const scan = async (start, n) => {
      const dates = [];
      for (let i = 0; i < n; i += 1) { const d = T.addDays(start, i); if (d <= last) dates.push(d); }
      // a day outside term, or one the salon does not open on, is never read from the store
      const openDay = (d) => (p.opening.sessions[T.dayKey(d)] || []).length > 0
        && p.opening.terms.some((t) => d >= t.from && d <= t.to) && !p.opening.closures.includes(d);
      const docs = await Promise.all(dates.map((d) => (openDay(d) ? ctx.store.get(K.day(d)) : null)));
      return dates.map((d, i) => {
        const slots = openDay(d) ? A.slotsForDate(request, d, dayDoc(docs[i]).bookings, fctx) : [];
        return { date: d, open: openDay(d), fullness: openDay(d) ? A.fullness(slots.length) : "closed",
          slots: slots.map((s) => ({ start: s.start, end: s.end, level: s.level, s: s.studentId, minutes: s.minutes, qualifiedMinutes: s.qualifiedMinutes,
            price: s.price, fullPrice: s.fullPrice, concession: s.concession, deposit: s.deposit, period: s.period })) };
      });
    };
    const days = await scan(from, p.booking.strip_days);
    let next = days.find((d) => d.slots.length) || null;
    for (let start = T.addDays(from, p.booking.strip_days); !next && start <= last; start = T.addDays(start, 14)) {
      next = (await scan(start, 14)).find((d) => d.slots.length) || null;
    }
    return ok({ from, days, next: next ? { date: next.date, start: next.slots[0].start } : null });
  } catch (e) {
    console.error("[salon availability]", e && e.message);
    return unavailable(l, "store-error");
  }
}

// ---------------------------------------------------------------------------------------------
// POST /api/salon/book
// ---------------------------------------------------------------------------------------------
const newRef = () => "CAS-" + crypto.randomBytes(4).toString("hex").toUpperCase();

async function book(ctx, body, req) {
  const b = body || {}, l = lang(b.lang), p = ctx.policy, state = openState(ctx);
  if (!state.open) return unavailable(l, state.reason);
  if (text(b.website, 10)) return ok({ ref: "CAS-00000000", status: "confirmed" });      // honeypot: a script gets a plausible nothing
  if (!sameOrigin(req)) return fail(403, "bad-request", l);
  if (await limited(ctx, "book", req, 12, 3600)) return fail(429, "rate", l);

  const service = p.serviceById.get(b.serviceId);
  if (!service) return fail(400, "unknown-service", l);
  const who = b.who === "any" || p.levels[b.who] ? b.who : null;
  if (!who) return fail(400, "unknown-level", l);
  const start = Number(b.start);
  if (!T.isDate(b.date) || !Number.isInteger(start)) return fail(400, "bad-request", l);
  const age = ageOf(b.age);
  if (!age) return fail(400, "age-missing", l);
  const under16 = age !== "adult";
  const choices = choicesOf(p, service, b);

  const client = { name: text(b.client && b.client.name, 80), email: text(b.client && b.client.email, 254).toLowerCase(),
    phone: text(b.client && b.client.phone, 30) };
  if (client.name.length < 2 || !EMAIL_RE.test(client.email)) return fail(400, "details", l);
  if (!(b.consent && b.consent.terms === true)) return fail(400, "consent-terms", l);
  const guardian = under16 ? { name: text(b.guardian && b.guardian.name, 80), confirmed: Boolean(b.guardian && b.guardian.confirmed === true) } : null;
  const guardianConsent = Boolean(guardian && guardian.confirmed && guardian.name.length >= 2);

  // Consultation answers are health data: kept only with explicit consent, only encrypted.
  let consultation = null;
  if (service.chemical) {
    const c = b.consultation || {};
    const reaction = bool(c.reaction);
    if (reaction === null) return fail(400, "details", l);
    if (reaction === true) return fail(409, "consultation-needed", l);
    if (!(b.consent && b.consent.health === true)) return fail(400, "consent-health", l);
    consultation = { reaction, notes: text(c.notes, 600), history: text(c.history, 40) };
  }
  const dataKey = S.keyFrom(ctx.env);
  const needsRecords = service.patch_test_product || service.consultation_first || service.is_patch_test || service.is_consultation;
  if ((consultation || needsRecords) && !dataKey) return unavailable(l, "no-encryption");
  let patchProduct = null;                    // what this appointment, once completed, puts on record
  if (service.is_patch_test || service.is_consultation) {
    patchProduct = recordFor(p, service, b.forProduct);
    if (!patchProduct) return fail(400, "bad-request", l);
  }

  const now = ctx.now();
  let record, students, patch;
  try {
    students = (await studentsOf(ctx)).list;
    patch = needsRecords ? await patchFor(ctx, client.email) : { clientKey: null, records: [] };
  } catch (e) { console.error("[salon book]", e && e.message); return unavailable(l, "store-error"); }

  // The learner the client was offered first, then anyone else at the level they chose.
  const people = A.candidatesFor(p, service, who, students);
  people.sort((x, y) => (y.id === b.s) - (x.id === b.s));
  if (!people.length) return refusal(ctx, { code: "student-unknown" }, l);
  const quoteAt = (level) => quote(p, { serviceId: service.id, level, answers: choices.answers, addons: choices.addons, concession: choices.concession, date: b.date });
  if (!state.payments && people.some((x) => { const q = quoteAt(x.level); return q.ok && q.deposit > 0; })) return unavailable(l, "no-payments");

  const id = newRef();
  const fctx = { policy: p, students, patch: patch.records, now };
  try {
    record = await transact(ctx.store, [K.day(b.date)], (cur) => {
      const doc = dayDoc(cur[K.day(b.date)]);
      let why = null;
      for (const student of people) {
        const q = quoteAt(student.level);
        if (!q.ok) { why = why || { code: q.code }; continue; }
        const cand = A.candidateFrom(q, { id, date: b.date, start, studentId: student.id, age, guardianConsent });
        const no = feasible(cand, doc.bookings, fctx);            // THE check that counts — inside the lock
        if (no) { why = why || no; continue; }
        const held = q.deposit > 0;
        const rec = {
          id, v: 1, createdAt: new Date(now).toISOString(), lang: l,
          date: b.date, start, segments: q.segments, minutes: q.minutes,
          serviceId: service.id, level: student.level, studentId: student.id,
          price: q.price, fullPrice: q.fullPrice, concession: q.concession, deposit: q.deposit,
          answers: q.answers, addons: q.addons, needsLevel: q.needsLevel,
          chemical: q.chemical, patchProduct: q.patchProduct, consultFirst: q.consultFirst,
          patchFor: patchProduct, clientKey: patch.clientKey,
          status: held ? "held" : "confirmed", heldUntil: held ? now + p.hold_minutes * 60000 : null,
          age, guardian: guardianConsent ? { name: guardian.name, at: new Date(now).toISOString() } : null,
          client,
          consultation: consultation ? S.seal(dataKey, id, consultation) : null,
          consent: { terms: { at: new Date(now).toISOString(), version: CONSENT_VERSION },
            health: consultation ? { at: new Date(now).toISOString(), version: CONSENT_VERSION } : null },
          payments: [], log: [{ at: new Date(now).toISOString(), by: "client", what: "created" }],
        };
        return { writes: { [K.day(b.date)]: { v: doc.v + 1, bookings: [...doc.bookings, rec] }, [K.ref(id)]: { date: b.date } }, result: rec };
      }
      throw new Refused(why || { code: "student-busy" });
    });
  } catch (e) {
    if (e instanceof Refused) return refusal(ctx, e.detail, l);
    console.error("[salon book]", e && e.message);
    return unavailable(l, "store-error");
  }

  if (record.status === "confirmed") {
    await sendConfirmation(ctx, record);
    return ok({ ref: record.id, status: "confirmed" });
  }
  try {
    const session = await stripe.createCheckout({
      key: stripe.secretKey(ctx.env), booking: record, base: stripe.returnBase(req && req.headers),
      paths: { book: l === "cy" ? "/cy/salon/archebu/" : "/salon/book/" }, holdUntil: record.heldUntil, fetchImpl: ctx.fetch,
      description: l === "cy"
        ? { name: "Blaendal — " + service.name.cy, detail: "Yn dod oddi ar eich bil ar y diwrnod. " + M.money(record.price - record.deposit) + " i'w dalu yn y salon." }
        : { name: "Deposit — " + service.name.en, detail: "Comes off your bill on the day. " + M.money(record.price - record.deposit) + " to pay in the salon." },
    });
    return ok({ ref: record.id, status: "held", checkout: session.url, heldUntil: record.heldUntil });
  } catch (e) {
    // No payment page, so no hold: free the slot rather than leave it blocked for half an hour.
    console.error("[salon book] checkout:", e && e.message);
    await change(ctx, record.id, (bk) => Object.assign(bk, { status: "cancelled", cancelReason: "checkout-failed" }), "system", "checkout failed").catch(() => {});
    return unavailable(l, "payments-error");
  }
}

/** Apply a change to one booking under its day's lock. `mutate` may throw Refused. */
async function change(ctx, id, mutate, by, what, extraKeys, extraWrites) {
  const ref = await ctx.store.get(K.ref(id));
  if (!ref) throw new Refused({ code: "not-found" });
  const now = ctx.now();
  return transact(ctx.store, [K.day(ref.date), ...(extraKeys || [])], (cur) => {
    const doc = dayDoc(cur[K.day(ref.date)]);
    const i = doc.bookings.findIndex((x) => x.id === id);
    if (i < 0) throw new Refused({ code: "not-found" });
    const before = doc.bookings[i];
    const after = mutate(JSON.parse(JSON.stringify(before)), doc, cur);
    if (!after) return { result: before };                                  // nothing to do
    after.v = before.v + 1;
    after.log = [...(after.log || []), { at: new Date(now).toISOString(), by, what }];
    const bookings = doc.bookings.slice(); bookings[i] = after;
    const writes = { [K.day(ref.date)]: { v: doc.v + 1, bookings } };
    if (extraWrites) Object.assign(writes, extraWrites(after, cur) || {});
    return { writes, result: after };
  });
}

async function sendConfirmation(ctx, record) {
  const p = ctx.policy, service = p.serviceById.get(record.serviceId);
  const l = lang(record.lang);
  const m = M.confirmation(record, service.name[l], p.levels[record.level].name[l], p, T.formatClock);
  const outcome = await mail.send(ctx.env, { to: record.client.email, subject: m.subject, text: m.text }, ctx.fetch);
  await change(ctx, record.id, (bk) => Object.assign(bk, { confirmationEmail: outcome }), "system", "confirmation email: " + outcome).catch(() => {});
  return outcome;
}

// GET /api/salon/book?ref= — what a returning client may see: status and time, never a name.
async function bookingStatus(ctx, query, req) {
  const l = lang(query.lang);
  if (!ctx.store) return unavailable(l, "no-store");
  if (await limited(ctx, "ref", req, 60, 600)) return fail(429, "rate", l);
  const id = text(query.ref, 20);
  if (!/^CAS-[0-9A-F]{8}$/.test(id)) return fail(404, "not-found", l);
  try {
    const ref = await ctx.store.get(K.ref(id));
    const bk = ref && dayDoc(await ctx.store.get(K.day(ref.date))).bookings.find((x) => x.id === id);
    if (!bk) return fail(404, "not-found", l);
    const now = ctx.now();
    const status = bk.status === "held" && !blocks(bk, now) ? "expired" : bk.status;
    return ok({ ref: bk.id, status, date: bk.date, start: bk.start, end: endOf(bk), serviceId: bk.serviceId, level: bk.level,
      price: bk.price, deposit: bk.deposit, depositPaid: bk.payments.some((x) => x.status === "paid") });
  } catch (e) { console.error("[salon ref]", e && e.message); return unavailable(l, "store-error"); }
}

// ---------------------------------------------------------------------------------------------
// POST /api/salon/stripe-webhook — the only code allowed to say a deposit was paid
// ---------------------------------------------------------------------------------------------
async function webhook(ctx, raw, signature) {
  const secret = stripe.webhookSecret(ctx.env);
  // No secret, no store: answer 503 so Stripe retries later. Nothing is ever marked paid.
  if (!secret || !ctx.store) return { status: 503, body: { ok: false, code: "unavailable" } };
  if (!stripe.verifySignature(raw, signature, secret, ctx.now())) return { status: 400, body: { ok: false, code: "bad-signature" } };
  let event;
  try { event = JSON.parse(Buffer.isBuffer(raw) ? raw.toString("utf8") : String(raw)); } catch { return { status: 400, body: { ok: false, code: "bad-body" } }; }
  if (!event || typeof event.id !== "string" || !event.data || !event.data.object) return { status: 400, body: { ok: false, code: "bad-body" } };
  if (await ctx.store.get(K.evt(event.id))) return ok({ received: true, duplicate: true });

  const o = event.data.object;
  const bookingId = text(o.client_reference_id || (o.metadata && o.metadata.booking_id), 20);
  let outcome = "ignored";
  if ((event.type === "checkout.session.completed" || event.type === "checkout.session.async_payment_succeeded") && o.payment_status === "paid") {
    outcome = await markPaid(ctx, bookingId, { amountPence: Number(o.amount_total) || 0, intent: text(o.payment_intent, 80), session: text(o.id, 80), eventId: event.id });
  } else if (event.type === "checkout.session.expired") {
    outcome = await release(ctx, bookingId);
  } else if (event.type === "charge.refunded") {
    outcome = await refunded(ctx, text(o.payment_intent, 80), Number(o.amount_refunded) || 0);
  }
  // Remembered only AFTER the work is done: if anything above threw, the answer is a 500 and
  // Stripe sends the event again.
  await ctx.store.set(K.evt(event.id), { type: event.type, outcome }, EVENT_MEMORY_SECONDS);
  return ok({ received: true, outcome });
}

async function unreconciled(ctx, entry) {
  await transact(ctx.store, [K.unreconciled], (cur) => ({ writes: { [K.unreconciled]: [...(cur[K.unreconciled] || []), entry].slice(-500) } }));
}

async function markPaid(ctx, bookingId, pay) {
  const now = ctx.now(), p = ctx.policy;
  const seen = await peek(ctx, bookingId);
  if (!seen) { await unreconciled(ctx, { at: new Date(now).toISOString(), why: "no such booking", bookingId, intent: pay.intent, amountPence: pay.amountPence }); return "unreconciled"; }
  const students = (await studentsOf(ctx)).list;
  const patch = await patchOfBooking(ctx, seen);
  let newlyConfirmed = false, result = "paid";
  const after = await change(ctx, bookingId, (bk, doc) => {
    if (bk.payments.some((x) => x.intent === pay.intent && x.status === "paid")) return null;     // Stripe sent it twice
    bk.payments.push({ phase: "deposit", status: "paid", amountPence: pay.amountPence, intent: pay.intent, session: pay.session, at: new Date(now).toISOString() });
    if (bk.status === "held" && blocks(bk, now)) {                        // paid inside the hold: the slot was theirs throughout
      bk.status = "confirmed"; bk.heldUntil = null; newlyConfirmed = true;
    } else if (bk.status === "held" || (bk.status === "cancelled" && bk.cancelReason === "hold-expired")) {
      // Paid after the hold ran out. The slot may have gone, so ask the one rule again — as
      // staff would, because the notice period was met when they booked.
      const taken = feasible(asCandidate(bk), doc.bookings, { policy: p, students, patch, now, actor: "staff" });
      if (taken === null) { bk.status = "confirmed"; bk.heldUntil = null; bk.cancelReason = undefined; newlyConfirmed = true; }
      else { bk.status = "cancelled"; bk.cancelReason = "paid-late-slot-gone"; bk.needsRefund = true; result = "needs-refund"; }
    } else if (bk.status === "cancelled") { bk.needsRefund = true; result = "needs-refund"; }
    return bk;
  }, "stripe", "deposit paid", null, (bk) => (pay.intent ? { ["salon:pi:" + pay.intent]: { id: bk.id } } : {}));
  if (result === "needs-refund") await unreconciled(ctx, { at: new Date(now).toISOString(), why: "paid after the slot was released — refund", bookingId, intent: pay.intent, amountPence: pay.amountPence });
  if (newlyConfirmed) await sendConfirmation(ctx, after);
  return result;
}

async function release(ctx, bookingId) {
  if (!bookingId || !(await ctx.store.get(K.ref(bookingId)))) return "ignored";
  await change(ctx, bookingId, (bk) => (bk.status === "held" ? Object.assign(bk, { status: "cancelled", cancelReason: "hold-expired", heldUntil: null }) : null), "stripe", "checkout expired");
  return "released";
}

async function refunded(ctx, intent, amountPence) {
  const hit = intent ? await ctx.store.get("salon:pi:" + intent) : null;
  if (!hit) return "ignored";
  await change(ctx, hit.id, (bk) => {
    const pay = bk.payments.find((x) => x.intent === intent);
    if (!pay || pay.refundedPence === amountPence) return null;
    pay.refundedPence = amountPence; bk.needsRefund = false;
    return bk;
  }, "stripe", "refunded");
  return "refunded";
}

// ---------------------------------------------------------------------------------------------
// POST /api/salon/models — the model register
// ---------------------------------------------------------------------------------------------
async function models(ctx, body, req) {
  const b = body || {}, l = lang(b.lang);
  if (text(b.website, 10)) return ok({});
  if (!sameOrigin(req)) return fail(403, "bad-request", l);
  if (await limited(ctx, "models", req, 5, 3600)) return fail(429, "rate", l);
  const entry = { name: text(b.name, 80), email: text(b.email, 254).toLowerCase(),
    interests: (Array.isArray(b.interests) ? b.interests : []).map((x) => text(x, 30)).filter((x) => ctx.policy.groups[x]).slice(0, 10),
    days: text(b.days, 120), lang: l, at: new Date(ctx.now()).toISOString() };
  if (entry.name.length < 2 || !EMAIL_RE.test(entry.email)) return fail(400, "details", l);
  if (b.consent !== true) return fail(400, "consent-terms", l);
  let stored = false;
  if (ctx.store) {
    try { await transact(ctx.store, [K.models], (cur) => ({ writes: { [K.models]: [...(cur[K.models] || []), entry].slice(-2000) } })); stored = true; }
    catch (e) { console.error("[salon models]", e && e.message); }
  }
  const mailed = await mail.send(ctx.env, { to: mail.CONTACT, replyTo: entry.email, subject: "Salon model register: " + entry.name,
    text: ["A new name for the salon model register.", "", "Name: " + entry.name, "Email: " + entry.email,
      "Interested in: " + (entry.interests.join(", ") || "anything"), "Days: " + (entry.days || "not given"), "Language: " + l].join("\n") }, ctx.fetch);
  if (!stored && mailed !== "sent") return unavailable(l, "no-store");          // nowhere to put it: say so
  return ok({});
}

// ---------------------------------------------------------------------------------------------
// POST /api/salon/staff — the day sheet. Every action needs the staff cookie except "login".
// ---------------------------------------------------------------------------------------------
const NEXT = {
  held: ["cancelled"], confirmed: ["arrived", "no_show", "cancelled"], arrived: ["in_progress", "cancelled"],
  in_progress: ["completed"], completed: [], no_show: ["confirmed"], cancelled: [],
};
const DAY_IDS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

function staffView(bk, now) {
  return { id: bk.id, v: bk.v, date: bk.date, start: bk.start, end: endOf(bk), minutes: bk.minutes, segments: bk.segments,
    serviceId: bk.serviceId, level: bk.level, studentId: bk.studentId, status: bk.status === "held" && !blocks(bk, now) ? "expired" : bk.status,
    next: NEXT[bk.status] || [], client: bk.client, price: bk.price, deposit: bk.deposit,
    depositPaid: bk.payments.some((x) => x.status === "paid"), needsRefund: bk.needsRefund === true,
    concession: bk.concession === true, answers: bk.answers || {}, addons: bk.addons || [],
    age: bk.age, guardian: bk.guardian ? bk.guardian.name : null, hasConsultation: Boolean(bk.consultation),
    patchFor: bk.patchFor || null, patchProduct: bk.patchProduct || null };
}

async function staff(ctx, body, req) {
  const b = body || {}, l = "en", action = text(b.action, 30);
  const pw = auth.password(ctx.env);
  if (!pw) return unavailable(l, "no-staff-password");
  if (!ctx.store) return unavailable(l, "no-store");
  if (!sameOrigin(req)) return fail(403, "bad-request", l);
  const now = ctx.now(), p = ctx.policy;

  if (action === "login") {
    const key = K.rl("login:" + ipOf(req));
    if (((await ctx.store.get(key)) || 0) >= 10) return fail(429, "rate", l);
    if (!auth.same(String(b.password || ""), pw)) { await ctx.store.bump(key, 900); return fail(401, "signin", l); }
    return ok({ signedIn: true }, { "Set-Cookie": auth.setCookie(auth.issue(pw, now)) });
  }
  if (action === "logout") return ok({ signedIn: false }, { "Set-Cookie": auth.clearCookie() });
  if (!auth.verify(auth.readCookie(req && req.headers), pw, now)) return fail(401, "signin", l);

  try {
    if (action === "day") {
      const date = T.isDate(b.date) ? b.date : T.isoDate(now);
      const [doc, roster] = [dayDoc(await ctx.store.get(K.day(date))), await studentsOf(ctx)];
      return ok({ date, v: doc.v, today: T.isoDate(now), students: roster.list, studentsV: roster.v,
        bookings: doc.bookings.map((x) => staffView(x, now)).filter((x) => x.status !== "expired").sort((x, y) => x.start - y.start),
        services: p.services.map((s) => ({ id: s.id, name: s.name.en })), levels: p.levelIds.map((id) => ({ id, name: p.levels[id].name.en })),
        products: Object.keys(p.patch_test.products).concat(p.services.filter((x) => x.consultation_first).map((x) => "consult:" + x.id)), encryption: Boolean(S.keyFrom(ctx.env)) });
    }

    if (action === "status") {
      const to = text(b.status, 20);
      let patchKey = null;
      const current = await peek(ctx, text(b.id, 20));
      // Completing a patch-test appointment is what CREATES the patch-test record.
      if (current && to === "completed" && current.patchFor && current.clientKey) patchKey = K.patch(current.clientKey);
      const after = await change(ctx, text(b.id, 20), (bk) => {
        if (bk.v !== Number(b.v)) throw new Refused({ code: "stale" });
        if (!(NEXT[bk.status] || []).includes(to)) throw new Refused({ code: "bad-transition" });
        bk.status = to;
        if (to === "cancelled") { bk.cancelReason = "staff"; bk.heldUntil = null; }
        return bk;
      }, "staff", "status: " + to, patchKey ? [patchKey] : null, (bk, cur) => (patchKey
        ? { [patchKey]: { records: [...(((cur[patchKey] || {}).records) || []), { product: bk.patchFor, testedAt: now, booking: bk.id }] } } : {}));
      return ok({ booking: staffView(after, now) });
    }

    if (action === "move" || action === "resize") {
      const id = text(b.id, 20);
      const ref = await ctx.store.get(K.ref(id));
      if (!ref) return fail(404, "not-found", l);
      const toDate = action === "move" && T.isDate(b.toDate) ? b.toDate : ref.date;
      const students = (await studentsOf(ctx)).list;
      const patch = await patchOfBooking(ctx, await peek(ctx, id));
      const moved = await transact(ctx.store, [K.day(ref.date), K.day(toDate)], (cur) => {
        const from = dayDoc(cur[K.day(ref.date)]), into = toDate === ref.date ? from : dayDoc(cur[K.day(toDate)]);
        const bk = from.bookings.find((x) => x.id === id);
        if (!bk) throw new Refused({ code: "not-found" });
        if (bk.v !== Number(b.v)) throw new Refused({ code: "stale" });
        if (!["held", "confirmed", "arrived", "in_progress"].includes(bk.status)) throw new Refused({ code: "bad-transition" });
        const next = JSON.parse(JSON.stringify(bk));
        if (action === "move") {
          next.date = toDate; next.start = Number(b.toStart);
          if (b.toStudent) next.studentId = text(b.toStudent, 40);
        } else {
          const want = Number(b.minutes);
          const i = next.segments.map((s) => s.kind).lastIndexOf("work");
          const delta = want - next.minutes;
          if (!Number.isInteger(want) || want % 5 !== 0 || i < 0 || next.segments[i].minutes + delta < 5) throw new Refused({ code: "bad-request" });
          next.segments[i].minutes += delta; next.minutes = want;
        }
        // The patch test was checked against the original time; a move must not land the
        // appointment outside its window, so the rule is asked again with the client's records.
        const no = feasible(asCandidate(next), into.bookings, { policy: p, students, patch, now, actor: "staff" });
        if (no) throw new Refused(no);
        next.v = bk.v + 1;
        next.log = [...(next.log || []), { at: new Date(now).toISOString(), by: "staff", what: action === "move" ? "moved to " + next.date + " " + T.formatClock(next.start) : "resized to " + next.minutes + " min" }];
        const writes = {};
        if (toDate === ref.date) {
          writes[K.day(ref.date)] = { v: from.v + 1, bookings: from.bookings.map((x) => (x.id === id ? next : x)) };
        } else {
          writes[K.day(ref.date)] = { v: from.v + 1, bookings: from.bookings.filter((x) => x.id !== id) };
          writes[K.day(toDate)] = { v: into.v + 1, bookings: [...into.bookings, next] };
          writes[K.ref(id)] = { date: toDate };
        }
        return { writes, result: next };
      });
      return ok({ booking: staffView(moved, now) });
    }

    if (action === "students-save") {
      const list = (Array.isArray(b.list) ? b.list : []).slice(0, 80).map((s) => ({
        id: /^st_[0-9a-f]{8}$/.test(String(s.id)) ? s.id : "st_" + crypto.randomBytes(4).toString("hex"),
        name: text(s.name, 60), level: p.levels[s.level] ? s.level : null,
        days: (Array.isArray(s.days) ? s.days : DAY_IDS).filter((d) => DAY_IDS.includes(d)),
        skills: Array.isArray(s.skills) ? s.skills.filter((x) => p.serviceById.has(x)) : undefined,
        active: s.active !== false }));
      if (list.some((s) => s.name.length < 1 || !s.level)) return fail(400, "details", l);
      const saved = await transact(ctx.store, [K.students], (cur) => {
        const was = cur[K.students] || { v: 0, list: [] };
        if (was.v !== Number(b.v)) throw new Refused({ code: "stale" });
        const next = { v: was.v + 1, list };
        return { writes: { [K.students]: next }, result: next };
      });
      return ok({ students: saved.list, studentsV: saved.v });
    }

    if (action === "patch-add") {
      const dataKey = S.keyFrom(ctx.env);
      if (!dataKey) return unavailable(l, "no-encryption");
      const email = text(b.email, 254).toLowerCase(), product = text(b.product, 40);
      const known = p.patch_test.products[product] || (/^consult:/.test(product) && (p.serviceById.get(product.slice(8)) || {}).consultation_first);
      if (!EMAIL_RE.test(email) || !known || !T.isDate(b.testedOn) || b.testedOn > T.isoDate(now)) return fail(400, "details", l);
      const key = K.patch(S.clientKey(dataKey, email));
      await transact(ctx.store, [key], (cur) => ({ writes: { [key]: { records: [...(((cur[key] || {}).records) || []),
        { product, testedAt: T.instantOf(b.testedOn, 12 * 60), by: "staff" }] } } }));
      return ok({});
    }

    if (action === "consultation") {
      const dataKey = S.keyFrom(ctx.env);
      if (!dataKey) return unavailable(l, "no-encryption");
      let answers = null;
      await change(ctx, text(b.id, 20), (bk) => {
        if (!bk.consultation) throw new Refused({ code: "not-found" });
        answers = S.open(dataKey, bk.id, bk.consultation);
        return bk;                                             // logged: who looked, and when
      }, "staff", "consultation viewed");
      return ok({ consultation: answers });
    }

    if (action === "models") return ok({ models: (await ctx.store.get(K.models)) || [] });
    if (action === "unreconciled") return ok({ unreconciled: (await ctx.store.get(K.unreconciled)) || [] });
    return fail(400, "bad-request", l);
  } catch (e) {
    if (e instanceof Refused) return refusal(ctx, e.detail, l);
    console.error("[salon staff]", e && e.message);
    return unavailable(l, "store-error");
  }
}

module.exports = { context, openState, config, quote: quoteHandler, availability, book, bookingStatus, webhook, models, staff, NEXT, CONSENT_VERSION };
