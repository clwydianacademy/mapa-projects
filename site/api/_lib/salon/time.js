/* Clwydian Academy training salon — dates and times.
 *
 * Everything is a plain calendar date ("2027-01-11") and minutes past midnight (570 = 09:30) in
 * Europe/London, and the two are never converted except in instantOf(). The functions run on a
 * server in UTC and describe a salon in Wales, so 09:30 must mean 09:30 in St Asaph in January
 * and in June.
 */
"use strict";

const ZONE = "Europe/London";

function parts(ms) {
  const f = new Intl.DateTimeFormat("en-GB", { timeZone: ZONE, hourCycle: "h23",
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  const o = {};
  for (const p of f.formatToParts(new Date(ms))) o[p.type] = p.value;
  return o;
}
/** The London calendar date at an instant. */
function isoDate(ms) { const p = parts(ms); return `${p.year}-${p.month}-${p.day}`; }
/** Minutes past London midnight at an instant. */
function minutesOfDay(ms) { const p = parts(ms); return Number(p.hour) * 60 + Number(p.minute); }

const isDate = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.parse(s + "T00:00:00Z"))
  && new Date(s + "T00:00:00Z").toISOString().slice(0, 10) === s;

function addDays(iso, n) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
const DAY_KEYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
const dayKey = (iso) => DAY_KEYS[new Date(iso + "T00:00:00Z").getUTCDay()];

/** The real instant (epoch ms) of a London wall-clock date and minute. Correct either side of a
 *  clock change: guess UTC, see what London calls that instant, correct by the difference. */
function instantOf(iso, minutes) {
  const guess = Date.parse(iso + "T00:00:00Z") + minutes * 60000;
  const seen = Date.parse(isoDate(guess) + "T00:00:00Z") + minutesOfDay(guess) * 60000;
  return guess - (seen - guess);
}
const hoursUntil = (iso, minutes, now) => (instantOf(iso, minutes) - now) / 3600000;

/** An instant `months` calendar months before another (12 months before 29 Feb is 28 Feb). */
function monthsBefore(ms, months) {
  const d = new Date(ms);
  const day = d.getUTCDate();
  d.setUTCDate(1);
  d.setUTCMonth(d.getUTCMonth() - months);
  const last = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)).getUTCDate();
  d.setUTCDate(Math.min(day, last));
  return d.getTime();
}

function parseClock(s) {
  const m = /^(\d{1,2}):(\d{2})$/.exec(String(s || ""));
  if (!m) throw new Error("not a clock time: " + s);
  return Number(m[1]) * 60 + Number(m[2]);
}
const formatClock = (min) => `${String(Math.floor(min / 60)).padStart(2, "0")}:${String(min % 60).padStart(2, "0")}`;
const roundUp5 = (n) => Math.ceil((n - 1e-9) / 5) * 5;

module.exports = { ZONE, isoDate, minutesOfDay, isDate, addDays, dayKey, instantOf, hoursUntil,
  monthsBefore, parseClock, formatClock, roundUp5 };
