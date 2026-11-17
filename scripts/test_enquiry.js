#!/usr/bin/env node
/* test_enquiry.js — the enquiry function, exercised without Vercel or Resend.

       node --test scripts/test_enquiry.js

   No dependencies: Node's built-in test runner (Node 18+). The function is called with a
   request shaped the way Vercel shapes it — in particular, a multipart/form-data body is NOT
   parsed (req.body is undefined), which is what broke the form for visitors with JavaScript.
   Outgoing mail is captured by replacing global fetch; nothing leaves the machine.
*/
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");

const handler = require(path.join(__dirname, "..", "clwydian-academy 2", "api", "enquiry.js"));

const fs = require("node:fs");
const SITE_EMAIL = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "_data", "site.json"), "utf8")).email;
const HOST = "www.clwydianacademy.co.uk";
const ORIGIN = "https://" + HOST;
const GOOD = { name: "Test Person", email: "test@example.com", phone: "", org: "", enquiry: "cpd",
               lang: "en", message: "Do you have seats in March?\nThanks", website: "" };
let ipCounter = 0;

/* Call the handler like Vercel would. `as` is how the body was sent. */
async function post(fields, { as = "form", headers = {}, key = "test-key" } = {}) {
  const sent = [];
  globalThis.fetch = async (url, init) => { sent.push({ url, mail: JSON.parse(init.body) }); return { ok: true, status: 200, text: async () => "" }; };
  if (key) process.env.RESEND_API_KEY = key; else delete process.env.RESEND_API_KEY;
  const types = { form: "application/x-www-form-urlencoded", json: "application/json", multipart: "multipart/form-data; boundary=x" };
  const req = {
    method: "POST",
    headers: Object.assign({ host: HOST, origin: ORIGIN, referer: ORIGIN + "/contact/", "content-type": types[as],
                             "x-forwarded-for": "10.0.0." + (++ipCounter) }, headers),
    body: as === "multipart" ? undefined : fields,          // Vercel parses form and JSON bodies, not multipart
    socket: {},
  };
  for (const k of Object.keys(req.headers)) if (req.headers[k] === null) delete req.headers[k];
  const res = { statusCode: 200, headers: {}, body: "",
    setHeader(k, v) { this.headers[k.toLowerCase()] = v; },
    status(c) { this.statusCode = c; return this; },
    json(o) { this.body = o; return this; }, send(s) { this.body = s; return this; }, end() { return this; } };
  await handler(req, res);
  return { status: res.statusCode, headers: res.headers, body: res.body, sent };
}
const old = (ms) => String(Date.now() - ms);
const JSON_ACCEPT = { accept: "application/json" };

test("JavaScript path: urlencoded body with a stamp sends both emails", async () => {
  const r = await post({ ...GOOD, ts: old(10000) }, { headers: JSON_ACCEPT });
  assert.equal(r.status, 200);
  assert.deepEqual(r.body, { ok: true, next: "/contact/thanks/" });
  assert.equal(r.sent.length, 2);
  assert.deepEqual(r.sent[0].mail.to, [SITE_EMAIL]);
  assert.equal(r.sent[0].mail.from, "Clwydian Academy <" + SITE_EMAIL + ">");
  assert.equal(r.sent[1].mail.reply_to, SITE_EMAIL);
  assert.match(r.sent[0].mail.text, /Do you have seats in March\?/);     // the academy gets the message
  assert.deepEqual(r.sent[1].mail.to, ["test@example.com"]);
});

test("a multipart body (what the old main.js sent) is rejected, not half-read", async () => {
  const r = await post({ ...GOOD, ts: old(10000) }, { as: "multipart", headers: JSON_ACCEPT });
  assert.equal(r.status, 400);
  assert.equal(r.body.error, "fields");
  assert.equal(r.sent.length, 0);
});

test("the confirmation email repeats nothing the visitor typed", async () => {
  const spam = { ...GOOD, name: "BUY-PILLS http://spam.example", message: "CLICK http://spam.example NOW", org: "SpamCo", ts: old(10000) };
  for (const lang of ["en", "cy"]) {
    const r = await post({ ...spam, lang });
    const reply = r.sent[1].mail;
    assert.deepEqual(reply.to, ["test@example.com"]);
    for (const part of [reply.subject, reply.text])
      assert.doesNotMatch(part, /spam\.example|BUY-PILLS|CLICK|SpamCo/, "auto-reply echoes typed text (" + lang + ")");
  }
});

