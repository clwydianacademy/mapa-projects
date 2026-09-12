#!/usr/bin/env python3
"""
check_dates.py — guard for _data/cpd-2027.json, the single source of every CPD date on the site.

Re-derives, from the data alone:
  * every date falls on its strand's weekday
  * no date falls on a listed closure (a single date, or any day of a closed week)
  * no two cohorts in one strand share a date
  * len(dates) == days for every cohort, and the strand's teaching_days is the sum
  * price == round((fixed + per_glh * glh) / round_to) * round_to, plus £50 for UHB206
  * dates are ascending and within the term

And, against the built tree (second argument, default "clwydian-academy 2"), every
Course / CourseInstance in the JSON-LD:
  * its startDate is a cohort in the data (and a unit code in the Course name, if any, agrees)
  * endDate, offers.price and maximumAttendeeCapacity match that cohort
  * Course.url and offers.url are the cohort's page_en (English page) or page_cy (Welsh),
    falling back to the calendar page where the cohort has no course page
  * the calendar page carries every cohort, once, in each language

    python3 scripts/check_dates.py [built-dir]   # exit 0 = clean, 1 = problems, 2 = no data

Change the data, not the site, when a date moves — then rebuild.
"""
import datetime, json, os, re, sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_data", "cpd-2027.json")
KIT_SUPPLEMENT = {"UHB206": 50}   # brand-partner hair and kit, on top of the tariff

def d(s):
    return datetime.date.fromisoformat(s)

def check(data):
    problems = []
    strands = {s["id"]: s for s in data["strands"]}
    weekdays = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    closed = set()
    for c in data["closures"]:
        if "date" in c:
            closed.add(d(c["date"]))
        else:
            start = d(c["week_commencing"])
            closed.update(start + datetime.timedelta(days=i) for i in range(7))
    first, last = d(data["term"]["first_day"]), d(data["term"]["last_day"])
    t = data["tariff"]
    seen = {}            # (strand, date) -> cohort id
    per_strand_days = {}
    for c in data["cohorts"]:
        cid, strand = c["id"], strands.get(c["strand"])
        if strand is None:
            problems.append(f"{cid}: unknown strand {c['strand']!r}"); continue
        wd = weekdays[strand["weekday"]]
        dates = [d(x) for x in c["dates"]]
        if len(dates) != c["days"]:
            problems.append(f"{cid}: {len(dates)} dates but days={c['days']}")
        if dates != sorted(dates):
            problems.append(f"{cid}: dates are not ascending")
        for x in dates:
            if x.weekday() != wd:
                problems.append(f"{cid}: {x} is a {x.strftime('%A')}, strand {strand['id']} runs on {strand['weekday']}")
            if x in closed:
                problems.append(f"{cid}: {x} is a listed closure")
            if not (first <= x <= last):
                problems.append(f"{cid}: {x} is outside the term {first}..{last}")
            key = (strand["id"], x)
            if key in seen:
                problems.append(f"{cid}: {x} is also used by {seen[key]} in strand {strand['id']}")
            seen[key] = cid
        per_strand_days[strand["id"]] = per_strand_days.get(strand["id"], 0) + len(dates)
        expected = round((t["fixed"] + t["per_glh"] * c["glh"]) / t["round_to"]) * t["round_to"] + KIT_SUPPLEMENT.get(c["unit"], 0)
        if c["price"] != expected:
            problems.append(f"{cid}: price {c['price']} but tariff gives {expected} "
                            f"({t['fixed']} + {t['per_glh']} x {c['glh']} GLH, rounded to £{t['round_to']}"
                            f"{' + £' + str(KIT_SUPPLEMENT[c['unit']]) + ' kit' if c['unit'] in KIT_SUPPLEMENT else ''})")
    for sid, s in strands.items():
        if per_strand_days.get(sid, 0) != s["teaching_days"]:
            problems.append(f"strand {sid}: {per_strand_days.get(sid, 0)} dates across cohorts but teaching_days={s['teaching_days']}")
    return problems

DOMAIN = "https://clwydianacademy.co.uk"
REGISTRY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "website", "_src", "pages.json")
UNIT_RE = re.compile(r"\b(U[A-Z]{1,3}\d{3,5})\b")

def calendar_paths():
    with open(REGISTRY, encoding="utf-8") as f:
        cal = next(p for p in json.load(f) if p.get("generated") == "cpd-calendar")
    return {"en": cal["en"]["path"], "cy": cal["cy"]["path"]}

