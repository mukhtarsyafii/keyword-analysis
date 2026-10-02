#!/usr/bin/env python3
"""Crawl each live landing page once -> data/live_audit.json.

Keyed by product id. Per page we capture what the SERP snippet actually is
today, so recommend.py can compare its proposal against reality instead of
guessing from the sheet keyword alone:
  live_title   - <title> text (entity-decoded, whitespace-collapsed)
  live_desc    - meta[name=description] content, or None
  has_faq      - FAQPage JSON-LD already present in the HTML
  h2_count     - number of <h2> tags on the page
  http_ok      - False when the fetch failed (recommend.py then falls back
                 to sheet-only logic and never claims a fix we couldn't verify)

Usage:
  python3 crawl_live.py            # crawl all Aktif products, merge into cache
  python3 crawl_live.py --id 7     # re-crawl one product
  python3 crawl_live.py --force    # ignore cache, refetch everything
"""
import argparse, html, json, os, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.path.join(DATA, "live_audit.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
# meta description: name attr may come before or after content
DESC_RE = [
    re.compile(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"'](.*?)[\"']", re.S | re.I),
    re.compile(r"<meta[^>]+content=[\"'](.*?)[\"'][^>]+name=[\"']description[\"']", re.S | re.I),
]


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "id,en;q=0.8"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")


def parse(doc):
    t = TITLE_RE.search(doc)
    live_title = None
    if t:
        live_title = re.sub(r"\s+", " ", html.unescape(t.group(1))).strip() or None
    live_desc = None
    for rx in DESC_RE:
        m = rx.search(doc)
        if m:
            live_desc = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip() or None
            if live_desc:
                break
    # FAQPage in JSON-LD or microdata: '@type' : 'FAQPage' (quote styles vary)
    has_faq = bool(re.search(r"[\"']@type[\"']\s*:\s*[\"']FAQPage", doc))
    h2_count = len(re.findall(r"<h2[\s>]", doc, re.I))
    return {"live_title": live_title, "live_desc": live_desc,
            "has_faq": has_faq, "h2_count": h2_count}


def load_cache():
    if os.path.exists(CACHE):
        with open(CACHE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE, "w") as f:
        json.dump(cache, f, indent=1, ensure_ascii=False)


def fetch_missing(products, workers=8, force=False):
    """Refresh cache entries for products that are uncached or failed.
    Returns the updated cache. recommend.py calls this so its live-page
    checks never go stale after a page flip or a failed crawl."""
    cache = load_cache()

    def stale(p):
        e = cache.get(str(p["id"]), {})
        # ids can shift when the sheet gains rows; a url mismatch means the
        # cached snapshot belongs to a different page and must be refetched
        return (force or not e.get("http_ok")
                or (e.get("url") or "").rstrip("/") != p["url"].rstrip("/"))

    targets = [p for p in products
               if p["url"] and p["status"].lower() == "aktif" and stale(p)]
    if not targets:
        return cache

    def work(p):
        sid = str(p["id"])
        try:
            doc = fetch(p["url"])
            return sid, {"url": p["url"], "http_ok": True, **parse(doc)}
        except Exception as e:
            prev = cache.get(sid, {})
            keep = {k: prev.get(k) for k in ("live_title", "live_desc", "has_faq", "h2_count")
                    if prev.get("http_ok")}
            return sid, {"url": p["url"], "http_ok": False, "error": str(e)[:120], **keep}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for sid, rec in ex.map(work, targets):
            cache[sid] = rec
    save_cache(cache)
    return cache


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, help="re-crawl a single product id")
    ap.add_argument("--force", action="store_true", help="refetch even if cached")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    products = json.load(open(os.path.join(DATA, "products.json")))
    if args.id:
        products = [p for p in products if p["id"] == args.id]
        if not products:
            sys.exit(f"no product with id {args.id}")
        if products[0]["status"].lower() != "aktif" or not products[0]["url"]:
            sys.exit(f"product {args.id} has no live URL")

    cache = fetch_missing(products, workers=args.workers, force=args.force)
    ok = sum(1 for v in cache.values() if v.get("http_ok"))
    print(f"crawled (force={args.force}) -> {ok}/{len(cache)} pages ok in live_audit.json")


if __name__ == "__main__":
    main()
