# AI App Tester

## Run
    pip install playwright && playwright install chromium
    cd demo-app && python -m http.server 8000      # terminal 1
    cd tester && python collect.py http://localhost:8000   # terminal 2

## Planted bugs in demo-app (your answer key)
1. Console error on load (undefined trackPageView)
2. /pricing link is a 404
3. Signup accepts empty/invalid email
4. Email input has no label (a11y)
5. Logo image has no alt text (a11y)
6. "Clear completed" does nothing
7. Task text injected via innerHTML (XSS) + empty tasks allowed
8. Long task text overflows the layout
Improvements: low-contrast tagline, no empty state, no feedback on add.
