#!/usr/bin/env python3
"""Ambil klik WhatsApp per landing page dari sheet WA log, tulis data/wa.json.

Sumber (kolom sama: timestamp,event,code,channel,...,page,...):
  GRC Indonesia -> sheet 1bPPlmIp_PqfAvGm8B1P3sjXuOQRWGES_aR4DPx5iIqE (gid 0)
  IPQI          -> sheet 1IfLSGTtqaxB-lbfYGlaNbold9mP0NkNf8Xvq9EJ_Vow (gid 0)

Join ke products.json lewat kolom `url` (dinormalisasi: tanpa scheme/www/trailing
slash/query). Hanya event wa_click yang dihitung.

Usage:
  python3 fetch_wa.py            # tulis data/wa.json
  python3 fetch_wa.py --check    # cetak agregat, tidak menulis
"""
import argparse, csv, datetime, io, json, os, re, subprocess, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

SOURCES = [
    ("GRC Indonesia", "1bPPlmIp_PqfAvGm8B1P3sjXuOQRWGES_aR4DPx5iIqE"),
    ("IPQI",          "1IfLSGTtqaxB-lbfYGlaNbold9mP0NkNf8Xvq9EJ_Vow"),
]

# GRC pakai "9/7/2026 15:54:59", IPQI pakai "2026-10-01 16:19:41".
FMTS = ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M", "%m/%d/%Y")


def norm_url(u):
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("?")[0].split("#")[0]
    return u.rstrip("/")


def host_of(key):
    return key.split("/")[0] if key else ""


def parse_ts(s):
    s = (s or "").strip()
    if not s:
        return None
    for f in FMTS:
        try:
            return datetime.datetime.strptime(s, f)
        except ValueError:
            continue
    return None


def fetch(sid):
    url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid=0"
    r = subprocess.run(["curl", "-sL", "--max-time", "90", url],
                       capture_output=True, text=True, timeout=120)
    txt = r.stdout or ""
    if not txt.strip() or txt.lstrip().startswith("<"):
        sys.exit(f"Sheet {sid} tidak terbaca (permission berubah / export diblokir)")
    return list(csv.DictReader(io.StringIO(txt)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="jangan menulis")
    args = ap.parse_args()

    pages = defaultdict(lambda: {"total": 0, "organic": 0, "ads": 0, "weeks": {},
                                 "dates": [], "from": {}})
    bad_ts = 0
    total_rows = 0
    per_brand = {}

    for brand, sid in SOURCES:
        rows = fetch(sid)
        n = 0
        for row in rows:
            if (row.get("event") or "").strip() != "wa_click":
                continue
            key = norm_url(row.get("page"))
            if not key:
                continue
            ts = parse_ts(row.get("timestamp"))
            if ts is None:
                bad_ts += 1
            ch = (row.get("channel") or "").strip().upper()
            e = pages[key]
            e["total"] += 1
            # Asal klik WA: halaman sebelum LP ini (referrer). Klik WA di
            # halaman hub (pelatihan-terkini) datang dari LP mana -> atribusi
            # tidak langsung ke LP tujuan. Referrer eksternal (google dll)
            # masuk bucket '(eksternal)', kosong = '(langsung)'.
            ref_raw = (row.get("referrer") or "").strip()
            ref = norm_url(ref_raw)
            if not ref_raw:
                e["from"]["(langsung)"] = e["from"].get("(langsung)", 0) + 1
            elif ref == key:
                pass  # self-referrer, tidak informatif
            elif host_of(ref) == host_of(key):
                e["from"][ref] = e["from"].get(ref, 0) + 1
            else:
                ext = host_of(ref) or "(eksternal)"
                e["from"]["(eksternal) " + ext] = e["from"].get("(eksternal) " + ext, 0) + 1
            if ch == "A":
                e["ads"] += 1
            elif ch == "O":
                e["organic"] += 1
            if ts:
                wk = f"{ts.isocalendar()[0]}W{ts.isocalendar()[1]:02d}"
                e["weeks"][wk] = e["weeks"].get(wk, 0) + 1
                e["dates"].append(ts.strftime("%Y-%m-%d"))
            n += 1
        per_brand[brand] = n
        total_rows += n

    out = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "pages": {k: {"total": v["total"], "organic": v["organic"], "ads": v["ads"],
                      "weeks": v["weeks"], "from": v["from"],
                      "first": min(v["dates"]) if v["dates"] else None,
                      "last": max(v["dates"]) if v["dates"] else None}
                  for k, v in sorted(pages.items())},
        "per_brand": per_brand,
        "total_clicks": total_rows,
    }

    # Laporan join: berapa LP dashboard yang ketemu klik WA.
    prod_path = os.path.join(DATA, "products.json")
    if os.path.exists(prod_path):
        prods = json.load(open(prod_path))
        hit = sum(1 for p in prods if norm_url(p.get("url")) in out["pages"])
        out["lp_matched"] = hit
        out["lp_total"] = len(prods)

    print(f"klik WA: {total_rows} | halaman unik: {len(out['pages'])} | "
          f"per brand: {per_brand}" + (f" | timestamp tak terbaca: {bad_ts}" if bad_ts else ""))
    if "lp_matched" in out:
        print(f"join ke dashboard: {out['lp_matched']}/{out['lp_total']} LP punya klik WA")
    top = sorted(out["pages"].items(), key=lambda kv: -kv[1]["total"])[:8]
    for u, v in top:
        print(f"  {v['total']:>4}  {u[:78]}")

    if args.check:
        return
    with open(os.path.join(DATA, "wa.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"wrote data/wa.json ({len(out['pages'])} halaman)")


if __name__ == "__main__":
    main()
