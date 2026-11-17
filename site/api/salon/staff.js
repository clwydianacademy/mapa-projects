/* POST /api/salon/staff { action } — the staff day sheet: sign in, the day, status changes, move, resize,
 * the learner list, patch-test records. Needs STAFF_PASSWORD; refuses without it. Logic: ../_lib/salon/handlers.js. */
"use strict";
const H = require("../_lib/salon/handlers");
const { bodyOf, run, notAllowed } = require("../_lib/salon/http");

module.exports = (req, res) => {
  if (req.method !== "POST") return notAllowed(res, "POST");
  return run(res, "staff", () => H.staff(H.context(), bodyOf(req), req));
};
