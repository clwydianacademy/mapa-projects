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

    python3 scripts/check_dates.py            # exit 0 = clean, 1 = problems, 2 = no data

Change the data, not the site, when a date moves — then rebuild.
"""
import datetime, json, os, sys

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

def main():
    if not os.path.exists(DATA):
        print(f"check_dates: no data file at {os.path.normpath(DATA)}"); return 2
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    problems = check(data)
    n = len(data["cohorts"]); nd = sum(len(c["dates"]) for c in data["cohorts"])
    if not problems:
        print(f"check_dates: {n} cohorts, {nd} dates, {len(data['closures'])} closures — 0 problems."); return 0
    print(f"check_dates: {n} cohorts, {nd} dates — {len(problems)} problem(s)\n")
    for p in problems: print("  ", p)
    print("\nFAIL — fix _data/cpd-2027.json (never the built pages) and rebuild.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
