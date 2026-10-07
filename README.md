# AI App Tester

## Terminal 1
    cd demo-app
    python -m http.server 8000

## Terminal 2
    cd tester
    python collect.py http://localhost:8000
    python explore.py http://localhost:8000
    python triage.py
    python report.py

## Gemini API
    $env:GEMINI_API_KEY="your-key"

## Demo Run
    cd tester
    python run_all.py http://localhost:8000

## Planted bugs in demo-app
1. Console error on load (undefined trackPageView)
2. /pricing link is a 404
3. Signup accepts empty/invalid email
4. Email input has no label (a11y)
5. Logo image has no alt text (a11y)
6. "Clear completed" does nothing
7. Task text injected via innerHTML (XSS) + empty tasks allowed
8. Long task text overflows the layout