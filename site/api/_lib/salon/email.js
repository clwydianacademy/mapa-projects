/* Clwydian Academy training salon — email, through the academy's existing Resend account.
 *
 * Same key (RESEND_API_KEY) and same sender as site/api/enquiry.js. Sending never throws into a
 * booking: a booking that is paid for is confirmed whether or not the email went, and the
 * caller records which.
 */
"use strict";
const { usable } = require("./store");

const RESEND_URL = "https://api.resend.com/emails";
// The one contact address — the same value as "email" in _data/site.json. scripts/test_salon_rules.js
// fails if they differ.
const CONTACT = "hello@clwydianacademy.co.uk";
const FROM = "Clwydian Academy <" + CONTACT + ">";

const resendKey = (env) => (usable(env.RESEND_API_KEY, { min: 8 }) ? String(env.RESEND_API_KEY).trim() : null);

/** @returns {Promise<"sent"|"not-configured"|"failed">} */
async function send(env, { to, subject, text, replyTo }, fetchImpl) {
  const key = resendKey(env);
  if (!key) return "not-configured";
  try {
    const r = await (fetchImpl || globalThis.fetch)(RESEND_URL, {
      method: "POST",
      headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
      body: JSON.stringify({ from: FROM, to: [to], subject, text, reply_to: replyTo || CONTACT }),
    });
    if (!r.ok) { console.error("[salon email] Resend " + r.status); return "failed"; }
    return "sent";
  } catch (e) {
    console.error("[salon email] " + (e && e.message));
    return "failed";
  }
}

module.exports = { send, resendKey, CONTACT, FROM };
