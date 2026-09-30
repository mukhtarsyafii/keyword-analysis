#!/usr/bin/env python3
"""Extract LP tracker sheet -> data/products.json (weekly series per product).

Source: public Google Sheet CSV export (the tracker Antigravity used).
Run: python3 extract_sheet.py
"""
import csv, io, json, os, re, urllib.request

SHEET_ID = "1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I"
GID = "844447021"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "products.json")


def num(s):
    s = (s or "").strip().replace(",", "").replace("%", "")
    if s in ("", "-", "–", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def categorize(name, kw):
    t = f"{name} {kw}".lower()
    if any(k in t for k in ("bnsp", "qrmo", "qrma", "qcro", "qrgp", "cgp", "qrmp", "ccgo", "sertifikasi")):
        return "Sertifikasi BNSP / Profesi"
    if any(k in t for k in ("iso", "bcms", "31000", "37001", "37301", "22301", "31022", "9001", "31010")):
        return "Standar ISO & Kepatuhan"
    if any(k in t for k in ("fraud", "dokumen", "audit", "investigasi", "grafologi", "icofr")):
        return "Audit, Fraud & Forensik"
    if any(k in t for k in ("ai", "data", "analytics")):
        return "AI & Data Governance"
    return "Tata Kelola & BUMN"


def main():
    raw = urllib.request.urlopen(URL, timeout=60).read().decode("utf-8", "ignore")
    rows = list(csv.reader(io.StringIO(raw)))
    hdr = rows[2]

    weeks = []
    for j, c in enumerate(hdr):
        m = re.match(r"^(W\d+)\s*—", c.strip())
        if m:
            # Normalize to the year-qualified key GSC uses (sheet covers 2026).
            weeks.append((j, f"2026W{int(m.group(1)[1:]):02d}"))

    # Keep the GSC daily series: this script owns the catalog columns, GSC owns
    # performance. Rebuilding products.json from scratch would drop `daily`.
    prev = {}
    if os.path.exists(OUT):
        try:
            for p in json.load(open(OUT)):
                if p.get("url"):
                    prev[p["url"].rstrip("/")] = p
        except (json.JSONDecodeError, OSError):
            pass

    products = []
    for r in rows[3:]:
        if len(r) < 13 or not r[1].strip():
            continue
        if r[0].strip().startswith(("💡", "Brand:")):
            continue

        series = []
        for j, wn in weeks:
            if j + 3 >= len(r):
                break
            impr, clk, ctr, rnk = num(r[j]), num(r[j + 1]), num(r[j + 2]), num(r[j + 3])
            if impr is None and clk is None:
                continue
            series.append({"w": wn, "impr": impr or 0, "clicks": clk or 0,
                           "ctr": ctr, "rank": rnk})

        # dedupe by week, keep last occurrence (sheet has a duplicate W36 block)
        seen = {}
        for s in series:
            seen[s["w"]] = s
        series = sorted(seen.values(), key=lambda s: s["w"])

        url = r[9].strip() if len(r) > 9 else ""
        old = prev.get(url.rstrip("/")) if url else None

        # GSC weeks win over the tracker's manual entry for the same week.
        if old:
            by_wk = {s["w"]: s for s in series}
            by_wk.update({s["w"]: s for s in old.get("weeks", [])})
            series = sorted(by_wk.values(), key=lambda s: s["w"])

        live = [s for s in series if s["impr"] or s["clicks"]]
        total_impr = sum(s["impr"] for s in live)
        total_clicks = sum(s["clicks"] for s in live)
        ranks = [s["rank"] for s in live if s["rank"]]
        latest_rank = live[-1]["rank"] if live and live[-1]["rank"] else 0

        p = {
            "id": int(r[0]) if r[0].strip().isdigit() else len(products) + 1,
            "name": r[1].strip(),
            "category": categorize(r[1], r[2]),
            "kw_utama": r[2].strip() or "-",
            "vol_utama": r[3].strip() or "-",
            "kw_target": r[4].strip() or "-",
            "vol_target": r[5].strip() or "-",
            "kw_info": r[6].strip() or "-",
            "vol_info": r[7].strip() or "-",
            "url": url,
            "status": (r[12].strip() if len(r) > 12 else "") or "Draft",
            "total_impr": int(total_impr),
            "total_clicks": int(total_clicks),
            "ctr": round(total_clicks / total_impr * 100, 2) if total_impr else 0.0,
            "avg_rank": round(sum(ranks) / len(ranks), 1) if ranks else 0,
            "latest_rank": latest_rank,
            "weeks": series,
        }
        if old and old.get("daily"):
            p["daily"] = old["daily"]
        products.append(p)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(products, f, indent=1, ensure_ascii=False)

    print(f"wrote {len(products)} products -> {OUT}")
    print(f"weeks per product: {len(weeks)}")
    print(f"total impr {sum(p['total_impr'] for p in products)}, "
          f"clicks {sum(p['total_clicks'] for p in products)}")
    print(f"aktif {sum(1 for p in products if p['status'].lower()=='aktif')}, "
          f"draft {sum(1 for p in products if p['status'].lower()!='aktif')}")


if __name__ == "__main__":
    main()
