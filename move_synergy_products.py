#!/usr/bin/env python3
"""Pindahkan 133 produk brand 'Synergy Solusi' dari file Produk ke tab ' LP SYNERGY SOLUSI'.

Template tracker (header row 3, data row 5+) diisi: No | Nama LP=Judul Produk |
Keyword Utama/Sekunder (cocokkan path URL dengan crawl) | URL=LP primer | Status.
Blok detail 29 kolom sumber ditempel di kanan grid mingguan (kolom ke-221 / HM),
baris header sama (row 3) supaya sejajar.

Run: python3 move_synergy_products.py [--dry]
"""
import json, os, re, sys, urllib.parse, urllib.request

SRC = '19yGQT8ww0K4fi6E8JqqHj24sibfhSLvtaH2Ie6ug_dY'
DST = '1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I'
TAB = "' LP SYNERGY SOLUSI'"
SID = 1228200395
D = '/Users/mukhtarsyafii/.hermes/cache/scratch/synergy'
NOTE = ("💡  Cara pakai: Setiap LP baru yang live, tambah baris baru.  Setiap Jumat, isi "
        "Impressions, Clicks, dan Ranking dari Google Search Console.  CTR otomatis terhitung.")

from google.oauth2.credentials import Credentials
import google.auth.transport.requests

creds = Credentials.from_authorized_user_file(os.path.expanduser('~/.hermes/google_token.json'))
if not creds.expiry or creds.expired:
    creds.refresh(google.auth.transport.requests.Request())
HDR = {'Authorization': 'Bearer ' + creds.token, 'Content-Type': 'application/json'}
BATCH = f'https://sheets.googleapis.com/v4/spreadsheets/{DST}:batchUpdate'


def get(rng, sid=DST):
    u = f'https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/' + urllib.parse.quote(rng)
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=HDR), timeout=120).read()).get('values', [])


def put(rng, vals):
    u = (f'https://sheets.googleapis.com/v4/spreadsheets/{DST}/values/{urllib.parse.quote(rng)}'
         '?valueInputOption=RAW')
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(u, data=json.dumps({'values': vals}).encode(), headers=HDR, method='PUT'),
        timeout=120).read())


def batch(reqs):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(BATCH, data=json.dumps({'requests': reqs}).encode(),
                               headers=HDR, method='POST'), timeout=120).read())


def colname(n):  # 1-based
    s = ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def main():
    dry = '--dry' in sys.argv
    src = json.load(open(f'{D}/products_src.json'))
    cands = json.load(open(f'{D}/lp_candidates.json'))
    src = [r + [''] * (29 - len(r)) for r in src]
    src.sort(key=lambda r: (r[3].strip().lower() != 'pelatihan', r[2].strip().lower(), r[5].strip().lower()))

    probe = json.load(open(f'{D}/src_url_probe.json'))
    rows = []
    for i, r in enumerate(src, 1):
        url = r[24].strip()
        st = probe.get(url, [None])[0] if url else None
        kw1 = kw2 = ''
        if url:
            path = urllib.parse.urlparse(url).path.rstrip('/') or '/'
            c = cands.get(path)
            if c:
                g = c['gsc']
                kw1 = g[0]['q']
                kw2 = g[1]['q'] if len(g) > 1 else ''
        if not kw1:
            # produk tidak ada di crawl LP: keyword utama = nama produk (lower),
            # diprefix 'pelatihan ' kalau jenis Pelatihan dan belum ada kata training
            nm = re.sub(r'\s+', ' ', r[5]).strip().lower()
            kw1 = nm if re.search(r'pelatihan|training|sertifikasi|kursus', nm) or r[3].strip().lower() != 'pelatihan' else 'pelatihan ' + nm
        rows.append([i, r[5].strip(), kw1, kw2, url, '', '', 'Aktif' if st == 200 else 'Draft'])
    n = len(rows)
    last = 4 + n
    print(f'{n} produk; {sum(1 for r in rows if r[4])} punya URL LP; kw terisi {sum(1 for r in rows if r[2])}')
    if dry:
        json.dump(rows, open(f'{D}/tracker_rows.json', 'w'), indent=1, ensure_ascii=False)
        return

    # unmerge merge di area data tracker (baris >=5, kolom A..H)
    m = json.loads(urllib.request.urlopen(urllib.request.Request(
        f'https://sheets.googleapis.com/v4/spreadsheets/{DST}?fields=sheets.merges', headers=HDR),
        timeout=120).read())
    reqs = [{'unmergeCells': {'range': mm}} for s in m['sheets']
            for mm in (s.get('merges') or [])
            if mm['sheetId'] == SID and mm['startRowIndex'] >= 4 and mm['startColumnIndex'] < 8]
    if reqs:
        batch(reqs)
        print(f'unmerged {len(reqs)} merge(s) di area data')

    # pastikan kolom cukup untuk blok detail (mulai kolom 221, 29 kolom -> 249)
    meta = json.loads(urllib.request.urlopen(urllib.request.Request(
        f'https://sheets.googleapis.com/v4/spreadsheets/{DST}?fields=sheets.properties',
        headers=HDR), timeout=120).read())
    cc = 0
    for s in meta['sheets']:
        if s['properties']['sheetId'] == SID:
            cc = s['properties']['gridProperties']['columnCount']
    if cc < 250:
        batch([{'appendDimension': {'sheetId': SID, 'dimension': 'COLUMNS', 'length': 250 - cc}}])
        print(f'added {250-cc} columns (was {cc})')

    put(f'{TAB}!A1:B2', [['LP TRACKER — SYNERGY SOLUSI — PRODUK (dari file Produk)'],
                         ['Brand: Synergy Solusi  |  Sumber: sheet Produk (133 item Pelatihan+Konsultasi)  |  Detail produk ada di kolom HM dst (kanan grid mingguan)']])
    put(f'{TAB}!A5:H{last}', rows)
    blank = [[''] * 8 for _ in range(220 - last)]
    if blank:
        put(f'{TAB}!A{last+1}:H220', blank)
    put(f'{TAB}!A{last+1}', [[NOTE]])

    # blok detail 29 kolom: header row 3, data rows 5..last
    c0 = colname(221)
    c1 = colname(221 + 28)
    put(f'{TAB}!{c0}3:{c1}3', [get('A1:AE1', SRC)[0]])
    put(f'{TAB}!{c0}5:{c1}{last}', src)
    print(f'detail block {c0}3:{c1}{last}')

    got = get(f'{TAB}!A5:H{last}')
    mm = [i + 5 for i, (w, h) in enumerate(zip(rows, got))
          if [str(x) for x in w] != [str(x) for x in h] + [''] * (8 - len(h))]
    print(f'wrote {n} rows | readback {len(got)} | mismatch {mm if mm else "none"}')


main()
