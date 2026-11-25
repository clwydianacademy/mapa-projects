#!/usr/bin/env python3
"""test_feed_sync.py — a price changed in the booking system reaches this site by itself, and only a real feed can.

    python3 scripts/test_feed_sync.py

scripts/sync_salon_feed.py fetches the booking system's live catalogue and, if it differs from
_data/salon/feed.json, replaces it. It runs unattended every night (.github/workflows/salon-feed.yml),
so what it REFUSES matters more than what it accepts: an error page, half a file, a feed for somebody
else, a price of nothing. Each refusal below is driven against a real local HTTP server.
Standard library only.
"""
import copy, http.server, json, os, shutil, sys, tempfile, threading

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import sync_salon_feed as sync

COMMITTED = os.path.join(REPO, "_data", "salon", "feed.json")
GOOD = json.load(open(COMMITTED, encoding="utf-8"))
# WHAT THE ENDPOINT REALLY SERVES (read from salon-booking's handler, 25 Nov): no _source line, and a
# generatedAt that is different every time it is asked. The first draft of this test left that
# field out, passed, and would have "changed" the feed every single night.
LIVE = {"version": GOOD["version"], "generatedAt": "2026-11-25T03:17:00.000Z"}
LIVE.update({k: v for k, v in GOOD.items() if k not in ("_source", "version")})

passed = failed = 0
def check(ok, what, detail=""):
    global passed, failed
    if ok: passed += 1; print("  ok    " + what)
    else: failed += 1; print("  FAIL  " + what + ("\n        " + str(detail)[:400] if detail else ""))

SERVE = {"status": 200, "body": b"", "type": "application/json"}
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(SERVE["status"]); self.send_header("Content-Type", SERVE["type"]); self.end_headers(); self.wfile.write(SERVE["body"])
    def log_message(self, *a): pass
server = http.server.HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/api/salon/feed/" % server.server_port

work = tempfile.mkdtemp(prefix="feed-sync-")
target = os.path.join(work, "feed.json")
def run(body, status=200, ctype="application/json", url=URL):
    shutil.copyfile(COMMITTED, target)
    SERVE.update(status=status, body=body if isinstance(body, bytes) else json.dumps(body).encode(), type=ctype)
    out = sync.sync(url, target, allow_http=True)
    return out, open(target, encoding="utf-8").read()
before = open(COMMITTED, encoding="utf-8").read()

# 1. the same catalogue: nothing changes, and the file is byte-for-byte what the booking system exports
out, after = run(LIVE)
check(out["changed"] is False and after == before, "the same catalogue changes nothing", out)
check(sync.render(LIVE) == before, "and what this would write is byte-for-byte what the booking system's own export writes")
later = dict(LIVE, generatedAt="2026-11-26T03:17:00.000Z")
out, after = run(later)
check(out["changed"] is False and after == before and "generatedAt" not in after, "asked again a night later with nothing changed: still no change (the time it was served is not part of the catalogue)", out)

# 2. a price changed in Settings: the file follows, and says what changed
dearer = copy.deepcopy(LIVE); dearer["services"][0]["levels"]["l2"]["price"] += 2; dearer["version"] = "0000000000000001"
out, after = run(dearer)
got = json.loads(after)
check(out["changed"] is True and got["services"][0]["levels"]["l2"]["price"] == LIVE["services"][0]["levels"]["l2"]["price"] + 2 and got["_source"] == GOOD["_source"], "a price changed in the booking system is written here", out)
check(any(LIVE["services"][0]["name"] in line for line in out.get("summary", [])), "and the change is named in words, for the commit message", out.get("summary"))

# 3. everything that is NOT a real feed leaves the file exactly as it was
def refused(label, body, **kw):
    out, after = run(body, **kw)
    check(out["changed"] is False and after == before and out.get("refused"), "refused, file untouched: " + label, out)
refused("an error page", b"<html><body>502 Bad Gateway</body></html>", ctype="text/html")
refused("a 500", LIVE, status=500)
refused("half a file", json.dumps(LIVE).encode()[:900])
refused("an empty object", {})
x = copy.deepcopy(LIVE); x["for"] = "Somebody Else's Salon"; refused("a feed for another business", x)
x = copy.deepcopy(LIVE); x["services"] = []; refused("no services at all", x)
x = copy.deepcopy(LIVE); x["services"] = x["services"][: max(1, len(x["services"]) // 3)]; refused("two thirds of the price list gone at once", x)
x = copy.deepcopy(LIVE); x["services"][0]["levels"]["l2"]["price"] = 0; refused("a price of nothing", x)
x = copy.deepcopy(LIVE); x["services"][0]["levels"]["l2"]["price"] = -5; refused("a negative price", x)
x = copy.deepcopy(LIVE); x["services"][0]["levels"]["l2"]["price"] = "26"; refused("a price that is text", x)
x = copy.deepcopy(LIVE); x["services"][0]["levels"]["l2"]["price"] *= 12; refused("a price twelve times what it was (a slip of the finger in Settings is checked by a person, not published overnight)", x)
x = copy.deepcopy(LIVE); x["services"][0]["levels"]["l2"]["minutes"] = 0; refused("an appointment of no minutes", x)
x = copy.deepcopy(LIVE); x["totalPrice"] = False; refused("prices that are not the total price", x)
x = copy.deepcopy(LIVE); x["currency"] = "USD"; refused("another currency", x)
x = copy.deepcopy(LIVE); x["hours"] = []; refused("no opening hours", x)
x = copy.deepcopy(LIVE); x["services"][0]["book"] = "https://evil.example/book/"; refused("a Book link to another site", x)
x = copy.deepcopy(LIVE); x["services"][0]["name"] = "Cut <script>alert(1)</script>"; refused("markup in a service name", x)
x = copy.deepcopy(LIVE); x["extra"] = "y" * 600000; refused("an absurdly large file", x)

# 4. the booking system not answering is not an alarm: nothing changes and nothing fails
shutil.copyfile(COMMITTED, target)
out = sync.sync("http://127.0.0.1:1/api/salon/feed/", target, allow_http=True)
check(out["changed"] is False and out.get("unreachable") and not out.get("refused") and open(target, encoding="utf-8").read() == before, "the booking system not answering changes nothing and is not an error", out)

# 5. only https, and only the salon's own booking host, unless a test says otherwise
shutil.copyfile(COMMITTED, target)
for bad in ["http://book.clwydianacademy.co.uk/api/salon/feed/", "https://evil.example/api/salon/feed/", "file:///etc/passwd"]:
    out = sync.sync(bad, target)
    check(out.get("refused") and out["changed"] is False, "will not fetch from " + bad, out)

# 6. the workflow commits source, builds, then commits output — separately (CLAUDE.md, build discipline)
wf = open(os.path.join(REPO, ".github", "workflows", "salon-feed.yml"), encoding="utf-8").read()
order = [wf.find("scripts/sync_salon_feed.py"), wf.find("git commit -m \"Salon feed"), wf.find("website/_src/build.py"), wf.find("git commit -m \"Build:")]
check(all(i > 0 for i in order) and order == sorted(order), "the nightly job fetches, commits the feed, builds, then commits the output — in that order", order)
check("scripts/test_salon_feed.py" in wf and "check_claims.py" in wf and wf.find("scripts/test_salon_feed.py") < wf.find("git push"), "and pushes nothing until the site's own checks pass")
check("schedule:" in wf and "workflow_dispatch" in wf and "contents: write" in wf, "it runs nightly, can be run by hand, and may write only to this repository's contents")

server.shutdown(); shutil.rmtree(work, ignore_errors=True)
print("\n  %d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
