#!/usr/bin/env python3
"""Pull competitor keyword intel from Ubersuggest (official MCP server) and
write data/competitors.json for the dashboard's Kompetitor tab.

Per product (top N by GSC impressions):
  1. GSC searchAnalytics (query+page filter) -> the real queries surfacing that page.
  2. Ubersuggest serp_analysis -> who ranks organically for each query.
  3. Our position taken from the same SERP payload (ground truth, not an estimate).
A query where a competitor sits above us = GAP.

Auth: reuses Hermes' stored OAuth token (~/.hermes/mcp-tokens/ubersuggest.json)
via uber_client.py. Raw responses cached in data/uber_cache.json so reruns don't
burn Ubersuggest's daily report quota.

Usage:
  python3 fetch_competitors.py                    # top 12 products, 5 queries each
  python3 fetch_competitors.py --products 20 --kw 8 --no-cache
"""
import argparse, datetime, json, os, subprocess, sys, urllib.parse, urllib.request

from fetch_gsc import access_token, api

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PY = sys.executable
CLIENT = os.path.join(HERE, "uber_client.py")
CACHE = os.path.join(DATA, "uber_cache.json")
GSC_TOKEN = os.path.expanduser("~/.hermes/google_token.json")
PROPERTY = "https://grc-indonesia.com/"   # default for gsc_queries(); per-brand value comes from brands_config.json
LANG, LOC = "id", 2360          # Indonesian / Indonesia (locId from location_suggest)


def uber(tool, args, cache=None):
    key = tool + "|" + json.dumps(args, sort_keys=True)
    if cache is not None and key in cache:
        return cache[key]
    r = subprocess.run([PY, CLIENT, tool, json.dumps(args)],
                       capture_output=True, text=True, timeout=300)
    if r.returncode:
        sys.stderr.write(f"  ! {tool} {args.get('keyword') or args.get('domain','')}: "
                         f"{(r.stderr or r.stdout).strip()[:140]}\n")
        return None
    try:
        val = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    if cache is not None:
        cache[key] = val
    return val


def gsc_queries(page_url, token, prop=PROPERTY, n=10):
    """Top queries driving impressions for one page, last 90 days."""
    end = datetime.date.today() - datetime.timedelta(days=3)
    start = end - datetime.timedelta(days=87)
    body = {"startDate": start.isoformat(), "endDate": end.isoformat(),
            "dimensions": ["query"], "rowLimit": 250,
            "dimensionFilterGroups": [{"filters": [{
                "dimension": "page", "operator": "equals",
                "expression": page_url}]}]}
    site_q = urllib.parse.quote(prop, safe="")
    # fetch_gsc.api retries transient RemoteDisconnected/timeouts; a bare
    # urlopen here killed the whole run on one flaky response.
    rows = api(f"webmasters/v3/sites/{site_q}/searchAnalytics/query",
               token, "POST", body).get("rows", [])
    rows.sort(key=lambda x: -x.get("impressions", 0))
    return [{"keyword": x["keys"][0], "impr": x.get("impressions", 0),
             "clicks": x.get("clicks", 0), "pos": round(x.get("position", 0), 1)}
            for x in rows[:n]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--products", type=int, default=12, help="top N products by impressions")
    ap.add_argument("--kw", type=int, default=5, help="queries per product")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--brand", help="only this brand (default: every brand in the catalog)")
    args = ap.parse_args()

    token = access_token()   # handles OAuth refresh (fetch_gsc.py)
    products = json.load(open(os.path.join(DATA, "products.json")))
    cache = {} if args.no_cache or not os.path.exists(CACHE) else json.load(open(CACHE))

    # Domain + GSC property per brand come from data/brands_config.json.
    cfg = json.load(open(os.path.join(DATA, "brands_config.json")))
    by_brand = {b["brand"]: b for b in cfg}
    if args.brand:
        by_brand = {k: v for k, v in by_brand.items() if k == args.brand}

    out, total_gaps = {}, 0
    # A brand-scoped run must not erase other brands' intel already on disk.
    path = os.path.join(DATA, "competitors.json")
    if os.path.exists(path):
        try:
            out.update(json.load(open(path)))
        except (json.JSONDecodeError, OSError):
            pass
    for brand, b in by_brand.items():
        site, prop = b["domain"], b["property"]
        targets = [p for p in sorted((p for p in products if p.get("brand") == brand),
                                     key=lambda p: -p["total_impr"])
                   if p["url"] and p["total_impr"]][: args.products]
        for p in targets:
            rows = []
            try:
                queries = gsc_queries(p["url"], token, prop=prop, n=args.kw * 3)
            except Exception as e:
                # One flaky page must not lose the whole run's intel.
                print(f"  [{brand}] {p['name'][:40]:40} SKIP: {type(e).__name__}: {e}")
                continue
            for s in queries:
                kw = s["keyword"]
                if len(kw) < 4 or kw.strip() in ("-", ""):
                    continue
                serp = uber("serp_analysis", {"keyword": kw, "language": LANG,
                                              "locId": LOC, "limit": 10}, cache)
                if not serp:
                    continue
                organic = [e for e in (serp.get("serpEntries") or [])
                           if e.get("type") == "organic"]
                top = next((e for e in organic if site not in (e.get("domain") or "")), None)
                ours = next((e for e in organic if site in (e.get("domain") or "")), None)
                we_rank = ours["position"] if ours else (s["pos"] or None)
                ov = uber("keyword_overview", {"keyword": kw, "language": LANG,
                                               "locId": LOC}, cache) or {}
                rows.append({
                    "keyword": kw,
                    "volume": ov.get("search_volume") or None,
                    "difficulty": ov.get("seo_difficulty"),
                    "top_competitor": (top or {}).get("domain") or "-",
                    "top_position": (top or {}).get("position"),
                    "we_rank": round(we_rank) if isinstance(we_rank, (int, float)) else None,
                })
                if len(rows) >= args.kw:
                    break
            gaps = sum(1 for r in rows if r["top_competitor"] != "-"
                       and (r["we_rank"] or 99) > (r["top_position"] or 0))
            total_gaps += gaps
            out[str(p["id"])] = {
                "product_name": p["name"],
                "brand": brand,
                "source": f"GSC queries + Ubersuggest SERP (id/Indonesia)",
                "competitor_keywords": rows,
            }
            print(f"  [{brand}] {p['name'][:40]:40} {len(rows)} kw, {gaps} kalah posisi")

    with open(os.path.join(DATA, "competitors.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(CACHE, "w") as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"wrote data/competitors.json: {len(out)} products, {total_gaps} keyword gaps")


if __name__ == "__main__":
    main()
