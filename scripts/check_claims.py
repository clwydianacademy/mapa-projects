#!/usr/bin/env python3
"""
check_claims.py — content guard for the Clwydian Academy site.

Fails the build on any claim the academy cannot stand behind, any regression to pre-August 2026
copy, and any personal contact detail or personal name (scans .html, .md, .txt, .json and .js in
the tree — .js so that the enquiry function's own addresses are covered). Run against the built output before every commit:

    python3 scripts/check_claims.py "clwydian-academy 2"

Exit 0 = clean. Exit 1 = findings. Add rules here rather than trusting anyone to remember.
Every rule below traces to CLAUDE.md; if you relax one, change CLAUDE.md in the same commit
and say why in prompts/RELAY.md.
"""
import os, re, sys

# Pages where PLA may honestly be discussed. Everywhere else it is a banned promise.
# The Welsh mirrors are /cy/ffioedd-a-chyllid/ and /cy/cyllidwyr/ (the real slugs, 11 Sep 2026).
# Pages where PLA is EXPLAINED, never offered (CLAUDE.md "Funding language"). Each entry needs a
# reason here and a line in prompts/RELAY.md.
PLA_ALLOWED = (
    "/funding/", "/cy/ffioedd-a-chyllid/",      # the honest explanation: PLA does not cover hairdressing
    "/funders/", "/cy/cyllidwyr/",              # the advocacy card: "fair funding for this trade"
    # the retraining guide: states that PLA does not cover hairdressing, with the six Medr priority
    # sectors named; makes no offer (Brief 11 / VERIFICATION 11 ruling, 13 Sep 2026)
    "/guides/retraining-as-a-hairdresser-in-wales/", "/cy/canllawiau/ailhyfforddi-fel-triniwr-gwallt-yng-nghymru/",
)

# (regex, why it fails)
BANNED = [
    (r"Charlotte\s+Eleanor\s+Academy",      "old entity name — renamed to Clwydian Academy CBC for funding separation"),
    (r"parentOrganization",                 "no parent organisation: the CIC is independent by design"),
    (r"Charlotte\s+Eleanor\s+Group",        "no related-party framing: the academy is independent of Charlotte Eleanor Group Cyf"),
    # Industry statistics: the unsourced originals are banned; the sourced versions live only in
    # _data/statistics.json and reach pages as {{stat:...}} tokens (Brief 12, 13 Sep 2026).
    (r"60\.5\s*%",                         "unsourced statistic — the sourced figure is 62% (NHBF evidence to Parliament, Sep 2024) via {{stat:self_employed:...}}"),
    (r"18,170|7,350",                       "unverified apprenticeship-starts pair — use {{stat:apprentice_starts:...}} (NHBF 2022 restatement) until Mark supplies a source"),
    (r"(nearly|around|bron|tua)\s+70\s*%",  "derived from the unverified 18,170/7,350 pair — use {{stat:apprentice_starts:...}}"),
    (r"no longer turning a net profit|ddim bellach yn gwneud elw net|bellach yn gwneud elw net", "imprecise restatement of the NHBF April 2025 survey — use {{stat:profit:...}} (40% profit / 39% break even / 21% loss)"),
    # Privacy (PM decision, 17 Nov 2026 — the published contact details were being abused). The site
    # names the organisation only: one address, hello@clwydianacademy.co.uk; no telephone number; no
    # personal names. These rules replace the old "red until the academy mailbox exists" rule, and
    # they fail the build if any of it comes back. The values live in _data/site.json.
    (r"@charlotteeleanorgroup\.uk",         "privacy — the old Group address; the only address on the site is hello@clwydianacademy.co.uk ({{site:email}})"),
    (r"(?:\+?44|0)[\s().-]*7714[\s().-]*198[\s.-]*743", "privacy — the personal mobile number; there is no telephone number on the site"),
    (r"href=\"tel:|\"telephone\"",          "privacy — no telephone number on the site, in a link or in structured data"),
    (r"Mark\s+Parker|Charlotte\s+Roberts|Charlotte\s+Parker", "privacy — no personal names on the site; name the role (Chief Executive Officer, Director of the Academy) or the organisation"),
    (r"Charlotte\s*(?:&amp;|&|and|a|ac)\s*Mark|Mark\s*(?:&amp;|&|and|a|ac)\s*Charlotte", "privacy — no personal names on the site"),
    (r"\b(?:Mark|Charlotte)\s+(?:directs|sy(?:&rsquo;|'|’)n\s+cyfarwyddo)", "privacy — no personal names on the site; write the sentence without the first name"),
    (r"\"@type\"\s*:\s*\"Person\"|\"founder\"", "privacy — no Person or founder in structured data; the Organization only"),
    (r"linkedin\.com/in/",                  "privacy — a personal profile link; link the organisation or nothing"),
    (r"franchise\s+network",                "no graduate route into a CEG franchise network"),
    (r"sister\s+compan(y|ies)",             "related-party framing removed in August"),
    (r"in-?house\s+(internal\s+)?quality",  "quality assurance is independent and external, not in-house"),
    (r"quality\s+assurance[^.]{0,40}in-?house", "quality assurance is independent and external"),
    (r"Deeside",                            "the academy is in St Asaph, Denbighshire"),
    (r"Check\s+PLA\s+funding",              "PLA is not a promise the academy can make"),
    (r"PLA\s+eligibility",                  "PLA is not a promise the academy can make"),
]

