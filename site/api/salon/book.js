/* POST /api/salon/book       — write a booking (re-checked under the lock) and start the deposit payment
 * GET  /api/salon/book?ref=  — the status of one booking, for the client returning from payment
 * Logic: ../_lib/salon/handlers.js. */
"use strict";
const H = require("../_lib/salon/handlers");
const { bodyOf, run, notAllowed } = require("../_lib/salon/http");

module.exports = (req, res) => {
  if (req.method === "GET") return run(res, "book", () => H.bookingStatus(H.context(), req.query || {}, req));
  if (req.method === "POST") return run(res, "book", () => H.book(H.context(), bodyOf(req), req));
  return notAllowed(res, "GET, POST");
};
