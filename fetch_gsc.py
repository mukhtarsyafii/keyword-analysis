#!/usr/bin/env python3
"""Fetch GSC data via API and refresh data/products.json weekly series.

Requires OAuth token with scope https://www.googleapis.com/auth/webmasters.readonly
at ~/.hermes/google_token.json (see oauth_gsc_only.py for the one-time setup).

Usage:
  python3 fetch_gsc.py --check                 # verify token + list properties
  python3 fetch_gsc.py --weeks 36              # every brand in data/brands_config.json
  python3 fetch_gsc.py --site sc-domain:ipqi.org --weeks 36
  python3 fetch_gsc.py --merge                 # merge into existing products.json

Writes data/gsc_raw.json (per page per week) and optionally merges into
products.json so build_dashboard.py picks it up.
"""
import argparse, json, os, re, sys, datetime, time, urllib.request, urllib.error, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TOKEN = os.path.expanduser("~/.hermes/google_token.json")
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"


def brands():
    """Brands to fetch: data/brands_config.json owns the property per brand."""
    p = os.path.join(DATA, "brands_config.json")
    if not os.path.exists(p):
        return []
    return json.load(open(p))


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


def api(path, token, method="GET", payload=None, attempts=3):
    """GSC occasionally stalls mid-read; retry transient network errors."""
    url = "https://searchconsole.googleapis.com/" + path.lstrip("/")
    data = json.dumps(payload).encode() if payload else None
    for i in range(attempts):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except (TimeoutError, urllib.error.URLError, ConnectionError) as e:
            if i == attempts - 1:
                raise
            print(f"  retry {i+1}/{attempts-1} after {type(e).__name__}: {e}")
            time.sleep(5 * (i + 1))
    raise RuntimeError("unreachable")  # loop always returns or raises


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--site", help="one GSC property (default: all in data/brands_config.json)")
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

    props = [args.site] if args.site else [b["property"] for b in brands()]
    if not props:
        sys.exit("no property: pass --site or fill data/brands_config.json")

    end = datetime.date.fromisoformat(args.end) if args.end else datetime.date.today()
    if args.start:
        start = datetime.date.fromisoformat(args.start)
    else:
        start = end - datetime.timedelta(weeks=args.weeks)

    out, per_day = {}, {}
    for site in props:
        # GSC caps a query at 25k rows. 36 weeks x ~600 pages x 7 days blows past
        # that, so fetch one week at a time (max ~4k rows/week, safely under).
        rows = []
        cur = start
        try:
            while cur <= end:
                w_end = min(cur + datetime.timedelta(days=6), end)
                body = {
                    "startDate": cur.isoformat(),
                    "endDate": w_end.isoformat(),
                    "dimensions": ["page", "date"],
                    "rowLimit": 25000,
                }
                site_q = urllib.parse.quote(site, safe="")
                res = api(f"webmasters/v3/sites/{site_q}/searchAnalytics/query",
                          token, "POST", body)
                got = res.get("rows", [])
                rows.extend(got)
                print(f"  {site} {cur} .. {w_end}: {len(got)} rows")
                cur = w_end + datetime.timedelta(days=1)
        except urllib.error.HTTPError as e:
            # one property being forbidden (query permission) must not kill the
            # whole refresh; that brand simply ships without GSC series this run.
            print(f"WARN: {site} HTTP {e.code}; skip (brand tanpa data GSC run ini)")
            continue

        print(f"fetched {len(rows)} page/date rows for {site} {start} .. {end}")

        # aggregate per page per ISO week, and keep the daily rows too so the
        # dashboard can bucket by day / week / month without a re-fetch.
        per_page = {}
        for r in rows:
            page = r["keys"][0]
            d = datetime.date.fromisoformat(r["keys"][1])
            iso = d.isocalendar()
            # Year-qualified key: plain "W<n>" wraps at the ISO year boundary and
            # sorts wrong once the series spans two years. "2025W01" sorts as a string.
            wk = f"{iso[0]}W{iso[1]:02d}"
            e = per_page.setdefault(page, {}).setdefault(wk, {"impr": 0, "clicks": 0, "pos": []})
            e["impr"] += r.get("impressions", 0)
            e["clicks"] += r.get("clicks", 0)
            if r.get("position"):
                e["pos"].append(r["position"])
            per_day.setdefault(page, {})[d.isoformat()] = {
                "impr": int(r.get("impressions", 0)),
                "clicks": int(r.get("clicks", 0)),
                "rank": round(r["position"], 1) if r.get("position") else None,
            }

        for page, weeks in per_page.items():
            out[page] = []
            for wk in sorted(weeks):
                v = weeks[wk]
                out[page].append({
                    "w": wk,
                    "impr": int(v["impr"]),
                    "clicks": int(v["clicks"]),
                    "ctr": round(v["clicks"] / v["impr"] * 100, 2) if v["impr"] else 0.0,
                    "rank": round(sum(v["pos"]) / len(v["pos"]), 1) if v["pos"] else None,
                })
        # daily series written separately (data/gsc_daily.json) -> bucketed
        # client-side into day / week / month in the dashboard.

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "gsc_raw.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"wrote data/gsc_raw.json ({len(out)} pages)")
    with open(os.path.join(DATA, "gsc_daily.json"), "w") as f:
        json.dump(per_day, f, indent=1, ensure_ascii=False)
    print(f"wrote data/gsc_daily.json ({len(per_day)} pages, daily rows)")

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
            daily = [{"d": k, **v} for k, v in sorted(per_day.get(page, {}).items())]
            for p in grp:
                # Merge by week key so a short refresh keeps older weeks.
                # A week re-fetched later is replaced (GSC revises recent data).
                by_wk = {s["w"]: s for s in p.get("weeks", [])
                         if re.match(r"^\d{4}W\d{2}$", s.get("w", ""))}
                by_wk.update({s["w"]: s for s in series})
                p["weeks"] = sorted(by_wk.values(), key=lambda s: s["w"])
                if daily:
                    by_d = {s["d"]: s for s in p.get("daily", [])}
                    by_d.update({s["d"]: s for s in daily})
                    p["daily"] = [by_d[k] for k in sorted(by_d)]
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
