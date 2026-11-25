#!/usr/bin/env python3
"""sync_salon_feed.py — bring the booking system's live catalogue into _data/salon/feed.json.

    python3 scripts/sync_salon_feed.py            # fetch, check, write if different; exit 0 either way
    python3 scripts/sync_salon_feed.py --check    # the same, but write nothing: say what would change

Mark, 25 November 2026: a price changed in the booking system's Settings must reach this website
by itself. This is that. It runs every night (.github/workflows/salon-feed.yml) with nobody
watching, so it is written to REFUSE: anything that is not plainly the salon's own catalogue —
an error page, half a file, another business, a price of nothing, a price that has moved more
than a person would mean — leaves the file exactly as it was and says why. A refusal is exit 2,
so the nightly job goes red and somebody looks. The booking system simply not answering is not
an alarm (exit 0): the committed feed stands.

It writes the file byte-for-byte as salon-booking's tools/export-feed.mjs does, so the two ways
of getting a feed can never disagree about formatting. Standard library only.
"""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FEED_PATH = os.path.join(REPO, "_data", "salon", "feed.json")
LIVE_URL = "https://book.clwydianacademy.co.uk/api/salon/feed/"
ALLOWED_HOST = "book.clwydianacademy.co.uk"
FOR = "Clwydian Academy Training Salon"
SOURCE = ("Exported from clwydianacademy/salon-booking by tools/export-feed.mjs. DO NOT EDIT BY HAND: change the price in the "
          "booking system and export again. The website builds its salon prices, times and hours from this file and from nothing else.")
MAX_BYTES = 300000
MAX_PRICE_MOVE = 4.0      # a price more than four times, or less than a quarter of, last night's is a person's job to confirm
MIN_KEPT = 0.5            # and so is losing more than half the price list in one night
PLAIN = re.compile(r"^[^<>{}\\\x00-\x1f]{1,120}$")

def render(feed):
    """The file's exact text: _source first, one-space indent, a final newline — as export-feed.mjs writes it."""
    body = {"_source": SOURCE}
    body.update({k: v for k, v in feed.items() if k not in ("_source", "generatedAt")})   # the time it was served is not part of the catalogue: export-feed.mjs leaves it out too, or every night would be "a change"
    return json.dumps(body, indent=1, ensure_ascii=False) + "\n"

def problems(feed, previous=None):
    """Every reason this is not a catalogue to publish. Empty means it may be written."""
    out = []
    if not isinstance(feed, dict): return ["it is not a JSON object"]
    if feed.get("for") != FOR: out.append("it is not for %s" % FOR)
    if feed.get("currency") != "GBP": out.append("the currency is not GBP")
    if feed.get("totalPrice") is not True: out.append("it does not say its prices are the total price")
    if not isinstance(feed.get("version"), str) or not feed.get("version"): out.append("it has no version")
    hours = feed.get("hours")
    if not isinstance(hours, list) or not hours or not all(isinstance(h, dict) and re.match(r"^\d\d:\d\d$", str(h.get("open", ""))) and re.match(r"^\d\d:\d\d$", str(h.get("close", ""))) and h["open"] < h["close"] for h in hours):
        out.append("the opening hours are missing or not times")
    levels = [l.get("id") for l in feed.get("levels", []) if isinstance(l, dict)] if isinstance(feed.get("levels"), list) else []
    if not levels: out.append("it names no learner levels")
    services = feed.get("services")
    if not isinstance(services, list) or not services: return out + ["it has no services"]
    seen = set()
    for s in services:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or not re.match(r"^[a-z0-9-]{1,60}$", s.get("id", "")):
            out.append("a service has no plain id"); continue
        sid = s["id"]
        if sid in seen: out.append("%s is listed twice" % sid)
        seen.add(sid)
        if not isinstance(s.get("name"), str) or not PLAIN.match(s["name"]): out.append("%s: the name is missing or is not plain text" % sid)
        book = urllib.parse.urlparse(str(s.get("book", "")))
        if book.scheme != "https" or book.hostname != ALLOWED_HOST: out.append("%s: its Book link does not go to %s" % (sid, ALLOWED_HOST))
        sold = s.get("levels")
        if not isinstance(sold, dict) or not any(v is not None for v in sold.values()): out.append("%s: it is sold at no level" % sid); continue
        for lid, f in sold.items():
            if f is None and lid in levels: continue          # null: not sold at this level (the page prints a dash)
            if lid not in levels or not isinstance(f, dict): out.append("%s: an unknown level %r" % (sid, lid)); continue
            price, minutes, deposit = f.get("price"), f.get("minutes"), f.get("deposit")
            if isinstance(price, bool) or not isinstance(price, (int, float)) or not (0 < price <= 500): out.append("%s at %s: the price is not a sum of money between nothing and £500" % (sid, lid))
            if isinstance(minutes, bool) or not isinstance(minutes, int) or not (5 <= minutes <= 600): out.append("%s at %s: the appointment length is not between 5 minutes and 10 hours" % (sid, lid))
            if isinstance(deposit, bool) or not isinstance(deposit, (int, float)) or deposit < 0 or (isinstance(price, (int, float)) and not isinstance(price, bool) and deposit > price): out.append("%s at %s: the deposit is not between nothing and the price" % (sid, lid))
    if previous:
        was = {s["id"]: s for s in previous.get("services", []) if isinstance(s, dict) and "id" in s}
        if was and len(seen & set(was)) < MIN_KEPT * len(was): out.append("more than half of last night's price list is gone (%d of %d left)" % (len(seen & set(was)), len(was)))
        for s in services:
            if not isinstance(s, dict) or not isinstance(s.get("levels"), dict): continue
            for lid, f in s["levels"].items():
                old = ((was.get(s.get("id"), {}).get("levels", {}) or {}).get(lid) or {}).get("price")
                new = f.get("price") if isinstance(f, dict) else None
                if isinstance(old, (int, float)) and isinstance(new, (int, float)) and not isinstance(new, bool) and old > 0 and new > 0 and not (1 / MAX_PRICE_MOVE <= new / old <= MAX_PRICE_MOVE):
                    out.append("%s at %s moved from £%s to £%s in one night — too far to publish unchecked" % (s.get("id"), lid, old, new))
    return out

