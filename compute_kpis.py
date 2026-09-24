import json

with open('/Users/mukhtarsyafii/.gemini/antigravity/scratch/products_data.json') as f:
    products = json.load(f)

total_impr = sum(p['total_impr'] for p in products)
total_clicks = sum(p['total_clicks'] for p in products)
active_count = sum(1 for p in products if p['status'] == 'Aktif')
draft_count = sum(1 for p in products if p['status'] == 'Draft')
avg_ctr = (total_clicks / total_impr * 100) if total_impr > 0 else 0

print(f"Total Products: {len(products)}")
print(f"Active: {active_count}, Draft: {draft_count}")
print(f"Total Impressions: {total_impr}")
print(f"Total Clicks: {total_clicks}")
print(f"Overall CTR: {avg_ctr:.2f}%")

# Aggregate weekly totals
weekly_totals = {}
for p in products:
    for w in p['weekly']:
        wk = w['week']
        if wk not in weekly_totals:
            weekly_totals[wk] = {'impr': 0, 'clicks': 0}
        weekly_totals[wk]['impr'] += w['impr']
        weekly_totals[wk]['clicks'] += w['clicks']

print("\nWeekly totals sample (first 10 and last 5):")
w_keys = list(weekly_totals.keys())
for k in w_keys[:10]:
    print(k, weekly_totals[k])
for k in w_keys[-5:]:
    print(k, weekly_totals[k])

# Categories count
cats = {}
for p in products:
    cats[p['category']] = cats.get(p['category'], 0) + 1
print("\nCategories:", cats)
