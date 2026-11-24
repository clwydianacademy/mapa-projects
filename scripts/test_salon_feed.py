#!/usr/bin/env python3
"""test_salon_feed.py — the website shows the booking system's figures, and only those.

    python3 scripts/test_salon_feed.py

_data/salon/feed.json is exported from the booking system (clwydianacademy/salon-booking,
tools/export-feed.mjs), where every figure in it is worked out by the code that prices a booking.
This test builds the salon's pages and READS THEM BACK:

  1. every service in the feed is on the price list, in both languages, and nothing else is;
  2. every price and every appointment length shown — the visible words, not only the data
     attributes — is the feed's, at each level, with "from" exactly where the feed says so and a
     dash where the feed says a level is not sold;
  3. every "Book" link beside a service opens the booking page ON THAT SERVICE (and in Welsh from
     a Welsh page);
  4. the deposit, and the opening hours wherever they are printed (the page and the structured
     data), are the feed's;
  5. policy.json and the generator hold no price or minutes of their own to disagree with it;
  6. where the booking system's repository is checked out beside this one, the feed here is
     byte-for-byte what that repository exports TODAY — so a price changed there and not
     re-exported here fails this test.

A guard is not a guard until it has been watched failing: checks 2 to 4 are each re-run against a
feed with one figure changed, and must fail. Standard library only.
"""
import copy, html as htmllib, json, os, re, shutil, subprocess, sys, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO, "website", "_src"))
import salon

FEED = json.load(open(os.path.join(REPO, "_data", "salon", "feed.json"), encoding="utf-8"))
POLICY = json.load(open(os.path.join(REPO, "_data", "salon", "policy.json"), encoding="utf-8"))
PREVIEW = tempfile.mkdtemp(prefix="salon-feed-")
subprocess.run([sys.executable, os.path.join(REPO, "website", "_src", "build.py"), "--salon-preview", PREVIEW], check=True, capture_output=True, text=True)
PAGES = {"en": {"prices": "salon/prices/index.html", "home": "salon/index.html"}, "cy": {"prices": "cy/salon/prisiau/index.html", "home": "cy/salon/index.html"}}
read = lambda rel: open(os.path.join(PREVIEW, rel), encoding="utf-8").read()
text = lambda fragment: re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()

passed = failed = 0
def test(name, fn):
    global passed, failed
    try:
        fn(); passed += 1; print("  ok   ", name)
    except AssertionError as e:
        failed += 1; print("  FAIL ", name, "\n        ", str(e)[:500])

def must_fail(fn, why):
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError(f"the check did not fail when {why} — it cannot catch a real difference")

def rows(loc):
    return {m.group(1): m.group(0) for m in re.finditer(r'<tr data-service="([^"]+)">.*?</tr>', read(PAGES[loc]["prices"]), re.S)}

def check_services(feed=FEED):
    for loc in ("en", "cy"):
        shown = set(rows(loc))
        want = {s["id"] for s in feed["services"]}
        assert shown == want, f"{loc}: on the page and not in the feed {sorted(shown - want)}; in the feed and not on the page {sorted(want - shown)}"

def check_figures(feed=FEED):
    n = 0
    for loc in ("en", "cy"):
        r = rows(loc)
        for s in feed["services"]:
            cells = re.findall(r"<td\b[^>]*>.*?</td>", r[s["id"]], re.S)
            assert len(cells) == len(feed["levels"]), f'{loc} {s["id"]}: {len(cells)} cells for {len(feed["levels"])} levels'
            for cell, level in zip(cells, [l["id"] for l in feed["levels"]]):
                f = s["levels"].get(level)
                seen = text(cell)
                if f is None:
                    assert "&pound;" not in cell and "£" not in seen, f'{loc} {s["id"]} {level}: a price is shown for a level the booking system does not sell'
                    continue
                assert f'data-price="{f["price"]}"' in cell and f'data-minutes="{f["minutes"]}"' in cell, f'{loc} {s["id"]} {level}: the cell is marked {cell[:90]}'
                assert re.search(rf"£{f['price']}(?!\d)", seen), f'{loc} {s["id"]} {level}: the feed says £{f["price"]}, the page says "{seen}"'
                assert salon.duration(f["minutes"], loc) in seen, f'{loc} {s["id"]} {level}: the feed says {salon.duration(f["minutes"], loc)}, the page says "{seen}"'
                has_from = bool(re.match(r"(from|o) £", seen))
                assert has_from == bool(f["from"]), f'{loc} {s["id"]} {level}: "from" is {"shown" if has_from else "missing"} and the feed says from={f["from"]}'
                # no OTHER price in the cell: one figure, the feed's
                assert len(re.findall(r"£\d+", seen)) == 1, f'{loc} {s["id"]} {level}: more than one price in "{seen}"'
                n += 1
    assert n >= 2 * 25, f"only {n} figures were compared"

def check_book_links(feed=FEED):
    for loc in ("en", "cy"):
        r = rows(loc)
        for s in feed["services"]:
            m = re.search(r'<a href="([^"]+)" data-book="([^"]+)"', r[s["id"]])
            assert m, f'{loc} {s["id"]}: no Book link beside the service'
            want = s["book"] + ("&lang=cy" if loc == "cy" else "")
            assert htmllib.unescape(m.group(1)) == want and m.group(2) == s["id"], f'{loc} {s["id"]}: the Book link goes to {m.group(1)}, the feed says {want}'
            assert f'service={s["id"]}' in m.group(1)

