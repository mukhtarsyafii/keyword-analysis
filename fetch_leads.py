#!/usr/bin/env python3
"""Lead & SO per landing page — rantai atribusi persis flow Academy
(dashboard.digitalfinger.id/academy/):

  1. Klik WA di LP menghasilkan kode unik (GRC11O-xxxx / IPQI3O-xxxx)
     -> sheet WA_LOG_GRC (1bPPlmIp...) & WA_LOG_IPQI (1IfLSGTt...)
  2. CS mencatat lead di Need Tracking, kolom `Kode Unik` = kode itu
     -> mirror Google Sheet `Academy GRC Need Mirror` (1l9yPZl2...,
        tab 'Need Tracking - New', header baris 2, data dari baris 3)
  3. Lead di-match ke Odoo crm.lead via 9-digit akhir phone / email
     (team GRC Training 1369 / IPQI Training 1370)
     -> sale_order_count & sale_amount_total = SO + nilai (kohort lead,
        tanggal order boleh di luar periode — sama seperti Academy)

Tulis data/leads.json:
  pages[normUrl] = {leads, qualified, so, so_value, weeks{isoW: leads},
                    so_weeks{isoW: so_value}}
Semua tahap non-fatal: tanpa Odoo tetap jalan (leads saja), tanpa Need
Sheet tetap jalan (nol lead, kolom '-' di dashboard).

Usage:
  python3 fetch_leads.py            # tulis data/leads.json
  python3 fetch_leads.py --check    # cetak agregat, tidak menulis
  python3 fetch_leads.py --no-odoo  # lewati langkah SO dari Odoo
"""
import argparse, csv, io, json, os, re, subprocess, sys
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

WA_SOURCES = [
    ("GRC Indonesia", "1bPPlmIp_PqfAvGm8B1P3sjXuOQRWGES_aR4DPx5iIqE"),
    ("IPQI",          "1IfLSGTtqaxB-lbfYGlaNbold9mP0NkNf8Xvq9EJ_Vow"),
]
NEED_SID = "1l9yPZl2v-Zwym9swERGeTpW3ykx_wejQTu-Nwr-j7E0"   # Academy GRC Need Mirror
NEED_TAB = "Need Tracking - New"
NEED_RANGE = f"'{NEED_TAB}'!A3:AZ"
# kolom (0-based) — sama dengan need_data.py Academy
COL = dict(date=0, company=1, brand=2, pipeline=4, status=5, name=7,
           phone=9, email=10, est_so=14, sales=18, sumber=19, kode=24,
           brand2=23)
CODE_RE = re.compile(r"([A-Z]{2,6}\d*[AOSLE]-[A-Za-z0-9]{4,6})", re.I)
ODOO_ENV = "/opt/ads/ssg/.env"
CRM_TEAMS = [1369, 1370]          # GRC Training, IPQI Training
GSHEET_TOKEN = os.path.expanduser("~/.hermes/google_token.json")

NOT_QUALIFIED = ("lost", "-", "", "pre leads", "pre hot oppo")


def norm_url(u):
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.split("?")[0].split("#")[0].rstrip("/")


def norm_phone(p):
    p = re.sub(r"[\s\-\(\)]", "", (p or "").strip())
    if p.startswith("0"):
        p = "62" + p[1:]
    return p.lstrip("+")


def iso_week(d):
    y, w, _ = d.isocalendar()
    return f"{y}W{w:02d}"


def parse_date(s):
    """'9/14/2026 7:27:15' | '2026-09-14' | '14/09/2026' -> date."""
    s = str(s or "").strip()
    if not s:
        return None
    d = s.split(" ")[0].split("T")[0]
    p = re.split(r"[/.\-]", d)
    if len(p) == 3:
        try:
            if len(p[2]) == 4:          # MM/DD/YYYY (format Academy)
                return datetime(int(p[2]), int(p[0]), int(p[1])).date()
            if len(p[0]) == 4:          # YYYY-MM-DD
                return datetime(int(p[0]), int(p[1]), int(p[2])).date()
            if len(p[2]) == 4:          # DD/MM/YYYY
                return datetime(int(p[2]), int(p[1]), int(p[0])).date()
        except ValueError:
            return None
    return None


