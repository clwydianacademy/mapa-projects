# RELAY — Clwydian Academy website

Two Claudes and one human.

- **PM** — Cowork, in the cloud. Writes briefs, supplies copy and data, researches, verifies
  diffs independently, checks the live site after deploy.
- **Coder** — Claude Code, on Mark's Mac, in this repo.
- **Mark** — reads both, decides anything marked NEEDS A HUMAN, owns every credential.

## Protocol

Append only. Never edit another party's section.

```
## BRIEF nn — <title>            (PM writes)
  what, why, acceptance criteria, anything supplied

## REPORT nn                     (coder writes when done)
  what changed, commit SHAs, what the diff actually contains,
  anything done that the brief did not ask for,
  ### WELSH FOR REVIEW
  ### NEEDS A HUMAN

## COWORK VERIFICATION nn        (PM writes after reading the real diff)
  verified / defects found / what the live site shows
```

Rules that make it work:

1. The PM verifies from `git --no-optional-locks show` and the built files, **never from the
   coder's summary**. On the booking system this caught seven defects the summaries missed.
2. The coder never guesses on regulatory, funding or Welsh-language copy. It goes under
   NEEDS A HUMAN and work stops on that item.
3. `CLAUDE.md` beats any brief. A brief that contradicts it gets challenged, not followed.
4. The PM cannot start, stop or prompt the coder — that is a separate terminal on the Mac.
   If the tree has uncommitted changes, or nothing has been committed for an hour with items
   open, the PM says plainly that the coder needs restarting.
5. One task at a time. The coder does not start the next brief early.

---

## BRIEF 01 — reconcile the generator with the live site

**Why.** `website/_src/build.py` is a working static-site generator that was abandoned in July
2026. Thirteen commits in August — the de-PLA work, the independence rebuild, the Charlotte
Roberts correction — went straight into the deployed HTML and never reached the source. The
generator therefore still carries `parentOrganization: Charlotte Eleanor Group`,
`legalName: Charlotte Eleanor Academy C.I.C.`, a PLA-based description, a Deeside address, a
GitHub Pages output path, and no Welsh at all. Running it today would push all of that back onto
a live site that is applying for public funding. Before we build anything new in code, the
generator has to be able to faithfully reproduce what is live.

**Do.**

1. Clone to `/Users/markparker/Desktop/Clwydian Academy/mapa-projects` so the PM can read the
   diffs. Branch `site-rebuild`.
2. Move `scripts/check_claims.py` in from `../website rebuild handoff/`. Run it against
   `clwydian-academy 2` and **report the failures without fixing them.** The PM expects roughly
   four and wants the exact list first.
3. Regenerate `website/_src/pages/*.html` from the deployed HTML, not from the stale `_src`.
4. Repair `build.py`: real paths, output to `clwydian-academy 2`, no CNAME, no `.nojekyll`,
   `ORG` dict replaced with the live values from `CLAUDE.md`.
5. Add Welsh as a **locale**, not a second set of fragments. CY output at `/cy/...`, `hreflang`
   pairs in every head, nav parity.
6. Build, then diff output against the deployed HTML. **The diff must be empty except for
   changes you can name and justify.** That list is the deliverable.

**Acceptance.** Build runs clean · diff explained line by line · `check_claims.py` findings
listed · every EN page has a CY counterpart · sitemap regenerated · nothing pushed to `main`.

**Not in this brief.** Do not fix the content the linter flags — Brief 02 does that with copy
the PM supplies. Do not start the CPD calendar.

**Supplied.** `CLAUDE.md` and `scripts/check_claims.py`, in
`/Users/markparker/Desktop/Clwydian Academy/website rebuild handoff/`.


---

## REPORT 01

**Coder, 11 September 2026, 11:55.** Branch `site-rebuild`, five commits on top of `main`
(`40723c9`), pushed to origin. Nothing on `main`. Working tree clean; a second run of
`build.py` produces no diff.

| SHA | What |
|---|---|
| `1352d9c` | `CLAUDE.md`, `prompts/RELAY.md`, `scripts/check_claims.py` — copied unchanged from the handoff folder |
| `f635915` | July generator imported **verbatim** so its repair is diffable (it was never in git — it lived at `Desktop/Clwydian Academy/website/_src/`, not in this repo, and `clwydian-academy-preview/` is not in the repo either) |
| `f4aa92b` | Generator source regenerated from the deployed HTML; `build.py` repaired; Welsh as a locale |
| `8b1914c` | Build output — the diff against the deployed HTML, every line named below |
| *(this)* | REPORT 01 |

Verify from `git --no-optional-locks show 8b1914c` (output) and `git --no-optional-locks diff
f635915 f4aa92b -- website/_src/build.py` (what changed in the generator).

### 1. `check_claims.py` on the live site: 83 findings on 30 of 39 pages, not four

Nothing fixed. Breakdown:

| Kind | Count | Where |
|---|---|---|
| BANNED `Charlotte Parker` | 25 | All in the **Organization JSON-LD `founder` block**, not visible prose: `/404.html`, `/privacy/`, all 10 EN course pages, all 10 CY course pages, `/cy/cysylltu/`, `/cy/i-salonau/`, `/cy/preifatrwydd/`. The August "Charlotte Roberts in structured data" commits reached 14 pages and stopped. |
| LEVEL | 19 | UNHB385 / UNHB379 shown as Level 3 (courses hub, CPD hub, both course pages, EN+CY); UHB204/205/206 shown as Level 3 on `/contact/` and `/cy/cysylltu/` |
| DURATION | 18 | UHB204 "4 Mondays", UHB205 "6 Mondays", UHB206 "4 Mondays", UNHB385 "4 Mondays", UNHB379 "4 weeks / 4 wythnos" — hubs and course pages, EN+CY |
| PLA outside funding pages | 9 | Every EN course page (`\bPLA\b` in body or JSON-LD); no CY course page trips it |
| BARBERING six-month | 4 | `/courses/nvq-level-2-barbering/` (four phrasings) |
| BANNED `Check PLA funding` | 3 | barbering, NVQ2, NVQ3 course pages |
| BANNED in-house quality | 4 | `/apprenticeships/` ×2, `/courses/nvq-level-2-hairdressing/`, `/for-salons/` |
| BANNED `franchise network` | 1 | `/courses/nvq-level-2-barbering/` |

The raw run, for the record:

