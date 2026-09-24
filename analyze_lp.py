import csv

with open('/Users/mukhtarsyafii/.gemini/antigravity/brain/c6c68bbe-3cc9-4b15-b1f6-efcac2aafc9c/.system_generated/steps/2/content.md') as f:
    lines = f.readlines()

# find header line
csv_lines = []
start = False
for line in lines:
    if line.startswith('No,Nama LP / Halaman'):
        start = True
    if start:
        csv_lines.append(line)

reader = csv.reader(csv_lines)
header1 = next(reader)
header2 = next(reader)

rows = []
for r in reader:
    if not r or not any(r):
        continue
    if r[0].startswith('💡') or r[0].startswith('Brand:'):
        continue
    rows.append(r)

print(f"Total rows: {len(rows)}")

products = []
for r in rows:
    if len(r) < 13:
        continue
    no = r[0].strip()
    name = r[1].strip()
    kw_utama = r[2].strip()
    vol_utama = r[3].strip()
    kw_target = r[4].strip()
    vol_target = r[5].strip()
    kw_info = r[6].strip()
    vol_info = r[7].strip()
    url = r[9].strip()
    tgl_live = r[10].strip()
    status = r[12].strip()
    
    # Let's see some metrics from recent weeks (e.g. around W30-W36)
    # columns are in groups of 4: Impr, Clicks, CTR, Rank
    # Let's inspect non-empty weekly metrics
    products.append({
        'no': no,
        'name': name,
        'kw_utama': kw_utama,
        'vol_utama': vol_utama,
        'kw_target': kw_target,
        'vol_target': vol_target,
        'kw_info': kw_info,
        'vol_info': vol_info,
        'url': url,
        'status': status,
        'raw_len': len(r)
    })

print(f"Parsed {len(products)} products:")
for p in products[:20]:
    print(f"#{p['no']} | {p['name']} | Status: {p['status']} | KW: {p['kw_utama']} ({p['vol_utama']}) | URL: {p['url']}")

print("\n--- Next batch ---")
for p in products[20:]:
    print(f"#{p['no']} | {p['name']} | Status: {p['status']} | KW: {p['kw_utama']} ({p['vol_utama']}) | URL: {p['url']}")
