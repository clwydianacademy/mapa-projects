/* Clwydian Academy training salon — the few lines every function in site/api/salon/ shares. */
"use strict";

/** Vercel parses JSON and form bodies into req.body; anything else arrives undefined. */
function bodyOf(req) {
  const b = req.body;
  if (b && typeof b === "object" && !Buffer.isBuffer(b)) return b;
  if (typeof b === "string") { try { return JSON.parse(b); } catch { return {}; } }
  return {};
}

function write(res, answer) {
  res.statusCode = answer.status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Robots-Tag", "noindex, nofollow");
  for (const k of Object.keys(answer.headers || {})) res.setHeader(k, answer.headers[k]);
  res.end(JSON.stringify(answer.body));
}

/** Run a handler; anything it throws becomes a plain 500 that names the email address. */
async function run(res, name, fn) {
  try { write(res, await fn()); }
  catch (e) {
    console.error("[salon " + name + "]", e && e.message);
    write(res, { status: 500, body: { ok: false, code: "unavailable", message: "Something went wrong at our end. Please email hello@clwydianacademy.co.uk.", contact: "hello@clwydianacademy.co.uk" } });
  }
}

const notAllowed = (res, allow) => { res.setHeader("Allow", allow); write(res, { status: 405, body: { ok: false, code: "method-not-allowed" } }); };

module.exports = { bodyOf, write, run, notAllowed };
