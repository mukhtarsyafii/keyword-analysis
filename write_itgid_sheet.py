#!/usr/bin/env python3
"""Write the ITGID LP listing (crawl itgid.org + GSC queries + Ubersuggest volumes)
into tab 'LP ITGID' (gid 1689687208) of the shared tracker sheet.

Layout of the tab (row 3 = header):
  A No | B Nama LP / Halaman | C Keyword Utama | D Volume | E Keyword Sekunder |
  F Volume | G Draf | H URL | I Tanggal Live | J PIC Buat | K Status LP

Existing Draf doc links are preserved by name match. Idempotent: rerun overwrites
the same block. Run: python3 write_itgid_sheet.py [--dry]
"""
import json, os, sys, urllib.parse

import google.auth
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
import urllib.request

SHEET_ID = "1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I"
TAB = "LP ITGID"
TOKEN = os.path.expanduser("~/.hermes/google_token.json")
D = "/Users/mukhtarsyafii/.hermes/cache/scratch/itgid"

# existing Draf links already in the tab, preserved by product path
KEEP_DRAF = {
    "/training/cobit-2019/": "https://docs.google.com/document/d/1XKPeWeRB6PzEJjmhuS3z6hzdrbpRnmWBQJvqhGv89HA/edit?usp=sharing",
    "/training/crisc-certified-risk-information-system-control/": "https://docs.google.com/document/d/1yLypHXWCZauaI6NrznciylrgnnKOV5s0_-bHTXSM4wc/edit",
}


def junk(q):
    """GSC noise: operator strings, domain lookups, version fragments, navigations."""
    q = q.lower()
    return (":" in q or "itgid" in q or q.startswith(("http", "www", "-"))
            or not any(c.isalpha() for c in q))


def rows():
    store = {p["permalink"].replace("https://itgid.org", ""): p
             for p in json.load(open(f"{D}/store.json"))}
    meta = json.load(open(f"{D}/prod_meta.json"))
    gsc = json.load(open(f"{D}/gsc_products.json"))
    try:
        gq = json.load(open(f"{D}/gsc_kw_vol.json"))
    except FileNotFoundError:
        gq = {}
    ov = json.load(open(f"{D}/kw_overview.json"))

    out = []
    for path in sorted(store, key=lambda p: -gsc.get(p, {}).get("impr", 0)):
        name = (meta.get(path, {}).get("h1") or store[path]["name"]).strip()
        url = "https://itgid.org" + path
        k1 = v1 = k2 = v2 = ""
        g = [x for x in (gq.get(path) or []) if not junk(x["kw"])]
        g_ok = [x for x in g if x["vol"] > 0]
        if g_ok:
            k1, v1 = g_ok[0]["kw"], g_ok[0]["vol"]
            second = next((x for x in g_ok[1:] if x["kw"] != k1), None)
            if second:
                k2, v2 = second["kw"], second["vol"]
        if not k1:
            cands = sorted(ov.get(path, []), key=lambda x: -x["vol"])
            if cands:
                k1, v1 = cands[0]["kw"], cands[0]["vol"]
            if len(cands) > 1:
                k2, v2 = cands[1]["kw"], cands[1]["vol"]
        if not k2:  # single GSC query -> fall back to the runner-up overview candidate
            cands = sorted(ov.get(path, []), key=lambda x: -x["vol"])
            alt = next((c for c in cands if c["kw"] != k1 and c["vol"] > 0), None)
            if alt:
                k2, v2 = alt["kw"], alt["vol"]
        out.append([name, k1, v1 or 0, k2, v2 or 0, KEEP_DRAF.get(path, ""), url, "", "", "Aktif"])
    # planned LP without a live page yet (kept from the tab's original draft rows)
    out.append(["Data Management (DAMABOK)", "data management", 0, "dmbok", 0, "", "", "", "", "Draft"])
    return out


def main():
    dry = "--dry" in sys.argv
    data = rows()
    values = [[i + 1] + r for i, r in enumerate(data)]
    n = len(values)
    print(f"{n} rows; first: {values[0]}")
    if dry:
        json.dump(values, open(f"{D}/itgid_values.json", "w"), indent=1, ensure_ascii=False)
        return

    creds = Credentials.from_authorized_user_file(TOKEN)
    if not creds.expiry or creds.expired:
        creds.refresh(google.auth.transport.requests.Request())
    hdr = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

    # clear old block rows 4..200 then write
    def put(rng, vals):
        body = json.dumps({"values": vals}).encode()
        u = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/"
             f"{urllib.parse.quote(rng)}?valueInputOption=RAW")
        req = urllib.request.Request(u, data=body, headers=hdr, method="PUT")
        return json.loads(urllib.request.urlopen(req, timeout=60).read())

    # row 1 title, row 2 brand line, row 3 header, row 4 subheader — data starts row 5
    last = 4 + n
    blank = [[""] * 11 for _ in range(200 - last)]
    if blank:
        put(f"{TAB}!A{last+1}:K200", blank)
    res = put(f"{TAB}!A5:K{last}", values)
    print("wrote:", res.get("updatedCells"), "cells ->", res.get("updatedRange"))


main()
