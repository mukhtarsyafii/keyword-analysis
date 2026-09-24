import json

with open('/Users/mukhtarsyafii/.gemini/antigravity/scratch/products_data.json') as f:
    products = json.load(f)

# Cross brand data from Dashboard tab
brands_data = [
    {"brand": "GRC Indonesia", "active_lp": 25, "impr": 713, "clicks": 25, "ctr": "3.51%", "focus": "Governance, Risk, Compliance, Fraud & ISO"},
    {"brand": "ISO Center", "active_lp": 24, "impr": 3324, "clicks": 96, "ctr": "2.89%", "focus": "Sistem Manajemen Mutu ISO (9001, 14001, 45001)"},
    {"brand": "Proxsis Academy", "active_lp": 21, "impr": 1202, "clicks": 13, "ctr": "1.08%", "focus": "Vokasi, Manajemen Bisnis & Leadership"},
    {"brand": "IPQI", "active_lp": 34, "impr": 518, "clicks": 8, "ctr": "1.54%", "focus": "Continuous Improvement, Lean, 5S/5R, Kalibrasi"},
    {"brand": "FS Institute", "active_lp": 8, "impr": 21, "clicks": 0, "ctr": "0.00%", "focus": "Food Safety, Keuangan Perbankan & Treasury"},
    {"brand": "ITGID", "active_lp": 12, "impr": 450, "clicks": 12, "ctr": "2.67%", "focus": "IT Governance, COBIT, Cybersecurity"},
    {"brand": "IMII", "active_lp": 6, "impr": 180, "clicks": 4, "ctr": "2.22%", "focus": "Maintenance, Asset Reliability & Plant Integrity"}
]

# Audits data
audit_items = [
    {
        "status": "MISMATCH", "severity": "HIGH", "brand": "GRC Indonesia", "row": 16,
        "name": "Training High Impact Report Audit Writing",
        "url": "https://grc-indonesia.com/training-high-impact-report-audit-writing/",
        "issue": "Judul & slug membahas audit writing, namun isi halaman web dan H2 berisi materi Training ISO 45001 (SMK3). Terjadi mismatch konten berat.",
        "action": "Segera ganti body konten dengan materi silabus Audit Writing, atau buat redirect 301 ke halaman yang benar."
    },
    {
        "status": "OPPORTUNITY", "severity": "HIGH", "brand": "GRC Indonesia", "row": 20,
        "name": "Training Sistem Manajemen Kepatuhan (ISO 37301)",
        "url": "https://grc-indonesia.com/pelatihan-sertifikasi-iso-37301-compliance/",
        "issue": "Mendapatkan 4.266 impresi dengan ranking rata-rata 3-5 di Google, namun menghasilkan 0 klik (CTR 0.00%).",
        "action": "Optimasi ulang Meta Title & Meta Description agar lebih click-worthy, cantumkan USP sertifikasi & tahun 2026."
    },
    {
        "status": "OPPORTUNITY", "severity": "MEDIUM", "brand": "GRC Indonesia", "row": 16,
        "name": "Sertifikasi QRMO BNSP",
        "url": "https://grc-indonesia.com/sertifikasi/qrmo-qualified-risk-management-officer/",
        "issue": "Impresi sangat besar (4.809) namun CTR hanya 0.75% (36 klik).",
        "action": "Tambahkan FAQ Schema, update jadwal kelas bulanan, dan perkuat snippet rich snippet di SERP."
    },
    {
        "status": "BROKEN", "severity": "HIGH", "brand": "GRC Indonesia", "row": 21,
        "name": "Pelatihan Integrasi ES-GRC",
        "url": "https://grc-indonesia.com/pelatihan-integrasi-es-grc-bersertifikat/",
        "issue": "URL sempat merespons HTTP 404 pada slug lama sebelum diperbarui.",
        "action": "Pastikan redirect 301 dari slug lama ke slug bersertifikat sudah permanen aktif."
    }
]

# Generate weekly totals for charting
weekly_chart = []
for i in range(1, 35):
    w_key = f"W{i}"
    tot_imp = 0
    tot_clk = 0
    for p in products:
        for w in p['weekly']:
            if w['week'] == w_key:
                tot_imp += w['impr']
                tot_clk += w['clicks']
    if tot_imp > 0 or tot_clk > 0:
        weekly_chart.append({"week": w_key, "impr": tot_imp, "clicks": tot_clk})

json_products = json.dumps(products)
json_brands = json.dumps(brands_data)
json_audits = json.dumps(audit_items)
json_weekly = json.dumps(weekly_chart)

print(f"Weekly chart points: {len(weekly_chart)}")
with open('/Users/mukhtarsyafii/.gemini/antigravity/scratch/data_prepared.json', 'w') as f:
    json.dump({
        "products": products,
        "brands": brands_data,
        "audits": audit_items,
        "weekly_chart": weekly_chart
    }, f)
print("Data prepared successfully.")