def check_built(data, root):
    """Every CourseInstance in the built JSON-LD describes a real cohort and points at its own page."""
    problems, seen_on_calendar, n_inst = [], {"en": set(), "cy": set()}, 0
    cal = calendar_paths()
    by_start = {}
    for c in data["cohorts"]:
        if c["dates"][0] in by_start:
            problems.append(f"data: {c['id']} and {by_start[c['dates'][0]]['id']} share a start date — JSON-LD cannot be matched")
        by_start[c["dates"][0]] = c
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            path = os.path.join(dirpath, fn)
            url = "/" + os.path.relpath(path, root).replace(os.sep, "/")
            url = url[:-len("index.html")] if url.endswith("/index.html") else url
            loc = "cy" if url.startswith("/cy/") else "en"
            html = open(path, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
                block = json.loads(m.group(1))
                if block.get("@type") != "Course":
                    continue
                inst = block.get("hasCourseInstance")
                if not inst:
                    continue
                if isinstance(inst, dict):
                    inst = [inst]
                um = UNIT_RE.search(block.get("name", ""))
                named_unit = um.group(1) if um else None
                for i in inst:
                    start = i.get("startDate")
                    if not start:
                        continue                      # an undated instance (the NVQ diplomas) is not a CPD cohort
                    n_inst += 1
                    cohort = by_start.get(start)
                    if cohort is None:
                        problems.append(f"{url}: CourseInstance starting {start} is not a cohort in the data"); continue
                    if named_unit and named_unit != cohort["unit"]:
                        problems.append(f"{url}: Course named {named_unit} carries {cohort['id']} ({cohort['unit']}) starting {start}")
                    want_page = (cohort.get("page_en") if loc == "en" else cohort.get("page_cy")) or cal[loc]
                    want_url = DOMAIN + want_page
                    if i.get("endDate") != cohort["dates"][-1]:
                        problems.append(f"{url}: {cohort['id']} endDate {i.get('endDate')} != {cohort['dates'][-1]}")
                    if str((i.get("offers") or {}).get("price")) != str(cohort["price"]):
                        problems.append(f"{url}: {cohort['id']} offers.price {(i.get('offers') or {}).get('price')} != {cohort['price']}")
                    if i.get("maximumAttendeeCapacity") != data["seats_per_cohort"]:
                        problems.append(f"{url}: {cohort['id']} maximumAttendeeCapacity {i.get('maximumAttendeeCapacity')} != {data['seats_per_cohort']}")
                    if (i.get("offers") or {}).get("url") != want_url:
                        problems.append(f"{url}: {cohort['id']} offers.url {(i.get('offers') or {}).get('url')} should be {want_url}")
                    if block.get("url") != want_url:
                        problems.append(f"{url}: {cohort['id']} Course.url {block.get('url')} should be {want_url}")
                    if (block.get("offers") or {}).get("url") not in (None, want_url):
                        problems.append(f"{url}: {cohort['id']} Course.offers.url {block['offers'].get('url')} should be {want_url}")
                    if url == cal[loc]:
                        if cohort["id"] in seen_on_calendar[loc]:
                            problems.append(f"{url}: {cohort['id']} appears twice")
                        seen_on_calendar[loc].add(cohort["id"])
    for loc in ("en", "cy"):
        missing = sorted(c["id"] for c in data["cohorts"] if c["id"] not in seen_on_calendar[loc])
        if missing:
            problems.append(f"{cal[loc]}: cohorts missing from the calendar JSON-LD: {', '.join(missing)}")
    return problems, n_inst

def main():
    if not os.path.exists(DATA):
        print(f"check_dates: no data file at {os.path.normpath(DATA)}"); return 2
    root = sys.argv[1] if len(sys.argv) > 1 else "clwydian-academy 2"
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    problems = check(data)
    n_inst = 0
    if os.path.isdir(root):
        built, n_inst = check_built(data, root)
        problems += built
    else:
        problems.append(f"built tree not found at {root} — JSON-LD not checked")
    n = len(data["cohorts"]); nd = sum(len(c["dates"]) for c in data["cohorts"])
    if not problems:
        print(f"check_dates: {n} cohorts, {nd} dates, {len(data['closures'])} closures; {n_inst} CourseInstances in the built tree — 0 problems."); return 0
    print(f"check_dates: {n} cohorts, {nd} dates; {n_inst} CourseInstances — {len(problems)} problem(s)\n")
    for p in problems: print("  ", p)
    generated = [p for p in problems if "should be" in p or "appears twice" in p or "missing from the calendar" in p
                 or "is not a cohort in the data" in p or "Course named" in p or "!=" in p]
    if generated and len(generated) == len(problems):
        print("\nFAIL — the data file is consistent; these are generator bugs. Fix website/_src/cpd.py "
              "(or the JSON-LD source), rebuild, never edit the built pages.")
    elif generated:
        print("\nFAIL — mixed: fix _data/cpd-2027.json for the data problems and website/_src/cpd.py for the "
              "generated-output problems, then rebuild. Never edit the built pages.")
    else:
        print("\nFAIL — fix _data/cpd-2027.json (never the built pages) and rebuild.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
