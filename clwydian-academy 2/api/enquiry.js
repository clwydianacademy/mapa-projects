/* Clwydian Academy — enquiry form handler (Vercel serverless function, Node runtime).
 *
 * POST /api/enquiry  ←  <form method="post" action="/api/enquiry">  (works without JavaScript)
 * Validates, sends two emails through Resend — one to the academy, one fixed-text confirmation
 * to the enquirer in their chosen language — then 303-redirects to the thank-you page. With
 * `Accept: application/json` (the progressive enhancement in main.js) it answers JSON instead.
 *
 * The body must arrive as application/x-www-form-urlencoded (a plain form post, and what main.js
 * sends) or application/json. Vercel does NOT parse multipart/form-data: posting a raw FormData
 * object reaches this function with an empty body.
 *
 * When a submission without JavaScript cannot be accepted (a field is wrong, or the form has not
 * been time-stamped yet), the function answers with the form itself, refilled with what the
 * visitor typed and with the fields that need attention marked — nothing they wrote is lost.
 *
 * Secrets: RESEND_API_KEY is read from process.env and is set by Mark in the Vercel dashboard.
 * It is never in this repo. ENQUIRY_TO and ENQUIRY_FROM are optional overrides.
 *
 * Abuse controls (all best effort — there is no CAPTCHA):
 *   - same-origin only: the Origin (or Referer) header must be this site
 *   - honeypot field ("website")
 *   - a time stamp ("ts") is REQUIRED and must be at least 3 s old: set by main.js on page load,
 *     or by this function when it re-serves the form to a visitor without JavaScript (who then
 *     presses send a second time). It is a speed bump, not a signature: a script can forge it.
 *   - in-memory per-IP rate limit (one map per warm instance)
 *   - the confirmation email carries no text typed by the visitor, so the form cannot be used
 *     to send somebody else's words to a third party from the academy's address
 */
"use strict";

const RESEND_URL = "https://api.resend.com/emails";
// The one contact address (the same value as "email" in _data/site.json — scripts/test_enquiry.js
// fails if they differ). Enquiries are delivered here unless ENQUIRY_TO is set in Vercel, and the
// confirmation is sent from here unless ENQUIRY_FROM is set.
const CONTACT = "hello@clwydianacademy.co.uk";
const TO_DEFAULT = CONTACT;
const FROM_DEFAULT = "Clwydian Academy <" + CONTACT + ">";
const SITE = "https://www.clwydianacademy.co.uk";
const SITE_HOSTS = ["www.clwydianacademy.co.uk", "clwydianacademy.co.uk"];

const THANKS = { en: "/contact/thanks/", cy: "/cy/cysylltu/diolch/" };
const BACK = { en: "/contact/", cy: "/cy/cysylltu/" };

const TS_MIN_MS = 3000;                   // faster than this from stamp to submit is a script
const TS_MAX_MS = 24 * 60 * 60 * 1000;    // a stamp older than a day is stale: ask again

const ENQUIRY = {
  course:     { en: "A course (NVQ Level 2 or 3)",        cy: "Cwrs (NVQ Lefel 2 neu 3)" },
  cpd:        { en: "CPD dates",                          cy: "Dyddiadau DPP" },
  team:       { en: "Team training for my salon",         cy: "Hyfforddiant tîm i'm salon" },
  apprentice: { en: "Taking on an apprentice",            cy: "Cymryd prentis" },
  funding:    { en: "Funding",                            cy: "Cyllid" },
  funder:     { en: "Funder or partner enquiry",          cy: "Ymholiad cyllidwr neu bartner" },
  other:      { en: "Something else",                     cy: "Rhywbeth arall" },
};
const isEnquiry = (k) => Object.prototype.hasOwnProperty.call(ENQUIRY, k);

// The confirmation email. Fixed text only: the enquiry type comes from the list above, never
// from the request, and neither the visitor's name nor their message is repeated.
const NEXT = {
  en: {
    subject: (t) => "We have your enquiry — " + t + " — Clwydian Academy",
    body: (t) =>
      "Hello,\n\n" +
      "Thank you — we have your enquiry about: " + t + ".\n\n" +
      "What happens next: a person reads it, not a pipeline. We reply within two working days, " +
      "by email, from this address. If your question is about a specific cohort or date, we will " +
      "confirm whether the seat is available in that reply.\n\n" +
      "If anything changes in the meantime, reply to this email.\n\n" +
      "Clwydian Academy CBC\nSt Asaph, Denbighshire\n" + SITE + "\n",
  },
  cy: {
    subject: (t) => "Mae eich ymholiad gennym — " + t + " — Clwydian Academy",
    body: (t) =>
      "Helo,\n\n" +
      "Diolch — mae eich ymholiad gennym am: " + t + ".\n\n" +
      "Beth sy'n digwydd nesaf: mae person yn ei ddarllen, nid piblinell. Byddwn yn ateb o fewn " +
      "dau ddiwrnod gwaith, drwy e-bost, o'r cyfeiriad hwn. Os yw eich cwestiwn am garfan neu " +
      "ddyddiad penodol, byddwn yn cadarnhau a yw'r sedd ar gael yn yr ateb hwnnw.\n\n" +
      "Os bydd unrhyw beth yn newid yn y cyfamser, atebwch yr e-bost hwn.\n\n" +
      "Clwydian Academy CBC\nLlanelwy, Sir Ddinbych\n" + SITE + "\n",
  },
};

