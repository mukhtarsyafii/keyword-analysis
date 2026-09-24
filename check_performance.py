import csv

with open('/Users/mukhtarsyafii/.gemini/antigravity/brain/c6c68bbe-3cc9-4b15-b1f6-efcac2aafc9c/.system_generated/steps/2/content.md') as f:
    lines = f.readlines()

csv_lines = [l for l in lines if l.startswith('No,Nama') or any(c.isdigit() for c in l[:4])]

# Let's inspect header weeks
reader = csv.reader(lines)
rows = list(reader)

# Find header
h1 = None
h2 = None
data_rows = []
for r in rows:
    if r and r[0] == 'No' and 'Nama LP / Halaman' in r[1]:
        h1 = r
    elif h1 and not h2 and 'Impr' in r[13]:
        h2 = r
    elif h2 and r and r[0].isdigit():
        data_rows.append(r)

print("Total data rows:", len(data_rows))

# Let's map week columns
weeks = []
for col_idx in range(13, len(h1), 4):
    w_name = h1[col_idx] if col_idx < len(h1) else f"Col_{col_idx}"
    if w_name:
        weeks.append((w_name, col_idx))

print("Weeks detected:", len(weeks))
for w_name, idx in weeks[:10]:
    print(w_name, idx)
print("...")
for w_name, idx in weeks[-5:]:
    print(w_name, idx)

# Check which weeks have non-zero impressions
active_weeks = []
for w_name, idx in weeks:
    total_impr = 0
    total_clicks = 0
    for r in data_rows:
        if idx < len(r) and r[idx].replace('.', '', 1).isdigit():
            total_impr += float(r[idx])
        if idx+1 < len(r) and r[idx+1].replace('.', '', 1).isdigit():
            total_clicks += float(r[idx+1])
    if total_impr > 0 or total_clicks > 0:
        active_weeks.append((w_name, idx, total_impr, total_clicks))

print("\nActive weeks with data:")
for w, idx, impr, clicks in active_weeks:
    print(f"{w}: Impr = {impr}, Clicks = {clicks}")