def gsheet_values(sid, rng):
    """Sheets API dengan token OAuth Hermes; fallback CSV export publik."""
    try:
        import requests
        t = json.load(open(GSHEET_TOKEN))
        tok = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": t["client_id"], "client_secret": t["client_secret"],
            "refresh_token": t["refresh_token"], "grant_type": "refresh_token"},
            timeout=30).json()["access_token"]
        r = requests.get(
            f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/{rng}",
            headers={"Authorization": "Bearer " + tok}, timeout=60)
        if r.status_code == 200 and r.json().get("values"):
            return r.json()["values"]
        print(f"WARN: Sheets API {r.status_code} utk {sid}; fallback export")
    except Exception as ex:
        print(f"WARN: Sheets API gagal ({str(ex)[:80]}); fallback export")
    url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid=0"
    out = subprocess.run(["curl", "-sL", "--max-time", "120", url],
                         capture_output=True, text=True, timeout=150).stdout
    if not out.strip() or out.lstrip().startswith("<"):
        return None
    rows = list(csv.reader(io.StringIO(out)))
    return rows[2:] if rows else None       # samakan offset: data dari baris 3


def load_wa_codes():
    """kode -> {page, ts} dari kedua sheet WA log."""
    codes = {}
    for brand, sid in WA_SOURCES:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid=0"
        out = subprocess.run(["curl", "-sL", "--max-time", "120", url],
                             capture_output=True, text=True, timeout=150).stdout
        if not out.strip() or out.lstrip().startswith("<"):
            print(f"WARN: WA log {brand} tidak terbaca")
            continue
        for row in csv.DictReader(io.StringIO(out)):
            if (row.get("event") or "").strip() != "wa_click":
                continue
            code = (row.get("code") or "").strip()
            page = norm_url(row.get("page"))
            if not code or not page:
                continue
            ts = parse_date(row.get("timestamp"))
            if code not in codes or (ts and codes[code]["date"] and ts < codes[code]["date"]):
                codes[code] = {"page": page, "brand": brand, "date": ts,
                               "referrer": (row.get("referrer") or "").strip()}
    return codes


def load_need_rows():
    vals = gsheet_values(NEED_SID, NEED_RANGE)
    if not vals:
        print("WARN: Need mirror tidak terbaca; lead = 0")
        return []
    rows = []
    for r in vals:
        def g(i):
            return (str(r[i]).replace("[", "").replace("]", "").strip()
                    if len(r) > i and r[i] is not None else "")
        kode = g(COL["kode"])
        m = CODE_RE.search(kode)
        rows.append({
            "date": parse_date(g(COL["date"])),
            "company": g(COL["company"]),
            "brand": g(COL["brand"]) or g(COL["brand2"]),
            "status": g(COL["status"]),
            "name": g(COL["name"]),
            "phone": norm_phone(g(COL["phone"])),
            "email": g(COL["email"]).lower().strip(),
            "kode": m.group(1) if m else kode,
        })
    return rows


