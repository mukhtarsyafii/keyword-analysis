#!/usr/bin/env python3
"""One-shot refresh: sheet -> products -> recommendations -> dashboard."""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["extract_sheet.py", "recommend.py", "build_dashboard.py"]

for s in STEPS:
    print(f"\n=== {s} ===")
    r = subprocess.run([sys.executable, os.path.join(HERE, s)], cwd=HERE)
    if r.returncode:
        sys.exit(f"{s} failed with {r.returncode}")
print("\nDone. Open dashboard.html")
