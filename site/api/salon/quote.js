/* GET  /api/salon/quote  — the services, levels and whether booking is open (what the journey draws from)
 * POST /api/salon/quote  — the length, price and deposit of one service at one learner level
 * The logic is in ../_lib/salon/handlers.js. */
"use strict";
const H = require("../_lib/salon/handlers");
const { bodyOf, run, notAllowed } = require("../_lib/salon/http");

module.exports = (req, res) => {
  if (req.method === "GET") return run(res, "quote", () => H.config(H.context()));
  if (req.method === "POST") return run(res, "quote", () => H.quote(H.context(), bodyOf(req)));
  return notAllowed(res, "GET, POST");
};