def odoo_crm_index():
    """crm.lead tim GRC/IPQI -> index 9-digit phone & email -> (so, rp)."""
    try:
        import xmlrpc.client
        env = {}
        for line in open(ODOO_ENV):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v.strip().strip('"').strip("'")
        url, db, u, key = (env["ODOO_URL"], env["ODOO_DB"],
                           env["ODOO_USERNAME"], env["ODOO_API_KEY"])
        uid = xmlrpc.client.ServerProxy(url + "/xmlrpc/2/common").authenticate(db, u, key, {})
        if not uid:
            print("WARN: Odoo auth gagal; SO = 0")
            return {}
        m = xmlrpc.client.ServerProxy(url + "/xmlrpc/2/object")
        me = m.execute_kw(db, uid, key, "res.users", "read", [[uid]],
                          {"fields": ["company_ids"]})
        ctx = {"allowed_company_ids": me[0]["company_ids"]}
        rows = m.execute_kw(db, uid, key, "crm.lead", "search_read",
                            [[["team_id", "in", CRM_TEAMS]]],
                            {"fields": ["id", "phone", "mobile", "email_from",
                                        "sale_order_count", "sale_amount_total"],
                             "context": ctx, "limit": 5000})
        idx = {}
        for c in rows:
            so = int(c.get("sale_order_count") or 0)
            rp = float(c.get("sale_amount_total") or 0)
            for f in ("mobile", "phone"):
                p = norm_phone(c.get(f) or "")
                if len(p) >= 9:
                    idx.setdefault(("p", p[-9:]), (so, rp))
            e = (c.get("email_from") or "").lower().strip()
            if e:
                idx.setdefault(("e", e), (so, rp))
        return idx
    except Exception as ex:
        print(f"WARN: langkah Odoo gagal ({str(ex)[:100]}); SO = 0")
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="jangan menulis")
    ap.add_argument("--no-odoo", action="store_true", help="lewati SO dari Odoo")
    args = ap.parse_args()

    codes = load_wa_codes()
    need = load_need_rows()
    hits = [n for n in need if n["kode"] and n["kode"] in codes]
    print(f"kode WA funnel: {len(codes)} | baris Need: {len(need)} | "
          f"lead ter-atribusi LP: {len(hits)}")

    crm = {} if args.no_odoo else odoo_crm_index()
    matched = 0

    pages = defaultdict(lambda: {"leads": 0, "qualified": 0, "so": 0,
                                 "so_value": 0.0, "weeks": {}, "so_weeks": {},
                                 "so_cnt_weeks": {}, "from": {}})
    seen = set()
    for n in hits:
        e = pages[codes[n["kode"]]["page"]]
        if n["kode"] in seen:
            continue          # satu kode = satu lead; dobel dicatat -> hitung sekali
        seen.add(n["kode"])
        e["leads"] += 1
        # asal lead: halaman sebelum LP tujuan (referrer klik WA). Penting utk
        # halaman hub (pelatihan-terkini) — CTA LP lain mengarah ke sana, jadi
        # lead 'milik' hub sebenarnya berawal dari LP spesifik.
        ref_raw = codes[n["kode"]].get("referrer") or ""
        ref = norm_url(ref_raw)
        pg = codes[n["kode"]]["page"]
        if not ref_raw:
            src = "(langsung)"
        elif ref == pg:
            src = "(halaman itu sendiri)"
        elif ref.split("/")[0] == pg.split("/")[0]:
            src = ref
        else:
            src = "(eksternal) " + (ref.split("/")[0] or "?")
        e["from"][src] = e["from"].get(src, 0) + 1
        if n["status"].lower() not in NOT_QUALIFIED:
            e["qualified"] += 1
        wk = iso_week(n["date"]) if n["date"] else None
        if wk:
            e["weeks"][wk] = e["weeks"].get(wk, 0) + 1
        so = None
        if n["phone"] and len(n["phone"]) >= 9:
            so = crm.get(("p", n["phone"][-9:]))
        if so is None and n["email"]:
            so = crm.get(("e", n["email"]))
        if so:
            matched += 1
            e["so"] += so[0]
            e["so_value"] += so[1]
            if wk:
                e["so_weeks"][wk] = e["so_weeks"].get(wk, 0) + so[1]
                e["so_cnt_weeks"][wk] = e["so_cnt_weeks"].get(wk, 0) + so[0]
    if not args.no_odoo:
        print(f"lead ketemu crm.lead Odoo: {matched}")

    out = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "chain": "kode WA -> Need Tracking (Kode Unik) -> crm.lead -> SO",
        "codes_total": len(codes),
        "leads_total": sum(v["leads"] for v in pages.values()),
        "so_total": sum(v["so"] for v in pages.values()),
        "so_value_total": round(sum(v["so_value"] for v in pages.values())),
        "pages": {k: {**v, "so_value": round(v["so_value"])}
                  for k, v in sorted(pages.items())},
    }

    prod_path = os.path.join(DATA, "products.json")
    if os.path.exists(prod_path):
        prods = json.load(open(prod_path))
        out["lp_matched"] = sum(1 for p in prods if norm_url(p.get("url")) in out["pages"])
        out["lp_total"] = len(prods)

    print(f"halaman dgn lead: {len(out['pages'])} | total lead: {out['leads_total']} | "
          f"SO: {out['so_total']} (Rp {out['so_value_total']:,.0f})")
    if "lp_matched" in out:
        print(f"join ke dashboard: {out['lp_matched']}/{out['lp_total']} LP punya lead tercatat")
    for u, v in sorted(out["pages"].items(), key=lambda kv: -kv[1]["leads"])[:8]:
        print(f"  lead {v['leads']:>3}  SO {v['so']:>3}  Rp {v['so_value']:>13,.0f}  {u[:60]}")

    if args.check:
        return
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "leads.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"wrote data/leads.json ({len(out['pages'])} halaman)")


if __name__ == "__main__":
    main()
