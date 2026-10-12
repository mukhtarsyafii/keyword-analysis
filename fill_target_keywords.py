#!/usr/bin/env python3
"""Isi kolom 'Keyword Sekunder' yang kosong di tab tracker (sumber kw_target dashboard).

Kandidat per LP, urut prioritas:
1. competitor_keywords dari competitors.json (GSC queries + Ubersuggest SERP, volume tertinggi,
   buang noise: site:, kata brand, <5 char, query berangka).
2. Fallback deterministik dari nama LP: buang parenthetical + awalan Pelatihan/Training, lowercase.

Idempoten: hanya menulis sel yang saat ini kosong, match baris via URL (bukan nomor baris).
Jalankan: python3 fill_target_keywords.py            (dry, cetak rencana)
          python3 fill_target_keywords.py --write
"""
import csv, io, json, os, re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_gsc as F  # noqa: E402

SID = "1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I"
CFG = os.path.join(HERE, "data", "brands_config.json")
WRITE = "--write" in sys.argv

NOISE = ("site:", "proxsis", "proxis", "grc indonesia", "ipqi", "fs institute", "itgid",
         "biztech", "icicert", "synergy", "iso center", "iec", "petrotraining", "isc safety")


def derive(name):
    s = re.sub(r"\s*\([^)]*\)", " ", name).strip()
    s = re.sub(r"^(pelatihan|training|kursus)\s+(dan\s+sertifikasi\s+)?", "", s, flags=re.I).strip()
    s = re.sub(r"\s+", " ", s).lower()
    s = re.sub(r"\s*\.{2,}\s*$|\s*…\s*$", "", s).strip()
    for n in NOISE:
        s = re.sub(r"\b" + re.escape(n) + r"\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" .:&|-")
    return s[:120] if len(s) > 3 else ""


def best_comp(c):
    cand = []
    for k in (c or {}).get("competitor_keywords") or []:
        q = (k.get("keyword") or "").strip().lower()
        if len(q) < 5 or len(q) > 80 or re.search(r"\d", q) or any(n in q for n in NOISE):
            continue
        cand.append((k.get("volume") or 0, q))
    cand.sort(reverse=True)
    return cand[0][1] if cand else ""


def sheet_title(sid, gid, tok):
    meta = json.load(urllib.request.urlopen(urllib.request.Request(
        f"https://sheets.googleapis.com/v4/spreadsheets/{sid}?fields=sheets.properties",
        headers={"Authorization": "Bearer " + tok}), timeout=30))
    return next(s["properties"]["title"] for s in meta["sheets"]
                if str(s["properties"]["sheetId"]) == str(gid))


def main():
    prods = json.load(open(os.path.join(HERE, "data", "products.json")))
    comp = json.load(open(os.path.join(HERE, "data", "competitors.json")))
    miss = [p for p in prods if (p.get("kw_target") or "-").strip() in ("", "-")]
    tok = F.access_token() if WRITE else None
    total = filled = 0
    for b in json.load(open(CFG)):
        want = {}
        for p in miss:
            if p["brand"] == b["brand"] and p.get("url"):
                kw = best_comp(comp.get(str(p["id"]))) or derive(p["name"])
                if kw:
                    want[p["url"].rstrip("/")] = kw
        if not want:
            continue
        raw = urllib.request.urlopen(
            f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid={b['gid']}",
            timeout=60).read().decode("utf-8", "ignore")
        rows = list(csv.reader(io.StringIO(raw)))
        hdr = [h.strip().lower() for h in rows[2]]
        it = next((hdr.index(n) for n in ("keyword sekunder", "target keyword") if n in hdr), None)
        iu = hdr.index("url") if "url" in hdr else None
        if it is None or iu is None:
            print(f"{b['brand']}: kolom tidak ada, skip")
            continue
        col = chr(65 + it)
        updates = []  # (sheet_row_1idx, keyword)
        for i, r in enumerate(rows[3:]):
            if len(r) <= max(it, iu):
                continue
            kw = want.get(r[iu].strip().rstrip("/"))
            cur = r[it].strip() if len(r) > it else ""
            if kw and not cur:
                updates.append((i + 4, kw))  # row 4 = rows[3] (1-indexed sheet row)
        if not updates:
            continue
        total += len(updates)
        print(f"{b['brand']}: {len(updates)} sel terisi")
        for row, kw in updates[:4]:
            print(f"   row {row}: {kw}")
        if WRITE:
            title = sheet_title(SID, b["gid"], tok)
            for row, kw in updates:
                rng = urllib.parse.quote(f"'{title}'!{col}{row}")
                req = urllib.request.Request(
                    f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/{rng}?valueInputOption=RAW",
                    data=json.dumps({"values": [[kw]]}).encode(),
                    headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
                    method="PUT")
                urllib.request.urlopen(req, timeout=30)
            filled += len(updates)
            print(f"   -> {len(updates)} sel ditulis")
    print(f"total kandidat {total}, tertulis {filled}")


if __name__ == "__main__":
    main()