// Everything the re-served form says. The Welsh is the wording already on /cy/cysylltu/ and in
// main.js, except `confirm`, which is new and machine-written (WELSH FOR REVIEW).
const TEXT = {
  en: {
    title: "Register your interest", home: "Clwydian Academy — home", back: "Contact",
    name: "Name", email: "Email", phone: "Phone", org: "Salon or business", optional: "(optional)",
    enquiry: "What is your enquiry about?", choose: "Choose one…", lang: "Reply to me in",
    message: "Your message", website: "Website (leave this empty)", send: "Send enquiry",
    privacy: "Privacy", privacyHref: "/privacy/",
    msg: {
      fields: "Please check the highlighted fields and try again.",
      confirm: "Nearly there — please check your details and press send once more to confirm.",
      rate: "Too many enquiries from this address — please try again in a few minutes.",
      config: "The form is not connected yet. Please email us directly.",
      send: "We could not send your enquiry. Please try again, or email us.",
    },
  },
  cy: {
    title: "Cofrestrwch eich diddordeb", home: "Clwydian Academy — hafan", back: "Cysylltu",
    name: "Enw", email: "E-bost", phone: "Ffôn", org: "Salon neu fusnes", optional: "(dewisol)",
    enquiry: "Am beth mae eich ymholiad?", choose: "Dewiswch un…", lang: "Atebwch fi yn",
    message: "Eich neges", website: "Gwefan (gadewch hwn yn wag)", send: "Anfon ymholiad",
    privacy: "Preifatrwydd", privacyHref: "/cy/preifatrwydd/",
    msg: {
      fields: "Gwiriwch y meysydd sydd wedi'u marcio a rhowch gynnig arall.",
      confirm: "Bron yno — gwiriwch eich manylion a phwyswch anfon unwaith eto i gadarnhau.",
      rate: "Gormod o ymholiadau o'r cyfeiriad hwn — rhowch gynnig arall mewn ychydig funudau.",
      config: "Nid yw'r ffurflen wedi'i chysylltu eto. E-bostiwch ni'n uniongyrchol.",
      send: "Ni allem anfon eich ymholiad. Rhowch gynnig arall, neu e-bostiwch ni.",
    },
  },
};

const hits = new Map();                   // ip -> [timestamps]
const LIMIT = 5, WINDOW_MS = 10 * 60 * 1000;

function rateLimited(ip) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  list.push(now);
  hits.set(ip, list);
  if (hits.size > 5000) hits.clear();      // never let the map grow without bound
  return list.length > LIMIT;
}

function parseBody(req) {
  const b = req.body;
  if (b && typeof b === "object" && !Buffer.isBuffer(b)) return b;
  if (typeof b === "string") {
    const ct = String(req.headers["content-type"] || "").toLowerCase();
    if (ct.includes("application/json")) { try { return JSON.parse(b) || {}; } catch (e) { return {}; } }
    return Object.fromEntries(new URLSearchParams(b));
  }
  return {};
}

// Multi-line text (the message) keeps its line breaks; everything else is a single line, so a
// name can never smuggle a line break into an email subject.
const clean = (v, max) => (typeof v === "string" ? v.trim().replace(/\r\n?/g, "\n") : "").slice(0, max);
const line = (v, max) => clean(v, max * 2).replace(/\s+/g, " ").slice(0, max);
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function validate(b) {
  const errors = [];
  const f = {
    name: line(b.name, 120),
    email: line(b.email, 200),
    phone: line(b.phone, 40),
    org: line(b.org, 120),
    enquiry: line(b.enquiry, 20),
    message: clean(b.message, 4000),
    lang: line(b.lang, 2) === "cy" ? "cy" : "en",
  };
  if (f.name.length < 2) errors.push("name");
  if (!EMAIL.test(f.email)) errors.push("email");
  if (!isEnquiry(f.enquiry)) errors.push("enquiry");
  if (f.message.length < 2) errors.push("message");
  return { f, errors };
}

function hostOf(value) {
  try { return new URL(String(value)).host.toLowerCase(); } catch (e) { return ""; }
}

