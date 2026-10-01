#!/usr/bin/env python3
"""Rule engine: per-product diagnosis + fix drafts.

Reads data/products.json (+ optional data/competitors.json), writes
data/recommendations.json with, per product:
  masalah[]      - what is wrong, with the numbers that prove it
  solusi[]       - what to do about it
  rekomendasi[]  - prioritised actions
  perbaikan      - ready-to-paste fixes (meta title, meta desc, FAQ schema, H2 outline)
  prioritas      - 1..5 score for sorting the Aksi column
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

YEAR = "2026"
DEFAULT_BRAND = "GRC Indonesia"
DEFAULT_AUDIENCE = ("Manajer risiko, auditor internal, compliance officer, dan tim tata kelola "
                    "yang bertanggung jawab atas kepatuhan organisasi.")


def load(name, default):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


# Brand copy (name + who the training is for) comes from data/brands_config.json,
# so adding a brand is a config edit, not a code edit.
BRAND_CFG = {b["brand"]: b for b in load("brands_config.json", [])}


def brand_of(p):
    return p.get("brand") or DEFAULT_BRAND


def audience_of(p):
    return BRAND_CFG.get(brand_of(p), {}).get("audience") or DEFAULT_AUDIENCE


def meta_title(p):
    """<=60 chars, keyword first, brand last."""
    kw = p["kw_utama"].strip()
    if kw in ("-", ""):
        kw = p["name"]
    kw = kw[:1].upper() + kw[1:]
    suffix = f" - {brand_of(p)}"
    budget = 60 - len(suffix)
    if len(kw) > budget:
        kw = kw[: budget - 1].rstrip() + "…"
    return f"{kw}{suffix}"


def meta_desc(p):
    """<=155 chars, benefit + proof + CTA."""
    kw = p["kw_target"] if p["kw_target"] not in ("-", "") else p["kw_utama"]
    if kw in ("-", ""):
        kw = p["name"]
    base = f"{kw} di {brand_of(p)}. Bersertifikat, trainer praktisi, jadwal {YEAR} tersedia."
    cta = " Konsultasi kebutuhan in-house sekarang."
    out = base + cta
    return out[:155]


def faq_schema(p):
    kw = p["kw_utama"] if p["kw_utama"] not in ("-", "") else p["name"]
    qs = [
        (f"Apa itu {kw}?",
         f"{kw} adalah program pelatihan {p['category']} dari {brand_of(p)} "
         f"yang membahas praktik dan penerapan di perusahaan."),
        (f"Siapa yang perlu mengikuti {kw}?", audience_of(p)),
        (f"Apakah {kw} bersertifikat?",
         "Ya. Program tersedia dalam skema bersertifikat BNSP maupun in-house training "
         "sesuai kebutuhan perusahaan."),
        ("Bagaimana cara mendaftar?",
         f"Hubungi tim {brand_of(p)} melalui formulir di halaman ini atau WhatsApp untuk "
         "jadwal kelas terdekat dan penawaran in-house."),
    ]
    items = [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in qs
    ]
    return json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items},
        indent=2, ensure_ascii=False)


def h2_outline(p):
    kw = p["kw_utama"] if p["kw_utama"] not in ("-", "") else p["name"]
    info = p["kw_info"] if p["kw_info"] not in ("-", "") else f"apa itu {kw.lower()}"
    return [
        f"Apa Itu {kw} dan Mengapa Penting bagi Perusahaan",
        f"Manfaat {kw} untuk Kepatuhan dan Tata Kelola",
        f"Materi dan Silabus {kw}",
        f"Siapa yang Wajib Mengikuti {kw}",
        f"Jadwal, Durasi, dan Metode Pelatihan",
        f"Sertifikasi dan Pengakuan {kw}",
        f"Studi Kasus Penerapan di Perusahaan",
        f"FAQ: {info.capitalize()}",
        f"Daftar dan Konsultasi In-House Training",
    ]


def diagnose(p, comp):
    masalah, solusi, rekomendasi = [], [], []
    impr, clicks, ctr = p["total_impr"], p["total_clicks"], p["ctr"]
    rank = p["latest_rank"]
    live = p["status"].lower() == "aktif"
    prio = 1

    # --- status ---
    if not live:
        masalah.append("Halaman masih DRAFT — belum tayang, jadi 0 impresi dan 0 klik.")
        solusi.append("Terbitkan halaman sesuai silabus, lalu daftarkan URL ke Google "
                      "Search Console (Inspeksi URL → Minta Pengindeksan).")
        rekomendasi.append(f"Target volume keyword utama {p['vol_utama']}/bln belum "
                           "tertangkap sama sekali. Publish = prioritas tertinggi.")
        prio = 5
    elif not p["url"]:
        masalah.append("Status Aktif tetapi URL landing page kosong di tracker.")
        solusi.append("Isi URL live di tracker agar pemantauan GSC per halaman bisa jalan.")
        prio = max(prio, 4)

    # --- high impressions, low CTR ---
    if live and impr >= 800 and ctr < 2.0:
        masalah.append(
            f"Impresi tinggi ({impr:,}) tetapi CTR hanya {ctr}% — "
            f"{impr - clicks:,} tayangan tidak menghasilkan klik.")
        solusi.append("Rombak Meta Title & Meta Description: taruh keyword di depan, "
                      "tambahkan penanda sertifikasi dan tahun, akhiri dengan CTA.")
        rekomendasi.append("Pasang FAQ Schema agar muncul rich result dan memakan "
                           "lebih banyak ruang SERP.")
        rekomendasi.append("Cantumkan jadwal kelas terdekat di meta description — "
                           "pemicu klik terkuat untuk pelatihan B2B.")
        prio = 5

    # --- zero clicks despite impressions ---
    if live and impr >= 500 and clicks == 0:
        masalah.append(f"{impr:,} impresi, 0 klik. Snippet tidak meyakinkan sama sekali.")
        solusi.append("Tulis ulang meta description dengan angka konkret "
                      "(durasi, jumlah peserta, sertifikat) dan CTA eksplisit.")
        prio = 5

    # --- rank ---
    if live and rank and rank > 10:
        masalah.append(f"Posisi rata-rata #{rank} — masih di halaman 2+ Google.")
        solusi.append("Perkuat internal linking dari artikel informasional "
                      f"\"{p['kw_info']}\" ke halaman transaksional ini.")
        rekomendasi.append("Tambahkan 1 artikel pendukung per bulan yang menargetkan "
                           "keyword informasional terkait.")
        prio = max(prio, 3)
    elif live and rank and rank <= 3 and ctr < 3.0:
        masalah.append(f"Peringkat #{rank} (halaman 1 teratas) tetapi CTR {ctr}% — "
                       "posisi bagus terbuang karena snippet lemah.")
        solusi.append("Optimasi snippet saja sudah cukup; tidak perlu backlink baru.")
        prio = 5

    # --- top performer ---
    if live and clicks >= 50 and ctr >= 5.0:
        masalah.append("Tidak ada masalah kritis — halaman ini top performer.")
        solusi.append("Pertahankan: perbarui jadwal kelas, tambah testimoni alumni "
                      "korporat, dan pastikan CTA WhatsApp/form berfungsi.")
        rekomendasi.append("Jadikan halaman ini contoh template untuk 29 halaman draft.")
        prio = 1

    # --- competitor gap ---
    if comp:
        missing = [k for k in comp.get("competitor_keywords", [])
                   if k.get("we_rank") is None]
        if missing:
            top = ", ".join(k["keyword"] for k in missing[:3])
            masalah.append(f"Kompetitor menempati {len(missing)} keyword yang kita "
                           f"belum sentuh: {top}.")
            solusi.append("Buat section atau halaman turunan yang menargetkan keyword "
                          "tersebut, mulai dari volume terbesar.")
            prio = max(prio, 4)
        if comp.get("gap_summary"):
            rekomendasi.append(comp["gap_summary"])

    if not masalah:
        masalah.append("Belum ada anomali signifikan pada data periode ini.")
        solusi.append("Lanjutkan pemantauan mingguan.")

    return {
        "masalah": masalah,
        "solusi": solusi,
        "rekomendasi": rekomendasi,
        "perbaikan": {
            "meta_title": meta_title(p),
            "meta_description": meta_desc(p),
            "faq_schema": faq_schema(p),
            "h2_outline": h2_outline(p),
        },
        "prioritas": prio,
    }


def main():
    products = load("products.json", [])
    comps = load("competitors.json", {})
    out = {}
    for p in products:
        comp = comps.get(str(p["id"])) or comps.get(p["name"])
        out[str(p["id"])] = diagnose(p, comp)

    with open(os.path.join(DATA, "recommendations.json"), "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    from collections import Counter
    c = Counter(v["prioritas"] for v in out.values())
    print(f"wrote {len(out)} recommendations")
    print("prioritas:", dict(sorted(c.items(), reverse=True)))


if __name__ == "__main__":
    main()
