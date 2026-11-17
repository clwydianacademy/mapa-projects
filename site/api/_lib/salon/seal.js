/* Clwydian Academy training salon — consultation and allergy answers, encrypted at rest.
 *
 * Health information is special-category personal data. It is stored only with the client's
 * explicit consent (recorded on the booking with the wording they agreed to), and only as
 * AES-256-GCM ciphertext under SALON_DATA_KEY — 32 random bytes, base64, held in Vercel and
 * nowhere else. The booking reference is bound in as additional data, so a sealed answer cannot
 * be moved onto another booking. Without a usable key nothing is stored: the caller refuses.
 */
"use strict";
const crypto = require("node:crypto");

function keyFrom(env) {
  const raw = String((env && env.SALON_DATA_KEY) || "").trim();
  if (!raw) return null;
  let key;
  try { key = Buffer.from(raw, "base64"); } catch { return null; }
  return key.length === 32 ? key : null;
}

function seal(key, bookingId, value) {
  const iv = crypto.randomBytes(12);
  const c = crypto.createCipheriv("aes-256-gcm", key, iv);
  c.setAAD(Buffer.from(String(bookingId), "utf8"));
  const ct = Buffer.concat([c.update(JSON.stringify(value), "utf8"), c.final()]);
  return { v: 1, alg: "A256GCM", iv: iv.toString("base64"), tag: c.getAuthTag().toString("base64"), ct: ct.toString("base64") };
}

/** Throws if the key is wrong, the data was altered, or it belongs to another booking. */
function open(key, bookingId, sealed) {
  const d = crypto.createDecipheriv("aes-256-gcm", key, Buffer.from(sealed.iv, "base64"));
  d.setAAD(Buffer.from(String(bookingId), "utf8"));
  d.setAuthTag(Buffer.from(sealed.tag, "base64"));
  return JSON.parse(Buffer.concat([d.update(Buffer.from(sealed.ct, "base64")), d.final()]).toString("utf8"));
}

/** The key a client's patch-test records are filed under: a keyed hash of their email, so the
 *  database holds no list of addresses against health-related records. */
function clientKey(key, email) {
  return crypto.createHmac("sha256", key).update("patch:" + String(email).trim().toLowerCase()).digest("hex").slice(0, 32);
}

module.exports = { keyFrom, seal, open, clientKey };