// Same-origin only. Browsers send Origin on every form POST and fetch POST; Referer is the
// fallback. A request that names neither, or names another site, is not from our form.
function sameOrigin(req) {
  const from = hostOf(req.headers.origin) || hostOf(req.headers.referer);
  if (!from) return false;
  const own = String(req.headers["x-forwarded-host"] || req.headers.host || "").toLowerCase();
  return from === own || SITE_HOSTS.includes(from);
}

// "ok" | "fast" (a script) | "missing" (absent, not a number, stale or in the future)
function stampState(raw) {
  const ts = Number(raw);
  if (!raw || !Number.isFinite(ts)) return "missing";
  const age = Date.now() - ts;
  if (age < -5 * 60 * 1000 || age > TS_MAX_MS) return "missing";
  return age < TS_MIN_MS ? "fast" : "ok";
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// The form, served by the function: refilled, time-stamped, and with the bad fields marked.
// Only reached without JavaScript — main.js shows the same messages inline.
function formPage(pageLang, f, bad, code, ts) {
  const t = TEXT[pageLang];
  const isBad = (n) => bad.includes(n);
  let focused = false;
  const attrs = (n) => {
    if (!isBad(n)) return "";
    const focus = focused ? "" : " autofocus";
    focused = true;
    return ' aria-invalid="true" aria-describedby="form-error"' + focus;
  };
  const field = (n, inner, full) =>
    '<div class="field' + (full ? " full" : "") + (isBad(n) ? " is-invalid" : "") + '">' + inner + "</div>";
  const input = (n, type, ac, extra, label) =>
    field(n, '<label for="f-' + n + '">' + label + "</label>" +
      '<input id="f-' + n + '" name="' + n + '" type="' + type + '" autocomplete="' + ac + '" ' + extra +
      ' value="' + esc(f[n]) + '"' + attrs(n) + ">");
  const opt = (value, label, chosen) =>
    '<option value="' + value + '"' + (value === chosen ? " selected" : "") + ">" + esc(label) + "</option>";
  const small = " <small>" + t.optional + "</small>";

  const fields = [
    input("name", "text", "name", 'required minlength="2" maxlength="120"', t.name),
    input("email", "email", "email", 'required maxlength="200"', t.email),
    input("phone", "tel", "tel", 'maxlength="40"', t.phone + small),
    input("org", "text", "organization", 'maxlength="120"', t.org + small),
    field("enquiry", '<label for="f-enquiry">' + t.enquiry + "</label>" +
      '<select id="f-enquiry" name="enquiry" required' + attrs("enquiry") + ">" +
      opt("", t.choose, isEnquiry(f.enquiry) ? f.enquiry : "") +
      Object.keys(ENQUIRY).map((k) => opt(k, ENQUIRY[k][pageLang], f.enquiry)).join("") + "</select>"),
    field("lang", '<label for="f-lang">' + t.lang + "</label>" +
      '<select id="f-lang" name="lang">' + opt("en", "English", f.lang) + opt("cy", "Cymraeg", f.lang) + "</select>"),
    field("message", '<label for="f-message">' + t.message + "</label>" +
      '<textarea id="f-message" name="message" rows="5" required minlength="2" maxlength="4000"' + attrs("message") + ">" +
      esc(f.message) + "</textarea>", true),
  ].join("\n");
  const submitFocus = focused ? "" : " autofocus";   // nothing to correct: land on the send button

  return "<!doctype html>\n" +
    '<html lang="' + (pageLang === "cy" ? "cy" : "en-GB") + '">\n<head>\n<meta charset="utf-8">\n' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n' +
    "<title>" + t.title + " | Clwydian Academy</title>\n" +
    '<meta name="robots" content="noindex, nofollow">\n' +
    '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n' +
    '<link rel="stylesheet" href="/assets/css/main.css">\n' +
    '<script src="/assets/js/main.js" defer></script>\n</head>\n<body>\n' +
    '<header class="site-header"><div class="wrap header-bar">' +
    '<a class="brand" href="' + (pageLang === "cy" ? "/cy/" : "/") + '" aria-label="' + t.home + '">' +
    '<img class="brand-seal" src="/assets/img/seal.svg" alt="" width="42" height="42">' +
    '<span class="brand-divider" aria-hidden="true"></span>' +
    '<span class="brand-text"><span class="brand-name">Clwydian</span>' +
    '<span class="brand-sub">Academy&nbsp;&middot;&nbsp;CBC</span></span></a>' +
    '<a href="' + BACK[pageLang] + '">' + t.back + "</a></div></header>\n" +
    '<main id="main"><section class="section section--tight"><div class="wrap" style="max-width:820px">\n' +
    "<h1>" + t.title + "</h1>\n" +
    '<p id="form-error" class="form-note form-alert mt-2" role="alert">' + esc(t.msg[code] || t.msg.fields) + "</p>\n" +
    '<form id="interest-form" class="form-grid mt-2" method="post" action="/api/enquiry">\n' +
    fields + "\n" +
    '<div class="field" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden" aria-hidden="true">' +
    '<label for="f-website">' + t.website + "</label>" +
    '<input id="f-website" name="website" type="text" tabindex="-1" autocomplete="off"></div>\n' +
    '<input type="hidden" name="ts" value="' + ts + '">\n' +
    '<input type="hidden" name="page" value="' + pageLang + '">\n' +
    '<div class="field full"><button class="btn btn-primary" type="submit"' + submitFocus + ">" + t.send +
    ' <span class="arr">&rarr;</span></button>' +
    '<p id="form-ok" class="form-note" role="status" hidden></p>' +
    '<p class="form-note mt-1"><a href="' + t.privacyHref + '">' + t.privacy + "</a></p></div>\n" +
    "</form>\n</div></section></main>\n</body>\n</html>\n";
}

async function send(key, payload) {
  const r = await fetch(RESEND_URL, {
    method: "POST",
    headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error("Resend " + r.status + ": " + (await r.text()).slice(0, 300));
}

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).send("Method not allowed");
  }
  const b = parseBody(req);
  const wantsJson = String(req.headers.accept || "").includes("application/json");
  const { f, errors } = validate(b);
  const lang = f.lang;
  // The language of the page the visitor is on (which is not always the language they want the
  // reply in): the re-served form says so itself, otherwise the Referer path does.
  const refPath = (() => { try { return new URL(String(req.headers.referer)).pathname; } catch (e) { return ""; } })();
  const pageLang = b.page === "cy" || b.page === "en" ? b.page
    : refPath.startsWith("/cy/") ? "cy" : refPath && !refPath.startsWith("/api/") ? "en" : lang;

  // The stamp the form should carry on its next submission: the one it has if that is usable,
  // a fresh one if it has none. (A "fast" stamp is kept, so the next press is no longer fast.)
  const stamp = stampState(b.ts);
  const nextStamp = stamp === "missing" ? Date.now() : Number(b.ts);

  // A failure the visitor can do something about: JSON for main.js, the refilled form otherwise.
  const fail = (status, code, bad) => {
    res.setHeader("Cache-Control", "no-store");
    if (wantsJson) return res.status(status).json({ ok: false, error: code, fields: bad || [], ts: nextStamp });
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    return res.status(status).send(formPage(pageLang, f, bad || [], code, nextStamp));
  };
  const done = () => {
    if (wantsJson) return res.status(200).json({ ok: true, next: THANKS[lang] });
    res.setHeader("Location", THANKS[lang]);
    return res.status(303).end();
  };

  // Not our form: answer nothing useful and send nothing.
  if (!sameOrigin(req)) {
    res.setHeader("Cache-Control", "no-store");
    if (wantsJson) return res.status(403).json({ ok: false, error: "origin", fields: [] });
    return res.status(403).send("Forbidden");
  }

  // Spam: honeypot filled → pretend success, send nothing.
  if (line(b.website, 10)) return done();

  const ip = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim() || (req.socket && req.socket.remoteAddress) || "?";
  if (rateLimited(ip)) return fail(429, "rate");

  if (errors.length) return fail(400, "fields", errors);
  // Valid, but the time stamp is not acceptable. It is required, so nothing is sent:
  //   missing — no JavaScript (or a very old tab): hand the form back stamped
  //   fast    — sent within 3 s of the stamp, which is a script or a very quick second press
  // Either way the visitor is asked for one more press of send, and nothing they typed is lost.
  if (stamp !== "ok") return fail(409, "confirm");

  const key = process.env.RESEND_API_KEY;
  if (!key) return fail(500, "config");
  const to = process.env.ENQUIRY_TO || TO_DEFAULT;
  const from = process.env.ENQUIRY_FROM || FROM_DEFAULT;
  const label = ENQUIRY[f.enquiry];

  const notification = {
    from, to: [to], reply_to: f.email,
    subject: "Enquiry — " + label.en + " — " + f.name,
    text:
      "New enquiry from " + SITE + "\n\n" +
      "Name: " + f.name + "\nEmail: " + f.email + "\nPhone: " + (f.phone || "—") + "\n" +
      "Salon / business: " + (f.org || "—") + "\nEnquiry: " + label.en + " (" + f.enquiry + ")\n" +
      "Reply in: " + (f.lang === "cy" ? "Cymraeg" : "English") + "\n\n" +
      "Message:\n" + f.message + "\n",
  };
  const autoReply = {
    from, to: [f.email], reply_to: to,
    subject: NEXT[f.lang].subject(label[f.lang]),
    text: NEXT[f.lang].body(label[f.lang]),
  };

  try {
    await send(key, notification);
    await send(key, autoReply);
  } catch (e) {
    console.error("enquiry: send failed —", e.message);
    return fail(502, "send");
  }
  return done();
};