test("a name cannot put a line break into an email subject", async () => {
  const r = await post({ ...GOOD, name: "Eve\r\nBcc: victim@example.com", ts: old(10000) });
  assert.doesNotMatch(r.sent[0].mail.subject, /[\r\n]/);
});

test("origin check: another site, or no Origin and no Referer, sends nothing", async () => {
  for (const headers of [{ origin: "https://evil.example", referer: "https://evil.example/x" },
                         { origin: null, referer: null },
                         { origin: "null", referer: null }]) {
    const r = await post({ ...GOOD, ts: old(10000) }, { headers });
    assert.equal(r.status, 403);
    assert.equal(r.sent.length, 0);
  }
});

test("origin check: the apex host, a preview host and a Referer-only request are accepted", async () => {
  for (const headers of [{ origin: "https://clwydianacademy.co.uk" },
                         { host: "mapa-projects-abc.vercel.app", origin: "https://mapa-projects-abc.vercel.app" },
                         { origin: null, referer: ORIGIN + "/cy/cysylltu/" }]) {
    const r = await post({ ...GOOD, ts: old(10000) }, { headers });
    assert.equal(r.status, 303, JSON.stringify(headers));
    assert.equal(r.sent.length, 2);
  }
});

test("ts is required: missing, empty, junk, stale and future stamps send nothing", async () => {
  for (const ts of [undefined, "", "abc", old(25 * 60 * 60 * 1000), String(Date.now() + 60 * 60 * 1000)]) {
    const fields = { ...GOOD }; if (ts !== undefined) fields.ts = ts;
    const r = await post(fields, { headers: JSON_ACCEPT });
    assert.equal(r.status, 409, "ts=" + ts);
    assert.equal(r.body.error, "confirm");
    assert.ok(Date.now() - r.body.ts < 1000, "a fresh stamp is handed back");
    assert.equal(r.sent.length, 0);
  }
});

test("ts under 3 seconds old sends nothing and keeps the stamp, so the next press works", async () => {
  const ts = old(500);
  const r = await post({ ...GOOD, ts }, { headers: JSON_ACCEPT });
  assert.equal(r.status, 409);
  assert.equal(String(r.body.ts), ts);
  assert.equal(r.sent.length, 0);
});

test("no JavaScript: first press returns the form refilled and stamped; second press sends", async () => {
  const first = await post({ ...GOOD, org: 'Curl & "Co" <salon>', ts: "" });
  assert.equal(first.status, 409);
  assert.equal(first.sent.length, 0);
  const html = first.body;
  assert.match(html, /<html lang="en-GB">/);
  assert.match(html, /name="name"[^>]*value="Test Person"/);
  assert.match(html, /name="email"[^>]*value="test@example\.com"/);
  assert.match(html, /value="Curl &amp; &quot;Co&quot; &lt;salon&gt;"/);          // escaped, not injected
  assert.match(html, /<option value="cpd" selected>/);
  assert.match(html, />Do you have seats in March\?\nThanks<\/textarea>/);
  assert.match(html, /press send once more/);
  assert.doesNotMatch(html, /aria-invalid/);
  const ts = html.match(/name="ts" value="(\d+)"/)[1];
  assert.ok(Date.now() - Number(ts) < 1000);
  // the second press, a few seconds later, from the re-served page
  const second = await post({ ...GOOD, ts: String(Number(ts) - 5000), page: "en" }, { headers: { referer: ORIGIN + "/api/enquiry" } });
  assert.equal(second.status, 303);
  assert.equal(second.headers.location, "/contact/thanks/");
  assert.equal(second.sent.length, 2);
});

test("no JavaScript: a bad submission keeps every value and marks only the bad fields", async () => {
  const r = await post({ ...GOOD, name: "x", email: "not-an-email", phone: "01745 000000", ts: old(10000) });
  assert.equal(r.status, 400);
  assert.equal(r.sent.length, 0);
  const html = r.body;
  assert.match(html, /name="name"[^>]*value="x"[^>]*aria-invalid="true"[^>]*autofocus/);   // first bad field takes focus
  assert.match(html, /name="email"[^>]*value="not-an-email"[^>]*aria-invalid="true"/);
  assert.match(html, /name="phone"[^>]*value="01745 000000">/);                              // good field: kept, unmarked
  assert.equal((html.match(/aria-invalid="true"/g) || []).length, 2);
  assert.match(html, /Please check the highlighted fields/);
  assert.match(html, />Do you have seats in March\?\nThanks<\/textarea>/);
});