def summary(previous, feed):
    """What changed, as sentences, for the commit message."""
    lines = []
    was = {s["id"]: s for s in previous.get("services", [])}
    now = {s["id"]: s for s in feed.get("services", [])}
    for sid in now:
        if sid not in was: lines.append("%s is new" % now[sid]["name"]); continue
        for lid, f in now[sid]["levels"].items():
            old = was[sid].get("levels", {}).get(lid)
            if f is None:
                if old is not None: lines.append("%s is no longer sold at %s" % (now[sid]["name"], lid))
                continue
            if old is None: lines.append("%s is now sold at %s" % (now[sid]["name"], lid)); continue
            for key, label, unit in (("price", "price", "£%s"), ("minutes", "time", "%s min"), ("deposit", "deposit", "£%s")):
                if old.get(key) != f.get(key): lines.append("%s (%s): %s %s to %s" % (now[sid]["name"], lid, label, unit % old.get(key), unit % f.get(key)))
    for sid in was:
        if sid not in now: lines.append("%s is no longer sold" % was[sid]["name"])
    for key, label in (("hours", "opening hours"), ("terms", "term dates"), ("closed", "closed dates"), ("deposit", "deposits")):
        if previous.get(key) != feed.get(key): lines.append("the %s changed" % label)
    return lines or ["the catalogue's version changed, with no change to a figure this site prints"]

def sync(url=LIVE_URL, path=FEED_PATH, allow_http=False, write=True):
    """Returns {'changed': bool, 'refused': [...] | None, 'unreachable': str | None, 'summary': [...]}. Never raises."""
    result = {"changed": False, "refused": None, "unreachable": None, "summary": []}
    parsed = urllib.parse.urlparse(url)
    if not allow_http and (parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST):
        result["refused"] = ["the address is not https on %s" % ALLOWED_HOST]; return result
    if parsed.scheme not in ("https", "http"):
        result["refused"] = ["the address is not a web address"]; return result
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "salon-feed-sync"})
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status; ctype = response.headers.get("Content-Type", ""); raw = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as error:
        result["refused"] = ["the booking system answered %s" % error.code]; return result
    except Exception as error:                      # not there yet, DNS, a timeout: the committed feed stands
        result["unreachable"] = "%s: %s" % (type(error).__name__, str(error)[:120]); return result
    if status != 200: result["refused"] = ["the booking system answered %s" % status]; return result
    if "json" not in ctype.lower(): result["refused"] = ["the answer is %s, not JSON" % (ctype or "of no stated type")]; return result
    if len(raw) > MAX_BYTES: result["refused"] = ["the answer is larger than a catalogue could be"]; return result
    try: feed = json.loads(raw.decode("utf-8"))
    except Exception: result["refused"] = ["the answer is not whole JSON"]; return result
    with open(path, encoding="utf-8") as f: before_text = f.read()
    previous = json.loads(before_text)
    wrong = problems(feed, previous)
    if wrong: result["refused"] = wrong; return result
    after_text = render(feed)
    if after_text == before_text: return result
    result["changed"] = True; result["summary"] = summary(previous, feed)
    if write:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: f.write(after_text)
        os.replace(tmp, path)
    return result

if __name__ == "__main__":
    out = sync(os.environ.get("SALON_FEED_URL", LIVE_URL), write="--check" not in sys.argv)
    if out["refused"]:
        print("salon feed: REFUSED — the file is unchanged.\n  " + "\n  ".join(out["refused"])); sys.exit(2)
    if out["unreachable"]:
        print("salon feed: the booking system did not answer (%s). The committed feed stands." % out["unreachable"]); sys.exit(0)
    if not out["changed"]:
        print("salon feed: no change."); sys.exit(0)
    print("salon feed: CHANGED\n  " + "\n  ".join(out["summary"]))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write("changed=true\nsummary<<EOF_SUMMARY\n" + "\n".join(out["summary"]) + "\nEOF_SUMMARY\n")
