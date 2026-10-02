# Keyword & Produk Dashboard — GRC Indonesia & IPQI

Dashboard kinerja SEO per landing page pelatihan, multi-brand (filter Brand di header).
Data GSC + rekomendasi aksi + analisis kompetitor.

**Live:** https://mukhtarsyafii.github.io/keyword-analysis/

> Repo ini **public**. Isinya data keyword, celah kompetitor, dan rekomendasi untuk
> grc-indonesia.com dan ipqi.org — siapa pun bisa membacanya. Kalau perlu ditutup, ubah ke private
> dan pindah hosting (Pages butuh repo public).

## Brand

Semua brand didaftarkan di `data/brands_config.json` — satu entri per brand:

```json
{ "brand": "IPQI", "gid": "1195768283", "domain": "ipqi.org",
  "property": "https://ipqi.org/", "id_base": 1000,
  "focus": "Continuous Improvement, Lean, 5S/5R, Kalibrasi",
  "audience": "Engineer produksi, supervisor shopfloor, tim QA/QC, ..." }
```

- `gid` = tab Google Sheet tracker brand itu (satu sheet, banyak tab `LP <Brand>`).
- `property` = URL GSC property (domain-level `sc-domain:` atau `https://.../`).
- `id_base` = basis ID produk (GRC 1.., IPQI 1001..) supaya key `recommendations.json`
  dan `competitors.json` tidak bentrok antar brand dan tidak berubah antar run.
- `audience` dipakai `recommend.py` untuk FAQ schema per brand.

Tambah brand baru = tambah entri di config + tab sheet + akses GSC, lalu `python3 refresh.py`.

## Alur

```
GSC API (semua brand)  ──> fetch_gsc.py   ──> data/products.json  (sumber utama)
Google Sheet tracker   ──> extract_sheet.py ─┘        │
GSC queries + Ubersuggest MCP ──> fetch_competitors.py ──> data/competitors.json
                                                      v
                                           recommend.py (rule engine)
                                                      │
                                                      v
                                           data/recommendations.json
                                                      │
                                                      v
                                           build_dashboard.py ──> dashboard.html
```

Satu perintah untuk refresh penuh (GSC + kompetitor + dashboard):
```bash
python3 refresh.py --start 2026-01-01 --end $(date +%F)   # histori lengkap
python3 refresh.py --weeks 12                              # refresh mingguan
python3 refresh.py --skip-competitors                      # GSC saja
python3 refresh.py --brand IPQI                            # intel kompetitor IPQI saja
```

## Perintah

```bash
python3 extract_sheet.py       # tarik semua tab LP di Google Sheet tracker (public, tanpa auth)
python3 fetch_gsc.py --check   # daftar property GSC yang bisa diakses token
python3 fetch_competitors.py   # keyword kompetitor via Ubersuggest MCP + GSC (per brand)
python3 recommend.py           # generate Masalah/Solusi/Rekomendasi/Perbaikan
python3 build_dashboard.py     # render dashboard.html
python3 dashboard.py           # satu langkah: ketiganya berurutan
node dashboard_smoke.js dashboard.html   # smoke test JS: render semua tab + filter brand
```

### Refresh mingguan otomatis (cron tiap Jumat 07:00)

Job Hermes `7d41e50037fa` menjalankan `~/.hermes/scripts/refresh_keyword_dashboard.sh`
dalam mode **`no_agent`** — stdout script dikirim apa adanya ke chat, tanpa LLM.

```
extract_sheet.py  →  fetch_gsc.py --merge  →  fetch_competitors.py
                  →  recommend.py  →  build_dashboard.py --standalone
                  →  git commit + push
```

`extract_sheet.py` jalan **pertama**: sheet tracker pemilik katalog (LP baru, keyword,
status), GSC pemilik performa. Script itu mempertahankan `weeks`/`daily` dari GSC yang
sudah ada, jadi katalog baru tidak menghapus data performa.

Push memicu GitHub Pages rebuild, jadi URL live ikut ter-update. Script mencetak
ringkasan (impresi, klik, CTR, prioritas 5, rentang data) yang diteruskan ke chat.

Kenapa `no_agent`: versi awal memakai agent untuk "menyampaikan ulang" output script,
dan job rutin gagal dengan `Response remained truncated after 4 continuation attempts`
padahal scriptnya sukses. Ringkasan sudah dicetak script, jadi LLM tidak diperlukan.

Kalau GSC timeout, `fetch_gsc.py` retry 3x; kalau tetap gagal, script melaporkan
error apa adanya dan **tidak** push — dashboard live tetap versi lama, bukan data rusak.
Kalau data tidak berubah, script keluar tanpa commit (perbandingan pada
`data/products.json` dkk, bukan pada HTML hasil build yang timestamp-nya selalu berubah).

Butuh mesin menyala saat Jumat 07:00. Kalau Mac mati, refresh terlewat — jalankan
manual: `bash ~/.hermes/scripts/refresh_keyword_dashboard.sh`

### Live di dashboard

