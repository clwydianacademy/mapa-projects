#!/usr/bin/env python3
"""test_showcase.py — the showcase's rules, each one watched failing.

    python3 scripts/test_showcase.py

Builds a preview (everything ON) into a temporary folder and reads what was written; drives the
guards in website/_src/showcase.py with input that is known to be bad; and checks that with the
switch OFF the deployed folder holds nothing of the showcase. Standard library only.
"""
import copy, json, os, re, subprocess, sys, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO, "website", "_src"))
import showcase

passed = failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn(); passed += 1; print("  ok   ", name)
    except AssertionError as e:
        failed += 1; print("  FAIL ", name, "\n        ", e)

def refused(fn, needle):
    """fn must stop the build (SystemExit) with a message containing needle."""
    try:
        fn()
    except SystemExit as e:
        assert needle in str(e), f"refused, but for another reason: {e}"
        return
    raise AssertionError(f"was not refused (expected: {needle})")

WORK = json.load(open(showcase.WORK_PATH, encoding="utf-8"))
GOOD = {"id": "cut-0001", "course": "l2-hairdressing", "badges": ["qualification"], "width": 900, "height": 1200,
        "consentRef": "CF-2027-0001", "consentDate": "2027-01-18", "originalsKept": True, "ownClient": True,
        "hairRetouched": False, "afterOnlyEdited": False,
        "alt": {"en": "A shoulder-length layered cut, blow-dried smooth", "cy": "Toriad haenog at yr ysgwydd, wedi'i chwythsychu'n llyfn"}}
FILES = {"cut-0001-before.jpg", "cut-0001-after.jpg"}

def pairs(**change):
    w = copy.deepcopy(WORK)
    p = copy.deepcopy(GOOD)
    for k, v in change.items():
        if v is KeyError: p.pop(k, None)
        else: p[k] = v
    w["pairs"] = [p]
    return lambda: showcase.validate_pairs(w, today="2027-02-01", files=FILES)

def t_pairs():
    assert len(pairs()()) == 1, "a complete pair was refused"
    for change, needle in [
        (dict(consentRef=KeyError), "consentRef"), (dict(consentRef="  "), "consentRef"),
        (dict(consentDate=KeyError), "consentDate"), (dict(consentDate="18 January"), "consentDate"),
        (dict(consentDate="2027-03-01"), "in the future"),
        (dict(originalsKept=KeyError), "originalsKept"), (dict(originalsKept=False), "originalsKept"), (dict(originalsKept="yes"), "originalsKept"),
        (dict(ownClient=False), "ownClient"), (dict(hairRetouched=True), "hairRetouched"), (dict(hairRetouched=KeyError), "hairRetouched"),
        (dict(afterOnlyEdited=True), "afterOnlyEdited"),
        (dict(course="l4-wizardry"), "course"), (dict(badges=["gold-star"]), "badge"),
        (dict(learnerName="A Learner"), "names a person"), (dict(alt={"en": "A sleek bob by Morgan", "cy": GOOD["alt"]["cy"]}), "name somebody"),
        (dict(alt={"en": "Bob", "cy": "Bob"}), "description"), (dict(width=KeyError), "width and height"), (dict(id="Cut 1"), "no id"),
    ]:
        refused(pairs(**change), needle)
    w = copy.deepcopy(WORK); w["pairs"] = [copy.deepcopy(GOOD)]
    refused(lambda: showcase.validate_pairs(w, today="2027-02-01", files={"cut-0001-before.jpg"}), "cut-0001-after.jpg")
    assert WORK["pairs"] == [], "a pair is in the data file: this test must then be extended to read its consent record"

def t_pair_html():
    w = copy.deepcopy(WORK); w["pairs"] = [copy.deepcopy(GOOD)]
    for loc in ("en", "cy"):
        html = showcase.pair_html(GOOD, w, loc)
        assert re.search(r'<input class="ba-range" id="ba-cut-0001" type="range" min="0" max="100"', html), "the slider is not a range input"
        assert f'<label class="ba-label" for="ba-cut-0001">' in html, "the slider has no label"
        assert html.count('width="900" height="1200"') == 2, "a picture has no width and height"
        assert "CF-2027-0001" not in html and "2027-01-18" not in html, "the consent record is printed on the page"
        assert 'data-lightbox' in html and 'href="/assets/img/work/cut-0001-after.jpg"' in html, "View larger is not a real link"

