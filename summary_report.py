import csv

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
    elif h2 and r and r[0].isdigit():
        data_rows.append(r)

weeks = []
for col_idx in range(13, len(h1), 4):
    w_name = h1[col_idx] if col_idx < len(h1) else f"Col_{col_idx}"
    if w_name:
        weeks.append((w_name, col_idx))

# Calculate total impressions, clicks, avg CTR, and latest rank for each product
summary = []
for r in data_rows:
    no = r[0]
    name = r[1]
    kw_utama = r[2]
    vol_utama = r[3]
    kw_target = r[4]
    vol_target = r[5]
    kw_info = r[6]
    vol_info = r[7]
    url = r[9]
    status = r[12]
    
    total_impr = 0
    total_clicks = 0
    ranks = []
    
    for w_name, idx in weeks:
        if idx < len(r) and r[idx].replace('.', '', 1).isdigit():
            total_impr += float(r[idx])
        if idx+1 < len(r) and r[idx+1].replace('.', '', 1).isdigit():
            total_clicks += float(r[idx+1])
        if idx+3 < len(r) and r[idx+3].replace('.', '', 1).isdigit():
            val = float(r[idx+3])
            if val > 0:
                ranks.append(val)
                
    avg_rank = sum(ranks)/len(ranks) if ranks else 0
    latest_rank = ranks[-1] if ranks else 0
    overall_ctr = (total_clicks / total_impr * 100) if total_impr > 0 else 0
    
    summary.append({
        'no': no,
        'name': name,
        'kw_utama': kw_utama,
        'vol_utama': vol_utama,
        'kw_target': kw_target,
        'kw_info': kw_info,
        'status': status,
        'total_impr': total_impr,
        'total_clicks': total_clicks,
        'ctr': overall_ctr,
        'avg_rank': avg_rank,
        'latest_rank': latest_rank,
        'url': url
    })

# Sort by total clicks descending
summary_sorted = sorted(summary, key=lambda x: x['total_clicks'], reverse=True)

print("TOP PRODUCTS BY CLICKS:")
print(f"{'No':<3} | {'Product Name':<45} | {'Impr':<7} | {'Clicks':<6} | {'CTR%':<6} | {'Rank':<5} | {'Status'}")
print("-" * 90)
for p in summary_sorted[:15]:
    print(f"{p['no']:<3} | {p['name'][:45]:<45} | {int(p['total_impr']):<7} | {int(p['total_clicks']):<6} | {p['ctr']:<6.2f}% | {p['latest_rank']:<5.1f} | {p['status']}")

print("\nREMAINING ACTIVE PRODUCTS:")
for p in summary_sorted[15:]:
    if p['status'] == 'Aktif':
        print(f"{p['no']:<3} | {p['name'][:45]:<45} | {int(p['total_impr']):<7} | {int(p['total_clicks']):<6} | {p['ctr']:<6.2f}% | {p['latest_rank']:<5.1f} | {p['status']}")

print(f"\nDRAFT PRODUCTS COUNT: {sum(1 for p in summary if p['status'] == 'Draft')}")
