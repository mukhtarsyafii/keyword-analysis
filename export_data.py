import csv
import json

with open('/Users/mukhtarsyafii/.gemini/antigravity/brain/c6c68bbe-3cc9-4b15-b1f6-efcac2aafc9c/.system_generated/steps/2/content.md') as f:
    lines = f.readlines()

reader = csv.reader(lines)
rows = list(reader)

h1, h2 = None, None
data_rows = []
for r in rows:
    if r and r[0] == 'No' and 'Nama LP / Halaman' in r[1]:
        h1 = r
    elif h1 and not h2 and 'Impr' in r[13]:
        h2 = r
    elif h2 and r and (r[0].isdigit() or (len(r) > 1 and r[1].strip())):
        data_rows.append(r)

weeks = []
for col_idx in range(13, len(h1), 4):
    w_name = h1[col_idx] if col_idx < len(h1) else f"Col_{col_idx}"
    if w_name and w_name.strip():
        # Short clean name: e.g. "W1 — Jan W1" -> "W1"
        clean_w = w_name.split('—')[0].strip()
        weeks.append((clean_w, col_idx))

print(f"Detected {len(weeks)} weeks. First 5: {[w[0] for w in weeks[:5]]}")

def categorize(name, kw):
    text = (name + " " + kw).lower()
    if 'bnsp' in text or 'qrmo' in text or 'qrma' in text or 'qcro' in text or 'qrgp' in text or 'cgp' in text or 'qrmp' in text or 'ccgo' in text or 'sertifikasi' in text:
        return 'Sertifikasi BNSP / Profesi'
    elif 'iso' in text or 'bcms' in text or '31000' in text or '37001' in text or '37301' in text or '22301' in text or '31022' in text or '9001' in text:
        return 'Standar ISO & Kepatuhan'
    elif 'fraud' in text or 'dokumen' in text or 'audit' in text or 'investigasi' in text or 'grafologi' in text or 'icofr' in text:
        return 'Audit, Fraud & Forensik'
    elif 'ai' in text or 'data' in text or 'analytics' in text:
        return 'AI & Data Governance'
    else:
        return 'Tata Kelola & BUMN'

parsed_products = []
auto_id = 1
for r in data_rows:
    raw_no = r[0].strip()
    name = r[1].strip() if len(r) > 1 else ''
    if not name:
        continue
    
    no = int(raw_no) if raw_no.isdigit() else auto_id
    auto_id = max(auto_id, no + 1)
    
    kw_utama = r[2].strip() if len(r) > 2 else ''
    vol_utama = r[3].strip() if len(r) > 3 else '-'
    kw_target = r[4].strip() if len(r) > 4 else ''
    vol_target = r[5].strip() if len(r) > 5 else '-'
    kw_info = r[6].strip() if len(r) > 6 else ''
    vol_info = r[7].strip() if len(r) > 7 else '-'
    url = r[9].strip() if len(r) > 9 else ''
    status = r[12].strip() if len(r) > 12 and r[12].strip() else 'Draft'
    
    weekly_data = []
    total_impr = 0
    total_clicks = 0
    ranks = []
    
    for w_name, idx in weeks:
        impr = 0
        clicks = 0
        rank = 0
        if idx < len(r) and r[idx].replace('.', '', 1).isdigit():
            impr = float(r[idx])
        if idx+1 < len(r) and r[idx+1].replace('.', '', 1).isdigit():
            clicks = float(r[idx+1])
        if idx+3 < len(r) and r[idx+3].replace('.', '', 1).isdigit():
            rank = float(r[idx+3])
        
        total_impr += impr
        total_clicks += clicks
        if rank > 0:
            ranks.append(rank)
            
        weekly_data.append({
            'week': w_name,
            'impr': int(impr),
            'clicks': int(clicks),
            'rank': round(rank, 1)
        })
        
    avg_rank = round(sum(ranks)/len(ranks), 1) if ranks else 0
    latest_rank = round(ranks[-1], 1) if ranks else 0
    ctr = round((total_clicks / total_impr * 100), 2) if total_impr > 0 else 0.0
    category = categorize(name, kw_utama + " " + kw_target)
    
    parsed_products.append({
        'id': no,
        'name': name,
        'category': category,
        'kw_utama': kw_utama or '-',
        'vol_utama': vol_utama or '-',
        'kw_target': kw_target or '-',
        'vol_target': vol_target or '-',
        'kw_info': kw_info or '-',
        'vol_info': vol_info or '-',
        'url': url,
        'status': status,
        'total_impr': int(total_impr),
        'total_clicks': int(total_clicks),
        'ctr': ctr,
        'avg_rank': avg_rank,
        'latest_rank': latest_rank,
        'weekly': weekly_data[:36]  # Active weeks up to W36
    })

print(f"Extracted {len(parsed_products)} products.")

# Export to json file in scratch
with open('/Users/mukhtarsyafii/.gemini/antigravity/scratch/products_data.json', 'w') as out:
    json.dump(parsed_products, out, indent=2)

print("Saved to scratch/products_data.json")