```
check_claims: 39 pages scanned — 83 finding(s)

  /404.html                                  [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /apprenticeships/                          [BANNED]  'in-house internal quality'
                                               → quality assurance is independent and external, not in-house
  /apprenticeships/                          [BANNED]  'in-house quality'
                                               → quality assurance is independent and external, not in-house
  /contact/                                  [LEVEL]  'UHB204 shown as Level 3'
                                               → UHB204 is Level 2
  /contact/                                  [LEVEL]  'UHB205 shown as Level 3'
                                               → UHB205 is Level 2
  /contact/                                  [LEVEL]  'UHB206 shown as Level 3'
                                               → UHB206 is Level 2
  /courses/                                  [DURATION]  'UHB204 shown as 4 Mondays'
                                               → UHB204 is 6 weeks (six)
  /courses/                                  [DURATION]  'UHB205 shown as 6 Mondays'
                                               → UHB205 is 8 weeks (eight)
  /courses/                                  [DURATION]  'UHB206 shown as 4 Mondays'
                                               → UHB206 is 6 weeks (six)
  /courses/                                  [DURATION]  'UNHB379 shown as 4 weeks'
                                               → UNHB379 is 6 weeks (six)
  /courses/                                  [DURATION]  'UNHB385 shown as 4 Mondays'
                                               → UNHB385 is 5 weeks (five)
  /courses/                                  [LEVEL]  'UNHB379 shown as Level 3'
                                               → UNHB379 is Level 2
  /courses/                                  [LEVEL]  'UNHB385 shown as Level 3'
                                               → UNHB385 is Level 2
  /courses/consultation-retail-cpd/          [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/consultation-retail-cpd/          [DURATION]  'UNHB385 shown as 4 Mondays'
                                               → UNHB385 is 5 weeks (five)
  /courses/consultation-retail-cpd/          [LEVEL]  'UNHB385 shown as Level 3'
                                               → UNHB385 is Level 2
  /courses/consultation-retail-cpd/          [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /courses/cpd-courses/                      [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/cpd-courses/                      [DURATION]  'UHB204 shown as 4 Mondays'
                                               → UHB204 is 6 weeks (six)
  /courses/cpd-courses/                      [DURATION]  'UHB205 shown as 6 Mondays'
                                               → UHB205 is 8 weeks (eight)
  /courses/cpd-courses/                      [DURATION]  'UHB206 shown as 4 Mondays'
                                               → UHB206 is 6 weeks (six)
  /courses/cpd-courses/                      [DURATION]  'UNHB379 shown as 4 weeks'
                                               → UNHB379 is 6 weeks (six)
  /courses/cpd-courses/                      [DURATION]  'UNHB385 shown as 4 Mondays'
                                               → UNHB385 is 5 weeks (five)
  /courses/cpd-courses/                      [LEVEL]  'UNHB379 shown as Level 3'
                                               → UNHB379 is Level 2
  /courses/cpd-courses/                      [LEVEL]  'UNHB385 shown as Level 3'
                                               → UNHB385 is Level 2
  /courses/hair-extensions-course/           [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/hair-extensions-course/           [DURATION]  'UHB206 shown as 4 Mondays'
                                               → UHB206 is 6 weeks (six)
  /courses/hair-extensions-course/           [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /courses/hair-relaxing-course/             [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/hair-relaxing-course/             [DURATION]  'UHB205 shown as 6 Mondays'
                                               → UHB205 is 8 weeks (eight)
  /courses/hair-relaxing-course/             [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /courses/nvq-level-2-barbering/            [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/nvq-level-2-barbering/            [BANNED]  'Check PLA funding'
                                               → PLA is not a promise the academy can make
  /courses/nvq-level-2-barbering/            [BANNED]  'franchise network'
                                               → no graduate route into a CEG franchise network
  /courses/nvq-level-2-barbering/            [BARBERING]  '6 month'
                                               → barbering is a 32-week Tuesday twilight course
  /courses/nvq-level-2-barbering/            [BARBERING]  'Six month'
                                               → barbering is a 32-week Tuesday twilight course
  /courses/nvq-level-2-barbering/            [BARBERING]  'six month'
                                               → barbering is a 32-week Tuesday twilight course
  /courses/nvq-level-2-barbering/            [BARBERING]  'six-month'
                                               → barbering is a 32-week Tuesday twilight course
  /courses/nvq-level-2-barbering/            [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /courses/nvq-level-2-hairdressing/         [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/nvq-level-2-hairdressing/         [BANNED]  'Check PLA funding'
                                               → PLA is not a promise the academy can make
  /courses/nvq-level-2-hairdressing/         [BANNED]  'in-house quality'
                                               → quality assurance is independent and external, not in-house
  /courses/nvq-level-2-hairdressing/         [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /courses/nvq-level-3-hairdressing/         [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/nvq-level-3-hairdressing/         [BANNED]  'Check PLA funding'
                                               → PLA is not a promise the academy can make
  /courses/nvq-level-3-hairdressing/         [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /courses/perming-course/                   [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/perming-course/                   [DURATION]  'UHB204 shown as 4 Mondays'
                                               → UHB204 is 6 weeks (six)
  /courses/perming-course/                   [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /courses/salon-business-course/            [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/salon-business-course/            [DURATION]  'UNHB379 shown as 4 weeks'
                                               → UNHB379 is 6 weeks (six)
  /courses/salon-business-course/            [LEVEL]  'UNHB379 shown as Level 3'
                                               → UNHB379 is Level 2
  /courses/salon-business-course/            [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /courses/skin-cancer-awareness/            [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /courses/skin-cancer-awareness/            [PLA]  'PLA'
                                               → PLA may only appear on the funding and funders pages
  /cy/cyrsiau/                               [DURATION]  'UNHB379 shown as 4 wythnos'
                                               → UNHB379 is 6 weeks (six)
  /cy/cyrsiau/                               [LEVEL]  'UNHB379 shown as Level 3'
                                               → UNHB379 is Level 2
  /cy/cyrsiau/                               [LEVEL]  'UNHB385 shown as Level 3'
                                               → UNHB385 is Level 2
  /cy/cyrsiau/barbro-nvq-lefel-2/            [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/cwrs-busnes-salon/             [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/cwrs-busnes-salon/             [DURATION]  'UNHB379 shown as 4 wythnos'
                                               → UNHB379 is 6 weeks (six)
  /cy/cyrsiau/cwrs-busnes-salon/             [LEVEL]  'UNHB379 shown as Level 3'
                                               → UNHB379 is Level 2
  /cy/cyrsiau/cwrs-estyniadau-gwallt/        [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/cwrs-llacio-gwallt/            [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/cwrs-permio/                   [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/cyrsiau-dpp/                   [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/cyrsiau-dpp/                   [DURATION]  'UNHB379 shown as 4 wythnos'
                                               → UNHB379 is 6 weeks (six)
  /cy/cyrsiau/cyrsiau-dpp/                   [LEVEL]  'UNHB379 shown as Level 3'
                                               → UNHB379 is Level 2
  /cy/cyrsiau/cyrsiau-dpp/                   [LEVEL]  'UNHB385 shown as Level 3'
                                               → UNHB385 is Level 2
  /cy/cyrsiau/dpp-ymgynghori-a-manwerthu/    [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/dpp-ymgynghori-a-manwerthu/    [LEVEL]  'UNHB385 shown as Level 3'
                                               → UNHB385 is Level 2
  /cy/cyrsiau/trin-gwallt-nvq-lefel-2/       [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/trin-gwallt-nvq-lefel-3/       [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cyrsiau/ymwybyddiaeth-canser-y-croen/  [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cysylltu/                              [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/cysylltu/                              [LEVEL]  'UHB204 shown as Level 3'
                                               → UHB204 is Level 2
  /cy/cysylltu/                              [LEVEL]  'UHB205 shown as Level 3'
                                               → UHB205 is Level 2
  /cy/cysylltu/                              [LEVEL]  'UHB206 shown as Level 3'
                                               → UHB206 is Level 2
  /cy/cysylltu/                              [LEVEL]  'UNHB385 shown as Level 3'
                                               → UNHB385 is Level 2
  /cy/i-salonau/                             [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /cy/preifatrwydd/                          [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy
  /for-salons/                               [BANNED]  'quality assurance run in-house'
                                               → quality assurance is independent and external
  /privacy/                                  [BANNED]  'Charlotte Parker'
                                               → wrong name — Charlotte Roberts, Director of the Academy

FAIL — fix these, or change CLAUDE.md and say why in prompts/RELAY.md.
```

### 2. What the generator is now

```
website/_src/
  build.py        chrome for both locales, ORG, NAV, sitemap, robots  -> writes clwydian-academy 2/
  extract.py      the reverse: deployed HTML -> pages/, jsonld/, pages.json  (used once, for this brief)
  pages.json      registry: 20 pages, each with en {path,title,desc} and cy {...} (404 has no cy)
  pages/en/*.html pages/cy/*.html   body fragments = the contents of <main id="main">, verbatim
  jsonld/en/*.json jsonld/cy/*.json page-specific JSON-LD (Course, BreadcrumbList, FAQPage, ...)
  preview.py      untouched — still has the sandbox paths; not in the brief
```

- Paths are relative to the repo. Output is `clwydian-academy 2`. No `CNAME`, no `.nojekyll` written.
- `ORG` is the live homepage block: `alternateName` Clwydian Academy CBC, no `legalName`, no
  `parentOrganization`, St Asaph / Denbighshire, Mark Parker CEO, Charlotte Roberts Director,
  `knowsLanguage` en+cy. `sameAs` carries the one LinkedIn URL the live site already had.
- Welsh is a locale: one `pages.json`, one `NAV`, one `CHROME` dict with the EN and CY strings
  side by side. Every page gets `hreflang` en / cy / x-default, a `lang-switch` link to its
  counterpart, and `og:locale` cy_GB / en_GB. The Welsh chrome strings are the ones already
  live, copied character for character. The Welsh **body** copy is necessarily a second set of
  fragments (`pages/cy/`) — a translation cannot be derived from the English — but there is one
  set of page definitions, which is what I took the brief to mean.
- Two chrome facts are per page in `pages.json`: `nav` (which item is `aria-current`) and
  `legal` — see NEEDS A HUMAN 1.

Run: `python3 website/_src/build.py && python3 scripts/check_claims.py "clwydian-academy 2"`.

### 3. The diff, line by line (`8b1914c`)

37 of 39 HTML pages differ; `/apprenticeships/` and `/cy/prentisiaethau/` are byte-identical.
No body copy changed on any page — every difference is in the head, the chrome, or whitespace.

**Substantive — 27 pages + sitemap**

1. **25 pages, one line each:** Organization JSON-LD `founder[1].name` `Charlotte Parker` →
   `Charlotte Roberts`. Consequence of step 4 (one `ORG` dict from `CLAUDE.md`); the block is now
   identical to the live homepage's on every page. This clears 25 of the 83 linter findings
   ahead of Brief 02 — see NEEDS A HUMAN 3.
