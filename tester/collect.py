"""Step 1: gather evidence from a running app. No AI yet, just facts.
Usage: python collect.py http://localhost:8000
"""
import sys, json, pathlib
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

AXE = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"
OUT = pathlib.Path("evidence"); OUT.mkdir(exist_ok=True)

def collect(url):
    ev = {"url": url, "console_errors": [], "failed_requests": [],
          "broken_links": [], "a11y": [], "elements": []}
    with sync_playwright() as p:
        b = p.chromium.launch(); page = b.new_page(viewport={"width": 1280, "height": 800})
        page.on("console", lambda m: m.type == "error" and ev["console_errors"].append(m.text))
        page.on("pageerror", lambda e: ev["console_errors"].append(str(e)))
        page.on("requestfailed", lambda r: ev["failed_requests"].append(r.url))
        page.on("response", lambda r: r.status >= 400 and
                ev["failed_requests"].append(f"{r.status} {r.url}"))
        page.goto(url, wait_until="networkidle")
        page.screenshot(path=str(OUT / "home.png"), full_page=True)

        # What can a user interact with? The AI will plan from this list.
        ev["elements"] = page.evaluate("""() => [...document.querySelectorAll(
          'a,button,input,select,textarea,[onclick]')].map((e,i) => ({
            i, tag: e.tagName.toLowerCase(), type: e.type || null,
            text: (e.innerText || e.placeholder || '').trim().slice(0, 60),
            id: e.id || null, href: e.getAttribute('href'),
            labelled: !!(e.labels && e.labels.length) || !!e.getAttribute('aria-label')
        }))""")

        # Broken links
        for l in {e["href"] for e in ev["elements"] if e["href"] and not e["href"].startswith("#")}:
            r = page.request.get(urljoin(url, l))
            if r.status >= 400: ev["broken_links"].append(f"{r.status} {l}")

        # Accessibility via axe-core
        try:
            page.add_script_tag(url=AXE)
            res = page.evaluate("axe.run()")
            ev["a11y"] = [{"rule": v["id"], "impact": v["impact"], "help": v["help"],
                           "count": len(v["nodes"])} for v in res["violations"]]
        except Exception as e:
            ev["a11y"] = [f"axe failed: {e}"]
        b.close()
    (OUT / "evidence.json").write_text(json.dumps(ev, indent=2))
    print(f"Saved evidence/evidence.json and evidence/home.png")
    return ev

if __name__ == "__main__":
    collect(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")