def t_stock():
    saved = showcase._load
    def with_alt(alt):
        def load(path):
            d = saved(path)
            if path == showcase.PHOTOS_PATH:
                d = copy.deepcopy(d); d["photos"][0]["alt"]["en"] = alt
            return d
        return load
    try:
        for bad in ("A bob cut by one of our learners", "A student's colour work", "A client of the academy salon"):
            showcase._load = with_alt(bad)
            refused(showcase.photos, "claims it as somebody's work")
        showcase._load = with_alt("Bob")
        refused(showcase.photos, "no real alt text")
    finally:
        showcase._load = saved
    data = saved(showcase.PHOTOS_PATH)
    assert len(data["photos"]) == 15 and all(p["stock"] is True for p in data["photos"]), "a photograph is not marked stock"
    for p in data["photos"]:
        assert not re.search(r"charlotte|eleanor|ce-|logo|mark|franchise", p["stem"], re.I), f"{p['stem']}: not a name to publish under"
        assert p["from"] not in ("band-franchise", "charlotte-at-work"), f"{p['from']} was excluded by the brief"

SITE = json.load(open(os.path.join(REPO, "_data", "site.json"), encoding="utf-8"))

def t_legal():
    assert showcase.legal_todos(SITE) == ["registered_in", "registered_office"], "a statutory value was filled in: check it against Companies House, then update this test"
    line = showcase.legal_line("en", SITE)
    assert "Clwydian Academy CBC is a community interest company and a limited company." in line and "Company number 17330962." in line
    assert "Registered office" not in line and "registered in" not in line, "a TODO_PM value was printed"
    assert not re.search(r"Bod Hyfryd|CH8", json.dumps(SITE["legal"])), "the residential address is in the legal block"
    done = copy.deepcopy(SITE)
    done["legal"]["registered_in"] = {"value": "PLACE"}; done["legal"]["registered_office"] = {"value": {"en": "1 Sample Street, Sampletown", "cy": "1 Stryd Sampl, Trefsampl"}}
    assert showcase.legal_todos(done) == []
    en, cy = showcase.legal_line("en", done), showcase.legal_line("cy", done)
    assert ", registered in PLACE. Company number 17330962. Registered office: 1 Sample Street, Sampletown." in en, en
    assert "wedi&rsquo;i gofrestru yn PLACE. Rhif cwmni 17330962. Swyddfa gofrestredig: 1 Stryd Sampl, Trefsampl." in cy, cy

def t_public_refused():
    code = ("import sys; sys.argv=['build.py']; sys.path.insert(0, %r); import showcase; showcase.is_public=lambda: True; "
            "import build; build.OUT=%r; build.build()") % (os.path.join(REPO, "website", "_src"), tempfile.mkdtemp())
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode != 0 and "the showcase cannot be public" in r.stderr and "registered_in" in r.stderr, r.stderr[-300:] or "the build went ahead"

def t_ld():
    refused(lambda: showcase.check_ld([{"@type": "HairSalon", "aggregateRating": {"ratingValue": 5}}], "/x/"), "aggregateRating")
    refused(lambda: showcase.check_ld([{"@type": "HairSalon", "review": []}], "/x/"), "review")
    refused(lambda: showcase.check_ld([{"@type": "HairSalon", "additionalType": "x"}], "/x/"), "additionalType")
    refused(lambda: showcase.check_ld([{"@graph": [{"@type": "FAQPage"}]}], "/x/"), "FAQPage")

def t_hreflang():
    page = {"key": "k", "en": {"path": "/a/"}, "cy": {"path": "/cy/a/"}}
    d = "https://x.example"
    good = lambda p: f'<link rel="canonical" href="{d}{p}">' + "".join(showcase.hreflang_links(page, d))
    built = {"/a/": good("/a/"), "/cy/a/": good("/cy/a/")}
    showcase.check_hreflang([page], built, d)
    refused(lambda: showcase.check_hreflang([{"key": "solo", "en": {"path": "/s/"}}], {}, d), "no Welsh page")
    refused(lambda: showcase.check_hreflang([page], dict(built, **{"/cy/a/": built["/cy/a/"].replace('hreflang="en-GB"', 'hreflang="en"')}), d), "is missing")
    refused(lambda: showcase.check_hreflang([page], dict(built, **{"/a/": built["/a/"].replace("canonical", "canonicle")}), d), "canonical")
    refused(lambda: showcase.check_hreflang([page, dict(page, key="dup")], built, d), "share a path")

