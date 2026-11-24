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
    # Everything in the data file today is SAMPLE data: a public build refuses every item of it.
    assert WORK["pairs"] and all(p.get("sample") is True for p in WORK["pairs"]), "a real pair is in the data file: extend this test to read its consent record"
    refused(lambda: showcase.validate_pairs(copy.deepcopy(WORK)), "SAMPLE data, which is built in previews only")
    refused(lambda: showcase.validate_portfolios(copy.deepcopy(WORK)), "SAMPLE data, which is built in previews only")
    assert len(showcase.validate_pairs(copy.deepcopy(WORK), preview=True)) == 2
    # A sample may never be a photograph, and a real pair may never be dressed as a sample.
    w = copy.deepcopy(WORK); w["pairs"][0]["ext"] = "jpg"
    refused(lambda: showcase.validate_pairs(w, preview=True, files={"sample-0001-before.jpg", "sample-0001-after.jpg", "sample-0002-before.svg", "sample-0002-after.svg"}), "never a photograph")
    w = copy.deepcopy(WORK); w["pairs"] = [dict(copy.deepcopy(GOOD), id="sample-9")]
    refused(lambda: showcase.validate_pairs(w, today="2027-02-01", files={"sample-9-before.jpg", "sample-9-after.jpg"}), "only sample data")

def t_portfolios():
    base = copy.deepcopy(WORK)
    real = {"slug": "learner-a7", "course": "l2-hairdressing", "started": "2027-01", "consentRef": "LC-0007", "consentDate": "2027-01-20",
            "achievements": [{"badge": "qualification", "date": "2027-03", "en": "Unit: cut hair using basic techniques", "cy": "Uned: torri gwallt"}]}
    def folio(**change):
        w = copy.deepcopy(base); w["pairs"] = []; p = copy.deepcopy(real)
        for k, v in change.items():
            if v is KeyError: p.pop(k, None)
            else: p[k] = v
        w["portfolios"] = [p]
        return lambda: showcase.validate_portfolios(w, today="2027-06-01")
    assert len(folio()()) == 1, "a complete portfolio was refused"
    for change, needle in [
        (dict(slug="morgan-jones"), "never a name"), (dict(slug="learner-Morgan"), "never a name"), (dict(slug="learner-averylongcode1"), "never a name"),
        (dict(name="A Learner"), "names a person"), (dict(consentRef=KeyError), "consentRef"), (dict(consentDate="soon"), "consentDate"),
        (dict(consentDate="2027-09-01"), "in the future"), (dict(course="l9"), "course"), (dict(started="January"), "YYYY-MM"),
        (dict(slug="sample-learner-zz"), "must be marked"), (dict(sample=True), "must start 'sample-'"),
        (dict(achievements=[{"badge": "gold-star", "date": "2027-03", "en": "Something", "cy": "Rhywbeth"}]), "badge"),
        (dict(achievements=[{"badge": "competition", "date": "2027-03", "en": "Won, styled by Morgan", "cy": "Enillodd y gystadleuaeth"}]), "name somebody"),
    ]:
        refused(folio(**change), needle)
    w = copy.deepcopy(base); w["portfolios"] = []
    refused(lambda: showcase.validate_portfolios(w, preview=True), "a portfolio that does not exist")

def t_preview_portfolio():
    for rel, back in (("work/sample-learner-a1/index.html", "/work/"), ("cy/gwaith/sample-learner-a1/index.html", "/cy/gwaith/")):
        h = read(rel)
        assert '<meta name="robots" content="noindex, nofollow">' in h, f"{rel}: a sample page is indexable"
        assert 'class="sc-sample-note" role="note"' in h and h.count("sc-badge--sample") >= 2, f"{rel}: sample data is not marked as sample"
        assert h.count("data-ba ") == 2 and h.count('type="range"') == 2, f"{rel}: not two before-and-after sliders"
        assert h.count('<li><span class="sc-badge">') == 3, f"{rel}: not three achievements with badges"
        assert "SAMPLE-LEARNER-A1" not in h and "SAMPLE-CLIENT" not in h, f"{rel}: a consent reference is printed"
        assert f'href="{back}"' in h
        assert '.svg"' in h and ".jpg" not in h.split("<main")[1].split("</main>")[0], f"{rel}: a sample uses a photograph"
        assert 'hreflang="en-GB"' in h and 'hreflang="cy"' in h
    assert 'href="/work/sample-learner-a1/"' in read("work/index.html"), "the gallery does not link to the portfolio"
    sm = read("sitemap.xml")
    assert "sample-learner" not in sm, "a sample page is in the sitemap"


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

