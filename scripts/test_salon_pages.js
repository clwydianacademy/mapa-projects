#!/usr/bin/env node
/* test_salon_pages.js — the training salon's marketing pages, and the switch that keeps them off.

       node --test scripts/test_salon_pages.js

   No dependencies (Node's built-in test runner, and python3 for the build). Two builds are read:

     - the COMMITTED output in site/, which must contain no trace of the salon while
       "public" is false in _data/salon/policy.json — merging must change nothing public;
     - a PREVIEW build with the salon switched on, made in a temporary folder by
       `build.py --salon-preview DIR`, which is what the pages will be when Mark says go.

   The booking engine is not in this repository. It lives in its own repository and its own
   Vercel project; these pages only link to it.
*/
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const REPO = path.join(__dirname, "..");
const SITE = path.join(REPO, "site");
const POLICY = JSON.parse(fs.readFileSync(path.join(REPO, "_data", "salon", "policy.json"), "utf8"));
const BOOK = "https://book.clwydianacademy.co.uk/book/";
const PAGES = ["salon", "salon/prices", "salon/models", "salon/terms", "cy/salon", "cy/salon/prisiau", "cy/salon/modelau", "cy/salon/telerau"];

const PREVIEW = fs.mkdtempSync(path.join(os.tmpdir(), "salon-preview-"));
execFileSync("python3", [path.join(REPO, "website", "_src", "build.py"), "--salon-preview", PREVIEW], { encoding: "utf8" });
test.after(() => fs.rmSync(PREVIEW, { recursive: true, force: true }));

const read = (root, p) => fs.readFileSync(path.join(root, p), "utf8");
const page = (p) => read(PREVIEW, path.join(p, "index.html"));
const visible = (html) => html.slice(html.indexOf("<body")).replace(/<script[\s\S]*?<\/script>/g, " ").replace(/<[^>]+>/g, " ").replace(/&pound;/g, "£").replace(/&rsquo;/g, "’").replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n))).replace(/\s+/g, " ");
const row = (html, name) => { const m = html.match(new RegExp('<tr\\b[^>]*><th scope="row">' + name + "[\\s\\S]*?</tr>")); assert.ok(m, "no row: " + name); return visible("<body>" + m[0]); };
// THE BOOKING SYSTEM'S OWN FIGURES: the only place a price, a time or an opening hour may come from
const FEED = JSON.parse(fs.readFileSync(path.join(REPO, "_data", "salon", "feed.json"), "utf8"));
function walk(dir, out) { for (const f of fs.readdirSync(dir, { withFileTypes: true })) { const p = path.join(dir, f.name); if (f.isDirectory()) walk(p, out); else out.push(p); } return out; }

// =================================================================================================
// The switch is OFF: the committed site has no salon in it
// =================================================================================================
test("flag off: the policy says the salon is not public", () => {
  assert.equal(POLICY.public, false, "_data/salon/policy.json 'public' must stay false until Mark says go");
});

test("flag off: no salon page, no staff page, no salon function, no salon script is in site/", () => {
  for (const p of ["salon", "cy/salon", "staff", "api/salon", "api/_lib", "assets/js/salon-book.js", "assets/js/salon-staff.js", "assets/js/salon-models.js"]) {
    assert.ok(!fs.existsSync(path.join(SITE, p)), "site/" + p + " must not exist while the salon is not public");
  }
  assert.deepEqual(fs.readdirSync(path.join(SITE, "api")), ["enquiry.js"], "the only function is the enquiry form");
});

