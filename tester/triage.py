"""Step 3: Gemini turns all the evidence into a short list of actionable findings.
Usage: python triage.py"""
import json, pathlib
from llm import ask_json

OUT = pathlib.Path("evidence")
ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

PROMPT = """You are a senior QA engineer writing up findings for the developers of a small web app.
Below are facts collected automatically from the running app, plus a log of experiments run on it.
Two screenshots are attached: the page at load, and the page after the experiments.

STATIC EVIDENCE (console errors, failed requests, broken links, accessibility audit, elements):
<<EVIDENCE>>

EXPERIMENT LOG (what was done, and what changed on the page):
<<EXPLORATION>>

Rules:
- Every finding MUST cite specific evidence (an exact error, status code, accessibility rule, or
  experiment step). If you cannot cite any, leave it out.
- type: "bug" = broken or wrong; "improvement" = works but could be better.
- Merge duplicates and closely related items into one finding.
- confidence: "high" = directly shown by the evidence, "medium" = inferred, "low" = speculative.
- severity: critical, high, medium or low. Write descriptions in plain English.
- General signals to look for: a control that produces no visible change when used; invalid or empty
  input accepted and a success message shown; a dialog appearing after HTML was entered (script
  injection); layout overflow on long input; inputs with no accessible label; missing empty states
  or user feedback.
Reply ONLY with JSON:
{"findings":[{"title":"","type":"bug or improvement","severity":"","confidence":"",
"description":"","steps_to_reproduce":[""],"evidence":""}]}"""

def main():
    evidence = (OUT / "evidence.json").read_text()
    exploration = (OUT / "exploration.json").read_text()
    prompt = PROMPT.replace("<<EVIDENCE>>", evidence).replace("<<EXPLORATION>>", exploration)
    print("Asking Gemini to triage...")
    result = ask_json(prompt, images=[OUT / "home.png", OUT / "explored.png"])
    findings = sorted(result["findings"], key=lambda f: ORDER.get(f.get("severity"), 9))
    (OUT / "findings.json").write_text(json.dumps(findings, indent=2))
    for f in findings:
        print(f"[{f['severity']:8}] [{f['type']:11}] {f['title']}  ({f['confidence']})")
    print(f"\n{len(findings)} findings saved to evidence/findings.json")

if __name__ == "__main__":
    main()
