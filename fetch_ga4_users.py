#!/usr/bin/env python3
"""Fetch GA4 users per page + channel breakdown -> data/ga4_users.json.

One runReport per brand property (paginated), dims pagePath x sessionDefaultChannelGroup,
metric totalUsers, cumulative since 2026-01-01. Key = domain+path normalized (same as
pageKeyOf in wcc lp-data.ts). Brands without ga4_property_id are skipped.

Usage: python3 fetch_ga4_users.py [--since 2026-01-01]
"""
import argparse, json, os, datetime, urllib.request, urllib.error, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TOKEN = os.path.expanduser("~/.hermes/google_token.json")
API = "https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"


def access_token():
    t = json.load(open(TOKEN))
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({
            "client_id": t["client_id"], "client_secret": t["client_secret"],
            "refresh_token": t["refresh_token"], "grant_type": "refresh_token",
        }).encode(), method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["access_token"]


def run_report(tok, prop, since, until, offset):
    body = {
        "dateRanges": [{"startDate": since, "endDate": until}],
        "dimensions": [{"name": "pagePath"}, {"name": "sessionDefaultChannelGroup"}],
        "metrics": [{"name": "totalUsers"}],
        "limit": "2500",
    }
    if offset:
        body["offset"] = str(offset)
    req = urllib.request.Request(API.format(prop=prop),
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
        method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-01-01")
    args = ap.parse_args()
    until = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()  # GA4 delay ~24h
    cfg = json.load(open(os.path.join(DATA, "brands_config.json")))
    tok = access_token()

    pages = {}
    for b in cfg:
        prop, dom = b.get("ga4_property_id"), (b.get("domain") or "").lower()
        if not prop or not dom:
            print(f"{b['brand']}: skip (no ga4_property_id)"); continue
        agg, offset, rows_total = {}, 0, 0
        while True:
            try:
                res = run_report(tok, prop, args.since, until, offset)
            except (urllib.error.HTTPError, urllib.error.URLError) as e:
                print(f"{b['brand']}: ERR {e}"); break
            rows = res.get("rows", [])
            rows_total += len(rows)
            for r in rows:
                path = r["dimensionValues"][0]["value"]
                ch = r["dimensionValues"][1]["value"]
                users = int(r["metricValues"][0]["value"])
                key = f"{dom}{path}".lower().split("?")[0].rstrip("/") if path != "/" else dom
                d = agg.setdefault(key, {})
                d[ch] = d.get(ch, 0) + users
            if len(rows) < 2500:
                break
            offset += 2500
        pages.update(agg)
        print(f"{b['brand']}: {rows_total} rows -> {len(agg)} pages")

    out = {"updated": datetime.date.today().isoformat(), "since": args.since, "until": until,
           "pages": pages}
    with open(os.path.join(DATA, "ga4_users.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"ga4_users.json: {len(pages)} pages")


if __name__ == "__main__":
    main()