def t_vercel():
    """A Vercel PREVIEW deployment builds everything on, marked as a preview, with the gaps shown
    as [TBC] and no page indexable. Production builds nothing. Run on a COPY of the repository."""
    import shutil
    copy = os.path.join(tempfile.mkdtemp(prefix="vercel-"), "repo")
    shutil.copytree(REPO, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
    cmd = json.load(open(os.path.join(copy, "site", "vercel.json")))["buildCommand"]
    before = open(os.path.join(copy, "site", "index.html"), encoding="utf-8").read()
    for env in ("production", ""):
        r = subprocess.run(["bash", "-c", cmd], cwd=os.path.join(copy, "site"), capture_output=True, text=True, env=dict(os.environ, VERCEL_ENV=env))
        assert r.returncode == 0 and "nothing built" in r.stdout, r.stdout[-200:] + r.stderr[-200:]
        assert open(os.path.join(copy, "site", "index.html"), encoding="utf-8").read() == before, f"VERCEL_ENV={env!r} changed the deployed home page"
    assert not os.path.exists(os.path.join(copy, "site", "work")), "production has a /work/ page"
    r = subprocess.run(["bash", "-c", cmd], cwd=os.path.join(copy, "site"), capture_output=True, text=True,
                       env=dict(os.environ, VERCEL_ENV="preview", VERCEL_GIT_COMMIT_REF="feat/salon", VERCEL_GIT_COMMIT_SHA="0123456789"))
    assert r.returncode == 0 and "showcase: ON (PREVIEW)" in r.stdout, r.stdout[-300:] + r.stderr[-300:]
    n = 0
    for dirpath, _d, files in os.walk(os.path.join(copy, "site")):
        for fn in files:
            if not fn.endswith(".html"): continue
            h = open(os.path.join(dirpath, fn), encoding="utf-8").read(); n += 1
            rel = os.path.relpath(os.path.join(dirpath, fn), copy)
            assert '<aside class="sc-preview" aria-label="Preview">Preview build' in h and "feat/salon 0123456" in h, f"{rel}: a preview page does not say it is a preview"
            assert '<meta name="robots" content="noindex, nofollow">' in h, f"{rel}: a preview page is indexable"
            assert h.count('<strong class="sc-tbc-mark">[TBC]</strong>') == 2, f"{rel}: the two missing statutory values are not marked TBC"
            assert "Bod Hyfryd" not in h
    assert n >= 60
    assert "<loc>" not in open(os.path.join(copy, "site", "sitemap.xml")).read(), "a preview deployment has a sitemap with pages in it"
    home = open(os.path.join(copy, "site", "index.html"), encoding="utf-8").read()
    nav = re.findall(r'<a href="([^"]+)"(?: aria-current="page")?>', home[home.index('<nav class="site-nav"'):home.index("</nav>")])
    assert nav == ["/courses/", "/apprenticeships/", "/funding/", "/salon/", "/work/", "/about/", "/contact/"], f"the trimmed nav is not the seven proposed: {nav}"
    foot = home[home.index('<footer class="site-footer">'):]
    assert 'href="/for-salons/"' in foot and 'href="/guides/"' in foot, "a page trimmed from the header is not in the footer"
    # [TBC] is for previews ONLY: a public line never carries it, and a public build still refuses.
    assert "TBC" not in showcase.legal_line("en", SITE) and "TBC" not in showcase.legal_line("cy", SITE)

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
        assert "2027" in h and h.count("sc-soon-h") >= 3, f"{rel}: the courses with no work yet have lost their placeholder"
        assert '<dialog class="sc-lightbox"' in h
    assert "/work/" in read("sitemap.xml") and "/cy/gwaith/" in read("sitemap.xml")

def t_prices():
    for rel in ("salon/prices/index.html", "cy/salon/prisiau/index.html"):
        h = read(rel)
        assert 'id="how"' in h, f"{rel}: no explanation of how a price is calculated"
        cells = re.findall(r"<td>.*?</td>", h, re.S)
        froms = [c for c in cells if re.search(r"<b>(?:from|o) &pound;", c)]
        assert froms, f"{rel}: fixture moved — no from-price on the page"
        for c in froms:
            assert 'class="salon-how"><a href="#how">' in c, f"{rel}: a from-price has no 'how this is calculated' beside it: {c[:90]}"
        for row in re.findall(r"<tr><th scope=\"row\">.*?</tr>", h, re.S):
            if "consultation first" in row or "Ymgynghoriad am ddim" in row:
                priced = [c for c in re.findall(r"<td>.*?</td>", row, re.S) if "&pound;" in c]
                assert all("salon-how" in c for c in priced), f"{rel}: a consultation price has no note beside it"
        assert re.search(r"supervised by a qualified educator|dan oruchwyliaeth addysgwr cymwysedig", h), f"{rel}: supervision is not stated"
        assert re.search(r"no booking fee and nothing is added at checkout|Nid oes ffi archebu", h), f"{rel}: the total-price statement is missing"

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
    ("a portfolio is refused with a name-like slug, a name, no learner consent, or unmarked sample data — 14 ways", t_portfolios),
    ("preview: the sample portfolio is marked SAMPLE, noindex, out of the sitemap, with two sliders and three badges — EN and CY", t_preview_portfolio),
    ("a pair renders as a labelled range slider with sized pictures, and never prints its consent record", t_pair_html),
    ("a stock photograph cannot be described as a learner's, student's or client's work; all 15 are stock and renamed", t_stock),
    ("the statutory line leaves a TODO_PM value out, never prints the residential address, and is complete once filled", t_legal),
    ("the build refuses to make the showcase public while a statutory value is TODO_PM", t_public_refused),
    ("Vercel: production builds nothing; a preview builds everything on, marked, noindex, gaps shown as [TBC], seven-item nav", t_vercel),
    ("structured data: review, aggregateRating, additionalType and FAQPage each stop the build", t_ld),
    ("hreflang: a missing pair, a one-way pair, a wrong canonical and a shared path each stop the build", t_hreflang),
    ("preview: the home page has three paths, sized images, no font service, and no placeholder address — EN and CY", t_preview_home),
    ("preview: every page carries the statutory line and no FAQPage, review markup or third-party font", t_preview_every_page),
    ("preview: HairSalon carries only confirmed values; one address feeds footer and JSON-LD", t_preview_salon_ld),
    ("preview: the learner-work page has four courses, placeholders, no pair, and is in the sitemap", t_preview_work),
    ("prices: every from-price and consultation price has 'how this is calculated' beside it; supervision and total price stated", t_prices),
    ("photographs: 66 files, renamed, no EXIF; the linter fails on an old name and on EXIF", t_photos),
    ("switch off: the deployed folder holds nothing of the showcase", t_off),
]:
    test(name, fn)
print(f"\n  {passed} passed, {failed} failed\n")
sys.exit(1 if failed else 0)
