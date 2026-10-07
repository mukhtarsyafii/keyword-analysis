#!/usr/bin/env python3
"""Extract LP tracker sheets -> data/products.json (weekly series per product).

One Google Sheet, one tab per brand (gid lives in data/brands_config.json).
Public CSV export, no auth. Run: python3 extract_sheet.py
"""
import csv, html, io, json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SHEET_ID = "1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I"
OUT = os.path.join(DATA, "products.json")
CFG = os.path.join(DATA, "brands_config.json")

# GRC keeps its original ids; the prev-map preserves weeks/daily by URL anyway.
KEEP_IDS = {"GRC Indonesia"}

# Column positions differ per tab (GRC has an extra "Draf" column), so every
# column is resolved by header name, never by index.
COL_ALIASES = {
    "no": ("No",),
    "name": ("Nama LP / Halaman",),
    "kw_utama": ("Keyword Utama",),
    "vol_utama": ("Estimasi Volume",),          # first occurrence
    "kw_target": ("Target Keyword", "Keyword Sekunder"),
    "kw_info": ("Keyword Informasional", "Keyword informasional"),
    "url": ("URL",),
    "status": ("Status LP",),
}

CAT_RULES = {
    "IPQI": [
        ("Metrologi & Laboratorium", ("kalibrasi", "17025", "laborator", "iso/jsa", "metrolog")),
        ("Maintenance & Aset", ("maintenance", "oee", "tpm", "reliability", "predictive", "asset")),
        ("Supply Chain & Inventori", ("inventory", "safety stock", "demand forecast", "warehouse", "supply chain")),
        ("Lean & Continuous Improvement", ("fmea", "8d", "kaizen", "lean", "six sigma", "qcc", "gugus kendali",
                                           "root cause", "31010", "spc", "apqp", "quality function",
                                           "problem solving", "control plan", "5s", "5r", "red tag")),
        ("Manajemen Mutu & ISO", ("iso", "mutu", "quality management", "iatf", "sistem manajemen", "auditor", "fmea")),
        ("Leadership & SDM", ("leadership", "communication", "negotiation", "lobbying", "budsia",
                              "budaya kerja", "pensiun", "training need", "5r", "budaya")),
        ("Business Process & Strategi", ("business process", "balanced scorecard", "strategic", "strategi",
                                         "energy management", "environmental", "social accountability", "sa8000")),
    ],
    "ITGID": [
        ("Audit & Assurance TI", ("cisa", "it audit", "audit ti", "it asset audit", "it governance audit",
                                  "it security audit", "audit tata kelola", "togaf", "itil")),
        ("Sertifikasi Keamanan Siber", ("cissp", "ceh", "cism", "ethical hacker", "cyber security", "keamanan siber",
                                        "penetration", "pentest", "cloud security", "vulnerability")),
        ("Tata Kelola & Risiko TI", ("cobit", "cgeit", "crisc", "it risk", "manajemen risiko", "iso 31000",
                                     "it governance", "tata kelola", "it master plan", "indi 4.0",
                                     "compliance", "identifikasi konteks")),
        ("Keamanan Informasi ISO", ("iso 27001", "isms", "lead implementer iso/iec 27001", "security governance")),
        ("BCM & Layanan TI", ("22301", "bcm", "bcp", "disaster recovery", "it bcp", "itsm", "20000",
                              "20001", "it service", "it operation")),
        ("Manajemen Proyek & Data", ("project management", "pmp", "agile", "data governance", "damabok",
                                     "identification risk", "mitigation risk", "compliance ojk")),
    ],
}
DEFAULT_CATS = [
    ("Sertifikasi BNSP / Profesi", ("bnsp", "qrmo", "qrma", "qcro", "qrgp", "cgp", "qrmp", "ccgo", "sertifikasi")),
    ("Standar ISO & Kepatuhan", ("iso", "bcms", "31000", "37001", "37301", "22301", "31022", "9001", "31010")),
    ("Audit, Fraud & Forensik", ("fraud", "dokumen", "audit", "investigasi", "grafologi", "icofr")),
    ("AI & Data Governance", ("ai", "data", "analytics")),
]


