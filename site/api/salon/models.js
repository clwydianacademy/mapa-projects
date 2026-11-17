/* POST /api/salon/models — add a name to the salon's model register. Logic: ../_lib/salon/handlers.js. */
"use strict";
const H = require("../_lib/salon/handlers");
const { bodyOf, run, notAllowed } = require("../_lib/salon/http");

module.exports = (req, res) => {
  if (req.method !== "POST") return notAllowed(res, "POST");
  return run(res, "models", () => H.models(H.context(), bodyOf(req), req));
};
