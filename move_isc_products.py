#!/usr/bin/env python3
"""Pindahkan 85 produk brand 'ISC Safety School' dari file Produk ke tab 'LP ISC'.

Pola sama move_petro_products.py, plus: keyword utama diambil dari GSC top query
per URL (isc_gsc_pq.json, 90 hari) bila ada; fallback nama produk.

Run: python3 move_isc_products.py [--dry]
"""
import json, os, re, sys, urllib.parse, urllib.request

SRC = '19yGQT8ww0K4fi6E8JqqHj24sibfhSLvtaH2Ie6ug_dY'
DST = '1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I'
TAB = "'LP ISC Safety School'"
SID = 1466899190
GRID_END = 223
D = '/Users/mukhtarsyafii/.hermes/cache/scratch/synergy'
NOTE = ("💡  Cara pakai: Setiap LP baru yang live, tambah baris baru.  Setiap Jumat, isi "
        "Impressions, Clicks, dan Ranking dari Google Search Console.  CTR otomatis terhitung.")

from google.oauth2.credentials import Credentials
import google.auth.transport.requests

creds = Credentials.from_authorized_user_file(os.path.expanduser('~/.hermes/google_token.json'))
if not creds.expiry or creds.expired:
    creds.refresh(google.auth.transport.requests.Request())
HDR = {'Authorization': 'Bearer ' + creds.token, 'Content-Type': 'application/json'}


def colname(n):
    s = ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def get(rng, sid=DST):
    u = f'https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/' + urllib.parse.quote(rng)
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=HDR), timeout=120).read()).get('values', [])


def put(rng, vals):
    u = (f'https://sheets.googleapis.com/v4/spreadsheets/{DST}/values/{urllib.parse.quote(rng)}'
         '?valueInputOption=RAW')
    urllib.request.urlopen(urllib.request.Request(u, data=json.dumps({'values': vals}).encode(),
                                                  headers=HDR, method='PUT'), timeout=120).read()


def batch(reqs):
    urllib.request.urlopen(urllib.request.Request(
        f'https://sheets.googleapis.com/v4/spreadsheets/{DST}:batchUpdate',
        data=json.dumps({'requests': reqs}).encode(), headers=HDR, method='POST'), timeout=120).read()


def main():
    dry = '--dry' in sys.argv
    src = json.load(open(f'{D}/isc_src.json'))
    probe = json.load(open(f'{D}/isc_url_probe.json'))
    gsc = json.load(open(f'{D}/isc_gsc_pq.json'))
    cache = json.load(open('/Users/mukhtarsyafii/Projects/keyword-analysis/data/uber_cache.json'))
    src.sort(key=lambda r: (r[3].strip().lower() == 'pelatihan', r[2].strip().lower(), r[5].strip().lower()))

    def vol(kw):
        v = cache.get('keyword_overview|' + json.dumps({"keyword": kw, "language": "id", "locId": 2360}, sort_keys=True))
        if not v:
            return None
        ms = [m.get("search_volume", 0) for m in (v or {}).get("monthly_searches") or []]
        return round(sum(ms) / len(ms)) if ms else int((v or {}).get("search_volume") or 0)

    def top_query(url):
        qs = gsc.get(url.rstrip('/'), [])
        if not qs:
            return None
        qs = sorted(qs, key=lambda x: (-x[2], -x[1]))  # impr desc
        for k, c, i in qs:
            if c + i > 0 and len(k) >= 3:
                return k.lower()
        return None

    rows = []
    for i, r in enumerate(src, 1):
        url = r[24].strip()
        st = probe.get(url, [None])[0] if url.startswith('http') else None
        nm = re.sub(r'\s+', ' ', r[5]).strip().lower()
        nm = re.sub(r'\s*\([^)]*\)\s*', ' ', nm).strip() or nm
        kw1 = top_query(url) if url.startswith('http') else None
        if not kw1:
            kw1 = nm if re.search(r'pelatihan|training|sertifikasi|kursus', nm) or r[3].strip().lower() != 'pelatihan' else 'pelatihan ' + nm
        kw2 = nm if kw1 != nm else f'{nm} 2026'
        v1, v2 = vol(kw1), vol(kw2)
        rows.append([i, r[5].strip(), kw1, v1 if v1 is not None else '', kw2, v2 if v2 is not None else '',
                     '', url, '', '', 'Aktif' if st == 200 else 'Draft'])
    n = len(rows)
    last = 4 + n
    print(f'{n} produk; {sum(1 for r in rows if r[7].startswith("http"))} URL; aktif {sum(1 for r in rows if r[10]=="Aktif")}; '
          f'vol>0 {sum(1 for r in rows if isinstance(r[3], int) and r[3] > 0)}; kw dari GSC {sum(1 for r in src if r[24].strip().startswith("http") and gsc.get(r[24].strip().rstrip("/")))}')
    if dry:
        json.dump(rows, open(f'{D}/isc_rows.json', 'w'), indent=1, ensure_ascii=False)
        return

    m = json.loads(urllib.request.urlopen(urllib.request.Request(
        f'https://sheets.googleapis.com/v4/spreadsheets/{DST}?fields=sheets.merges', headers=HDR),
        timeout=120).read())
    reqs = [{'unmergeCells': {'range': mm}} for s in m['sheets'] for mm in (s.get('merges') or [])
            if mm['sheetId'] == SID and (mm['startRowIndex'] >= 4 or
                                         (mm['startRowIndex'] == 2 and mm['endColumnIndex'] > GRID_END))]
    if reqs:
        batch(reqs)
        print(f'unmerged {len(reqs)}')

    cc = next(s['properties']['gridProperties']['columnCount'] for s in
              json.loads(urllib.request.urlopen(urllib.request.Request(
                  f'https://sheets.googleapis.com/v4/spreadsheets/{DST}?fields=sheets.properties',
                  headers=HDR), timeout=120).read())['sheets'] if s['properties']['sheetId'] == SID)
    if cc < GRID_END + 29 + 2:
        batch([{'appendDimension': {'sheetId': SID, 'dimension': 'COLUMNS', 'length': GRID_END + 31 - cc}}])
        print(f'cols {cc} -> {GRID_END+31}')

    c0, c1 = colname(GRID_END + 1), colname(GRID_END + 29)
    put(f'{TAB}!{c0}4:{c1}4', [[''] * 29])
    put(f'{TAB}!A1:B2', [['LP TRACKER — ISC SAFETY SCHOOL 2026'],
                         ['Brand: ISC Safety School  |  Sumber: sheet Produk (85 item Pelatihan)  |  Keyword utama: GSC top query 90 hari bila ada  |  Detail produk di blok ' + c0 + ' dst']])
    put(f'{TAB}!A5:K{last}', rows)
    if last + 1 <= 220:
        put(f'{TAB}!A{last+1}:K220', [[''] * 11 for _ in range(220 - last)])
    put(f'{TAB}!A{last+1}', [[NOTE]])
    put(f'{TAB}!{c0}3:{c1}3', [get('A1:AE1', SRC)[0]])
    put(f'{TAB}!{c0}5:{c1}{last}', src)

    got = get(f'{TAB}!A5:K{last}')
    mm = [i + 5 for i, (w, h) in enumerate(zip(rows, got))
          if [str(x) for x in w] != [str(x) for x in h] + [''] * (11 - len(h))]
    print(f'wrote {n} | readback {len(got)} | mismatch {mm if mm else "none"}')


main()