# Unit code -> (correct level, correct number of weeks). From the Sep 2026 schemes of learning.
UNITS = {
    "UV21577": (2, 1), "UNHB385": (2, 5), "UNHB379": (2, 6),
    "UHB206": (2, 6), "UHB204": (2, 6), "UHB205": (2, 8), "UNHB374": (3, 10),
}
WEEK_WORD = {1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten"}
LEVEL_RE = re.compile(r"(?:Level|Lefel)\s*([123])", re.I)
WEEKS_RE = re.compile(r"(\d+)\s*(?:weeks?|wythnos|Mondays?|Wednesdays?|Llun|Mercher)", re.I)

# Block-level tags end a segment; inline tags do not. Level and duration claims are only
# checked WITHIN one segment, so a <option>NVQ Level 3 Hairdressing</option> cannot be read
# as a claim about the UHB206 in the option below it. (Fixed 11 Sep 2026 after that exact
# false positive on /contact/ and /cy/cysylltu/.)
BLOCK = (r"p|div|section|article|aside|header|footer|main|nav|ul|ol|li|dl|dt|dd|"
         r"table|thead|tbody|tr|td|th|h[1-6]|option|optgroup|select|label|fieldset|"
         r"legend|form|figure|figcaption|blockquote|pre|hr|details|summary|tfoot|caption")
BLOCK_RE = re.compile(rf"</?(?:{BLOCK})\b[^>]*>", re.I)

def text_of(html):
    """Whole-page text, tags stripped — used for the banned-phrase scan."""
    return re.sub(r"<[^>]+>", " ", html)

def segments(html):
    """Page text split at block boundaries, so a claim cannot bleed across list items."""
    for chunk in BLOCK_RE.split(html):
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", chunk)).strip()
        if txt:
            yield txt

def check(root):
    findings = []
    pages = 0
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith((".html", ".md", ".txt", ".json", ".js")):
                continue
            path = os.path.join(dirpath, fn)
            rel = "/" + os.path.relpath(path, root).replace(os.sep, "/")
            url = rel.replace("/index.html", "/")
            pages += 1
            raw = open(path, encoding="utf-8", errors="replace").read()
            body = text_of(raw)  # banned-phrase + barbering scan

            for rx, why in BANNED:
                for m in re.finditer(rx, raw, re.I):
                    findings.append((url, "BANNED", m.group(0).strip(), why))

            if not any(a in url for a in PLA_ALLOWED):
                # CDP = Cyfrif Dysgu Personol, the Welsh form of PLA
                for m in re.finditer(r"Personal\s+Learning\s+Account|\bPLA\b|Cyfrif\s+Dysgu\s+Personol|\bCDP\b", raw):
                    findings.append((url, "PLA", m.group(0),
                                     "PLA may only appear on the funding and funders pages"))

            segs = list(segments(raw))
            for code, (level, weeks) in UNITS.items():
                for window in [s for s in segs if re.search(re.escape(code), s, re.I)]:
                    for lm in LEVEL_RE.finditer(window):
                        if int(lm.group(1)) != level:
                            findings.append((url, "LEVEL", f"{code} shown as Level {lm.group(1)}",
                                             f"{code} is Level {level}"))
                            break
                    for wm in WEEKS_RE.finditer(window):
                        n = int(wm.group(1))
                        if n in WEEK_WORD and n != weeks and n <= 12:
                            findings.append((url, "DURATION", f"{code} shown as {n} {wm.group(0).split()[-1]}",
                                             f"{code} is {weeks} weeks ({WEEK_WORD[weeks]})"))
                            break

            if "barber" in url.lower():
                for m in re.finditer(r"six[- ]month|6[- ]month|chwe\s+mis", body, re.I):
                    findings.append((url, "BARBERING", m.group(0),
                                     "barbering is a 32-week Tuesday twilight course"))
    return findings, pages

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "clwydian-academy 2"
    if not os.path.isdir(root):
        print(f"check_claims: no such directory: {root}"); return 2
    findings, pages = check(root)
    # de-duplicate identical findings on the same page
    seen, uniq = set(), []
    for f in findings:
        if f not in seen:
            seen.add(f); uniq.append(f)
    if not uniq:
        print(f"check_claims: {pages} pages scanned — clean.")
        return 0
    print(f"check_claims: {pages} pages scanned — {len(uniq)} finding(s)\n")
    width = max(len(f[0]) for f in uniq)
    for url, kind, hit, why in sorted(uniq):
        print(f"  {url:<{width}}  [{kind}]  {hit!r}\n{'':{width+4}}  → {why}")
    print("\nFAIL — fix these, or change CLAUDE.md and say why in prompts/RELAY.md.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
