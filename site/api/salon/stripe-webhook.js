/* POST /api/salon/stripe-webhook — Stripe tells us a deposit was paid, a payment page expired, or a refund went out.
 *
 * READ THIS BEFORE MAKING IT LOOK LIKE THE OTHER FILES IN THIS FOLDER.
 *
 * Stripe signs the exact bytes it sent. A body that has been parsed and re-serialised never
 * verifies. So this function must NOT read req.body: on Vercel that property is a getter that
 * parses the body when touched. It reads the request stream itself.
 *
 * NOT YET PROVEN ON VERCEL. If the platform has already consumed the stream, the body read here
 * is empty, the signature fails, and the answer is 400 — nothing is ever marked paid on an
 * unverified body. Send a Stripe test event to a preview deployment before relying on this.
 *
 * The work happens BEFORE the 200: an event we failed to record answers 500, and Stripe retries.
 */
"use strict";
const H = require("../_lib/salon/handlers");
const { write, notAllowed } = require("../_lib/salon/http");

function rawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (c) => { size += c.length; if (size > 1024 * 1024) { reject(new Error("body too large")); req.destroy(); } else chunks.push(Buffer.from(c)); });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

module.exports = async (req, res) => {
  if (req.method !== "POST") return notAllowed(res, "POST");
  try {
    const raw = await rawBody(req);
    write(res, await H.webhook(H.context(), raw, req.headers["stripe-signature"]));
  } catch (e) {
    console.error("[salon stripe-webhook]", e && e.message);
    write(res, { status: 500, body: { ok: false } });          // Stripe retries a 500
  }
};
module.exports.rawBody = rawBody;