def check_deposit_and_hours(feed=FEED):
    for loc in ("en", "cy"):
        prices = text(read(PAGES[loc]["prices"]))
        for kind in ("cutting", "colour"):
            assert re.search(rf"£{feed['deposit'][kind]}(?!\d)", prices), f'{loc}: the deposit for {kind} (£{feed["deposit"][kind]}) is not on the prices page'
        home = read(PAGES[loc]["home"])
        # opening hours are printed only once Mark has confirmed them; whenever they ARE, they are the feed's
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', home, re.S):
            for node in ([json.loads(block)] if not isinstance(json.loads(block), list) else json.loads(block)):
                for spec in node.get("openingHoursSpecification", []) if isinstance(node, dict) else []:
                    day = spec["dayOfWeek"].rsplit("/", 1)[-1][:3].lower()
                    h = next((x for x in feed["hours"] if x["day"] == day), None)
                    assert h and spec["opens"] == h["open"] and spec["closes"] == h["close"], f"{loc}: structured data says {spec}, the feed says {h}"
        for d, ss in salon.sessions().items():
            h = next(x for x in feed["hours"] if x["day"] == d)
            assert ss == [{"open": h["open"], "close": h["close"]}]
            if f'{h["open"]}&ndash;' in home:
                assert f'{h["open"]}&ndash;{h["close"]}' in home, f'{loc}: {d} opens at {h["open"]} on the page but does not close at {h["close"]}'

def check_no_second_source():
    for s in POLICY["services"]:
        for k in ("stylist_price", "base_minutes", "price", "minutes"):
            assert k not in s, f'policy.json: {s["id"]} carries "{k}" — a second place for a figure to live'
    assert "l2_percent_off" not in POLICY["pricing"] and all("factors" not in l for l in POLICY["levels"].values())
    src = open(os.path.join(REPO, "website", "_src", "salon.py"), encoding="utf-8").read()
    for gone in ('s["stylist_price"]', 's["base_minutes"]', '"l2_percent_off"', 'policy["educator"]["minutes"]'):
        assert gone not in src, f"salon.py still reads {gone}"
    # every service the website can NAME is one the booking system sells, or it is simply not listed
    unsold = [s["id"] for s in POLICY["services"] if not salon.priced(s)]
    listed = set(rows("en"))
    assert not (set(unsold) & listed), f"listed although the booking system does not sell them: {sorted(set(unsold) & listed)}"
    missing_names = [s["id"] for s in FEED["services"] if not any(p["id"] == s["id"] for p in POLICY["services"])]
    assert not missing_names, f"the booking system sells these and the website has no name for them (add the bilingual name to policy.json): {missing_names}"

def check_same_as_booking_repo():
    other = os.path.join(REPO, "..", "salon-booking", "tools", "export-feed.mjs")
    if not os.path.exists(other) or not shutil.which("node"):
        print("  ----  the booking system's repository is not checked out beside this one: the feed was NOT compared with it")
        return
    out = subprocess.run(["node", other], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(other)), env={k: v for k, v in os.environ.items() if not k.startswith("KV_")})
    assert out.returncode == 0, out.stderr[-400:]
    now = json.loads(out.stdout)
    if now != FEED:
        changed = [s["id"] for s in now["services"] if next((x for x in FEED["services"] if x["id"] == s["id"]), None) != s]
        raise AssertionError(f'the booking system\'s catalogue has changed since feed.json was exported (version {now["version"]} there, {FEED["version"]} here; services that differ: {changed or "none — hours, deposit or terms"}). '
                             'Run: node ../salon-booking/tools/export-feed.mjs _data/salon/feed.json  — then rebuild.')

def changed(mutate):
    f = copy.deepcopy(FEED); mutate(f); return f

test("every service the booking system sells is on the price list, in both languages, and nothing else is", check_services)
test("every price and appointment length on the page is the feed's — the words a visitor reads, at each level", check_figures)
test("  …and that check FAILS when a price, a time, a 'from' or a level differs", lambda: [
    must_fail(lambda: check_figures(changed(lambda f: f["services"][0]["levels"]["l3"].__setitem__("price", f["services"][0]["levels"]["l3"]["price"] + 1))), "a price is £1 out"),
    must_fail(lambda: check_figures(changed(lambda f: f["services"][3]["levels"]["l3"].__setitem__("minutes", f["services"][3]["levels"]["l3"]["minutes"] + 5))), "a time is five minutes out"),
    must_fail(lambda: check_figures(changed(lambda f: f["services"][0]["levels"]["l2"].__setitem__("from", not f["services"][0]["levels"]["l2"]["from"]))), "'from' is wrong"),
    must_fail(lambda: check_figures(changed(lambda f: f["services"][0]["levels"].__setitem__("l2", None))), "a level is shown that is not sold"),
    must_fail(lambda: check_services(changed(lambda f: f["services"].pop())), "a service is listed that the feed does not have"),
])
test("every Book link beside a service opens the booking page on that service, in the page's language", check_book_links)
test("  …and that check FAILS when a link points at another service", lambda: must_fail(lambda: check_book_links(changed(lambda f: f["services"][1].__setitem__("book", f["services"][0]["book"]))), "a Book link is for the wrong service"))
test("the deposit and the opening hours are the feed's wherever they are printed", check_deposit_and_hours)
test("  …and that check FAILS when the deposit differs", lambda: must_fail(lambda: check_deposit_and_hours(changed(lambda f: f["deposit"].__setitem__("colour", 99))), "the deposit is different"))
test("the website holds no price or minutes of its own: policy.json and the generator have none", check_no_second_source)
test("feed.json is exactly what the booking system's repository exports today", check_same_as_booking_repo)

shutil.rmtree(PREVIEW, ignore_errors=True)
print(f"\n  {passed} passed, {failed} failed\n")
sys.exit(1 if failed else 0)