2. **`/funding/`:** `twitter:description` was a shorter string than the meta description; the
   generator derives all three from one `desc`, so it now matches (gains "Fast-track NVQ £4,500
   all-in."). Its Organization block was a third variant — `legalName: "Clwydian Academy CBC"`,
   `identifier` Companies House 17330962, and a funding-flavoured description — now the site-wide
   block. See NEEDS A HUMAN 2.
3. **`/cy/ffioedd-a-chyllid/`:** had **no** Organization block at all — now has the site-wide
   one. `og:description` and `twitter:description` now equal the meta description (gain "NVQ
   carlam £4,500 yn cynnwys popeth."). Skip-link `Neidio i'r cynnwys` → `Neidio i&rsquo;r
   cynnwys` (the other 18 Welsh pages use the curly form). Footer tagline was a different
   sentence from the other 18 Welsh pages; now the majority one — both quoted under WELSH FOR
   REVIEW.
4. **`sitemap.xml`:** same 38 URLs, same hreflang alternates, same priorities (checked by
   sorted comparison). Order is now all EN then all CY (the live file had the eight July-11
   pages interleaved at the end); `lastmod` is the build date on every URL, where the live file
   said 2026-07-06 / 2026-07-11 for pages edited in August.

**Whitespace only — 10 pages** (`/`, `/about/`, `/courses/`, `/for-salons/`, `/funders/`,
`/contact/`, `/cy/`, `/cy/amdanom/`, `/cy/cyllidwyr/`, `/cy/cyrsiau/`): the blank line before
`</main>` is gone (23 pages had one, 16 didn't); every file now ends `</html>\n` (26 live files
had no trailing newline); `/contact/` and `/cy/cyrsiau/` had `  </html>` indented. `git diff -w
--ignore-blank-lines` hides all of this and shows only items 1–4.

**Unchanged:** `robots.txt` byte-identical. `assets/`, `favicon.*`, `README.md`, `CNAME` not
touched by the build.

### 4. Acceptance

- Build runs clean — yes, and a second run is a no-op.
- Diff explained line by line — section 3.
- `check_claims.py` findings listed — section 1. On the build output: **58** (the same 83 minus
  the 25 JSON-LD name hits), all in body fragments, all for Brief 02.
- Every EN page has a CY counterpart — 19 of 20. `/404.html` has none and never did; Vercel
  serves the one 404 for both languages. Nav parity: 9 links in each header, same order.
- Internal links: 1,404 root-relative `href`/`src` references checked across the built tree, 0
  broken.
- Sitemap regenerated — yes, 38 URLs with alternates.
- Nothing pushed to `main` — correct. `site-rebuild` is pushed (Vercel preview).

### 5. Done that the brief did not ask for

- Committed the July generator verbatim before repairing it (`f635915`), so the repair is a
  readable diff rather than a new file.
- Committed `extract.py`. It is the audit trail for how `pages/` was produced and the tool for
  the next time someone edits the deployed HTML by hand.
- Whitespace normalisation and the `/cy/ffioedd-a-chyllid/` chrome unification (section 3).
- `sameAs` left with the LinkedIn URL that was live, rather than emptied — the opening brief
  said "stays empty until Mark confirms the socials", but emptying it would have removed
  something already published. Flagged, not decided.

### WELSH FOR REVIEW

No new Welsh was written. Three existing strings were chosen between or moved:

- `/cy/ffioedd-a-chyllid/` footer tagline, now the sentence used on the other 18 Welsh pages:
  "Hyfforddiant trin gwallt galwedigaethol carlam yn Llanelwy — wedi'i enwi ar ôl Bryniau Clwyd,
  ac wedi'i adeiladu ar gyfer pobl sy'n newid gyrfa ledled Gogledd Cymru a'r gororau."
  The sentence it replaces on that one page: "… wedi'i adeiladu ar gyfer newidwyr gyrfa ar draws
  Gogledd Cymru a siroedd y ffin." A native speaker should say which is better and it should
  then be the only one.
- `/cy/ffioedd-a-chyllid/` `og:description` / `twitter:description` now carry the page's own
  meta description, which ends "NVQ carlam £4,500 yn cynnwys popeth."
- Skip link on that page: straight apostrophe → `&rsquo;`, matching the rest of the Welsh site.

### NEEDS A HUMAN

1. **Footer legal line.** Two of 39 pages (`/funding/`, `/cy/ffioedd-a-chyllid/`) carry
   "Clwydian Academy CBC (Cwmni Buddiant Cymunedol) · Company no. 17330962 · Registered office:
   2 Bod Hyfryd, Rhes-y-Cae, Holywell CH8 8JG." The other 37 carry "a community benefit
   company, constituted as a Community Interest Company." The generator reproduces both via a
   `legal` flag per page, so nothing changed. UK companies are generally required to show
   registered name, number and office on their website; if that applies, the registered line
   should be site-wide. Mark decides; it is a one-word change per page in `pages.json`.
2. **Organization JSON-LD extras.** `/funding/` alone had `legalName: "Clwydian Academy CBC"`
   and a Companies House `identifier` 17330962. `CLAUDE.md` forbids only the *old* legalName.
   Should both go site-wide in `ORG`? Until decided they are dropped (item 3.2 above).
3. **25 linter findings cleared ahead of Brief 02.** Unavoidable with one `ORG` dict — the
   alternative is a generator that emits a banned name. Say if you want it otherwise.
4. **`README.md` inside `clwydian-academy 2`** still describes GitHub Pages hosting and calls the
   academy "trading name of Charlotte Eleanor Academy C.I.C." The linter only scans `.html`, so
   it passes silently. Vercel returns 404 for `/README.md` (checked), so it is not public — but
   it is in the deployed folder. Brief 02 copy, or delete?
5. **`CNAME`** is still in `clwydian-academy 2` and is served at `/CNAME` (200). The build no
   longer writes it; I did not delete it. Delete?
6. **`sameAs`** — see section 5.
7. **`sitemap.xml` `lastmod`** is now the build date for every URL on every build. Fine, or
   derive from git?

**Addendum, 11 September 2026, 12:05 — branch not pushed.** `git push -u origin site-rebuild`
was refused: `Permission to markp-del/mapa-projects.git denied to markp-del` (HTTP 403). The
keychain token is the same one that pushes `charlotte-eleanor-booking` fine, so it is almost
certainly a fine-grained token limited to selected repositories that does not include
`mapa-projects`. I have not touched the credential. All five commits are local on
`site-rebuild` in the shared folder, so the PM can read them now; the Vercel preview will
appear once Mark either adds `mapa-projects` to the token's repository list or runs the push
himself:

```
cd "/Users/markparker/Desktop/Clwydian Academy/mapa-projects" && git push -u origin site-rebuild
```

Added to NEEDS A HUMAN as item 8. Section 4's "site-rebuild is pushed" is therefore not yet
true.

---

## COWORK VERIFICATION 01

**PM, 11 September 2026.** Verified from the repository, not from REPORT 01. Everything below
was re-derived independently before reading the report's corresponding claim.

### Verified

| Claim | How checked | Result |
|---|---|---|
| `main` untouched | `git log main` | tip still `40723c9`. Clean. |
| Six commits on `site-rebuild`, tree clean | `git log main..site-rebuild`, `git status` | Confirmed (five + the addendum). |
| **The committed output is the generator's output** | re-ran `python3 website/_src/build.py`, then `git status` | **No diff.** This is the claim that mattered most and it holds. |
| Deployed-folder diff is small and named | `git diff --numstat main..site-rebuild -- "clwydian-academy 2"` | 38 files, +131 / −153. |
| No body copy changed | `git diff -w --ignore-blank-lines`, unique changed lines | Only Organization JSON-LD (27+/26−), three `/cy/ffioedd-a-chyllid/` chrome lines, sitemap. Nothing else. |
| 25 × `Charlotte Parker` on live | `git grep -o` on `main` | Exactly 25, across 25 files. |
| 0 after the build | `git grep -o` on `site-rebuild` | Zero. |
| Organization block now uniform | parsed every `EducationalOrganization` block in the built tree | 39 pages, **1 distinct variant**. `alternateName` Clwydian Academy CBC · no `parentOrganization` · St Asaph / Denbighshire · Mark Parker + Charlotte Roberts. |
| Linter 83 → 58 | ran `check_claims.py` against `main` (via `git archive`) and against the build | 83 and 58, kind-for-kind. |

REPORT 01 contained one inaccuracy — §4's "site-rebuild is pushed" — which the coder found and
corrected itself in the addendum before I read it. Nothing else in the report overstated what
the diff does.

### One defect, and it is mine

**Seven of the nineteen LEVEL findings are false positives caused by my linter, not by the site.**
`/contact/` and `/cy/cysylltu/` carry an enquiry dropdown:

```
NVQ Level 3 Hairdressing (fast-track)
CPD — Hair Extensions (UHB206)
CPD — Perming & Texture (UHB204)
```

My 220-character proximity window read the `Level 3` from one `<option>` as a claim about the
unit code in the next one. UHB204/205/206 are not labelled Level 3 anywhere on those pages.

Fixed: level and duration claims are now tested **within a single block-level element**, so a
claim cannot bleed across list items, table rows or options. Inline tags don't break a segment,
so `<strong>Level 3</strong> UNHB385` still trips correctly.

**True counts: 76 on the live site, 51 on the build output** — not 83 and 58. The corrected
`check_claims.py` is in `../website rebuild handoff/`. Move it in as the first commit of Brief 02
so the fix is a reviewable diff.

### Decisions on NEEDS A HUMAN

1. **Footer legal line — go site-wide.** I read the statute rather than a summary of it.
   Regulation 25 of the Company, LLP and Business (Names and Trading Disclosures) Regulations
   2015 requires disclosure **"on — (a) its business letters; (b) its order forms; and (c) its
   websites"** of the part of the UK in which the company is registered, the registered number,
   and the registered office address — and it separately requires a **community interest company
   to identify its status**. Websites are named in the regulation. Practitioner guidance is that
   it need not be on every page so long as it is easily found, but a footer is the cheap,
   unambiguous answer. So: `legal: true` on all 39 pages.
   Two conditions. **(a)** Take the "part of the United Kingdom" wording verbatim from the
   Companies House record for 17330962 — do not infer it from the address. **(b)** The current
   line names a residential registered office; Mark has been told and it is his call, and when
   the St Asaph lease completes and the registered office moves, the footer follows from one
   string in `pages.json`.
2. **Organization JSON-LD extras — put both back, site-wide.** `legalName: "Clwydian Academy
   CBC"` is the correct current legal name and `identifier` 17330962 is a verifiable Companies
   House number that helps search engines resolve the entity to the right company. `CLAUDE.md`
   bans the *old* legalName only; I have amended it to say so explicitly. Add
   `"legalName": "Clwydian Academy CBC"` and the `identifier` to `ORG`.
3. **25 findings cleared early — approved.** The alternative was a generator that emits a banned
   name. Right call.
4. **`README.md` in the deployed folder — delete it.** It describes GitHub Pages hosting that is
   dead and calls the academy a "trading name of Charlotte Eleanor Academy C.I.C." — the exact
   related-party claim this whole exercise removes. That it currently 404s is a hosting
   coincidence, not a safeguard. Delete, and extend the linter to scan `.md` and `.txt` in the
   deployed tree so the next one cannot hide.
5. **`CNAME` — delete.** GitHub Pages artefact, served at `/CNAME` with a 200.
6. **`sameAs` — keep the LinkedIn URL.** My opening brief said "empty until Mark confirms"; you
   were right to flag rather than delete something already published. It is Mark's public
   professional profile and it strengthens entity linkage. Keep exactly the one URL.
7. **`sitemap.xml` `lastmod` — derive from git.** A sitemap claiming all 38 URLs changed today on
   every build teaches crawlers to ignore the field. Use the last commit date touching that
   page's source fragment (`git log -1 --format=%cI -- <fragment>`), falling back to the build
   date for a page with no history.
8. **Push — Mark's, not ours.** Neither of us touches the credential. He adds `mapa-projects` to
   the token's repository list or runs the push himself.

Brief 02 follows.

---

## BRIEF 02 — make every claim on the site one the academy can evidence

**Why.** 51 true findings stand on the build output. They are not cosmetic: a course sold as
Level 3 that is Level 2, a six-week course advertised as four, and a PLA funding promise the
academy cannot honour are the three things most likely to be read by a Medr or National Lottery
assessor, or by a salon owner who later feels misled. Everything here is a correction toward
what is already true in the schemes of learning.

**Order of work.** Commit 1: the corrected linter. Commit 2: housekeeping (items 4–7 above).
Commit 3: English claim fixes. Commit 4: Welsh. Commit 5: rebuild + report.

### 1. Levels — 12 findings

`UNHB385` and `UNHB379` are **Level 2**, not Level 3, everywhere they appear: `/courses/`,
`/courses/cpd-courses/`, `/courses/consultation-retail-cpd/`, `/courses/salon-business-course/`
and the four Welsh counterparts. `UNHB374` stays Level 3 — it genuinely is.

### 2. Durations — 18 findings

Replace with the true figures from the schemes of learning. These are the awarding body's
guided-learning hours, not marketing lengths:

| Unit | Currently advertised | Correct | GLH |
|---|---|---|---|
| UHB204 Perming | 4 Mondays | **6 Mondays** | 93 |
| UHB205 Relaxing | 6 Mondays | **8 Mondays** | 125 |
| UHB206 Extensions | 4 Mondays | **6 Mondays** | 90 |
| UNHB385 Consultation | 4 Mondays | **5 Mondays** | 60 |
| UNHB379 Salon Business | 4 weeks / 4 wythnos | **6 Mondays / 6 dydd Llun** | 75 |

Welsh numerals and `Lefel 3` → `Lefel 2` are mechanical — make them directly.

### 3. Barbering — 4 findings

`/courses/nvq-level-2-barbering/` sells a six-month fast-track. The course is **32 weeks,
one evening a week — Tuesdays 5pm to 9pm — plus timetabled distance learning**, with the
showcase as a Saturday event. Rewrite the four six-month phrasings to that. Do not carry the
"six months, not two years" framing across from the hairdressing page; it is not true here.

While you are on that page: `franchise network` → graduate routes are **employment, chair
rental, or a mobile business** (the August wording used elsewhere on the site).

### 4. PLA — 9 findings plus 3 CTAs

Remove `Check PLA funding` from the barbering, NVQ2 and NVQ3 course pages; the August standard
CTA is **"Am I funded? Check your options"** linking to `/funding/`. Remove every other `PLA` /
`Personal Learning Account` occurrence from the nine English course pages, in body copy and in
JSON-LD. Permitted funding language, and the only permitted funding language: fully funded
apprenticeship route under the Welsh framework · ReAct+ support up to £1,500 · instalments of
£500 plus £500 × 8 · self-funded £4,500. PLA survives only on `/funding/` and `/funders/`.

### 5. In-house quality assurance — 4 findings

`/apprenticeships/` ×2, `/courses/nvq-level-2-hairdressing/`, `/for-salons/`. Use the phrase
already deployed elsewhere: **"independent internal quality assurance"**. Do not upgrade it into
a claim about external verification that has not happened.

### 6. Welsh

Numerals and level numbers: change directly. **Prose changes — barbering, the franchise line,
the PLA sentences — draft them, do not skip them** (leaving a wrong Welsh claim live is worse
than an unreviewed correct one), and list **every** new or changed Welsh string under
`### WELSH FOR REVIEW` with the English it renders. A native-speaker review of the whole Welsh
site is an open action of Mark's from August; this list feeds it.

**Acceptance.** `check_claims.py` returns **0** on the build output · a second build is a no-op ·
`main` untouched · every changed Welsh string listed · no claim strengthened beyond what the
schemes of learning support · `git diff -w` reviewed by you before committing.

**Not in this brief.** The CPD calendar and the `_data/cpd-2027.json` work — that is Brief 03,
and the PM has the verified dataset ready. Do not start it.

**Supplied.** Corrected `check_claims.py` and an amended `CLAUDE.md` in
`/Users/markparker/Desktop/Clwydian Academy/website rebuild handoff/`.

---

## RUN INSTRUCTION — continuous working, from Mark

Mark has asked for a continuous run rather than a stop after each brief. **Work 02 → 03 → 04
without waiting for a COWORK VERIFICATION between them.** The PM verifies afterwards, from the
commits. Three things make that safe, and they are not optional.

**1. Each brief is gated by a machine check, not by your judgement.** Do not begin the next
brief until the gate on the one before it passes:

| Gate | Command | Must be |
|---|---|---|
| after 02 | `python3 scripts/check_claims.py "clwydian-academy 2"` | `0 findings` |
| after 02 and 03 | `python3 website/_src/build.py && git --no-optional-locks status --porcelain` | empty |
| after 03 | `python3 scripts/check_dates.py` (you write it — see Brief 03) | `0 problems` |

If a gate fails, stay on that brief until it passes. A failing gate is the one thing that
legitimately consumes the whole hour.

**2. Never halt the run for a decision — log it and move on.** Anything needing Mark goes under
`### NEEDS A HUMAN` in that brief's report and you continue with the next item. The only things
that stop work entirely: a credential prompt of any kind, anything that would touch `main`, and
anything that would publish. Stop, write it down, carry on with what is left.

**3. Commit per step, never in a lump.** Small commits with real messages are what lets the PM
unpick a wrong turn without losing the right ones. Nothing is pushed. Nothing goes near `main`.

Write a separate `## REPORT 02`, `## REPORT 03`, `## REPORT 04` as you finish each, not one
report at the end — if the run is interrupted, whatever is finished is still reviewable. Finish
with a one-line `## RUN SUMMARY` naming which briefs completed, which gates passed, and how many
items are sitting under NEEDS A HUMAN.

Commit `prompts/RELAY.md` as it stands now as your first commit — the PM edited it in the
working tree and cannot commit to this repo.

---

## BRIEF 03 — the CPD calendar, from data

**Why.** Ten cohorts, 54 dates, seven prices derived from one tariff, in two languages. Kept as
prose it will be wrong within a month and wrong in Welsh first. Kept as data it regenerates,
and it can carry `CourseInstance` structured data with real start dates — which is what lets a
search for "hair extensions course St Asaph" surface an actual date.

**Supplied.** `../website rebuild handoff/cpd-2027.json` → commit to `_data/cpd-2027.json`.
Every date, price, level, GLH and day-count in it has been generated and independently
re-verified. **Treat it as read-only input.** If something in it looks wrong, say so in the
report — do not correct it.

**Do.**

1. `scripts/check_dates.py` — a guard, the same shape as `check_claims.py`. Re-derives from
   `_data/cpd-2027.json`: every date falls on its strand's weekday; no date falls on a listed
   closure; no two cohorts in one strand share a date; `len(dates) == days`; and
   `price == round((fixed + per_glh × glh) / 5) × 5`, plus £50 for UHB206. Exit 1 on any
   problem. This is the gate for this brief and it must pass.
2. New page `/courses/cpd-calendar/` and its Welsh counterpart, generated from the data:
   the two strands side by side, each cohort with its unit code, level, GLH, academy days, the
   individual dates, price, assessment and client requirement; the closure list; the tariff
   stated as the formula it is (`£160.81 + £4.274 × GLH`, rounded to £5) with both published
   anchors named; and the team-rate tiers. Nav entry under Courses in both languages.
3. On each existing CPD course page, inject that unit's **next start date and full date list**
   from the same data — EN and CY. No dates typed by hand anywhere.
4. `Course` + `CourseInstance` JSON-LD on the calendar page and on each CPD course page:
   `startDate`, `endDate`, `courseMode` `Blended`, `location` St Asaph, `offers` with the seat
   price in GBP, `maximumAttendeeCapacity` 10. Validate the JSON parses before committing.
5. `UNHB374 Colour & Lightening` has **no course page yet** — it appears on the calendar and
   links to `/courses/cpd-courses/`. Do not invent a page for it; that is Brief 05 with copy
   from the PM.
6. Welsh: take course names, and any phrasing you can, from the existing Welsh course pages
   rather than translating afresh. Everything genuinely new goes under `WELSH FOR REVIEW`.

**Acceptance.** `check_dates.py` 0 · `check_claims.py` still 0 · build is a no-op on second run ·
every date on the site traceable to `_data/cpd-2027.json` · JSON-LD parses · nav parity.

---

## BRIEF 04 — the guards, widened

Overflow work. All of it is machine-checkable and none of it needs a decision, so it is the
right thing to fill the end of a run with.

1. **Linter scans more than HTML.** Extend `check_claims.py` to `.md`, `.txt` and `.json` in the
   deployed tree. The `README.md` that Verification 01 told you to delete is the reason; the
   guard should mean the next one cannot hide.
2. **`scripts/check_links.py`** — commit the internal link check you ran by hand in Brief 01, so
   it is repeatable: every root-relative `href`/`src` in the built tree resolves to a file.
   Exit 1 on any break.
3. **`scripts/check_locale.py`** — every EN page has a CY counterpart and the reverse (`/404.html`
   excepted); every page's `hreflang` pair round-trips to a page that points back; nav item
   counts match between locales.
4. **Alt text audit.** List every `<img>` in the built tree without a non-empty `alt`. Fix the
   decorative ones with `alt=""`; anything needing real words goes in the report for the PM to
   write, not guessed.
5. Run all four guards plus the build and put the output in `REPORT 04`.

Do not start Brief 05.


---

## REPORT 02

**Coder, 11 September 2026, 21:10.** Brief 02 complete. Both gates pass. `main` still `40723c9`. Nothing pushed.

| SHA | Step |
|---|---|
| `8deb647` | 1/5 corrected `check_claims.py`, amended `CLAUDE.md` (with Mark's footer decision recorded), PM's VERIFICATION 01 + BRIEF 02 |
| `0dcffd2` | 2/5 housekeeping — README/CNAME deleted, ORG `legalName` + `identifier`, git `lastmod`, linter reach |
| `6b425d1` | 3/5 English claim fixes |
| `8c4b260` | RELAY: RUN INSTRUCTION, BRIEF 03, BRIEF 04 as the PM wrote them (committed as instructed) |
| `42ad4db` | 4/5 Welsh claim fixes |
| `bb57d3b` | 4b Welsh contact meta description (last CDP) |
| `d9c0e44` | 5/5 build output — linter clean |
| `cf79128` | 6 contact-form 'fast-track' barbering option; CPD hub eyebrow |
| `a7eb941` | 7 build output — linter clean |

### Gates

```
python3 scripts/check_claims.py "clwydian-academy 2"        -> check_claims: 40 pages scanned — clean.
python3 website/_src/build.py && git status --porcelain     -> (empty)
```

### Mark's instruction on the footer

Mark, to the coder, 11 September: "Keep it as it is currently for the address please." I read
that as overriding decision 1 (registered line site-wide). The footer is unchanged — the
registered line stays on `/funding/` and `/cy/ffioedd-a-chyllid/` only — and `CLAUDE.md`'s
trading-disclosure section now records that as Mark's decision, with the statutory point left
open for him. If the PM reads Mark's sentence differently, it is a one-word change per page in
`pages.json` and no other code.

### What changed (all in `website/_src/`, output regenerated)

- **Levels** — UNHB385 and UNHB379 are Level 2 / Lefel 2 on both hubs, both course pages, their
  JSON-LD, EN and CY. "Regulated advanced unit" → "Regulated unit".
- **Durations** — UHB204 6, UHB205 8, UHB206 6, UNHB385 5, UNHB379 6 Mondays, in every kicker,
  eyebrow, Duration row, lede, section heading, JSON-LD description and `courseWorkload`
  (P6W/P8W/P5W), EN and CY. CPD hub "four or six of them" → "five to eight of them". Relaxing
  "just over £115 per week" → "under £90 per week" (695 ÷ 8 = £86.88).
- **Barbering** — 32-week Tuesday twilight course, 5pm–9pm, timetabled distance learning,
  Saturday showcase: h1, lede, eyebrow, Duration and Format rows, section h2 and paragraph,
  progression line, JSON-LD name/description/`courseWorkload` P32W, page title and meta
  description, and the barbering cards on `/` and `/courses/`. EN and CY. The "six months, not
  two years" framing is gone from the page.
- **PLA** — CTAs on barbering, NVQ2, NVQ3 → "Am I funded? Check your options" (the August
  homepage CTA) / "Ydw i'n cael cyllid? Gwiriwch eich opsiynau" (the Welsh homepage CTA).
  "; PLA drawdown follows Medr registration" removed from Centre status on all ten course pages,
  and its Welsh "; daw cyllid CDP yn dilyn cofrestriad Medr" from nine. No PLA/CDP outside
  `/funding/`, `/funders/` and their Welsh mirrors.
- **QA** — "independent internal quality assurance" / "sicrwydd ansawdd mewnol annibynnol" on
  apprenticeships, NVQ2, for-salons (EN 4 places, CY 5 — the Welsh had one more bare "mewnol").
- **Franchise** — barbering progression line and NVQ2 "supported franchise business through the
  Charlotte Eleanor Group" → employment, chair rental or a mobile business, EN and CY.

### Done that the brief did not list

1. **The Welsh site was carrying PLA under its Welsh name.** The linter's PLA rule was
   English-only, and its `PLA_ALLOWED` list used guessed slugs (`/cy/funding/`) rather than the
   real ones, so no Welsh page could ever trip it. Added `CDP` / `Cyfrif Dysgu Personol` to the
   rule and the real slugs to the allow-list: 14 findings surfaced — three "Gwirio cyllid CDP"
   buttons, nine Centre-status clauses, the contact form's "cymhwysedd CDP" option and label, and
   the contact page's meta description. All fixed (commits 4/5, 4b).
2. **`Charlotte Eleanor Group` banned outright** in the linter (the email domain does not match
   the regex; the funders page has no other use of the phrase). It caught the NVQ2 "franchise
   business through the Charlotte Eleanor Group" line that `franchise network` missed.
3. Contact form option "NVQ Level 2 Barbering (fast-track)" and the CPD hub eyebrow "1–5 day
   intensives" corrected (commit 6). Neither is linter-reachable.
4. The relaxing JSON-LD offer text "Complete six-week programme" → eight-week.
5. Housekeeping items 4–7 from Verification 01 done as decided (commit 2/5).

### WELSH FOR REVIEW

No native-speaker review has happened. Every changed Welsh string, with the English it renders.
Mechanical numeral/level changes first, then drafted prose.

**Mechanical** (same change on every page listed):
| Welsh (after) | English | Where |
|---|---|---|
| `Lefel 2 UNHB385`, `Lefel 2 UNHB379` (was Lefel 3) | Level 2 | cyrsiau, cyrsiau-dpp, dpp-ymgynghori-a-manwerthu, cwrs-busnes-salon + JSON-LD |
| `6 dydd Llun` (was 4) · `Y chwe dydd Llun` (was Y pedwar) · `chwe dydd Llun` in JSON-LD | 6 Mondays / The six Mondays | UHB204 cwrs-permio, UHB206 cwrs-estyniadau-gwallt, both hubs |
| `8 dydd Llun` (was 6) · `wyth dydd Llun` · `Wyth dydd Llun, wedi'u strwythuro` · `Rhaglen wyth wythnos gyflawn` | 8 Mondays / Eight Mondays, structured / Complete eight-week programme | UHB205 cwrs-llacio-gwallt + JSON-LD, both hubs |
| `5 dydd Llun` (was 4) · `Y pum dydd Llun` · `pum dydd Llun` | 5 Mondays / The five Mondays | UNHB385 dpp-ymgynghori-a-manwerthu + JSON-LD, both hubs |
| `6 dydd Llun` (was `4 wythnos`) · `chwe dydd Llun hwn` (was `pedair wythnos hwn`) · `6 dydd Llun, amserlen strwythuredig` | 6 Mondays (was 4 weeks) / this six-Monday masterclass / 6 Mondays, structured timetable | UNHB379 cwrs-busnes-salon + JSON-LD, both hubs |
| `rhwng pump ac wyth ohonynt` (was `pedwar neu chwech ohonynt`) | five to eight of them | cyrsiau-dpp |
| `Llai na £90 yr wythnos` (was `Ychydig dros £115`) | Under £90 per week | cwrs-llacio-gwallt |
| `Arholiad theori allanol swyddogol VTCT + asesiad ymarferol model byw` (week numbers removed) | Official VTCT external theory exam + live-model practical assessment | cwrs-permio, cwrs-llacio-gwallt |
| `Uned reoledig — statws proffesiynol go iawn, nid seminar gwerthu` (was `Uned uwch reoledig — bri proffesiynol go iawn…`) | Regulated unit — genuine professional standing, not a sales seminar | dpp-ymgynghori-a-manwerthu |
| `Mae'r dosbarth meistr Lefel 2 hwn` (was Lefel 3) | This Level 2 masterclass | dpp-ymgynghori-a-manwerthu lede |
| `Daw'r gymeradwyaeth cyn cyflwyno` / `…cyn y garfan gyntaf` (clause after `;` removed) | Approval precedes first delivery / the first cohort | nine course pages |
| `sicrwydd ansawdd mewnol annibynnol` (was `…mewnol` or `…mewnol yn cael ei redeg gennym ni ein hunain`) | independent internal quality assurance | prentisiaethau ×3, trin-gwallt-nvq-lefel-2, i-salonau |
| `32 wythnos, un noson yr wythnos` (was `6 mis`) | 32 weeks, one evening a week | barbering cards on /cy/ and /cy/cyrsiau/ |

**Drafted** — barbering page `/cy/cyrsiau/barbro-nvq-lefel-2/` and its JSON-LD:
| Welsh (new) | English it renders |
|---|---|
| Cwrs gyda'r hwyr · Dechreuwyr a thrinwyr gwallt sy'n croesfapio | Twilight course · Beginners & cross-mapping hairdressers (also fixes the typo `s'yn` → `sy'n`) |
| Barbro NVQ Lefel 2, un noson yr wythnos. | NVQ Level 2 Barbering, one evening a week. |
| …mae ein diploma gyda'r hwyr 32 wythnos yn mynd â chi yno un nos Fawrth yr wythnos, o amgylch y swydd sydd gennych eisoes. | …our 32-week twilight diploma takes you there one Tuesday evening a week, around the job you already have. |
| 32 wythnos, carfannau wedi'u capio ar 10 | 32 weeks, cohorts capped at 10 |
| Un noson yr wythnos — nos Fawrth, 5pm i 9pm, yn Llanelwy / Dysgu o bell wedi'i amserlennu rhwng sesiynau; digwyddiad dydd Sadwrn yw'r arddangosfa | One evening a week — Tuesdays, 5pm to 9pm, at St Asaph / Timetabled distance learning between sessions; the showcase is a Saturday event |
| Un noson yr wythnos. Nid tri diwrnod yr wythnos yn y coleg, nid dwy flynedd o ryddhau am ddiwrnod. | One evening a week. Not three days a week at college, not two years on day-release. |
| Mae ein model gyda'r hwyr — un nos Fawrth yr wythnos yn yr academi, 5pm i 9pm, gyda dysgu o bell wedi'i amserlennu rhyngddynt — yn eich cael yn gymwysedig mewn 32 wythnos heb ildio'ch swydd bob dydd. | Our twilight model — one Tuesday evening a week at the academy, 5pm to 9pm, with timetabled distance learning between — gets you qualified in 32 weeks without giving up your day job. |
| Llwybrau ymlaen i Drin Gwallt NVQ Lefel 2 a Lefel 3, a llwybrau graddedigion i gyflogaeth, rhentu cadair neu fusnes symudol | Progression routes into NVQ Level 2 Hairdressing and Level 3, and graduate routes into employment, chair rental or a mobile business |
| JSON-LD name: Diploma NVQ Lefel 2 mewn Barbro — Gyda'r Hwyr | NVQ Level 2 Diploma in Barbering — Twilight |
| JSON-LD description: Cwrs barbro gyda'r hwyr 32 wythnos yn Llanelwy: un noson yr wythnos (nos Fawrth 5pm–9pm) ynghyd â dysgu o bell wedi'i amserlennu, yn arwain at gymhwyster barbro VTCT NVQ Lefel 2. | 32-week twilight barbering course in St Asaph: one evening a week (Tuesdays 5pm–9pm) plus timetabled distance learning, leading to a VTCT NVQ Level 2 barbering qualification. |
| Title: Cwrs Barbro NVQ Lefel 2, Un Noson yr Wythnos \| Clwydian Academy | NVQ Level 2 Barbering Course, One Evening a Week |
| Meta: Barbwr cymwysedig mewn 32 wythnos, un nos Fawrth yr wythnos. … | Qualified barber in 32 weeks, one Tuesday evening a week. … |

**Drafted** — elsewhere:
| Welsh (new) | English | Where |
|---|---|---|
| Ydw i'n cael cyllid? Gwiriwch eich opsiynau | Am I funded? Check your options (copied from the live Welsh homepage) | barbro, trin-gwallt-nvq-lefel-2, trin-gwallt-nvq-lefel-3 |
| Cwestiwn cyllid — ReAct+, prentisiaethau, rhandaliadau | Funding question — ReAct+, apprenticeships, instalments | cysylltu form option |
| (yn ein helpu i wirio eich opsiynau cyllid) | (helps us check your funding options) | cysylltu form label |
| …holwch am eich opsiynau cyllid… | …ask about funding options… | cysylltu meta description |
| neu fusnes symudol eich hun gyda chefnogaeth lawn | or a fully supported mobile business of your own (copied from the live Welsh homepage) | trin-gwallt-nvq-lefel-2 |
| Barbro NVQ Lefel 2 (gyda'r hwyr, un noson yr wythnos) | NVQ Level 2 Barbering (twilight, one evening a week) | cysylltu form option |
| I weithwyr proffesiynol cymwysedig · O un diwrnod i wyth dydd Llun | For qualified professionals · From one day to eight Mondays | cyrsiau-dpp eyebrow |

### NEEDS A HUMAN

1. **The CPD week-by-week schedules are now shorter than the courses.** Perming, extensions
   and consultation list four "Week n" items under a heading that now says six (or five)
   Mondays; relaxing lists weeks 1–6 under eight. I did not write weeks 5–8 — that is scheme-of-
   learning content I do not have. The exam/practical week numbers in the Assessment rows were
   removed rather than guessed. The PM has the schemes: supply the week plans (EN; I will draft
   CY) and the exam placement, and the blocks can be completed. Until then the pages are
   incomplete, not wrong.
2. **"Twilight"** is my word for the barbering format, chosen because CLAUDE.md uses it. If
   Mark markets it as something else ("evening course", "Tuesday club"), it is in eleven
   strings, all listed above.
3. **`/courses/` section eyebrow** still says "Fast-track NVQ diplomas · 6 months" over three
   cards, one of which is now the 32-week barbering course. The two hairdressing diplomas are
   six months, so the line is two-thirds true. Suggest "NVQ diplomas · fast-track and twilight",
   but that is copy, so not done.
4. **CPD hub pricing sentence** ("Relaxing & Smoothing is £695 and Skin Cancer Awareness £195;
   the remaining masterclasses are enquire-for-pricing while launch dates are finalised") is
   about to be false once Brief 03 publishes the tariff. Brief 03 replaces it with data-driven
   text; noting here so the PM knows it was seen.


---

## REPORT 03

**Coder, 11 September 2026, 21:17.** Brief 03 complete. All three gates pass. `main` still `40723c9`. Nothing pushed.

| SHA | Step |
|---|---|
| `9c4dd71` | 1/4 `_data/cpd-2027.json` as supplied; `scripts/check_dates.py` |
| `978e2ca` | 2/4 `website/_src/cpd.py`, build integration, registry entry, placeholders, links |
| `0baa29b` | 3/4 build output |
| *(this)* | 4/4 REPORT 03 |

### Gates

```
python3 scripts/check_dates.py                              -> 10 cohorts, 54 dates, 5 closures — 0 problems.
python3 scripts/check_claims.py "clwydian-academy 2"        -> 42 pages scanned — clean.
python3 website/_src/build.py && git status --porcelain     -> (empty)
```
Every JSON-LD block on the built site parses (114 blocks; 38 `CourseInstance`s carry
`startDate`/`endDate`). 1,569 root-relative references, 0 broken. Both navs 9 links.

### What was built

- **`_data/cpd-2027.json`** committed unchanged. Nothing in it looked wrong; the guard
  re-derives every rule the brief listed and passes. A deliberately broken copy trips six.
- **`/courses/cpd-calendar/` and `/cy/cyrsiau/calendr-dpp/`**, rendered by `cpd.py` from the
  data: the two strands side by side (weekday, hours, teaching days, seats), each cohort as a
  card with unit, level (Award where flagged), GLH, day count, start and end, the full date run
  grouped by month, price per seat (with the UHB206 kit note), assessment and what to bring, and
  a link to its course page. UNHB374 links to the CPD hub with "Course page to follow". Then the
  tariff as the formula it is (`£160.81 + £4.274 × GLH`, rounded to £5, both anchors named, the
  £50 kit supplement), the team-rate tiers, the closure list, and a CTA.
- **Each of the six CPD course pages** gains two rows in its at-a-glance panel, EN and CY:
  *Next start* (weekday date · strand · day count · price per seat · seats) and *2027 dates*
  (the full run; two cohorts where the unit runs twice) with a link to the calendar. The rows
  are injected at build from a `<!-- cpd-dates -->` placeholder — no date is typed in a fragment.
- **JSON-LD**: the calendar page carries one `Course` per unit (seven) each with its
  `CourseInstance`s; every CPD course page's existing `Course` block now has a
  `hasCourseInstance` list from the data — `startDate`, `endDate`, `courseMode` Blended,
  `courseWorkload` `PT<GLH>H`, St Asaph `location`, `maximumAttendeeCapacity` 10, and an
  `Offer` in GBP at the seat price, plus a `Course`-level `Offer`. `@id`s are shared between the
  calendar and the course page so both describe the same entity.
- **Navigation**: the footer's *Courses* column (the nav labelled "Courses") gains "CPD calendar
  2027" / "Calendr DPP 2027"; the CPD hub's pricing paragraph and its CTA lede now point at the
  calendar; the courses hub's CPD lede links to it. Sitemap has 40 URLs with alternates.
- `lastmod` for the calendar and the six CPD pages also follows the data file and `cpd.py`.

### WELSH FOR REVIEW

All new. The course names are the ones on the live Welsh CPD hub, except UNHB374 (drafted,
marked). Chrome and labels for the calendar, from `cpd.py`:

| Welsh | English |
|---|---|
| Hafan | Home |
| Cyrsiau | Courses |
| Calendr DPP 2027 | CPD Calendar 2027 |
| Dosbarthiadau meistr DPP · Ionawr – Gorffennaf 2027 · Llanelwy | CPD masterclasses · January – July 2027 · St Asaph |
| Calendr DPP 2027. | The 2027 CPD calendar. |
| Dau linyn, deg carfan, pob dyddiad wedi’i bennu. Mae pob carfan wedi’i chapio ar ddeg sedd. Daw’r prisiau o un tariff cyhoeddedig, nid o drafodaeth. | Two strands, ten cohorts, every date fixed. Each cohort is capped at ten seats. Prices come from one published tariff, not a negotiation. |
| Holi / cadw sedd | Enquire / reserve a seat |
| Llinyn | Strand |
| diwrnod dysgu | teaching days |
| Lefel | Level |
| Dyfarniad | Award |
| GLH | GLH |
| sedd y garfan | seats per cohort |
| Yn dechrau | Starts |
| yn gorffen | ends |
| Dyddiadau | Dates |
| Pris | Price |
| y sedd | per seat |
| Asesu | Assessment |
| Beth i ddod gyda chi | What you bring |
| Manylion y cwrs | Course details |
| Tudalen cwrs i ddilyn — gweler dosbarthiadau meistr DPP | Course page to follow — see CPD masterclasses |
| Dyddiau cau’r academi | Academy closures |
| Nid oes carfan yn cyfarfod ar y dyddiau hyn; mae’r dyddiadau uchod eisoes yn eu hepgor. | No cohort meets on these days; the dates above already skip them. |
| Wythnos yn dechrau | Week commencing |
| Sut mae pob pris yn cael ei osod | How every price is set |
| Y tariff | The tariff |
| Un fformiwla yw pob pris sedd ar y dudalen hon: <strong>£{fixed} + £{per_glh} × oriau dysgu dan arweiniad</strong>, wedi’i dalgrynnu i’r £{round_to} agosaf. | Every seat price on this page is one formula: <strong>£{fixed} + £{per_glh} × guided learning hours</strong>, rounded to the nearest £{round_to}. |
| Mae wedi’i angori ar ddau bris cyhoeddedig — {anchors} — ac mae Estyniadau Gwallt yn cario atodiad o £50 am wallt a phecyn y brand partner. | It is anchored on two published prices — {anchors} — and Hair Extensions carries a £50 supplement for brand-partner hair and kit. |
| Cyfraddau tîm | Team rates |
| Archebwch o un salon, campfa neu glinig a chaiff yr archeb gyfan ei gostwng: | Book from one salon, gym or clinic and the whole booking is discounted: |
| {a}–{b} o bobl: {pct}% i ffwrdd | {a}–{b} people: {pct}% off |
| {a} o bobl (carfan gyfan): {pct}% i ffwrdd | {a} people (a whole cohort): {pct}% off |
| Dewiswch ddyddiad. Yna dywedwch wrthym. | Pick a date. Then tell us. |
| Cofrestrwch eich diddordeb gyda’r garfan rydych ei heisiau a byddwn yn cadarnhau’r sedd. | Register your interest with the cohort you want and we will confirm the seat. |
| Cofrestru diddordeb | Register interest |
| Dechrau nesaf | Next start |
| Dyddiadau 2027 | 2027 dates |
| Calendr llawn, dyddiau cau a thariff: | Full calendar, closures and tariff: |
| Calendr DPP 2027 | CPD calendar 2027 |
| Carfan | Cohort |
| Llinyn | Strand |
| Lliwio a Goleuo *(UNHB374 — drafted, no Welsh page exists)* | Colour & Lightening |
| Calendr DPP 2027 *(footer)* | CPD calendar 2027 |
| Calendr DPP Ionawr – Gorffennaf 2027 \| Clwydian Academy *(title)* | CPD Calendar January – July 2027 |
| Pob carfan DPP 2027 yn Llanelwy gyda dyddiadau, prisiau, lefelau ac oriau dysgu dan arweiniad — llinynnau dydd Llun a dydd Mercher, dyddiau cau'r academi a'r tariff cyhoeddedig. *(meta)* | Every 2027 CPD cohort at St Asaph with dates, prices, levels and guided learning hours — Monday and Wednesday strands, academy closures and the published tariff. |
| Mae pob carfan 2027 — dyddiadau, prisiau, lefelau ac oriau dysgu dan arweiniad — ar y calendr DPP, ynghyd â'r tariff y daw'r prisiau ohono. *(cyrsiau-dpp)* | Every 2027 cohort — dates, prices, levels and guided learning hours — is on the CPD calendar, together with the tariff the prices come from. |
| Mae calendr 2027 wedi'i gyhoeddi — dewiswch eich dyddiadau, yna cofrestrwch eich diddordeb. *(cyrsiau-dpp CTA)* | The 2027 calendar is published — choose your dates, then register your interest. |
| Mae pob dyddiad 2027 ar y calendr DPP. *(cyrsiau)* | Every 2027 date is on the CPD calendar. |

Assessment, requirement and price-note strings — the data supplies these in English only:

| Welsh | English |
|---|---|
| Portffolio a phapur amlddewis allanol | Portfolio and an external multiple-choice paper |
| Portffolio | Portfolio |
| Portffolio, papur uned a phapur trosfwaol | Portfolio, a unit paper and an overarching paper |
| Gwybodaeth yn unig | Knowledge only |
| Tri chleient ar wahanol gamau aildyfiant, a phedwerydd i lenwi bylchau | Three clients at different stages of regrowth, plus a fourth to fill gaps |
| Modelau ar draws y technegau dirwyn a ddysgir | Models across the winding techniques taught |
| Un arsylwad ar gleient sydd eisoes ag estyniadau wedi’u gosod | One observation on a client who already has extensions fitted |
| Cleientiaid ar gyfer tystiolaeth ymgynghori a manwerthu | Clients for consultation and retail evidence |
| Dim — dim angen cymhwyster blaenorol | None — no prior qualification needed |
| Prawf croen wedi’i archebu a’i gofnodi cyn pob sesiwn cleient | A skin test booked and recorded before every client session |
| Mae’r tri arsylwad yn digwydd mewn amgylchedd gwaith go iawn | All three observations take place in a real working environment |
| yn cynnwys gwallt a phecyn y brand partner | includes brand-partner hair and kit |

Month and weekday names (Ionawr … Gorffennaf; Dydd Llun, Dydd Mercher) are standard.

### NEEDS A HUMAN

1. **"Nav entry under Courses."** The primary nav is flat — no dropdowns exist in the CSS or
   JS — so I put the entry in the footer nav that is labelled *Courses*, and linked from both
   hubs. If Mark wants it in the header bar, that is a ninth top-level item and a design call.
2. **Prices are now published for four units that were "enquire for pricing"** on the live
   site: Perming £560, Extensions £595, Consultation £415, Salon Business £480 — on the calendar
   and in the *Next start* row of each course page. They are the tariff's own figures, but they
   were not public before today.
3. **UNHB374 in Welsh** is "Lliwio a Goleuo" — drafted, nothing to copy from.
4. **"Next start" moves with the build date.** It is the first cohort starting on or after the
   day of the build. Once a cohort has started, the row is stale until someone rebuilds; there
   is no scheduled rebuild. Worth a note in whatever release routine emerges.
5. **Data observation, not a correction:** `UV21577` is flagged `"award": true` and rendered as
   "Level 2 (Award)"; the live course page says "VTCT Level 2 Award". Consistent. Nothing else
   in the file gave me pause.
6. The CPD hub cards still show a price on only two of six (the two the live site had). Adding
   the tariff price to every card is a one-line change in `cpd.py` if wanted — left as is.


---

## REPORT 04

**Coder, 11 September 2026, 21:18.** Brief 04 complete. Four guards, all passing, all committed. `main` still
`40723c9`. Nothing pushed.

| SHA | Step |
|---|---|
| `9bd43ae` | 1/5 `check_claims.py` scans `.json` as well as `.html`, `.md`, `.txt` |
| `7f24065` | 2/5 `scripts/check_links.py` |
| `06029c3` | 3/5 `scripts/check_locale.py` |
| — | 4/5 alt-text audit — nothing to change, see below |
| *(this)* | 5/5 REPORT 04 |

### The guards and the build, run together

```
$ python3 website/_src/build.py | tail -1
built sitemap.xml (40 urls), robots.txt
$ python3 scripts/check_claims.py "clwydian-academy 2"
check_claims: 42 pages scanned — clean.
$ python3 scripts/check_dates.py
check_dates: 10 cohorts, 54 dates, 5 closures — 0 problems.
$ python3 scripts/check_links.py "clwydian-academy 2"
check_links: 1571 internal references checked — 0 broken.
$ python3 scripts/check_locale.py "clwydian-academy 2"
check_locale: 41 pages — every EN page has a CY mirror and back, navs match, sitemap complete.
$ git --no-optional-locks status --porcelain
(empty)
```

Each guard was also run against a deliberately broken copy of the tree and failed as it
should (a removed Welsh page, a misspelt href, a Tuesday date, a wrong price, a duplicate date).

### What each guard covers

- **`check_claims.py`** — banned phrases (old entity, parent organisation, Charlotte Eleanor
  Group, Charlotte Parker, franchise/sister framing, in-house QA, Deeside, PLA CTAs), PLA/CDP
  outside the funding pages, unit level and duration per segment, barbering six-month
  phrasings; `.html`, `.md`, `.txt`, `.json` anywhere in the deployed tree.
- **`check_dates.py`** — `_data/cpd-2027.json`: weekday per strand, closures, no shared dates
  in a strand, date counts, strand totals, term bounds, tariff arithmetic.
- **`check_links.py`** — every root-relative `href`, `src`, `srcset`, `poster`, `data` in the
  built HTML resolves to a file (directory URLs need an `index.html`).
- **`check_locale.py`** — `<html lang>`, the three `hreflang`s with `x-default` = `en`, the
  counterpart exists and points straight back, the header language switch agrees, nav link
  counts match, and the sitemap lists every indexable page in both languages and nothing else.

### Alt-text audit

145 `<img>` elements in the built tree have no non-empty `alt`. All 145 already carry
`alt=""`; none is missing the attribute.

| Count | Image | Context | Verdict |
|---|---|---|---|
| 82 | `seal.svg` | brand mark inside `<a class="brand" aria-label="Clwydian Academy — home">` (header + footer) | decorative, the link is labelled — correct as is |
| 62 | `seal.svg` | `class="watermark" aria-hidden="true"` section backdrops | decorative — correct as is |
| 1 | `seal-512.png` | `/404.html`, the seal above "Page not found" | **content image with empty alt — PM to decide.** The same image on the homepage has `alt="Clwydian Academy seal on a heather field"`; on a 404 page it may be decorative, in which case `alt=""` is right. Not guessed. |

No image was changed.

### NEEDS A HUMAN

1. The 404 page seal — decorative (leave `alt=""`) or content (PM supplies the words)?

---

## RUN SUMMARY

Briefs 02, 03 and 04 completed in one run (23 commits on `site-rebuild` since `main`,
none pushed, `main` untouched). Gates: after 02 — `check_claims` 0 and clean rebuild, passed;
after 03 — `check_dates` 0, `check_claims` 0, clean rebuild, passed; after 04 — all four guards
and the build, passed. Under NEEDS A HUMAN: 4 items in REPORT 02, 6 in REPORT 03, 1 in
REPORT 04 — 11 in total, none blocking. Still open from before the run: the push (token scope,
Mark's) and Mark's footer decision, which is applied and recorded in CLAUDE.md.

---

## COWORK VERIFICATION 02–04

**PM, 11 September 2026.** Re-derived independently before reading REPORT 02, 03 or 04.

### Gates re-run by me, not taken on trust

| Gate | Result |
|---|---|
| `check_claims.py` | 42 files scanned — **clean** |
| `check_dates.py` | 10 cohorts, 54 dates, 5 closures — **0 problems** |
| `check_links.py` | 1,571 internal references — **0 broken** |
| `check_locale.py` | 41 pages — every EN page mirrored and back, navs match, sitemap complete |
| build is a no-op | **yes** (the one "change" on my run was an untracked `__pycache__/` my own run created) |
| `main` untouched | **yes**, still `40723c9`. 23 commits on `site-rebuild`, none pushed. |

`_data/cpd-2027.json` is byte-identical to what I supplied — treated as read-only input, as asked.
All 54 dates and all 10 prices appear on the built calendar page and match the dataset exactly;
9 JSON-LD blocks parse; 10 `CourseInstance` entries.

Two of my own checks raised false alarms before I caught them: dates are rendered grouped by
month ("11, 18, 25 January · 1, 8, 15, 22 February") and prices as `&pound;`, so a naive
substring search reports 26 missing dates and 10 missing prices. They are all present. Noting it
because the same trap will catch the next person who audits this page.

### Defect — four wrong URLs in the structured data, one root cause

**The second run of a repeated cohort inherits the previous cohort's course URL.**

| Page | Cohort | Start | `offers.url` says | Should say |
|---|---|---|---|---|
| `/courses/cpd-calendar/` | `unhb379-b2` | 2027-06-16 | `/courses/consultation-retail-cpd/` | `/courses/salon-business-course/` |
| `/courses/cpd-calendar/` | `uv21577-b2` | 2027-07-28 | `/courses/consultation-retail-cpd/` | `/courses/skin-cancer-awareness/` |
| `/cy/cyrsiau/calendr-dpp/` | `unhb379-b2` | 2027-06-16 | `/cy/cyrsiau/dpp-ymgynghori-a-manwerthu/` | `/cy/cyrsiau/cwrs-busnes-salon/` |
| `/cy/cyrsiau/calendr-dpp/` | `uv21577-b2` | 2027-07-28 | `/cy/cyrsiau/dpp-ymgynghori-a-manwerthu/` | `/cy/cyrsiau/ymwybyddiaeth-canser-y-croen/` |

Both locales, same two cohorts, and both sit after `unhb385-b` in the data — a page variable
carried forward across iterations rather than being read per cohort. The individual course pages
are clean, so it is the calendar generator only. Prices, dates, durations and levels on those
same entries are all correct, which is why every gate passed: **nothing tested that a
`CourseInstance` points at the course it describes.** That is the gap, more than the bug.

### Accepted, not defects

- `UNHB374` Course `url` points at `/courses/cpd-calendar/` rather than the `/courses/cpd-courses/`
  hub my brief suggested. Yours is better — the calendar is the page that actually describes that
  course. Keep it.
- `__pycache__/` under `website/_src/` is untracked and ungitignored. Housekeeping, below.

REPORT 02, 03 and 04 were accurate about what they changed. The run did what was asked.

---

## BRIEF 05 — the URL leak, and a guard that would have caught it

Small and surgical. Do this before any new pages.

1. **Fix the leak in the calendar generator.** Read the course page per cohort inside the loop
   rather than carrying it between iterations. Both locales. Rebuild; the four URLs above must
   resolve to the right course.
2. **Close the gap in `check_dates.py`.** For every `Course` / `CourseInstance` in the built tree:
   the instance's `startDate` must match a cohort in `_data/cpd-2027.json`; `offers.price` must
   equal that cohort's price; and both the `Course.url` and the `offers.url` must be that
   cohort's `page_en` on an English page and `page_cy` on a Welsh one — falling back to the
   calendar page where the cohort has no course page (UNHB374). Exit 1 on any mismatch. Confirm
   it **fails on the current output before you fix the generator**, then passes after. A guard
   never seen to fail is not a guard.
3. **`.gitignore`** — add `__pycache__/` and `*.pyc`, and remove the tracked-nothing directory
   sitting under `website/_src/`.
4. Re-run all five guards and the build. `REPORT 05`, short.

**Not in this brief.** The `UNHB374 Colour & Lightening` course page still does not exist. It
needs English copy and a Welsh draft from me, and it is the next thing I write — do not draft it
yourself. Same for the salon section.


---

## REPORT 05

**Coder, 12 September 2026, 10:12.** Brief 05 complete. All five guards pass; rebuild is a no-op; `main` still
`40723c9`; nothing pushed (token, as before).

| SHA | Step |
|---|---|
| `c21cbfd` | RELAY: COWORK VERIFICATION 02–04 and BRIEF 05 as the PM wrote them |
| `bd5230c` | 1/4 `check_dates.py` audits every dated `CourseInstance` in the built tree — **seen failing first: 4 problems, exactly the PM's four URLs** |
| `5042386` | 2/4 `cpd.py`: `page_for(c, loc)` is read per cohort inside the loop; rebuild — 0 problems |
| `95119fb` | 3/4 `.gitignore` (`__pycache__/`, `*.pyc`, `.DS_Store`); the stray `__pycache__` removed |
| `(3b)` | sitemap `lastmod` refreshed — see the process note below |
| *(this)* | 4/4 REPORT 05 |

### Guards and build

```
build                     -> built sitemap.xml (40 urls), robots.txt
check_claims.py           -> 42 pages scanned — clean.
check_dates.py            -> 10 cohorts, 54 dates, 5 closures; 38 CourseInstances in the built tree — 0 problems.
check_links.py            -> 1571 internal references checked — 0 broken.
check_locale.py           -> 41 pages — every EN page has a CY mirror and back, navs match, sitemap complete.
git status --porcelain    -> (empty, after a further rebuild)
```

### The gap, closed

`check_dates.py` now takes the built directory (default `clwydian-academy 2`) and, for every
`CourseInstance` that has a `startDate`: matches it to a cohort by start date (start dates are
unique across the ten cohorts; the guard says so if they ever stop being); checks `endDate`,
`offers.price`, `maximumAttendeeCapacity`; checks `Course.url`, instance `offers.url` and
`Course.offers.url` against `page_en` on an English page, `page_cy` on a Welsh one, or the
calendar page when the cohort has none; checks that a unit code in the `Course` name, where
there is one, agrees; and checks that each calendar page carries every cohort exactly once.
Undated instances — the NVQ diplomas' July-style single block — are out of scope and skipped.

My first draft keyed on the unit code in the `Course` name and false-alarmed on eight pages
(Skin Cancer Awareness's name says "Award", the NVQ names have no code). Re-keyed on
`startDate` before committing; the four real problems were the only ones left, then none.

### Process note — worth a line in CLAUDE.md if the PM agrees

`lastmod` comes from the last commit touching a page's sources. If source and output go in
**one** commit, the output was built before that commit existed, so its `lastmod` is one commit
stale and the next rebuild is not a no-op. Order is: commit source → build → commit output. I
broke that in 2/4 and fixed it in 3b.

### NEEDS A HUMAN

Nothing new. The UNHB374 page and the salon section wait on the PM's copy, as the brief says.
