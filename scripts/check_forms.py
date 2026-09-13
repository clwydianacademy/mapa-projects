#!/usr/bin/env python3
"""
check_forms.py — the enquiry route is a real form, everywhere, in both languages.

    python3 scripts/check_forms.py ["clwydian-academy 2"]

  * no <a class="btn …" href="mailto:…"> anywhere — a mailto in a CTA position is a dead end on
    a phone (a plain email address in an address block or a policy is fine)
  * every <form> posts to an action that exists: /api/<name> must have <root>/api/<name>.js,
    any other action must be a built page
  * every visible input/select/textarea has an id and a <label for=…>
  * every form carries the honeypot (name="website"), the time stamp (name="ts") and the
    fields the brief fixed: name, email, enquiry, message, lang
Exit 0 = clean, 1 = problems, 2 = no dir.
"""
import os, re, sys

REQUIRED = ("name", "email", "enquiry", "message", "lang")
HONEYPOT, STAMP = "website", "ts"

def check(root):
    problems, forms, pages = [], 0, 0
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            pages += 1
            url = "/" + os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
            url = url[:-len("index.html")] if url.endswith("/index.html") else url
            html = open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace").read()
            for m in re.finditer(r"<a\b[^>]*>", html):
                tag = m.group(0)
                if 'href="mailto:' in tag and re.search(r'class="[^"]*\bbtn\b', tag):
                    snippet = re.sub(r"\s+", " ", tag)[:90]
                    problems.append(f"{url}: mailto in a CTA — {snippet}")
            for fm in re.finditer(r"<form\b[^>]*>(.*?)</form>", html, re.S):
                forms += 1
                head, body = fm.group(0).split(">", 1)[0], fm.group(1)
                method = re.search(r'method="([^"]+)"', head)
                action = re.search(r'action="([^"]+)"', head)
                if not method or method.group(1).lower() != "post":
                    problems.append(f"{url}: form does not POST")
                if not action:
                    problems.append(f"{url}: form has no action"); continue
                a = action.group(1)
                if a.startswith("/api/"):
                    fpath = os.path.join(root, "api", a[len("/api/"):].split("?")[0] + ".js")
                    if not os.path.isfile(fpath):
                        problems.append(f"{url}: action {a} has no function at {os.path.relpath(fpath, root)}")
                else:
                    p = os.path.join(root, a.lstrip("/"), "index.html") if a.endswith("/") else os.path.join(root, a.lstrip("/"))
                    if not os.path.exists(p):
                        problems.append(f"{url}: action {a} is not a built page")
                names = set(re.findall(r'\bname="([^"]+)"', body))
                for r in REQUIRED + (HONEYPOT, STAMP):
                    if r not in names:
                        problems.append(f"{url}: form lacks field name=\"{r}\"")
                labels = set(re.findall(r'<label\b[^>]*\bfor="([^"]+)"', body))
                for cm in re.finditer(r"<(input|select|textarea)\b[^>]*>", body):
                    tag = cm.group(0)
                    t = re.search(r'type="([^"]+)"', tag)
                    if t and t.group(1) in ("hidden", "submit"):
                        continue
                    i = re.search(r'\bid="([^"]+)"', tag)
                    if not i:
                        problems.append(f"{url}: control without id — {tag[:70]}")
                    elif i.group(1) not in labels:
                        problems.append(f"{url}: no <label for=\"{i.group(1)}\">")
    return problems, forms, pages

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "clwydian-academy 2"
    if not os.path.isdir(root):
        print(f"check_forms: no such directory: {root}"); return 2
    problems, forms, pages = check(root)
    if not problems:
        print(f"check_forms: {pages} pages, {forms} forms — no mailto CTAs, every form posts to a real action, every control labelled."); return 0
    print(f"check_forms: {pages} pages, {forms} forms — {len(problems)} problem(s)\n")
    for p in problems: print("  ", p)
    print("\nFAIL — fix the fragment (or add the function under clwydian-academy 2/api/), then rebuild.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
