#!/usr/bin/env python3
"""Weekly refresh: GSC API -> products.json -> recommendations -> dashboard.

Requires the OAuth token at ~/.hermes/google_token.json with the
webmasters.readonly scope (see oauth_loopback.py for the one-time setup).

Usage:
  python3 refresh.py                       # last 12 weeks
  python3 refresh.py --weeks 36
  python3 refresh.py --start 2026-01-01 --end 2026-09-24
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
SITE = "https://grc-indonesia.com/"


def run(args):
    print(f"\n=== {' '.join(os.path.basename(a) if a.endswith('.py') else a for a in args)} ===")
    r = subprocess.run([PY] + args, cwd=HERE)
    if r.returncode:
        sys.exit(f"failed: {args[0]} (exit {r.returncode})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=int, default=12)
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--site", default=SITE)
    args = ap.parse_args()

    gsc = [os.path.join(HERE, "fetch_gsc.py"), "--site", args.site, "--merge"]
    if args.start:
        gsc += ["--start", args.start]
    else:
        gsc += ["--weeks", str(args.weeks)]
    if args.end:
        gsc += ["--end", args.end]

    run(gsc)
    run([os.path.join(HERE, "recommend.py")])
    run([os.path.join(HERE, "build_dashboard.py")])
    print("\nDone. dashboard.html refreshed.")


if __name__ == "__main__":
    main()
