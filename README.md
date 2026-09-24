# Keyword & Produk Dashboard — GRC Indonesia

Dashboard kinerja SEO per landing page pelatihan. Data GSC + rekomendasi aksi + analisis kompetitor.

## Alur

```
GSC API (langsung)     ──> fetch_gsc.py   ──> data/products.json  (sumber utama)
Google Sheet tracker   ──> extract_sheet.py ─┘        │
Ubersuggest export     ──> data/competitors.json ─────┤
                                                      v
                                           recommend.py (rule engine)
                                                      │
                                                      v
                                           data/recommendations.json
                                                      │
                                                      v
                                           build_dashboard.py ──> dashboard.html
```

Satu perintah untuk refresh penuh dari GSC:
```bash
python3 refresh.py --start 2026-01-01 --end $(date +%F)   # histori lengkap
python3 refresh.py --weeks 12                              # refresh mingguan
```

## Perintah

```bash
python3 extract_sheet.py       # tarik Google Sheet tracker (public, tanpa auth)
python3 recommend.py           # generate Masalah/Solusi/Rekomendasi/Perbaikan
python3 build_dashboard.py     # render dashboard.html
python3 dashboard.py           # satu langkah: ketiganya berurutan
```

### Refresh mingguan otomatis (cron tiap Jumat 07:00)
```bash
hermes cron add --schedule "0 7 * * 5" --command "cd ~/Projects/keyword-analysis && python3 dashboard.py"
```

## Sumber data

| File | Sumber | Cara isi |
|---|---|---|
| `data/products.json` | Google Sheet LP Tracker | `extract_sheet.py` (otomatis) atau `fetch_gsc.py --merge` (GSC API) |
| `data/competitors.json` | Ekspor Ubersuggest | manual, lihat skema di bawah |
| `data/brands.json` | Tab Dashboard lintas brand | manual |
| `data/wp_config.json` | WordPress Application Password | manual, **gitignored** |

## GSC API langsung (pengganti Sheet)

Butuh OAuth client + scope `webmasters.readonly`:
```bash
GSETUP="python3 ~/.hermes/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --client-secret ~/Downloads/client_secret_xxx.json
$GSETUP --auth-url --services webmaster   # jika option belum ada, tambah scope manual
$GSETUP --auth-code "URL_YANG_DI_PASTE"
python3 fetch_gsc.py --check
python3 fetch_gsc.py --site sc-domain:grc-indonesia.com --weeks 36 --merge
```

## WordPress: perbaikan langsung

Buat Application Password: WP admin → Users → Profile → Application Passwords.
```bash
cat > data/wp_config.json <<'EOF'
{ "base_url": "https://grc-indonesia.com", "user": "USERNAME", "app_password": "xxxx xxxx xxxx xxxx" }
EOF
python3 push_wp.py --list
python3 push_wp.py --id 20 --dry-run
python3 push_wp.py --top 5
```
Hanya menulis `title` + Yoast meta. Tidak menyentuh isi halaman.

## Skema `data/competitors.json`

Key = product id (string). Ekspor Ubersuggest → kolom `Keyword`, `Volume`, `Difficulty`,
`Top URL/Site`, lalu petakan:

```json
{
  "13": {
    "source": "Ubersuggest — Agu 2026",
    "gap_summary": "3 kompetitor pegang keyword 'training icofr 2026' volume 720; kita belum ranking.",
    "competitor_keywords": [
      { "keyword": "training icofr bank", "volume": 720, "difficulty": 24,
        "top_competitor": "ajkacademy.com", "we_rank": null },
      { "keyword": "icofr certification", "volume": 390, "difficulty": 18,
        "top_competitor": "grc-indonesia.com", "we_rank": 9 }
    ]
  }
}
```
`we_rank: null` = celah (kita belum ranking) → masuk daftar Masalah di dashboard.

## Prioritas aksi

| P | Artinya |
|---|---|
| 5 | Darurat: draft belum tayang, impresi tinggi CTR <2%, rank ≤3 tapi CTR <3% |
| 4 | URL kosong di tracker, celah keyword kompetitor |
| 3 | Rank >10 (halaman 2+) — perlu internal linking |
| 1 | Sehat / top performer — pertahankan |
