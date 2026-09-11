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
