"""Step 4: turn evidence/findings.json into one self-contained report.html.
Usage: python report.py"""
import json, base64, html, pathlib, datetime, webbrowser

OUT = pathlib.Path("evidence")
esc = lambda x: html.escape("" if x is None else str(x))

def img(name, caption):
    p = OUT / name
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (f'<figure><img alt="{esc(caption)}" src="data:image/png;base64,{b64}">'
            f'<figcaption>{esc(caption)}</figcaption></figure>')

def as_list(x):
    if isinstance(x, list): return [str(i) for i in x]
    return [str(x)] if x else []

def card(f):
    sev, typ = f.get("severity", "low"), f.get("type", "bug")
    steps = "".join(f"<li>{esc(s)}</li>" for s in as_list(f.get("steps_to_reproduce")))
    ev = f.get("evidence")
    ev = ev if isinstance(ev, str) else json.dumps(ev, indent=2)
    return f"""<article class="card sev-{esc(sev)}" data-type="{esc(typ)}">
  <div class="badges"><span class="badge type-{esc(typ)}">{esc(typ)}</span>
  <span class="badge">severity: {esc(sev)}</span>
  <span class="badge">confidence: {esc(f.get('confidence'))}</span></div>
  <h3>{esc(f.get('title'))}</h3><p>{esc(f.get('description'))}</p>
  <details><summary>Steps to reproduce</summary><ol>{steps or '<li>Not provided</li>'}</ol></details>
  <details><summary>Evidence</summary><pre>{esc(ev)}</pre></details></article>"""

def log_rows(log):
    rows = []
    for e in log:
        notes = []
        if e.get("error"): notes.append("action failed")
        if e.get("dialogs"): notes.append("alert popped up")
        if e.get("horizontal_overflow"): notes.append("layout overflow")
        if e.get("new_console_errors"): notes.append("console error")
        if e.get("text_changed"): notes.append("page changed")
        rows.append(f"<tr><td>{e.get('round')}</td><td>{esc(e.get('action'))} {esc(e.get('element'))}</td>"
                    f"<td>{esc(e.get('why'))}</td><td>{esc(', '.join(notes) or 'no visible change')}</td></tr>")
    return "".join(rows)

CSS = """
:root{--bg:#f6f4ee;--fg:#172026;--mut:#5b6670;--card:#fffdf8;--line:#ddd8cc;--acc:#176b57;
--crit:#b3261e;--high:#c4560a;--med:#9a7b00;--low:#4a6a8a}
@media (prefers-color-scheme:dark){:root{--bg:#141a1d;--fg:#eef0ee;--mut:#9aa6ad;--card:#1c2428;
--line:#2f3a40;--acc:#5cc4a6;--crit:#ff8a80;--high:#ffab70;--med:#e6c84f;--low:#8fb4d8}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 system-ui,Segoe UI,Arial,sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:32px 20px 64px}
h1{font-family:Georgia,serif;font-weight:400;font-size:2.4rem;margin:0}
h2{font-family:Georgia,serif;font-weight:400;margin:40px 0 12px}
.meta{color:var(--mut)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.stat b{display:block;font-size:2rem;font-family:Georgia,serif}
.filters button{font:inherit;padding:6px 14px;border:1px solid var(--line);background:var(--card);
color:var(--fg);border-radius:999px;cursor:pointer;margin-right:8px}
.filters button[aria-pressed=true]{background:var(--acc);color:var(--bg);border-color:var(--acc)}
.card{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--low);
border-radius:12px;padding:16px 20px;margin:14px 0}
.sev-critical{border-left-color:var(--crit)}.sev-high{border-left-color:var(--high)}
.sev-medium{border-left-color:var(--med)}.card h3{margin:8px 0 4px}
.badge{display:inline-block;font-size:.8rem;border:1px solid var(--line);border-radius:999px;
padding:1px 10px;margin-right:6px;color:var(--mut)}
.type-bug{color:var(--crit);border-color:var(--crit)}.type-improvement{color:var(--acc);border-color:var(--acc)}
details{margin-top:8px}summary{cursor:pointer;color:var(--acc)}
pre{white-space:pre-wrap;word-break:break-word;background:var(--bg);padding:12px;border-radius:8px;
font-size:.85rem;overflow-x:auto}
figure{margin:16px 0}img{max-width:100%;border:1px solid var(--line);border-radius:8px}
figcaption{color:var(--mut);font-size:.9rem}
table{width:100%;border-collapse:collapse;font-size:.9rem}
td,th{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
@media print{.filters{display:none}body{background:#fff;color:#000}}
"""

def main():
    findings = json.loads((OUT / "findings.json").read_text())
    ev = json.loads((OUT / "evidence.json").read_text())
    log_p = OUT / "exploration.json"
    log = json.loads(log_p.read_text()) if log_p.exists() else []
    bugs = sum(f.get("type") == "bug" for f in findings)
    imps = len(findings) - bugs
    urgent = sum(f.get("severity") in ("critical", "high") for f in findings)
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>AI App Tester report</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>AI App Tester report</h1>
<p class="meta">{esc(ev.get('url'))} · {datetime.datetime.now():%d %b %Y, %H:%M}</p>
<div class="stats"><div class="stat"><b>{len(findings)}</b>findings</div>
<div class="stat"><b>{bugs}</b>bugs</div><div class="stat"><b>{imps}</b>improvements</div>
<div class="stat"><b>{urgent}</b>high or critical</div></div>
<div class="filters" role="group" aria-label="Filter findings">
<button data-f="all" aria-pressed="true">All</button><button data-f="bug" aria-pressed="false">Bugs</button>
<button data-f="improvement" aria-pressed="false">Improvements</button></div>
<section id="list">{''.join(card(f) for f in findings)}</section>
<h2>Screenshots</h2>{img('home.png', 'Page when first loaded')}{img('explored.png', 'Page after the AI ran its experiments')}
<h2>How this was tested</h2>
<p>A real browser first collected facts: {len(ev.get('console_errors', []))} console error(s),
{len(ev.get('broken_links', []))} broken link(s), {len(ev.get('a11y', []))} accessibility rule(s) flagged.
Then an AI planned and ran {len(log)} experiments, and a second AI pass turned the evidence into the findings above.
Every finding cites the evidence behind it.</p>
<details><summary>Experiment log ({len(log)} steps)</summary>
<table><tr><th>Round</th><th>Action</th><th>What it was probing</th><th>What happened</th></tr>{log_rows(log)}</table></details>
</div><script>
document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{{
document.querySelectorAll('.filters button').forEach(x=>x.setAttribute('aria-pressed',x===b));
document.querySelectorAll('.card').forEach(c=>c.style.display=(b.dataset.f==='all'||c.dataset.type===b.dataset.f)?'':'none');}});
</script></body></html>"""
    out = pathlib.Path("report.html")
    out.write_text(page, encoding="utf-8")
    print(f"Report saved to {out.resolve()}")
    try: webbrowser.open(out.resolve().as_uri())
    except Exception: pass

if __name__ == "__main__":
    main()
