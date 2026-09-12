# Clwydian Academy website — standing facts

Read before every task. If a brief contradicts this file, say so in `prompts/RELAY.md`
under `### NEEDS A HUMAN` rather than following the brief.

## Deployment
- Live at `https://www.clwydianacademy.co.uk`. Host **Vercel**, team
  `charlotte-eleanor-s-projects`, project `mapa-projects`, production branch `main`,
  **root directory `clwydian-academy 2`** (with the space and the 2). Static build, ~1 min.
- `clwydian-academy/` and `clwydian-academy-preview/` at repo root are stale. Never edit.
- GitHub Pages is **dead** for this site. Do not write `CNAME` or `.nojekyll`.
- The deployed HTML in `clwydian-academy 2` is the source of truth for content.
  `website/_src/` is a July 2026 generator that missed every August edit.

## The entity — funding-critical, never regress
- Legal name: **Clwydian Academy CBC** (Cwmni Buddiant Cymunedol — the Welsh designation for
  a Community Interest Company, not a separate legal form). `alternateName` is
  "Clwydian Academy CBC".
- **No `parentOrganization`. No `legalName` of "Charlotte Eleanor Academy C.I.C.". No
  "Charlotte Eleanor Academy CIC" anywhere.** The *current* legal name is correct and wanted:
  `legalName: "Clwydian Academy CBC"` and `identifier` (Companies House) `17330962` belong in
  the site-wide Organization block. Only the OLD name is banned. The academy was renamed from Charlotte Eleanor
  Academy precisely to hold it at arm's length from Charlotte Eleanor Group Cyf for funding
  eligibility. Any copy or structured data implying a parent, sister or franchise relationship
  is a regression.
- **No routes into a "Charlotte Eleanor Group franchise network"** as a graduate destination.
  Graduate routes are employment, chair rental, or a mobile business.
- People: **Mark Parker**, Chief Executive Officer. **Charlotte Roberts**, Director of the
  Academy. Never "Charlotte Parker" — that name was corrected across 14 files in August.
- Quality assurance is **independent external IQA**. Never "run in-house".

## Funding language
- The **Personal Learning Account (PLA) is not a promise the academy can make.** PLA may appear
  in exactly two places and nowhere else: the honest explanation on `/funding/`, and the
  advocacy card on `/funders/` ("fair funding for this trade"). No PLA CTAs, no
  "Check PLA funding" buttons, no PLA in any meta description or JSON-LD.
- Permitted funding language: fully funded apprenticeship route (Welsh framework), ReAct+
  support up to £1,500, instalments (£500 + £500 × 8), self-funded £4,500.

## Trading disclosure — statutory, not optional
- Regulation 25 of the Company, LLP and Business (Names and Trading Disclosures) Regulations
  2015 requires disclosure **on a company's websites** of: the part of the UK in which the
  company is registered, the registered number, and the registered office address — and
  requires a **community interest company to identify its status**. Company number **17330962**,
  incorporated 9 July 2026, private company limited by guarantee, CIC.
- **Mark's decision, 11 September 2026: the footer stays as it is.** The registered line
  (number + registered office) appears on `/funding/` and `/cy/ffioedd-a-chyllid/` only; every
  other page carries the community-benefit line. Do not roll the registered office out
  site-wide without a new instruction from Mark. The statutory point above stays open for him.
  If and when it goes site-wide, take the "part of the United Kingdom" wording verbatim from the
  Companies House record — never infer it from the address.
- The registered office is a residential address. When the St Asaph premises are taken and the
  registered office is changed at Companies House, the footer follows from one string.

## Location
- **St Asaph, Denbighshire, North Wales.** Confirmed by Mark, 11 September 2026.
  Not Deeside — the July generator's "Deeside Industrial Park" address is wrong.

## Curriculum facts (from the Sep 2026 schemes of learning — the site currently misstates several)
| Unit | Course | Level | Weeks | GLH |
|---|---|---|---|---|
| UV21577 | Skin Cancer Awareness | 2 (Award) | 1 day | 8 |
| UNHB385 | Consultation, Instruct & Advise | **2** | 5 | 60 |
| UNHB379 | Salon Business Support | **2** | 6 | 75 |
| UHB206 | Hair Extensions | 2 | **6** | 90 |
| UHB204 | Modern Perming & Texture | 2 | **6** | 93 |
| UHB205 | Relaxing & Smoothing | 2 | **8** | 125 |
| UNHB374 | Colour & Lightening | **3** | 10 | 158 |

- UNHB385 and UNHB379 are **Level 2**. The live site advertises both as Level 3. Wrong.
- Advertised durations are all short: UHB204 is 6 weeks not 4, UHB205 8 not 6, UHB206 6 not 4.
- **Barbering is a 32-week Tuesday twilight course** (one evening 5–9pm plus distance learning),
  not a six-month fast-track with two academy days a fortnight.
- UHB205 is the only regulated route to relaxing competence in either VTCT family — a genuine
  regional differentiator, safe to claim.
- CPD runs daytime, 9am–5pm, plus guided distance learning. Two strands from Jan 2027:
  Mondays and Wednesdays. 10 seats per cohort.

## Bilingual
- Every English page has a Welsh mirror at `/cy/...`. Nav and `hreflang` must stay in parity.
- **The Welsh is machine-written and has never been reviewed by a native speaker.** Any new or
  changed Welsh string must be listed in the REPORT under `### WELSH FOR REVIEW`.

## Build discipline
- **Commit source, build, then commit output — in that order, as separate commits.**
  `sitemap.xml` `lastmod` is derived from the last commit touching a page's source, so
  committing source and output together stamps the output with the *previous* commit's date
  and leaves every lastmod one commit stale. (Found by the coder in Brief 05, 11 Sep 2026.)
- A guard is not a guard until you have watched it fail. When you add or extend one, run it
  against output you know is broken, record what it said, and only then fix the thing.
- A failure message must point at the right file. A wrong URL in generated JSON-LD is a
  generator bug, not a data-file bug — say so.

## Safety
- `git --no-optional-locks` for all git reads. A plain `git status` leaves an index lock that
  blocks commits.
- Never change Vercel deployment protection, environment variables, or any credential field.
  Mark's password manager autofills on focus.
- Never open `Start Up Loan application/` — personal financial data, irrelevant to code.
- Secrets never enter the repo.
