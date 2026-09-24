#!/usr/bin/env python3
"""Fetch GSC data via API and refresh data/products.json weekly series.

Requires OAuth token with scope https://www.googleapis.com/auth/webmasters.readonly
at ~/.hermes/google_token.json (see google-workspace skill setup).

Usage:
  python3 fetch_gsc.py --check                 # verify token + list properties
  python3 fetch_gsc.py --site sc-domain:grc-indonesia.com --weeks 36
  python3 fetch_gsc.py --site ... --merge     # merge into existing products.json

Writes data/gsc_raw.json (per page per week) and optionally merges into
products.json so build_dashboard.py picks it up.
"""
import argparse, json, os, sys, datetime, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TOKEN = os.path.expanduser("~/.hermes/google_token.json")
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"


def access_token():
    if not os.path.exists(TOKEN):
        sys.exit(f"No token at {TOKEN}. Run the google-workspace setup first.")
    with open(TOKEN) as f:
        tok = json.load(f)
    granted = tok.get("scopes") or tok.get("scope") or []
    if isinstance(granted, str):
        granted = granted.split()
    if SCOPE not in granted:
        sys.exit("Token lacks webmasters.readonly scope.\n"
                 "Re-run google-workspace setup with that scope added to SCOPES.")
    # refresh if needed
    exp = tok.get("expiry")
    if exp:
        try:
            e = datetime.datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if e.tzinfo is None:
                e = e.replace(tzinfo=datetime.timezone.utc)
            if e <= datetime.datetime.now(datetime.timezone.utc):
                tok = _refresh(tok)
        except ValueError:
            pass
    return tok["token"]


def _refresh(tok):
    body = urllib.parse.urlencode({
        "client_id": tok["client_id"],
        "client_secret": tok["client_secret"],
        "refresh_token": tok["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body)
    with urllib.request.urlopen(req, timeout=30) as r:
        new = json.loads(r.read().decode())
    tok["token"] = new["access_token"]
    tok["expiry"] = (datetime.datetime.now(datetime.timezone.utc)
                     + datetime.timedelta(seconds=new.get("expires_in", 3600))).isoformat()
    with open(TOKEN, "w") as f:
        json.dump(tok, f)
    return tok


def api(path, token, method="GET", payload=None):
    url = "https://searchconsole.googleapis.com/" + path.lstrip("/")
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--site")
    ap.add_argument("--weeks", type=int, default=36)
    ap.add_argument("--start", help="YYYY-MM-DD (overrides --weeks)")
    ap.add_argument("--end", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()

    token = access_token()

    if args.check:
        sites = api("webmasters/v3/sites", token)
        print("properties:")
        for s in sites.get("siteEntry", []):
            print("  ", s["siteUrl"], s["permissionLevel"])
        return

    if not args.site:
        sys.exit("--site required (e.g. sc-domain:grc-indonesia.com)")

    end = datetime.date.fromisoformat(args.end) if args.end else datetime.date.today()
    if args.start:
        start = datetime.date.fromisoformat(args.start)
    else:
        start = end - datetime.timedelta(weeks=args.weeks)

    site_q = urllib.parse.quote(args.site, safe="")

    # GSC caps a query at 25k rows. 36 weeks x ~600 pages x 7 days blows past that,
    # so fetch one week at a time (max ~4k rows/week, safely under the cap).
    rows = []
    cur = start
    while cur <= end:
        w_end = min(cur + datetime.timedelta(days=6), end)
        body = {
            "startDate": cur.isoformat(),
            "endDate": w_end.isoformat(),
            "dimensions": ["page", "date"],
            "rowLimit": 25000,
        }
        res = api(f"webmasters/v3/sites/{site_q}/searchAnalytics/query",
                  token, "POST", body)
        got = res.get("rows", [])
        rows.extend(got)
        print(f"  {cur} .. {w_end}: {len(got)} rows")
        cur = w_end + datetime.timedelta(days=1)

    print(f"fetched {len(rows)} page/date rows {start} .. {end}")

    # aggregate per page per ISO week
    per_page = {}
    for r in rows:
        page = r["keys"][0]
        d = datetime.date.fromisoformat(r["keys"][1])
        wk = f"W{d.isocalendar()[1]}"
        e = per_page.setdefault(page, {}).setdefault(wk, {"impr": 0, "clicks": 0, "pos": []})
        e["impr"] += r.get("impressions", 0)
        e["clicks"] += r.get("clicks", 0)
        if r.get("position"):
            e["pos"].append(r["position"])

    out = {}
    for page, weeks in per_page.items():
        out[page] = []
        for wk in sorted(weeks, key=lambda w: int(w[1:])):
            v = weeks[wk]
            out[page].append({
                "w": wk,
                "impr": int(v["impr"]),
                "clicks": int(v["clicks"]),
                "ctr": round(v["clicks"] / v["impr"] * 100, 2) if v["impr"] else 0.0,
                "rank": round(sum(v["pos"]) / len(v["pos"]), 1) if v["pos"] else None,
            })

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "gsc_raw.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"wrote data/gsc_raw.json ({len(out)} pages)")

    if args.merge:
        ppath = os.path.join(DATA, "products.json")
        products = json.load(open(ppath))
        # A URL can be shared by several catalog rows (draft vs live duplicates).
        # Group first so each shared row gets the same page data instead of
        # only the last one winning.
        groups = {}
        for p in products:
            if p["url"]:
                groups.setdefault(p["url"].rstrip("/"), []).append(p)
        merged = 0
        shared = 0
        for page, series in out.items():
            grp = groups.get(page.rstrip("/"))
            if not grp:
                continue
            if len(grp) > 1:
                shared += 1
            for p in grp:
                # Merge by week key so a short refresh keeps older weeks.
                # A week re-fetched later is replaced (GSC revises recent data).
                by_wk = {s["w"]: s for s in p.get("weeks", [])}
                by_wk.update({s["w"]: s for s in series})
                p["weeks"] = sorted(by_wk.values(), key=lambda s: int(s["w"][1:]))
                live = [s for s in p["weeks"] if s["impr"] or s["clicks"]]
                p["total_impr"] = sum(s["impr"] for s in live)
                p["total_clicks"] = sum(s["clicks"] for s in live)
                p["ctr"] = round(p["total_clicks"] / p["total_impr"] * 100, 2) if p["total_impr"] else 0.0
                ranks = [s["rank"] for s in live if s["rank"]]
                p["avg_rank"] = round(sum(ranks) / len(ranks), 1) if ranks else 0
                p["latest_rank"] = live[-1]["rank"] if live and live[-1]["rank"] else 0
                merged += 1
        with open(ppath, "w") as f:
            json.dump(products, f, indent=1, ensure_ascii=False)
        print(f"merged GSC data into {merged} products "
              f"({len(groups)} unique URLs, {shared} shared by duplicate rows)")


if __name__ == "__main__":
    main()
