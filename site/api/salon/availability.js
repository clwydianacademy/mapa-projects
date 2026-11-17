/* GET /api/salon/availability?serviceId=&who=&under16=&from=  — a 14-day strip of slots, and the next available.
 * Every slot it returns has passed the same feasible() the save path runs. Logic: ../_lib/salon/handlers.js. */
"use strict";
const H = require("../_lib/salon/handlers");
const { run, notAllowed } = require("../_lib/salon/http");

module.exports = (req, res) => {
  if (req.method !== "GET") return notAllowed(res, "GET");
  return run(res, "availability", () => H.availability(H.context(), req.query || {}, req));
};