PREVIEW = tempfile.mkdtemp(prefix="showcase-preview-")
BUILD = subprocess.run([sys.executable, os.path.join(REPO, "website", "_src", "build.py"), "--preview", PREVIEW], capture_output=True, text=True)

def read(rel):
    return open(os.path.join(PREVIEW, rel), encoding="utf-8").read()

def html_pages():
    for dirpath, _d, files in os.walk(PREVIEW):
        for fn in files:
            if fn.endswith(".html"):
                yield os.path.relpath(os.path.join(dirpath, fn), PREVIEW), open(os.path.join(dirpath, fn), encoding="utf-8").read()

def t_preview_home():
    assert BUILD.returncode == 0, BUILD.stderr[-400:]
    for rel, lang in (("index.html", "en"), ("cy/index.html", "cy")):
        h = read(rel)
        assert h.count('class="sc-path"') == 3, f"{rel}: not three paths"
        for href in ((("/courses/", "/salon/", "/work/") if lang == "en" else ("/cy/cyrsiau/", "/cy/salon/", "/cy/gwaith/"))):
            assert f'<a class="sc-path" href="{href}">' in h, f"{rel}: no path to {href}"
        assert len(re.findall(r"<h1[ >]", h)) == 1
        assert "fonts.googleapis.com" not in h and "fonts.gstatic.com" not in h, f"{rel}: asks a font service"
        assert 'hreflang="en-GB"' in h and 'hreflang="x-default"' in h
        for img in re.findall(r"<img [^>]+>", h):
            assert re.search(r'width="\d+" height="\d+"', img), f"{rel}: an image has no size: {img[:80]}"
            assert re.search(r'alt="[^"]*"', img), f"{rel}: an image has no alt"
        assert "illustration" in h or "darlunio" in h, f"{rel}: stock photographs are not labelled as illustration"
        assert "St Asaph Business Park" in h or "Parc Busnes Llanelwy" in h
        assert "Unit N" not in h and "Uned N" not in h and "LL17 0LJ" not in h, f"{rel}: the placeholder unit or postcode is printed"

def t_preview_every_page():
    n = 0
    for rel, h in html_pages():
        n += 1
        assert '<span class="sc-legal">' in h, f"{rel}: no statutory line in the footer"
        assert "Company number 17330962" in h or "Rhif cwmni 17330962" in h, f"{rel}: no company number"
        assert "FAQPage" not in h, f"{rel}: FAQPage markup"
        assert not re.search(r'"(?:aggregateRating|review|additionalType)"', h), f"{rel}: review or additionalType markup"
        assert "Bod Hyfryd" not in h, f"{rel}: the residential registered office is published"
        assert "googleapis" not in h, f"{rel}: third-party font request"
    assert n >= 60, f"only {n} pages built"
    # FAQs stay as visible content where they were.
    assert "<details" in read("funding/index.html") or 'class="faq' in read("funding/index.html"), "the funding FAQs are no longer on the page"

def t_preview_salon_ld():
    h = read("salon/index.html")
    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)]
    salon = [b for b in blocks if b.get("@type") == "HairSalon"]
    assert len(salon) == 1, "no single HairSalon block"
    s = salon[0]
    assert s["address"]["addressLocality"] == "St Asaph" and s["address"]["addressCountry"] == "GB"
    assert "streetAddress" not in s["address"] and "postalCode" not in s["address"], "a placeholder street or postcode is in the structured data"
    assert "geo" not in s and "openingHoursSpecification" not in s and "priceRange" not in s, "an unconfirmed value is in the structured data"
    assert 'id="find-us"' in h, "the salon page has no Find us block"
    assert "<title>Hairdresser &amp; Barber in St Asaph | Clwydian Academy Salon</title>" in h
    site = copy.deepcopy(SITE); site["salon_address"]["todo_pm"] = False; site["salon_address"]["geo"]["todo_pm"] = False
    full = showcase.hairsalon_ld("en", "https://x.example", {"@type": "EducationalOrganization", "@id": "o", "image": "i"}, site)[0]
    assert full["address"]["streetAddress"].endswith("Ffordd Richard Davies") and full["address"]["postalCode"] == "LL17 0LJ"
    assert full["geo"]["@type"] == "GeoCoordinates"
    assert showcase.address_text("en", site) == site["salon_address"]["value"]["en"], "the footer and the JSON-LD would not share one address"

