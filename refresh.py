#!/usr/bin/env python3
"""Refresh: Google Sheet tracker -> GSC API -> recommendations -> dashboard.

Requires the OAuth token at ~/.hermes/google_token.json with the
webmasters.readonly scope (see oauth_gsc_only.py for the one-time setup).
Every brand listed in data/brands_config.json is fetched.

Usage:
  python3 refresh.py                       # last 12 weeks, all brands
  python3 refresh.py --weeks 36
  python3 refresh.py --start 2026-01-01 --end 2026-09-24
  python3 refresh.py --skip-sheet          # GSC only, keep the current catalog
  python3 refresh.py --brand IPQI          # one brand for competitors
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


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
    ap.add_argument("--brand", help="limit competitor intel to one brand")
    ap.add_argument("--skip-sheet", action="store_true",
                    help="don't re-read the Google Sheet tracker")
    ap.add_argument("--skip-competitors", action="store_true",
                    help="don't refresh Ubersuggest competitor intel")
    args = ap.parse_args()

    # Sheet first: it owns the catalog (new LPs, keywords, status). It preserves
    # the GSC weeks/daily already in products.json, so nothing is lost.
    if not args.skip_sheet:
        run([os.path.join(HERE, "extract_sheet.py")])

    gsc = [os.path.join(HERE, "fetch_gsc.py"), "--merge"]
    if args.start:
        gsc += ["--start", args.start]
    else:
        gsc += ["--weeks", str(args.weeks)]
    if args.end:
        gsc += ["--end", args.end]

    run(gsc)
    # Klik WA per LP: non-fatal, dashboard tetap jalan tanpa kolom ini.
    r = subprocess.run([PY, os.path.join(HERE, "fetch_wa.py")], cwd=HERE)
    if r.returncode:
        print("WARN: fetch_wa gagal; pakai data/wa.json terakhir")
    # Leads & SO per LP (Need Tracking + Odoo): non-fatal juga.
    r = subprocess.run([PY, os.path.join(HERE, "fetch_leads.py")], cwd=HERE)
    if r.returncode:
        print("WARN: fetch_leads gagal; pakai data/leads.json terakhir")
    if not args.skip_competitors:
        # Non-fatal: Ubersuggest has a daily report quota and its OAuth token
        # can expire; the dashboard still builds with the last cached intel.
        cmd = [os.path.join(HERE, "fetch_competitors.py")]
        if args.brand:
            cmd += ["--brand", args.brand]
        r = subprocess.run([PY] + cmd, cwd=HERE)
        if r.returncode:
            print("WARN: fetch_competitors failed; keeping previous competitors.json")
    run([os.path.join(HERE, "recommend.py")])
    run([os.path.join(HERE, "build_dashboard.py")])
    print("\nDone. dashboard.html refreshed.")


if __name__ == "__main__":
    main()
