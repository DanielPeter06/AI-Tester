"""Step 2: Gemini decides what to try, Playwright does it, we record what happened.
Usage: python explore.py http://localhost:8000"""
import sys, json, pathlib
from playwright.sync_api import sync_playwright
from llm import ask_json

OUT = pathlib.Path("evidence"); OUT.mkdir(exist_ok=True)
ROUNDS, PER_ROUND = 2, 6
SEL = "a,button,input,select,textarea,[onclick]"
INVENTORY = """(sel) => [...document.querySelectorAll(sel)].map((e,i) => ({
  i, tag: e.tagName.toLowerCase(), type: e.type || null,
  text: (e.innerText || e.placeholder || '').trim().slice(0,60),
  id: e.id || null, href: e.getAttribute('href'),
  labelled: !!(e.labels && e.labels.length) || !!e.getAttribute('aria-label')}))"""
SNAP = """() => ({text: document.body.innerText.slice(0,600),
  html_len: document.body.innerHTML.length,
  overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth})"""

PLAN = """You are a skeptical QA engineer testing a web app you have never seen.

Visible page text:
<<TEXT>>

Interactive elements (refer to them by their "i" number):
<<ELEMENTS>>

Actions already tried and what happened:
<<HISTORY>>

Plan up to <<N>> NEW actions most likely to expose bugs. Think like a user who is careless
or hostile: submit forms empty, enter invalid values, whitespace only, very long text
(write out about 200 characters), special characters, HTML such as <img src=x onerror=alert(1)>,
then click buttons to see whether they actually do anything. Fill a field BEFORE clicking its
submit button. Do not click links that navigate away.
Reply ONLY with JSON:
{"actions":[{"action":"fill" or "click","index":<int>,"value":"<text, for fill only>","why":"<what you are probing>"}]}"""

def fill(template, **kw):
    for k, v in kw.items():
        template = template.replace(f"<<{k}>>", str(v))
    return template

def run(url):
    log = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        errors, dialogs = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        def on_dialog(d): dialogs.append(d.message); d.dismiss()
        page.on("dialog", on_dialog)
        page.goto(url, wait_until="networkidle")

        for rnd in range(ROUNDS):
            els = page.evaluate(INVENTORY, SEL)
            snap = page.evaluate(SNAP)
            print(f"Round {rnd+1}: asking Gemini what to try...")
            plan = ask_json(fill(PLAN, TEXT=snap["text"], ELEMENTS=json.dumps(els),
                                 HISTORY=json.dumps(log[-12:]) or "none", N=PER_ROUND))
            for a in plan.get("actions", [])[:PER_ROUND]:
                before = page.evaluate(SNAP); errors.clear(); dialogs.clear(); err = None
                idx = int(a.get("index", -1))
                try:
                    loc = page.locator(SEL).nth(idx)
                    if a["action"] == "fill": loc.fill(a.get("value", ""), timeout=2000)
                    else: loc.click(timeout=2000)
                    page.wait_for_timeout(600)
                except Exception as e:
                    err = str(e).splitlines()[0][:150]
                if page.url.split("#")[0].rstrip("/") != url.rstrip("/"):
                    page.goto(url, wait_until="networkidle")
                after = page.evaluate(SNAP)
                el = els[idx] if 0 <= idx < len(els) else {}
                entry = {"round": rnd + 1, "action": a["action"],
                         "element": el.get("id") or el.get("text"),
                         "value_length": len(a.get("value", "")),
                         "value_preview": a.get("value", "")[:80],
                         "why": a.get("why"), "error": err,
                         "text_changed": before["text"] != after["text"],
                         "html_changed": before["html_len"] != after["html_len"],
                         "text_after": after["text"][:300],
                         "new_console_errors": list(errors), "dialogs": list(dialogs),
                         "horizontal_overflow": after["overflow"]}
                log.append(entry)
                print(f"  {entry['action']:5} {str(entry['element']):16} {entry['why']}")
        page.screenshot(path=str(OUT / "explored.png"), full_page=True)
        browser.close()
    (OUT / "exploration.json").write_text(json.dumps(log, indent=2))
    print(f"Saved {len(log)} steps to evidence/exploration.json")

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")