test("no JavaScript, Welsh page: the form comes back in Welsh", async () => {
  const r = await post({ ...GOOD, lang: "en", email: "", ts: old(10000) }, { headers: { referer: ORIGIN + "/cy/cysylltu/" } });
  assert.equal(r.status, 400);
  assert.match(r.body, /<html lang="cy">/);
  assert.match(r.body, /Gwiriwch y meysydd/);
  assert.match(r.body, /<option value="en" selected>English<\/option>/);   // their reply-language choice is kept
});

test("JavaScript path: a bad submission names the fields", async () => {
  const r = await post({ ...GOOD, email: "nope", message: "", ts: old(10000) }, { headers: JSON_ACCEPT });
  assert.equal(r.status, 400);
  assert.equal(r.body.error, "fields");
  assert.deepEqual(r.body.fields, ["email", "message"]);
});

test("an enquiry type that is not on the list is refused (including inherited property names)", async () => {
  for (const enquiry of ["", "nonsense", "constructor", "__proto__"]) {
    const r = await post({ ...GOOD, enquiry, ts: old(10000) }, { headers: JSON_ACCEPT });
    assert.equal(r.status, 400, enquiry);
    assert.deepEqual(r.body.fields, ["enquiry"]);
  }
});

test("honeypot filled: looks like success, sends nothing", async () => {
  const r = await post({ ...GOOD, website: "http://bot.example", ts: old(10000) });
  assert.equal(r.status, 303);
  assert.equal(r.sent.length, 0);
});

test("Welsh reply language: Welsh confirmation and Welsh thank-you page", async () => {
  const r = await post({ ...GOOD, lang: "cy", ts: old(10000) });
  assert.equal(r.headers.location, "/cy/cysylltu/diolch/");
  assert.match(r.sent[1].mail.subject, /^Mae eich ymholiad gennym — Dyddiadau DPP/);
});

test("no API key: nothing is sent and the visitor keeps their input", async () => {
  const r = await post({ ...GOOD, ts: old(10000) }, { key: null });
  assert.equal(r.status, 500);
  assert.match(r.body, /The form is not connected yet/);
  assert.match(r.body, /value="Test Person"/);
  assert.equal(r.sent.length, 0);
});

test("rate limit: the sixth enquiry from one address in ten minutes is refused", async () => {
  const headers = { "x-forwarded-for": "203.0.113.9", accept: "application/json" };
  for (let i = 0; i < 5; i++) assert.equal((await post({ ...GOOD, ts: old(10000) }, { headers })).status, 200);
  const r = await post({ ...GOOD, ts: old(10000) }, { headers });
  assert.equal(r.status, 429);
  assert.equal(r.body.error, "rate");
  assert.equal(r.sent.length, 0);
});

test("the function's address is the one in _data/site.json, and the old address and phone are gone", () => {
  const src = fs.readFileSync(path.join(__dirname, "..", "clwydian-academy 2", "api", "enquiry.js"), "utf8");
  assert.equal(SITE_EMAIL, "hello@clwydianacademy.co.uk");
  assert.ok(src.includes('const CONTACT = "' + SITE_EMAIL + '";'), "enquiry.js CONTACT differs from _data/site.json email");
  assert.doesNotMatch(src, /charlotteeleanorgroup|7714/);
});

test("ENQUIRY_TO and ENQUIRY_FROM, when set in the environment, override the defaults", async () => {
  process.env.ENQUIRY_TO = "override@example.org"; process.env.ENQUIRY_FROM = "Someone <from@example.org>";
  try {
    const r = await post({ ...GOOD, ts: old(10000) });
    assert.deepEqual(r.sent[0].mail.to, ["override@example.org"]);
    assert.equal(r.sent[0].mail.from, "Someone <from@example.org>");
  } finally { delete process.env.ENQUIRY_TO; delete process.env.ENQUIRY_FROM; }
});

test("GET is not allowed", async () => {
  const res = { headers: {}, setHeader(k, v) { this.headers[k] = v; }, status(c) { this.code = c; return this; }, send() { return this; } };
  await handler({ method: "GET", headers: {} }, res);
  assert.equal(res.code, 405);
});
