/* Clwydian Academy — enquiry form handler (Vercel serverless function, Node runtime).
 *
 * POST /api/enquiry  ←  <form method="post" action="/api/enquiry">  (works without JavaScript)
 * Validates, sends two emails through Resend — one to the academy, one auto-reply to the
 * enquirer in their chosen language — then 303-redirects to the thank-you page. With
 * `Accept: application/json` (the progressive enhancement in main.js) it answers JSON instead.
 *
 * Secrets: RESEND_API_KEY is read from process.env and is set by Mark in the Vercel dashboard.
 * It is never in this repo. ENQUIRY_TO and ENQUIRY_FROM are optional overrides.
 *
 * Spam: honeypot field ("website"), a time-to-submit check when the page's script stamped the
 * form, and an in-memory per-IP rate limit (best effort — one map per warm instance). No CAPTCHA.
 */
"use strict";

const RESEND_URL = "https://api.resend.com/emails";
const TO_DEFAULT = "markp@charlotteeleanorgroup.uk";
const FROM_DEFAULT = "Clwydian Academy <enquiries@clwydianacademy.co.uk>";
const SITE = "https://www.clwydianacademy.co.uk";

const THANKS = { en: "/contact/thanks/", cy: "/cy/cysylltu/diolch/" };
const BACK = { en: "/contact/", cy: "/cy/cysylltu/" };

const ENQUIRY = {
  course:     { en: "A course (NVQ Level 2 or 3)",        cy: "Cwrs (NVQ Lefel 2 neu 3)" },
  cpd:        { en: "CPD dates",                          cy: "Dyddiadau DPP" },
  team:       { en: "Team training for my salon",         cy: "Hyfforddiant tîm i'm salon" },
  apprentice: { en: "Taking on an apprentice",            cy: "Cymryd prentis" },
  funding:    { en: "Funding",                            cy: "Cyllid" },
  funder:     { en: "Funder or partner enquiry",          cy: "Ymholiad cyllidwr neu bartner" },
  other:      { en: "Something else",                     cy: "Rhywbeth arall" },
};

const NEXT = {
  en: {
    subject: (t) => "We have your enquiry — " + t + " — Clwydian Academy",
    body: (name, t, msg) =>
      "Hello " + name + ",\n\n" +
      "Thank you — we have your enquiry about: " + t + ".\n\n" +
      "What happens next: a person reads it, not a pipeline. We reply within two working days, " +
      "by email, from this address. If your question is about a specific cohort or date, we will " +
      "confirm whether the seat is available in that reply.\n\n" +
      "What you told us:\n" + msg + "\n\n" +
      "If anything changes in the meantime, reply to this email.\n\n" +
      "Clwydian Academy CBC\nSt Asaph, Denbighshire\n" + SITE + "\n",
  },
  cy: {
    subject: (t) => "Mae eich ymholiad gennym — " + t + " — Clwydian Academy",
    body: (name, t, msg) =>
      "Helo " + name + ",\n\n" +
      "Diolch — mae eich ymholiad gennym am: " + t + ".\n\n" +
      "Beth sy'n digwydd nesaf: mae person yn ei ddarllen, nid piblinell. Byddwn yn ateb o fewn " +
      "dau ddiwrnod gwaith, drwy e-bost, o'r cyfeiriad hwn. Os yw eich cwestiwn am garfan neu " +
      "ddyddiad penodol, byddwn yn cadarnhau a yw'r sedd ar gael yn yr ateb hwnnw.\n\n" +
      "Yr hyn a ddywedoch wrthym:\n" + msg + "\n\n" +
      "Os bydd unrhyw beth yn newid yn y cyfamser, atebwch yr e-bost hwn.\n\n" +
      "Clwydian Academy CBC\nLlanelwy, Sir Ddinbych\n" + SITE + "\n",
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
  if (b && typeof b === "object") return b;
  if (typeof b === "string") {
    const ct = (req.headers["content-type"] || "").toLowerCase();
    if (ct.includes("application/json")) { try { return JSON.parse(b); } catch (e) { return {}; } }
    return Object.fromEntries(new URLSearchParams(b));
  }
  return {};
}

const clean = (v, max) => (typeof v === "string" ? v.trim().replace(/\r\n?/g, "\n") : "").slice(0, max);
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function validate(b) {
  const errors = [];
  const f = {
    name: clean(b.name, 120),
    email: clean(b.email, 200),
    phone: clean(b.phone, 40),
    org: clean(b.org, 120),
    enquiry: clean(b.enquiry, 20),
    message: clean(b.message, 4000),
    lang: clean(b.lang, 2) === "cy" ? "cy" : "en",
  };
  if (f.name.length < 2) errors.push("name");
  if (!EMAIL.test(f.email)) errors.push("email");
  if (!ENQUIRY[f.enquiry]) errors.push("enquiry");
  if (f.message.length < 2) errors.push("message");
  return { f, errors };
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
  const wantsJson = (req.headers.accept || "").includes("application/json");
  const lang = clean(b.lang, 2) === "cy" ? "cy" : "en";
  const fail = (status, code) => {
    if (wantsJson) return res.status(status).json({ ok: false, error: code });
    res.setHeader("Location", BACK[lang] + "?error=" + encodeURIComponent(code) + "#register");
    return res.status(303).end();
  };
  const done = () => {
    if (wantsJson) return res.status(200).json({ ok: true, next: THANKS[lang] });
    res.setHeader("Location", THANKS[lang]);
    return res.status(303).end();
  };

  // Spam: honeypot filled, or submitted within 3 s of the page stamping the form → pretend success.
  if (clean(b.website, 10)) return done();
  const ts = Number(b.ts);
  if (ts && Date.now() - ts < 3000) return done();

  const ip = (req.headers["x-forwarded-for"] || "").split(",")[0].trim() || req.socket?.remoteAddress || "?";
  if (rateLimited(ip)) return fail(429, "rate");

  const { f, errors } = validate(b);
  if (errors.length) return fail(400, errors.join(","));

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
    text: NEXT[f.lang].body(f.name, label[f.lang], f.message),
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
