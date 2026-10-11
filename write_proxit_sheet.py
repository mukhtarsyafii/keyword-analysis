#!/usr/bin/env python3
"""Fill tab 'LP Proxsis IT GRC' (gid 1892690756) with the crawl of it.proxsisgroup.com.

Tab schema is No | Nama LP | Keyword Utama | Keyword Sekunder | URL | Tanggal Live |
PIC Buat | Status LP (no Volume columns, unlike LP ITGID). Two Volume columns are
inserted first (D and F) so the sheet matches the requested listing format:
Nama halaman | Keyword Utama | Volume | Keyword Sekunder | Volume | URL.
Sheets API shifts the weekly GSC blocks right automatically on insertDimension.

Run: python3 write_proxit_sheet.py [--dry]
"""
import json, os, sys, urllib.parse, urllib.request

SHEET_ID = "1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I"
TAB = "LP Proxsis IT GRC"
TOKEN = os.path.expanduser("~/.hermes/google_token.json")
D = "/Users/mukhtarsyafii/.hermes/cache/scratch/proxit"

from google.oauth2.credentials import Credentials
import google.auth.transport.requests

creds = Credentials.from_authorized_user_file(TOKEN)
if not creds.expiry or creds.expired:
    creds.refresh(google.auth.transport.requests.Request())
HDR = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
BATCH = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}:batchUpdate"


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


SID = 1892690756  # grid id == gid of this tab (confirmed from sheets.merges)


def sheet_merges():
    d = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}?fields=sheets.merges",
        headers=HDR), timeout=90).read())
    return [m for s in d["sheets"] for m in (s.get("merges") or []) if m["sheetId"] == SID]


def build_rows():
    cands = json.load(open(f"{D}/lp_candidates.json"))
    vol = json.load(open(f"{D}/kw_vol.json"))
    rows = []
    for c in sorted(cands, key=lambda x: -x["impr"]):
        qs = vol.get(c["path"], [])
        ok = [q for q in qs if q["vol"] > 0]
        # prefer GSC-derived queries (ranked by impressions) that have volume
        gsc = [q for q in ok if q["kw"] in [g["q"] for g in c["gsc"]]]
        pick = gsc or ok or qs
        k1 = pick[0]["kw"] if pick else "-"
        v1 = pick[0]["vol"] if pick else 0
        k2 = v2 = ""
        for q in pick[1:]:
            if q["kw"] != k1:
                k2, v2 = q["kw"], q["vol"]
                break
        rows.append([c["name"], k1, v1, k2, v2, "https://it.proxsisgroup.com" + c["path"], "", "", "Aktif"])
    return rows


def main():
    dry = "--dry" in sys.argv
    rows = build_rows()
    values = [[i + 1] + r for i, r in enumerate(rows)]
    n = len(values)
    print(f"{n} rows; first: {values[0]}")
    if dry:
        json.dump(values, open(f"{D}/biztech_values.json", "w"), indent=1, ensure_ascii=False)
        return

    sid = SID
    hdr = get(f"{TAB}!A3:J3")
    has_vol = len(hdr[0]) > 5 and hdr[0][3].strip().lower() == "volume"
    if not has_vol:
        # insert Volume after Keyword Sekunder (col F, idx 5), then after Keyword Utama (col D, idx 3)
        batch([{"insertDimension": {"range": {"sheetId": sid, "dimension": "COLUMNS",
                                              "startIndex": 5, "endIndex": 6}, "inheritFromBefore": False}},
               {"insertDimension": {"range": {"sheetId": sid, "dimension": "COLUMNS",
                                              "startIndex": 3, "endIndex": 4}, "inheritFromBefore": False}}])
        put(f"{TAB}!D3", [["Volume"]])
        put(f"{TAB}!F3", [["Volume"]])
        put(f"{TAB}!G3", [["URL"]])  # F3 insert rewrites the old URL cell
        print("inserted Volume columns D and F")

    # unmerge any full-width merge inside the data area (would swallow all but col A)
    reqs = [{"unmergeCells": {"range": m}} for m in sheet_merges()
            if m["startRowIndex"] >= 4 and m["startColumnIndex"] < 11]
    if reqs:
        batch(reqs)
        print(f"unmerged {len(reqs)} data-area merge(s)")

    last = 4 + n
    put(f"{TAB}!A1:B2", [["LP TRACKER — IT PROXSIS GROUP (PROXSIS ACADEMY) 2026"],
                         ["Brand: IT Proxsis GRC  |  Target: Min. 2 LP baru/minggu  |  Data performa dari Google Search Console setiap Jumat  |  Pre-fill 12 minggu — tambah kolom manual jika perlu"]])
    put(f"{TAB}!A5:J{last}", values)
    blank = [[""] * 10 for _ in range(200 - last)]
    if blank:
        put(f"{TAB}!A{last+1}:J200", blank)

    got = get(f"{TAB}!A5:J{last}")
    mm = []
    for i, (w, h) in enumerate(zip(values, got)):
        ws = [str(x) for x in w]
        hs = [str(x) for x in h] + [""] * (10 - len(h))
        if ws[:6] != hs[:6]:
            mm.append(i + 5)
    print(f"wrote {n} rows | readback rows {len(got)} | mismatch {mm if mm else 'none'}")


main()
