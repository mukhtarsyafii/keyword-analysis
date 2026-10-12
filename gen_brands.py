#!/usr/bin/env python3
"""Regenerasi data/brands.json dari brands_config.json + products.json.

brands.json adalah daftar brand utk pill dashboard; dulu ditulis manual dan
pernah basi (nama lama ISO Center/IMII masih live). Jalankan tiap tambah brand.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "data", "brands_config.json")))
prods = json.load(open(os.path.join(HERE, "data", "products.json")))

by_brand = {}
for p in prods:
    by_brand.setdefault(p["brand"], []).append(p)

out = []
for b in cfg:
    name = b["brand"]
    rows = by_brand.get(name, [])
    active = sum(1 for r in rows if (r.get("status") or "").lower() == "aktif")
    impr = sum(r.get("total_impr", 0) for r in rows)
    clicks = sum(r.get("total_clicks", 0) for r in rows)
    ctr = round(clicks / impr * 100, 2) if impr else 0.0
    out.append({
        "brand": name,
        "active_lp": active or len(rows),
        "impr": impr,
        "clicks": clicks,
        "ctr": f"{ctr:.2f}%",
        "focus": b.get("focus", ""),
    })
    if not rows:
        print(f"WARN: {name} ada di config tapi 0 LP di products.json")

with open(os.path.join(HERE, "data", "brands.json"), "w") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(f"wrote {len(out)} brands, total LP {sum(r['active_lp'] for r in out)}")
