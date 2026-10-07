"""One command for the live demo: collect -> explore -> triage -> report.
Usage: python run_all.py http://localhost:8000"""
import sys
from collect import collect
from explore import run
import triage, report

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
print("STEP 1/4  Collecting facts..."); collect(url)
print("\nSTEP 2/4  AI exploring the app..."); run(url)
print("\nSTEP 3/4  AI triaging findings..."); triage.main()
print("\nSTEP 4/4  Building report..."); report.main()
