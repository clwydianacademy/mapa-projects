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