def t_preview_work():
    for rel in ("work/index.html", "cy/gwaith/index.html"):
        h = read(rel)
        assert h.count('class="sc-course') == 4, f"{rel}: not four courses"
        assert "2027" in h and 'data-ba' not in h, f"{rel}: a pair is shown, or no placeholder"
        assert '<dialog class="sc-lightbox"' in h
    assert "/work/" in read("sitemap.xml") and "/cy/gwaith/" in read("sitemap.xml")

def t_photos():
    d = os.path.join(PREVIEW, "assets", "img", "photos")
    files = sorted(os.listdir(d))
    assert len(files) == 66, f"{len(files)} photograph files"
    for fn in files:
        assert not re.search(r"charlotte|eleanor|logo|mark|franchise|^(hero|band|split|svc|tile)", fn, re.I), fn
        head = open(os.path.join(d, fn), "rb").read(4096)
        assert b"Exif" not in head and b"GPS" not in head, f"{fn} carries EXIF"
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_claims.py"), PREVIEW], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-400:]
    # The linter is watched failing on each thing it now guards.
    bad = os.path.join(d, "svc-colour-720.jpg"); open(bad, "wb").write(b"x")
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_claims.py"), PREVIEW], capture_output=True, text=True)
    os.remove(bad)
    assert r.returncode != 0 and "svc-" in r.stdout, "the linter passed a photograph under its old name"
    bad = os.path.join(d, "salon-test-1.jpg"); open(bad, "wb").write(b"\xff\xd8\xff\xe1\x00\x10Exif\x00\x00MM")
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_claims.py"), PREVIEW], capture_output=True, text=True)
    os.remove(bad)
    assert r.returncode != 0 and "EXIF" in r.stdout, "the linter passed a photograph with EXIF"

def t_off():
    site = os.path.join(REPO, "site")
    for rel in ("assets/img/photos", "assets/fonts", "assets/css/showcase.css", "assets/js/showcase.js", "work", "cy/gwaith"):
        assert not os.path.exists(os.path.join(site, rel)), f"site/{rel} exists with the switch off"
    assert json.load(open(showcase.SWITCH_PATH))["public"] is False, "the showcase switch is ON in the repository"
    home = open(os.path.join(site, "index.html"), encoding="utf-8").read()
    assert "sc-path" not in home and "sc-legal" not in home, "the deployed home page is the showcase"

for name, fn in [
    ("a before-and-after pair is refused without consent ref, a real consent date, originals, own client, no retouching — 20 ways", t_pairs),
    ("a pair renders as a labelled range slider with sized pictures, and never prints its consent record", t_pair_html),
    ("a stock photograph cannot be described as a learner's, student's or client's work; all 15 are stock and renamed", t_stock),
    ("the statutory line leaves a TODO_PM value out, never prints the residential address, and is complete once filled", t_legal),
    ("the build refuses to make the showcase public while a statutory value is TODO_PM", t_public_refused),
    ("structured data: review, aggregateRating, additionalType and FAQPage each stop the build", t_ld),
    ("hreflang: a missing pair, a one-way pair, a wrong canonical and a shared path each stop the build", t_hreflang),
    ("preview: the home page has three paths, sized images, no font service, and no placeholder address — EN and CY", t_preview_home),
    ("preview: every page carries the statutory line and no FAQPage, review markup or third-party font", t_preview_every_page),
    ("preview: HairSalon carries only confirmed values; one address feeds footer and JSON-LD", t_preview_salon_ld),
    ("preview: the learner-work page has four courses, placeholders, no pair, and is in the sitemap", t_preview_work),
    ("photographs: 66 files, renamed, no EXIF; the linter fails on an old name and on EXIF", t_photos),
    ("switch off: the deployed folder holds nothing of the showcase", t_off),
]:
    test(name, fn)
print(f"\n  {passed} passed, {failed} failed\n")
sys.exit(1 if failed else 0)