Tombol **⟳ Refresh** dan **▶ Live 5 menit** di header memuat ulang `data/*.json`
dan me-render ulang tanpa reload halaman. Ini bekerja di URL GitHub Pages (http/https,
origin sama). Kalau `index.html` dibuka langsung dari disk (`file://`), browser memblokir
`fetch` dan tombolnya memberi pesan jelas alih-alih gagal diam-diam.

Batasnya: halaman ini statis. "Live" = mengambil JSON terbaru yang sudah di-push.
Data baru muncul setelah pipeline jalan (cron Jumat, atau manual). Tidak ada streaming
dari GSC/Ubersuggest langsung ke browser — API mereka butuh OAuth server-side.

### Live Chat AI (tombol ✦ kanan bawah)

Widget tanya-jawab soal data dashboard. Konteks (program, seri mingguan, rekomendasi,
celah kompetitor) dikirim klien dari JSON yang sudah dimuat, model menjawab dari angka itu.

- **Publik (github.io)**: POST `https://dashboard.digitalfinger.id/keyword-ai/chat`
  → FastAPI `keyword-ai` (port 8611, `/opt/keyword-ai/app.py`) → 9router → LLM.
  Key provider hanya ada di server, tidak pernah masuk repo. Header `X-Widget-Token`
  (nilai sudah public di repo) cuma remah biaya, bukan rahasia.
- **Lokal (localhost)**: langsung ke API server Hermes (`⚙` untuk endpoint + key,
  tersimpan di localStorage browser).
- `file://` → tombol disembunyikan (Origin null, CORS).

Catatan: fungsi Netlify `netlify/functions/ai-chat.mjs` tidak pernah ter-deploy
(site `keyword-analysis.netlify.app` 404 di path fungsi), jadi jalur proxy pindah ke
VPS. Kalau VPS mati, widget publik ikut mati — data dashboard tetap terbaca.

## Sumber data

| File | Sumber | Cara isi |
|---|---|---|
| `data/products.json` | Google Search Console API | `fetch_gsc.py --merge` (otomatis) |
| `data/competitors.json` | GSC queries + Ubersuggest MCP | `fetch_competitors.py` (otomatis) |
| `data/uber_cache.json` | cache respons Ubersuggest | otomatis, hemat kuota harian |
| `data/brands.json` | Tab Dashboard lintas brand | manual |
| `data/wp_config.json` | WordPress Application Password | manual, **gitignored** |

## Ubersuggest via MCP

Server MCP resmi: `https://ubersuggest-mcp.neilpatelapi.com/mcp` (OAuth, 58 tools).
Terdaftar di Hermes sebagai `ubersuggest`; token di `~/.hermes/mcp-tokens/ubersuggest.json`.

```bash
hermes mcp test ubersuggest
python3 uber_client.py --list                       # daftar tool
python3 uber_client.py auth_status '{}'
python3 uber_client.py competitors '{"domain":"grc-indonesia.com","language":"id","locId":2360}'
```

`uber_client.py` = klien MCP minimal (stdlib) yang memakai token OAuth Hermes, supaya
script pipeline bisa memanggil Ubersuggest tanpa lewat agen.

Catatan: `oauth.cimd: false` wajib di config server ini — server Ubersuggest menolak
Client ID Metadata Document Hermes, jadi pakai dynamic client registration.

## GSC API langsung (pengganti Sheet)

Butuh OAuth client + scope `webmasters.readonly`:
```bash
python3 oauth_gsc_only.py      # server callback lokal di :8765, sekali saja
python3 fetch_gsc.py --check   # daftar property yang bisa diakses token
python3 fetch_gsc.py --weeks 36 --merge          # semua brand di brands_config.json
python3 fetch_gsc.py --site https://ipqi.org/ --weeks 36 --merge   # satu property
```

Token lama bisa dicabut Google (error `invalid_grant` / HTTP 400 saat refresh) —
jalankan `oauth_gsc_only.py` lagi, buka URL yang dicetak, lalu Allow.

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

Diisi otomatis oleh `fetch_competitors.py`. Key = product id (string).

```json
{
  "13": {
    "product_name": "Training ICOFR",
    "source": "GSC queries + Ubersuggest SERP (id/Indonesia)",
    "competitor_keywords": [
      { "keyword": "training icofr bank", "volume": 720, "difficulty": 24,
        "top_competitor": "ajkacademy.com", "top_position": 1, "we_rank": null },
      { "keyword": "icofr certification", "volume": 390, "difficulty": 18,
        "top_competitor": "metricstream.com", "top_position": 3, "we_rank": 9 }
    ]
  }
}
```
`we_rank: null` = kita belum ranking; kalau `we_rank > top_position` = kalah posisi.
Keduanya dihitung sebagai GAP di tab Kompetitor.

## Prioritas aksi

| P | Artinya |
|---|---|
| 5 | Darurat: draft belum tayang, impresi tinggi CTR <2%, rank ≤3 tapi CTR <3% |
| 4 | URL kosong di tracker, celah keyword kompetitor |
| 3 | Rank >10 (halaman 2+) — perlu internal linking |
| 1 | Sehat / top performer — pertahankan |
