#!/usr/bin/env python3
"""Push meta title/description to WordPress via REST API.

Credentials: data/wp_config.json (gitignored)
{
  "base_url": "https://grc-indonesia.com",
  "user": "USERNAME",
  "app_password": "xxxx xxxx xxxx xxxx"
}
App password: WP admin → Users → Profile → Application Passwords.

Usage:
  python3 push_wp.py --list              # find post/page id per LP URL
  python3 push_wp.py --id 20 --dry-run   # preview payload
  python3 push_wp.py --id 20             # apply (asks confirm)
  python3 push_wp.py --top 5             # apply for priority-5 products one by one

Only writes Yoast meta (if plugin active) + WP title/excerpt fallback.
Never touches body content.
"""
import argparse, json, os, sys, urllib.request, urllib.parse, base64

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "data", "wp_config.json")


def load_cfg():
    if not os.path.exists(CFG):
        sys.exit(f"Missing {CFG}\nCreate it with base_url, user, app_password.")
    with open(CFG) as f:
        return json.load(f)


def wp_request(cfg, path, method="GET", payload=None):
    url = cfg["base_url"].rstrip("/") + "/wp-json/wp/v2/" + path.lstrip("/")
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    tok = base64.b64encode(f"{cfg['user']}:{cfg['app_password'].replace(' ','')}".encode()).decode()
    req.add_header("Authorization", "Basic " + tok)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def find_post(cfg, url):
    """Resolve WP post id from a landing page URL."""
    slug = url.rstrip("/").split("/")[-1]
    for typ in ("pages", "posts"):
        try:
            hits = wp_request(cfg, f"{typ}?slug={urllib.parse.quote(slug)}")
            if hits:
                return typ, hits[0]
        except Exception:
            continue
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", type=int, help="product id from data/products.json")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--top", type=int, default=0)
    args = ap.parse_args()

    cfg = load_cfg()
    products = json.load(open(os.path.join(HERE, "data", "products.json")))
    recs = json.load(open(os.path.join(HERE, "data", "recommendations.json")))

    targets = [p for p in products if str(p["id"]) in recs]
    if args.top:
        targets = sorted(targets, key=lambda p: -recs[str(p["id"])]["prioritas"])[: args.top]
    elif args.id:
        targets = [p for p in products if p["id"] == args.id]
    if not targets:
        sys.exit("No target. Use --id N or --top N.")

    for p in targets:
        fix = recs[str(p["id"])]["perbaikan"]
        if not p["url"]:
            print(f"[skip] #{p['id']} {p['name']} — no URL")
            continue
        typ, post = find_post(cfg, p["url"])
        if not post:
            print(f"[skip] #{p['id']} {p['name']} — WP post not found for {p['url']}")
            continue
        payload = {
            "title": fix["meta_title"],
            "meta": {"_yoast_wpseo_title": fix["meta_title"],
                     "_yoast_wpseo_metadesc": fix["meta_description"]},
        }
        print(f"\n#{p['id']} {p['name']}\n  {typ}/{post['id']}  {p['url']}")
        print(f"  title: {fix['meta_title']}")
        print(f"  desc : {fix['meta_description'][:80]}...")
        if args.dry_run:
            print("  [dry-run] nothing sent")
            continue
        ok = input("  Apply? [y/N] ").strip().lower() == "y"
        if not ok:
            print("  skipped")
            continue
        res = wp_request(cfg, f"{typ}/{post['id']}", "POST", payload)
        print(f"  -> updated {res.get('link','?')}")


if __name__ == "__main__":
    main()
