#!/usr/bin/env python3
"""Fill tab 'LP SYNERGY' (gid 642436703) with the crawl of synergysolusi.com.

Tab already has both Volume columns (schema: No | Nama LP | Keyword Utama | Volume |
Keyword Sekunder | Volume | Draf | URL | Tanggal Live | PIC Buat | Status LP) so no
insertDimension is needed; write 11 columns A..K.

Run: python3 write_synergy_sheet.py [--dry]
"""
import json, os, sys, urllib.parse, urllib.request

SHEET_ID = "1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I"
TAB = "LP SYNERGY"
TOKEN = os.path.expanduser("~/.hermes/google_token.json")
D = "/Users/mukhtarsyafii/.hermes/cache/scratch/synergy"

from google.oauth2.credentials import Credentials
import google.auth.transport.requests

creds = Credentials.from_authorized_user_file(TOKEN)
if not creds.expiry or creds.expired:
    creds.refresh(google.auth.transport.requests.Request())
HDR = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
BATCH = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}:batchUpdate"

SID = 642436703  # grid id == gid of this tab (confirmed from sheets.merges)
NOTE = ("💡  Cara pakai: Setiap LP baru yang live, tambah baris baru.  Setiap Jumat, isi "
        "Impressions, Clicks, dan Ranking dari GSC.  CTR otomatis terhitung.  "
        "Sudah tersedia 53 minggu (full year 2026).")


def batch(reqs):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(BATCH, data=json.dumps({"requests": reqs}).encode(),
                               headers=HDR, method="POST"), timeout=90).read())


def put(rng, vals):
    u = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/"
         f"{urllib.parse.quote(rng)}?valueInputOption=RAW")
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(u, data=json.dumps({"values": vals}).encode(),
                               headers=HDR, method="PUT"), timeout=90).read())


def get(rng):
    u = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{urllib.parse.quote(rng)}"
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=HDR), timeout=90).read()).get("values", [])


def sheet_merges():
    d = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}?fields=sheets.merges",
        headers=HDR), timeout=90).read())
    return [m for s in d["sheets"] for m in (s.get("merges") or []) if m["sheetId"] == SID]


def build_rows():
    cands = json.load(open(f"{D}/lp_candidates.json"))
    vol = json.load(open(f"{D}/kw_vol.json"))
    rows = []
    for c in sorted(cands.values(), key=lambda x: -x["impr"]):
        qs = vol.get(c["path"], [])
        if not qs:
            qs = [{"kw": g["q"], "vol": 0, "qtype": "gsc"} for g in c["gsc"][:2]]
        ok = [q for q in qs if q["vol"] > 0]
        gsc = [q for q in ok if q["kw"] in [g["q"] for g in c["gsc"]]]
        pick = gsc or ok or qs
        k1 = pick[0]["kw"] if pick else "-"
        v1 = pick[0]["vol"] if pick else 0
        k2 = v2 = ""
        for q in pick[1:]:
            if q["kw"] != k1:
                k2, v2 = q["kw"], q["vol"]
                break
        # col G is the tab's 'Draf' scratch column - leave empty
        rows.append([c["name"], k1, v1, k2, v2, "", "https://synergysolusi.com" + c["path"],
                     "", "", "Aktif"])
    return rows


def main():
    dry = "--dry" in sys.argv
    rows = build_rows()
    values = [[i + 1] + r for i, r in enumerate(rows)]
    n = len(values)
    print(f"{n} rows; first: {values[0]}")
    if dry:
        json.dump(values, open(f"{D}/synergy_values.json", "w"), indent=1, ensure_ascii=False)
        return

    hdr = get(f"{TAB}!A3:K3")
    if not (len(hdr[0]) > 5 and hdr[0][3].strip().lower() == "volume"):
        sys.exit(f"unexpected header, aborting: {hdr}")

    reqs = [{"unmergeCells": {"range": m}} for m in sheet_merges()
            if m["startRowIndex"] >= 4 and m["startColumnIndex"] < 12]
    if reqs:
        batch(reqs)
        print(f"unmerged {len(reqs)} data-area merge(s)")

    last = 4 + n
    put(f"{TAB}!A1:B2", [["LP TRACKER — SYNERGY SOLUSI 2026"],
                         ["Brand: Synergy Solusi  |  Target: Min. 2 LP baru/minggu  |  Data performa dari Google Search Console setiap Jumat  |  Pre-fill 12 minggu — tambah kolom manual jika perlu"]])
    put(f"{TAB}!A5:K{last}", values)
    blank = [[""] * 11 for _ in range(220 - last)]
    if blank:
        put(f"{TAB}!A{last+1}:K220", blank)
    put(f"{TAB}!A{last+1}", [[NOTE]])

    got = get(f"{TAB}!A5:K{last}")
    mm = []
    for i, (w, h) in enumerate(zip(values, got)):
        ws = [str(x) for x in w]
        hs = [str(x) for x in h] + [""] * (11 - len(h))
        if ws[:8] != hs[:8]:
            mm.append(i + 5)
    print(f"wrote {n} rows | readback rows {len(got)} | mismatch {mm if mm else 'none'}")


main()