def num(s):
    s = (s or "").strip().replace(",", "").replace("%", "")
    if s in ("", "-", "–", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def categorize(name, kw, brand):
    t = f"{name} {kw}".lower()
    for cat, keys in CAT_RULES.get(brand, []):
        if any(k in t for k in keys):
            return cat
    if brand in CAT_RULES:
        return "Pelatihan Umum"
    for cat, keys in DEFAULT_CATS:
        if any(k in t for k in keys):
            return cat
    return "Tata Kelola & BUMN"


def col_idx(hdr, field):
    names = [h.strip().lower() for h in hdr]
    for want in COL_ALIASES[field]:
        want = want.strip().lower()
        for i, h in enumerate(names):
            if h == want:
                return i
    return None


def parse_brand(rows, brand):
    hdr = rows[2]
    weeks = []
    for j, c in enumerate(hdr):
        m = re.match(r"^(W\d+)\s*—", c.strip())
        if m:
            # Normalize to the year-qualified key GSC uses (sheet covers 2026).
            weeks.append((j, f"2026W{int(m.group(1)[1:]):02d}"))

    ix = {f: col_idx(hdr, f) for f in COL_ALIASES}
    # Volume columns repeat per keyword group; tabs name them "Estimasi Volume"
    # (GRC/IPQI) or plain "Volume" (ITGID) — match either, in order.
    vol_idx = [i for i, h in enumerate([c.strip() for c in hdr])
               if h in ("Estimasi Volume", "Volume")]

    out = []
    for r in rows[3:]:
        if len(r) < 13 or not (r[ix["name"]] or "").strip():
            continue
        if (r[ix["no"]] or "").strip().startswith(("💡", "Brand:")):
            continue

        def get(f, vol=0):
            if f == "vol":
                i = vol_idx[vol] if vol < len(vol_idx) else None
            else:
                i = ix[f]
            return html.unescape(r[i].strip()) if i is not None and i < len(r) else ""

        series = []
        for j, wn in weeks:
            if j + 3 >= len(r):
                break
            impr, clk, ctr, rnk = num(r[j]), num(r[j + 1]), num(r[j + 2]), num(r[j + 3])
            if impr is None and clk is None:
                continue
            series.append({"w": wn, "impr": impr or 0, "clicks": clk or 0,
                           "ctr": ctr, "rank": rnk})

        # dedupe by week, keep last occurrence (sheets carry duplicate week blocks)
        seen = {}
        for s in series:
            seen[s["w"]] = s
        series = sorted(seen.values(), key=lambda s: s["w"])

        out.append({
            "brand": brand,
            "name": get("name"),
            "category": categorize(get("name"), get("kw_utama"), brand),
            "kw_utama": get("kw_utama") or "-",
            "vol_utama": get("vol", 0) or "-",
            "kw_target": get("kw_target") or "-",
            "vol_target": get("vol", 1) or "-",
            "kw_info": get("kw_info") or "-",
            "vol_info": get("vol", 2) or "-",
            "url": get("url"),
            "status": get("status") or "Draft",
            "total_impr": 0, "total_clicks": 0, "ctr": 0.0,
            "avg_rank": 0, "latest_rank": 0,
            "weeks": series,
        })
    return out


def main():
    cfg = json.load(open(CFG))
    prev = {}
    if os.path.exists(OUT):
        try:
            for p in json.load(open(OUT)):
                if p.get("url"):
                    prev[p["url"].rstrip("/")] = p
        except (json.JSONDecodeError, OSError):
            pass

    products = []
    for b in cfg:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={b['gid']}"
        raw = urllib.request.urlopen(url, timeout=60).read().decode("utf-8", "ignore")
        rows = list(csv.reader(io.StringIO(raw)))
        brand_rows = parse_brand(rows, b["brand"])
        products.extend(brand_rows)
        print(f"{b['brand']}: {len(brand_rows)} LP")

    # Preserve GSC weeks/daily: this script owns the catalog columns, GSC owns
    # performance. Rebuilding products.json from scratch would drop `daily`.
    for p in products:
        old = prev.get(p["url"].rstrip("/")) if p["url"] else None
        if old:
            by_wk = {s["w"]: s for s in p["weeks"]}
            by_wk.update({s["w"]: s for s in old.get("weeks", [])})  # GSC weeks win
            p["weeks"] = sorted(by_wk.values(), key=lambda s: s["w"])
            if old.get("daily"):
                p["daily"] = old["daily"]

        live = [s for s in p["weeks"] if s["impr"] or s["clicks"]]
        p["total_impr"] = int(sum(s["impr"] for s in live))
        p["total_clicks"] = int(sum(s["clicks"] for s in live))
        p["ctr"] = round(p["total_clicks"] / p["total_impr"] * 100, 2) if p["total_impr"] else 0.0
        ranks = [s["rank"] for s in live if s["rank"]]
        p["avg_rank"] = round(sum(ranks) / len(ranks), 1) if ranks else 0
        p["latest_rank"] = live[-1]["rank"] if live and live[-1]["rank"] else 0

    # Brand-scoped ids (GRC 1.., IPQI 1001..) so recommendations.json and
    # competitors.json keys never collide across brands and never drift.
    base = {b["brand"]: b.get("id_base", 0) for b in cfg}
    for b in {p["brand"] for p in products}:
        rows = [p for p in products if p["brand"] == b]
        if b in KEEP_IDS:
            for p in rows:
                old = prev.get(p["url"].rstrip("/")) if p["url"] else None
                if isinstance((old or {}).get("id"), int):
                    p["id"] = old["id"]
        taken = set()
        # pass 1: reserve every inherited id first, in row order — a dup row must
        # not steal an id whose owner row comes later in the sheet
        for p in rows:
            pid = p.get("id")
            if isinstance(pid, int) and pid not in taken:
                taken.add(pid)
            else:
                # two sheet rows can share one URL; prev-by-lookup hands them the
                # same id and recommendations.json silently drops one of them
                p["id"] = None
        n = base.get(b, 0)
        for p in rows:
            if p["id"] is None:
                n += 1
                while n in taken:
                    n += 1
                p["id"] = n
                taken.add(n)

    with open(OUT, "w") as f:
        json.dump(products, f, indent=1, ensure_ascii=False)

    print(f"wrote {len(products)} products -> {OUT}")
    print(f"total impr {sum(p['total_impr'] for p in products):,}, "
          f"clicks {sum(p['total_clicks'] for p in products):,}")
    print(f"aktif {sum(1 for p in products if p['status'].lower()=='aktif')}, "
          f"draft {sum(1 for p in products if p['status'].lower()!='aktif')}")


if __name__ == "__main__":
    main()
