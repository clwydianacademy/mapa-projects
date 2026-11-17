/* Clwydian Academy training salon — staff sign-in for the day sheet.
 *
 * One shared password (STAFF_PASSWORD in Vercel), no user database. Signing in sets a cookie
 * holding a signed claim: base64url JSON, a dot, an HMAC-SHA256 over it. The signing key is
 * derived from the password, so changing the password signs everybody out. Without a usable
 * password every staff action refuses — it fails closed.
 */
"use strict";
const crypto = require("node:crypto");
const { usable } = require("./store");

const COOKIE = "ca_salon_staff";
const TTL_SECONDS = 12 * 60 * 60;

const password = (env) => (usable(env.STAFF_PASSWORD, { min: 10 }) ? String(env.STAFF_PASSWORD) : null);
const signingKey = (pw) => crypto.createHash("sha256").update("ca-salon-staff-v1:" + pw).digest();
const b64 = (buf) => Buffer.from(buf).toString("base64url");

/** Constant-time comparison of two strings of any length (compares their hashes). */
function same(a, b) {
  const ha = crypto.createHash("sha256").update(String(a)).digest();
  const hb = crypto.createHash("sha256").update(String(b)).digest();
  return crypto.timingSafeEqual(ha, hb);
}

function issue(pw, nowMs) {
  const payload = b64(JSON.stringify({ role: "staff", exp: Math.floor(nowMs / 1000) + TTL_SECONDS }));
  return payload + "." + b64(crypto.createHmac("sha256", signingKey(pw)).update(payload).digest());
}

function verify(token, pw, nowMs) {
  if (typeof token !== "string" || !pw) return false;
  const i = token.indexOf(".");
  if (i < 1) return false;
  const payload = token.slice(0, i);
  const want = b64(crypto.createHmac("sha256", signingKey(pw)).update(payload).digest());
  if (!same(token.slice(i + 1), want)) return false;
  try {
    const claim = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    return claim.role === "staff" && typeof claim.exp === "number" && claim.exp * 1000 > nowMs;
  } catch { return false; }
}

function readCookie(headers) {
  const raw = String((headers && headers.cookie) || "");
  for (const part of raw.split(";")) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i).trim() === COOKIE) return part.slice(i + 1).trim();
  }
  return null;
}
const setCookie = (token) => `${COOKIE}=${token}; Path=/api/salon/; HttpOnly; Secure; SameSite=Strict; Max-Age=${TTL_SECONDS}`;
const clearCookie = () => `${COOKIE}=; Path=/api/salon/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`;

module.exports = { COOKIE, password, same, issue, verify, readCookie, setCookie, clearCookie };