test("flag off: no page links to the salon, the nav is as it was, and the sitemap and robots do not mention it", () => {
  const html = walk(SITE, []).filter((f) => f.endsWith(".html"));
  assert.ok(html.length >= 57);
  for (const f of html) {
    const text = fs.readFileSync(f, "utf8");
    assert.ok(!/href="\/(cy\/)?salon\//.test(text), path.relative(SITE, f) + " links to the salon");
    assert.ok(!/Our Salon|Ein Salon|book\.clwydianacademy/.test(text), path.relative(SITE, f) + " mentions the salon");
    const nav = text.match(/<nav class="site-nav"[\s\S]*?<\/nav>/);
    if (nav) assert.equal((nav[0].match(/<a /g) || []).length, f.endsWith("404.html") ? 8 : 9, path.relative(SITE, f) + ": the nav has gained or lost a link");
  }
  assert.ok(!/clwydianacademy\.co\.uk\/(cy\/)?salon\//.test(read(SITE, "sitemap.xml")), "the sitemap lists a salon page");
  assert.equal(read(SITE, "robots.txt"), "User-agent: *\nAllow: /\n\nSitemap: https://www.clwydianacademy.co.uk/sitemap.xml\n");
});

test("flag off: the deployed output is byte-for-byte what main deploys", () => {
  // Everything under site/ except the salon stylesheet (which no page loads while the flag is off).
  const out = execFileSync("git", ["--no-optional-locks", "diff", "--name-only", "origin/main", "--", "site"], { cwd: REPO, encoding: "utf8" }).trim().split("\n").filter(Boolean);
  // …and vercel.json, which gains ONE key: the build step that rebuilds a PREVIEW deployment with
  // the switches on. Its redirects must be main's, and the step must do nothing on production.
  assert.deepEqual(out, ["site/assets/css/salon.css", "site/vercel.json"], "site/ differs from main in: " + out.join(", "));
  const mine = JSON.parse(read(SITE, "vercel.json"));
  const mains = JSON.parse(execFileSync("git", ["--no-optional-locks", "show", "origin/main:site/vercel.json"], { cwd: REPO, encoding: "utf8" }));
  assert.deepEqual(Object.keys(mine).sort(), ["buildCommand", "outputDirectory", "redirects"]);
  assert.equal(mine.outputDirectory, ".", "with a build command Vercel needs to be told the built site is this folder");
  assert.deepEqual(mine.redirects, mains.redirects, "the redirects are not main's");
  assert.match(mine.buildCommand, /^cd \.\. && \(python3 website\/_src\/build\.py --vercel \|\| echo /, "the build step is not the guarded preview build");
  for (const env of ["production", "", "development"]) {
    const r = execFileSync("python3", [path.join(REPO, "website", "_src", "build.py"), "--vercel"], { cwd: REPO, encoding: "utf8", env: { ...process.env, VERCEL_ENV: env } });
    assert.match(r, /nothing built/, "VERCEL_ENV=" + JSON.stringify(env) + " built something");
  }
  const after = execFileSync("git", ["--no-optional-locks", "diff", "--name-only", "origin/main", "--", "site"], { cwd: REPO, encoding: "utf8" }).trim().split("\n").filter(Boolean);
  assert.deepEqual(after, out, "a production deployment's build step changed the deployed folder");
});

// =================================================================================================
// The switch is ON (preview build): what the pages will be
// =================================================================================================
test("preview: the eight salon pages are built, in both languages, with nothing unfinished showing", () => {
  for (const p of PAGES) {
    const text = visible(page(p));
    assert.ok(!/\{[a-z_]+\}/.test(text), p + ": an unfilled {token} is visible: " + (text.match(/\{[a-z_]+\}/) || [""])[0]);
    assert.ok(!/\[\('|'\)\]|\bNone\b|\bundefined\b|<function/.test(text), p + ": generator debris is visible");
  }
  for (const gone of ["salon/book", "cy/salon/archebu", "staff"]) assert.ok(!fs.existsSync(path.join(PREVIEW, gone)), gone + " is not part of this site any more");
});

test("preview: the nav item is 'Our Salon' / 'Ein Salon' on every page, and both navs have the same number of links", () => {
  assert.match(read(PREVIEW, "index.html"), /<a href="\/salon\/">Our Salon<\/a>/);
  assert.match(read(PREVIEW, "cy/index.html"), /<a href="\/cy\/salon\/">Ein Salon<\/a>/);
  assert.match(page("salon"), /<a href="\/salon\/" aria-current="page">Our Salon<\/a>/);
});

test("preview: every 'Book' control goes to the booking site, and nothing posts to this site", () => {
  for (const p of PAGES) {
    const html = page(p);
    assert.ok(html.includes('href="' + BOOK + '"'), p + " has no link to the booking site");
    assert.ok(!/\/api\/salon|salon-book\.js|salon-staff\.js|salon-models\.js|id="salon-data"/.test(html), p + " still refers to the removed engine");
    assert.ok(!/<form\b/.test(html.slice(html.indexOf("<main"), html.indexOf("</main>"))), p + " has a form with nowhere to post");
    // a booking link is the booking page itself, or the booking page opened on ONE service the feed lists
    const cy = p.startsWith("cy/");
    const deep = new Set(FEED.services.map((s) => s.book.replace(/&/g, "&amp;") + (cy ? "&amp;lang=cy" : "")).concat(FEED.services.map((s) => s.book + (cy ? "&lang=cy" : ""))));
    for (const m of html.matchAll(/<a\b[^>]*href="(https:\/\/book\.[^"]*)"[^>]*>/g)) assert.ok(m[1] === BOOK || deep.has(m[1]), "an odd booking link: " + m[0]);
  }
});

test("preview: prices — Level 3 is the stylist price; Level 2 is 25% off cutting and styling, 20% off colour, in whole pounds", () => {
  const html = page("salon/prices");
  const want = { "Cut and blow-dry": [26, 35], "Gents cut": [14, 18], "Full head colour": [44, 55], "Root retouch": [30, 38], "Blow-dry": [17, 22], "Half head foils": [48, 60], "Full head foils": [56, 70] };
  for (const name of Object.keys(want)) {
    const r = row(html, name);
    assert.match(r, new RegExp("£" + want[name][0] + "\\b.*£" + want[name][1] + "\\b"), name + ": " + r);
  }
  // every figure on the page is the booking system's: each service in the feed, at each level it is sold at
  let n = 0;
  for (const f of FEED.services) {
    const s = POLICY.services.find((x) => x.id === f.id);
    assert.ok(s, f.id + " is sold by the booking system and is not on the website's list");
    const r = row(html, s.name.en.replace(/[()/]/g, "."));
    for (const level of ["l2", "l3"]) if (f.levels[level]) assert.ok(r.includes("£" + f.levels[level].price), f.id + " at " + level + ": expected £" + f.levels[level].price + " in: " + r);
    n += 1;
  }
  for (const s of POLICY.services) for (const k of ["stylist_price", "base_minutes"]) assert.equal(s[k], undefined, s.id + " still carries " + k + ": the website must hold no figure of its own");
  assert.ok(n >= 10);
});

test("preview: restyle, balayage, colour correction and occasion hair are Level 3 only; there is no graduate tier and no Level 1", () => {
  const html = page("salon/prices");
  for (const name of ["Restyle", "Balayage", "Colour correction", "Occasion hair"]) {
    const r = row(html, name);
    assert.match(r, /Not offered at this level/, name + " must not be offered at Level 2: " + r);
    assert.equal((r.match(/£/g) || []).length, 1, name + " has one price, the Level 3 one: " + r);
  }
  for (const p of PAGES) assert.ok(!/Graduate|graddedig|Level 1|Lefel 1/.test(visible(page(p))), p + " mentions a tier that does not exist");
  assert.deepEqual(Object.keys(POLICY.levels), ["l2", "l3"]);
});

test("preview: a value nobody has decided is never printed; a draft is printed only under a 'Draft' notice", () => {
  const html = page("salon/prices");
  // a service the booking system does not sell cannot be booked, so it is not listed at all
  assert.ok(!/Clipper cut|Hot towel shave/.test(visible(html)), "a service that is not in the booking system's catalogue is on the price list");
  assert.match(html, /Draft/, "durations, deposits and the concession are drafts, so the page says so");
  assert.match(page("cy/salon/prisiau"), /Drafft/);
});

test("preview: adults only — said on the terms page, and nothing about under-16s or guardians remains", () => {
  assert.match(visible(page("salon/terms")), /18 or over/);
  assert.match(visible(page("cy/salon/telerau")), /18 oed neu h[ŷy]n/);
  for (const p of PAGES) assert.ok(!/under 16|under 12|guardian|o dan 16|o dan 12|gwarcheidwad|Children/i.test(visible(page(p))), p + " still talks about children: " + (visible(page(p)).match(/.{30}(under 16|under 12|guardian|o dan 16|gwarcheidwad|Children).{30}/i) || [""])[0]);
});

test("preview: unconfirmed means noindex and out of the sitemap, even with the switch on", () => {
  const sitemap = read(PREVIEW, "sitemap.xml");
  for (const p of PAGES) {
    assert.match(page(p), /<meta name="robots" content="noindex, nofollow">/, p);
    assert.ok(!sitemap.includes("/" + p + "/</loc>"), p + " is in the sitemap");
  }
});

test("preview: HairSalon structured data is tied to the academy's own Organization, with no parent and no phone", () => {
  for (const p of ["salon", "cy/salon"]) {
    const blocks = [...page(p).matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map((m) => JSON.parse(m[1]));
    const org = blocks.find((b) => b["@id"] === "https://www.clwydianacademy.co.uk/#organization" && b.name);
    const salon = blocks.find((b) => b["@type"] === "HairSalon");
    const link = blocks.find((b) => b.department);
    assert.ok(org && salon && link, p);
    assert.equal(link["@id"], org["@id"]); assert.equal(link.department["@id"], salon["@id"]);
    assert.equal(salon.address.streetAddress, undefined); assert.equal(salon.openingHoursSpecification, undefined);
    assert.ok(!/parentOrganization|"telephone"|"founder"|"Person"/.test(JSON.stringify(blocks)));
  }
});

test("preview: the site's own checks pass on the preview build", () => {
  for (const check of ["check_claims", "check_links", "check_locale", "check_forms"]) {
    try { execFileSync("python3", [path.join(REPO, "scripts", check + ".py"), PREVIEW], { encoding: "utf8" }); }
    catch (e) { assert.fail(check + " failed on the preview build:\n" + String(e.stdout).slice(0, 1500)); }
  }
});

test("preview: nothing names the other business, its colour, or a percentage of its prices", () => {
  for (const p of PAGES) {
    const html = page(p);
    assert.ok(!/charlotte[\s._-]*eleanor|#4e1622/i.test(html), p);
    assert.ok(!/% of\b/i.test(visible(html)), p + ": a percentage OF something is printed");
  }
  assert.ok(!/charlotte|eleanor|\bCE\b/i.test(JSON.stringify(POLICY)), "the policy file names the source");
});
