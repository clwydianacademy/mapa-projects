/* Clwydian Academy training salon — Stripe, by plain fetch against the REST API. No SDK.
 *
 * THE MONEY RULE: nothing outside the VERIFIED webhook may mark a deposit paid. A client coming
 * back to the success page is a hint — they can forge it, and a client who closes the tab
 * before it loads has still paid. The signature is the fact.
 */
"use strict";
const crypto = require("node:crypto");
const { usable } = require("./store");

const SESSIONS = "https://api.stripe.com/v1/checkout/sessions";
const TOLERANCE_SECONDS = 300;

/** Pounds to pence. The only place that multiplies by a hundred. */
const toPence = (pounds) => Math.round((pounds || 0) * 100);

const secretKey = (env) => (usable(env.STRIPE_SECRET_KEY, { min: 12, prefixes: ["sk_", "rk_"] }) ? String(env.STRIPE_SECRET_KEY).trim() : null);
const webhookSecret = (env) => (usable(env.STRIPE_WEBHOOK_SECRET, { min: 12, prefixes: ["whsec_"] }) ? String(env.STRIPE_WEBHOOK_SECRET).trim() : null);
const isLiveKey = (key) => /^(sk|rk)_live_/.test(key || "");

/** Hosts a paying client may be sent back to. An allow-list, not "whatever the Host header
 *  said": the return address is a redirect target. Anchored at both ends. */
const RETURN_HOST = /^(?:(?:www\.)?clwydianacademy\.co\.uk|[a-z0-9-]+\.vercel\.app|localhost(?::\d+)?)$/i;
function returnBase(headers) {
  const host = String((headers && (headers["x-forwarded-host"] || headers.host)) || "").split(",")[0].trim();
  if (!RETURN_HOST.test(host)) return "https://www.clwydianacademy.co.uk";
  return (host.startsWith("localhost") ? "http://" : "https://") + host;
}

/**
 * @returns {Promise<{id:string,url:string}>}  throws on any failure — the caller releases the hold
 */
async function createCheckout({ key, booking, base, paths, description, holdUntil, fetchImpl }) {
  const f = new URLSearchParams();
  f.set("mode", "payment");
  f.set("success_url", base + paths.book + "?ref=" + encodeURIComponent(booking.id) + "&back=paid");
  f.set("cancel_url", base + paths.book + "?ref=" + encodeURIComponent(booking.id) + "&back=cancelled");
  f.set("client_reference_id", booking.id);
  f.set("customer_email", booking.client.email);
  f.set("line_items[0][quantity]", "1");
  f.set("line_items[0][price_data][currency]", "gbp");
  f.set("line_items[0][price_data][unit_amount]", String(toPence(booking.deposit)));
  f.set("line_items[0][price_data][product_data][name]", description.name);
  f.set("line_items[0][price_data][product_data][description]", description.detail);
  // Matched to the hold. Left unset Stripe allows 24 hours, so a slot could be released, taken
  // by someone else, and still paid for the next morning.
  f.set("expires_at", String(Math.floor(holdUntil / 1000)));
  f.set("metadata[booking_id]", booking.id);
  f.set("metadata[booking_date]", booking.date);
  f.set("payment_intent_data[metadata][booking_id]", booking.id);
  const r = await (fetchImpl || globalThis.fetch)(SESSIONS, {
    method: "POST",
    headers: { Authorization: "Bearer " + key, "Content-Type": "application/x-www-form-urlencoded",
      "Idempotency-Key": "salon-" + booking.id + "-deposit" },      // a retry never takes two deposits
    body: f.toString(),
  });
  if (!r.ok) throw new Error("Stripe " + r.status);
  const s = await r.json();
  if (!s || !s.url || !s.id) throw new Error("Stripe answered without a session");
  return { id: s.id, url: s.url };
}

function parseHeader(header) {
  let t = null; const v1 = [];
  for (const part of String(header).split(",")) {
    const i = part.indexOf("=");
    if (i < 0) continue;
    const k = part.slice(0, i).trim(), v = part.slice(i + 1).trim();
    if (k === "t" && /^\d+$/.test(v)) t = Number(v);
    if (k === "v1" && /^[0-9a-f]+$/i.test(v)) v1.push(v);
  }
  return t === null ? null : { t, v1 };
}

/** True only if `raw` is byte-for-byte what Stripe signed with `secret`, recently. */
function verifySignature(raw, header, secret, nowMs) {
  if (typeof secret !== "string" || !secret || typeof header !== "string" || !header) return false;
  const parsed = parseHeader(header);
  if (!parsed || !parsed.v1.length) return false;
  if (Math.abs(Math.floor(nowMs / 1000) - parsed.t) > TOLERANCE_SECONDS) return false;
  const body = Buffer.isBuffer(raw) ? raw : Buffer.from(String(raw === undefined || raw === null ? "" : raw), "utf8");
  const expected = crypto.createHmac("sha256", secret).update(Buffer.concat([Buffer.from(parsed.t + ".", "utf8"), body])).digest();
  return parsed.v1.some((hex) => {
    const got = Buffer.from(hex, "hex");
    // timingSafeEqual THROWS on unequal lengths — check first, or a bad signature becomes a 500
    return got.length === expected.length && crypto.timingSafeEqual(got, expected);
  });
}

module.exports = { toPence, secretKey, webhookSecret, isLiveKey, returnBase, createCheckout, verifySignature, TOLERANCE_SECONDS };
