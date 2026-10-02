#!/usr/bin/env python3
"""Build dashboard.html from data/*.json (single self-contained file).

Run: python3 build_dashboard.py
"""
import argparse, json, os, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "dashboard.html")


def load(name, default):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


HTML = r"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Kinerja Keyword &amp; Produk — GRC Indonesia</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  ::-webkit-scrollbar{width:6px;height:6px}
  ::-webkit-scrollbar-thumb{background:rgba(150,150,150,.3);border-radius:9999px}
  .badge{display:inline-flex;align-items:center;padding:.125rem .5rem;border-radius:9999px;font-size:.75rem;font-weight:500}
  .tab-btn.active{background:#3b82f6;color:#fff;border-color:transparent}
  .pill-btn.active{background:#3b82f6;color:#fff}
  .copy-btn{font-size:11px}
  pre.snippet{white-space:pre-wrap;word-break:break-word;font-size:11px;line-height:1.5}
  /* One shared tooltip, position:fixed so it escapes the tables' overflow-x-auto
     (an absolutely-positioned child would be clipped by the scroll container). */
  .th-info{display:inline-flex;align-items:center;justify-content:center;width:13px;height:13px;
    margin-left:4px;border-radius:9999px;border:1px solid rgba(148,163,184,.5);color:#94a3b8;
    font-size:9px;font-weight:700;line-height:1;cursor:help;vertical-align:middle;user-select:none}
  .th-info:hover{border-color:#60a5fa;color:#60a5fa}
  #tip{position:fixed;z-index:80;max-width:280px;padding:8px 10px;border-radius:8px;
    background:#0f172a;border:1px solid #334155;color:#e2e8f0;font-size:11px;line-height:1.5;
    box-shadow:0 8px 24px rgba(0,0,0,.5);pointer-events:none;opacity:0;transition:opacity .12s}
  #tip.on{opacity:1}
</style>
</head>
<body class="bg-slate-900 text-slate-100 antialiased p-4 sm:p-6 min-h-screen">
<div class="max-w-7xl mx-auto space-y-6">

  <header class="bg-slate-800 border border-slate-700 rounded-2xl p-5">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 mb-1 flex-wrap">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">GSC Live Tracker</span>
          <span class="text-xs text-slate-400" id="dataStamp">—</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight">Dashboard Kinerja Keyword &amp; Produk</h1>
        <p class="text-sm text-slate-400 mt-1" id="brandSubtitle">Matriks Impresi / Klik / CTR / Rank + Rekomendasi Aksi</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="text-right hidden sm:block">
          <div class="text-xs text-slate-400">Total Portofolio</div>
          <div class="text-lg font-bold" id="totalPortfolio">—</div>
        </div>
        <div class="flex flex-col items-end gap-1">
          <div class="flex items-center gap-2">
            <button onclick="liveRefresh(true)" class="px-3 py-2 text-xs font-medium rounded-lg border border-slate-700 hover:bg-slate-700" title="Muat ulang data tanpa reload">⟳ Refresh</button>
            <button onclick="toggleLive()" id="liveBtn" class="px-3 py-2 text-xs font-medium rounded-lg border border-slate-700 hover:bg-slate-700">▶ Live 5 menit</button>
          </div>
          <span class="text-[11px] text-slate-500" id="liveStatus"></span>
        </div>
        <button onclick="resetFilters()" class="px-3 py-2 text-xs font-medium rounded-lg border border-slate-700 hover:bg-slate-700">Reset Filter</button>
      </div>
    </div>
  </header>

  <div class="flex flex-wrap items-center gap-1.5 text-xs" id="brandBar"></div>

  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4" id="kpiRow"></div>

  <div class="flex flex-wrap items-center gap-2 border-b border-slate-700 pb-3">
    <button onclick="switchTab('matrix')" id="btn-tab-matrix" class="tab-btn active px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700">📊 Matriks Kinerja</button>
    <button onclick="switchTab('aksi')" id="btn-tab-aksi" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700 text-slate-400">🛠️ Aksi &amp; Perbaikan</button>
    <button onclick="switchTab('kompetitor')" id="btn-tab-kompetitor" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700 text-slate-400">🥊 Keyword Kompetitor</button>
    <button onclick="switchTab('tren')" id="btn-tab-tren" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700 text-slate-400">📈 Tren Harian/Mingguan/Bulanan</button>
    <button onclick="switchTab('brands')" id="btn-tab-brands" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700 text-slate-400">🌐 Lintas Brand</button>
  </div>

  <!-- MATRIX -->
  <div id="view-matrix" class="space-y-4">
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-4">
      <div class="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <div class="relative flex-1">
          <input type="text" id="searchInput" oninput="renderMatrix()" placeholder="Cari program, keyword utama, target keyword..." class="w-full pl-3 pr-4 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs sm:text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-slate-400 whitespace-nowrap">Urutkan:</span>
          <select id="sortSelect" onchange="renderMatrix()" class="px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs focus:outline-none">
            <option value="prio-desc">Prioritas Aksi (Tertinggi)</option>
            <option value="impr-desc">Impresi (Tertinggi)</option>
            <option value="clicks-desc">Klik (Tertinggi)</option>
            <option value="ctr-desc">CTR (Tertinggi)</option>
            <option value="ctr-asc">CTR (Terendah)</option>
            <option value="rank-asc">Rank Terbaik</option>
            <option value="name-asc">Nama (A-Z)</option>
          </select>
        </div>
      </div>
      <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-700">
        <div class="flex flex-wrap items-center gap-1.5 text-xs">
          <span class="text-slate-400 mr-1">Kategori:</span>
          <span id="catPills" class="contents"></span>
        </div>
        <div class="flex items-center gap-1.5 text-xs">
          <span class="text-slate-400 mr-1">Status:</span>
          <button onclick="setStatusFilter('all')" class="status-btn px-2 py-1 rounded border border-slate-700 bg-blue-600 text-white" data-status="all">Semua</button>
          <button onclick="setStatusFilter('Aktif')" class="status-btn px-2 py-1 rounded border border-slate-700 text-slate-400" data-status="Aktif">Aktif</button>
          <button onclick="setStatusFilter('Draft')" class="status-btn px-2 py-1 rounded border border-slate-700 text-slate-400" data-status="Draft">Draft</button>
        </div>
      </div>
    </div>

    <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs sm:text-sm">
          <thead class="bg-slate-900/70 text-slate-400 border-b border-slate-700">
            <tr>
              <th class="px-3 py-3 font-semibold w-10">#<i class="th-info" data-tip="Nomor urut program di sheet tracker brand masing-masing.">i</i></th>
              <th class="px-3 py-3 font-semibold min-w-[230px]">Program Layanan<i class="th-info" data-tip="Nama landing page / program pelatihan beserta URL live-nya. Satu program = satu halaman.">i</i></th>
              <th class="px-3 py-3 font-semibold min-w-[150px]">Kategori / Status<i class="th-info" data-tip="Kategori dikelompokkan otomatis dari nama program &amp; keyword utama. Status: Aktif = LP sudah live, Draft = belum tayang.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Impresi<i class="th-info" data-tip="Jumlah kali halaman muncul di hasil pencarian Google, di luar pencarian brand sendiri. Sumber: Google Search Console, kumulatif seluruh minggu yang tersedia.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Klik<i class="th-info" data-tip="Jumlah kunjungan dari hasil pencarian organik Google ke halaman tersebut. Sumber: Google Search Console.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">CTR<i class="th-info" data-tip="Click-Through Rate = Klik ÷ Impresi × 100%. Hijau ≥5%, biru ≥2%, merah kalau impresi &gt;1.000 tapi CTR &lt;1% (halaman muncul tapi jarang diklik).">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Rank<i class="th-info" data-tip="Posisi rata-rata halaman di Google pada minggu terakhir yang punya data. Angka kecil = makin dekat posisi #1. #11–#20 berarti halaman 2.">i</i></th>
              <th class="px-3 py-3 font-semibold text-center min-w-[90px]">Tren<i class="th-info" data-tip="Sparkline impresi mingguan. Hijau = minggu terakhir naik dibanding sebelumnya, merah = turun. Perlu minimal 2 minggu data.">i</i></th>
              <th class="px-3 py-3 font-semibold text-center w-24">Aksi<i class="th-info" data-tip="Buka detail Masalah, Solusi, Rekomendasi, dan Perbaikan siap-tempel (meta title, meta description, FAQ schema, outline H2).">i</i></th>
            </tr>
          </thead>
          <tbody id="matrixBody" class="divide-y divide-slate-700"></tbody>
        </table>
      </div>
      <div id="matrixEmpty" class="hidden p-8 text-center text-sm text-slate-400">Tidak ada produk yang cocok.</div>
      <div class="px-4 py-3 border-t border-slate-700 bg-slate-900/40 flex items-center justify-between text-xs text-slate-400">
        <span id="rowCountLabel">—</span>
        <span>Klik "Aksi" untuk Masalah, Solusi, Rekomendasi &amp; Perbaikan siap-tempel</span>
      </div>
    </div>
  </div>

  <!-- AKSI -->
  <div id="view-aksi" class="hidden space-y-4">
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <h2 class="text-lg font-bold text-amber-400">🛠️ Daftar Aksi — diurutkan berdasarkan prioritas</h2>
      <p class="text-xs text-slate-400 mt-1">Setiap kartu berisi <strong>Masalah</strong> (dengan angka bukti), <strong>Solusi</strong>, <strong>Rekomendasi</strong>, dan <strong>Perbaikan langsung</strong> (meta title, meta description, FAQ schema, outline H2) yang bisa disalin atau dikirim ke WordPress.</p>
    </div>
    <div class="space-y-3" id="aksiList"></div>
  </div>

  <!-- KOMPETITOR -->
  <div id="view-kompetitor" class="hidden space-y-4">
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <h2 class="text-lg font-bold text-sky-400">🥊 Analisis Keyword Kompetitor per Produk</h2>
      <p class="text-xs text-slate-400 mt-1">Sumber: ekspor Ubersuggest. Kolom <em>Posisi Kita</em> kosong berarti keyword tersebut belum kita sentuh sama sekali — itu celah yang harus diisi.</p>
    </div>
    <div id="kompetitorList" class="space-y-3"></div>
  </div>

  <!-- TREN -->
  <div id="view-tren" class="hidden space-y-6">
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 class="text-lg font-bold">Tren Trafik &amp; Posisi Keyword</h2>
          <p class="text-xs text-slate-400" id="trendSubtitle">Total impresi, klik &amp; rata-rata posisi seluruh landing page</p>
        </div>
        <div class="flex items-center gap-4 text-xs">
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-blue-500"></span> Impresi</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-400"></span> Klik</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-amber-400"></span> Posisi (skala terbalik)</span>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-1.5 text-xs pt-1 border-t border-slate-700">
        <span class="text-slate-400 mr-1">Periode:</span>
        <button onclick="setPeriod('daily')" class="pill-btn period-btn px-2.5 py-1 rounded-md border border-slate-700 text-slate-400" data-period="daily">Harian</button>
        <button onclick="setPeriod('weekly')" class="pill-btn period-btn active px-2.5 py-1 rounded-md border border-slate-700" data-period="weekly">Mingguan</button>
        <button onclick="setPeriod('monthly')" class="pill-btn period-btn px-2.5 py-1 rounded-md border border-slate-700 text-slate-400" data-period="monthly">Bulanan</button>
        <span class="text-slate-500 ml-auto" id="periodLabel">—</span>
      </div>
      <div class="flex flex-wrap items-center gap-2 text-xs">
        <span class="text-slate-400">Rentang tanggal:</span>
        <input type="date" id="dateFrom" onchange="applyDateRange()" class="px-2 py-1 rounded-md bg-slate-900 border border-slate-700 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500">
        <span class="text-slate-500">s/d</span>
        <input type="date" id="dateTo" onchange="applyDateRange()" class="px-2 py-1 rounded-md bg-slate-900 border border-slate-700 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500">
        <button onclick="setDatePreset(7)" class="px-2 py-1 rounded-md border border-slate-700 text-slate-400 hover:bg-slate-700">7 hari</button>
        <button onclick="setDatePreset(30)" class="px-2 py-1 rounded-md border border-slate-700 text-slate-400 hover:bg-slate-700">30 hari</button>
        <button onclick="setDatePreset(90)" class="px-2 py-1 rounded-md border border-slate-700 text-slate-400 hover:bg-slate-700">90 hari</button>
        <button onclick="clearDateRange()" class="px-2 py-1 rounded-md border border-slate-700 text-slate-400 hover:bg-slate-700">Semua</button>
      </div>
      <div class="w-full overflow-x-auto pt-4"><div class="min-w-[700px] h-72" id="chartContainer"></div></div>
    </div>

    <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <div class="p-4 border-b border-slate-700 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 class="text-sm font-bold">Pergerakan Posisi Keyword per Program</h3>
          <p class="text-xs text-slate-400 mt-0.5">Posisi awal vs akhir pada periode terpilih. <span class="text-emerald-400">Naik</span> = angka posisi mengecil (makin dekat #1).</p>
        </div>
        <span class="text-xs text-slate-500" id="rankPeriodLabel">—</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs sm:text-sm">
          <thead class="bg-slate-900/70 text-slate-400 border-b border-slate-700">
            <tr>
              <th class="px-3 py-3 font-semibold min-w-[220px]">Program<i class="th-info" data-tip="Program yang punya data posisi di periode terpilih. Diurutkan dari kenaikan posisi terbesar.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Posisi Awal<i class="th-info" data-tip="Posisi rata-rata pada titik pertama periode terpilih (minggu/bulan/hari paling awal).">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Posisi Akhir<i class="th-info" data-tip="Posisi rata-rata pada titik terakhir periode terpilih — kondisi terkini.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Δ Posisi<i class="th-info" data-tip="Selisih Posisi Awal − Posisi Akhir. ▲ hijau = naik (angka posisi mengecil, makin dekat #1). ▼ merah = turun.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Impresi<i class="th-info" data-tip="Total impresi program ini selama periode terpilih.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Klik<i class="th-info" data-tip="Total klik organik program ini selama periode terpilih.">i</i></th>
              <th class="px-3 py-3 font-semibold text-center">Tren<i class="th-info" data-tip="Garis posisi sepanjang periode. Sumbu dibalik: #1 di atas, posisi terburuk di bawah. Hijau = membaik, merah = memburuk.">i</i></th>
            </tr>
          </thead>
          <tbody id="rankMoveBody" class="divide-y divide-slate-700"></tbody>
        </table>
      </div>
      <div class="px-4 py-3 border-t border-slate-700 bg-slate-900/40 text-xs text-slate-400" id="rankMoveFoot">—</div>
    </div>

    <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <div class="p-4 border-b border-slate-700 space-y-3">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h3 class="text-sm font-bold">🆚 Perbandingan Dua Rentang Tanggal</h3>
            <p class="text-xs text-slate-400 mt-0.5">Metrik per program: Periode B (baru) vs Periode A (dasar). <span class="text-emerald-400">▲</span> = membaik.</p>
          </div>
          <div class="flex flex-wrap gap-1.5 text-xs">
            <button onclick="setComparePreset(7)" class="px-2.5 py-1 rounded-md border border-slate-700 text-slate-400 hover:bg-slate-700">Minggu ini vs lalu</button>
            <button onclick="setComparePreset(30)" class="px-2.5 py-1 rounded-md border border-slate-700 text-slate-400 hover:bg-slate-700">30 hari vs 30 hari lalu</button>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-2 text-xs">
          <span class="badge bg-slate-700 text-slate-300">A</span>
          <input type="date" id="cmpAFrom" onchange="renderCompare()" class="px-2 py-1 rounded-md bg-slate-900 border border-slate-700 text-xs focus:outline-none">
          <span class="text-slate-500">s/d</span>
          <input type="date" id="cmpATo" onchange="renderCompare()" class="px-2 py-1 rounded-md bg-slate-900 border border-slate-700 text-xs focus:outline-none">
          <span class="badge bg-blue-500/20 text-blue-300">B</span>
          <input type="date" id="cmpBFrom" onchange="renderCompare()" class="px-2 py-1 rounded-md bg-slate-900 border border-slate-700 text-xs focus:outline-none">
          <span class="text-slate-500">s/d</span>
          <input type="date" id="cmpBTo" onchange="renderCompare()" class="px-2 py-1 rounded-md bg-slate-900 border border-slate-700 text-xs focus:outline-none">
          <select id="cmpSort" onchange="renderCompare()" class="px-2 py-1 rounded-md bg-slate-900 border border-slate-700 text-xs focus:outline-none ml-auto">
            <option value="dI">Urut: Δ Impresi</option>
            <option value="dC">Urut: Δ Klik</option>
            <option value="dR">Urut: Δ Posisi terbaik</option>
            <option value="ib">Urut: Impresi B</option>
            <option value="nm">Urut: Nama</option>
          </select>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs sm:text-sm">
          <thead class="bg-slate-900/70 text-slate-400 border-b border-slate-700">
            <tr>
              <th class="px-3 py-3 font-semibold min-w-[200px]">Program<i class="th-info" data-tip="Program yang punya data di salah satu dari dua rentang. Baris dengan '▲ baru' = dulu nol, sekarang ada.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Impresi A<i class="th-info" data-tip="Total impresi pada rentang A (periode dasar, yang lebih lama).">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Impresi B<i class="th-info" data-tip="Total impresi pada rentang B (periode pembanding, yang lebih baru).">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Δ Impr<i class="th-info" data-tip="Perubahan impresi B terhadap A dalam persen. ▲ hijau = naik.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Klik A<i class="th-info" data-tip="Total klik organik pada rentang A.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Klik B<i class="th-info" data-tip="Total klik organik pada rentang B.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Δ Klik<i class="th-info" data-tip="Perubahan klik B terhadap A dalam persen.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Posisi A<i class="th-info" data-tip="Posisi rata-rata Google selama rentang A.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Posisi B<i class="th-info" data-tip="Posisi rata-rata Google selama rentang B.">i</i></th>
              <th class="px-3 py-3 font-semibold text-right">Δ Posisi<i class="th-info" data-tip="A − B. ▲ hijau = posisi membaik (angka mengecil, makin dekat #1).">i</i></th>
            </tr>
          </thead>
          <tbody id="cmpBody" class="divide-y divide-slate-700"></tbody>
        </table>
      </div>
      <div class="px-4 py-3 border-t border-slate-700 bg-slate-900/40 text-xs text-slate-400" id="cmpFoot">—</div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-3">
        <h3 class="text-sm font-bold">Distribusi Klik per Kategori</h3>
        <div class="space-y-3 pt-2" id="categoryBars"></div>
      </div>
      <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-3">
        <h3 class="text-sm font-bold">Top 5 Keyword Konversi Klik</h3>
        <div class="divide-y divide-slate-700 text-xs" id="topKeywords"></div>
      </div>
    </div>
  </div>

  <!-- BRANDS -->
  <div id="view-brands" class="hidden space-y-4">
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <h2 class="text-lg font-bold">🌐 Snapshot Kinerja Lintas Brand</h2>
      <p class="text-xs text-slate-400 mt-1">Perbandingan performa organik mingguan antar brand.</p>
    </div>
    <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <table class="w-full text-left text-xs sm:text-sm">
        <thead class="bg-slate-900/70 text-slate-400 border-b border-slate-700">
          <tr>
            <th class="px-4 py-3 font-semibold">Brand / Unit Bisnis<i class="th-info" data-tip="Unit bisnis di bawah Proxsis Academy yang punya landing page sendiri.">i</i></th>
            <th class="px-4 py-3 font-semibold">Fokus<i class="th-info" data-tip="Bidang utama yang digarap brand tersebut.">i</i></th>
            <th class="px-4 py-3 font-semibold text-center">LP Aktif/Total<i class="th-info" data-tip="Jumlah landing page yang sudah live dibanding total program brand ini di tracker.">i</i></th>
            <th class="px-4 py-3 font-semibold text-right">Total Impresi<i class="th-info" data-tip="Kumulatif impresi organik seluruh landing page brand ini, dari Google Search Console. Klik baris untuk filter dashboard ke brand tersebut.">i</i></th>
            <th class="px-4 py-3 font-semibold text-right">Total Klik<i class="th-info" data-tip="Kumulatif klik organik seluruh landing page brand ini.">i</i></th>
            <th class="px-4 py-3 font-semibold text-right">Avg CTR<i class="th-info" data-tip="CTR rata-rata seluruh LP brand ini = total klik ÷ total impresi × 100%.">i</i></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-700" id="brandsBody"></tbody>
      </table>
    </div>
  </div>

</div>

<!-- MODAL -->
<div id="tip" role="tooltip"></div>

<!-- HERMES AI CHAT WIDGET -->
<button id="aiFab" aria-label="Buka chat Hermes AI" title="Tanya Hermes AI tentang data ini"
        class="fixed bottom-5 right-5 z-40 w-14 h-14 rounded-full bg-blue-600 hover:bg-blue-500 text-white text-2xl shadow-xl flex items-center justify-center">✦</button>
<div id="aiPanel" class="fixed bottom-5 right-5 z-50 hidden flex-col bg-slate-800 border border-slate-600 rounded-2xl shadow-2xl"
     style="width:min(400px,calc(100vw - 24px));height:min(560px,calc(100vh - 24px))">
  <div class="flex items-center gap-2 px-4 py-3 border-b border-slate-700">
    <span id="aiDot" class="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
    <div class="font-semibold text-sm text-slate-100">Hermes AI <span class="text-slate-400 font-normal">• asisten dashboard</span></div>
    <button id="aiClear" class="text-slate-400 hover:text-white text-xs px-1" title="Mulai percakapan baru">reset</button>
    <button id="aiCfg" class="text-slate-400 hover:text-white text-xs px-1" title="Atur endpoint + API key">⚙</button>
    <button id="aiClose" class="ml-auto text-slate-400 hover:text-white text-lg px-1" aria-label="Tutup chat">×</button>
  </div>
  <div id="aiLog" class="flex-1 overflow-y-auto px-3 py-3 space-y-2 text-sm"></div>
  <div id="aiQuick" class="px-3 pb-2 flex flex-wrap gap-1.5"></div>
  <div class="flex gap-2 px-3 pb-3">
    <textarea id="aiInput" rows="1" placeholder="Tanya soal data dashboard…"
              class="flex-1 resize-none rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none"></textarea>
    <button id="aiSend" class="rounded-lg bg-blue-600 hover:bg-blue-500 px-3 text-sm font-medium text-white">Kirim</button>
  </div>
</div>
<div id="detailModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden items-center justify-center p-4">
  <div class="bg-slate-800 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-5">
    <div class="flex items-start justify-between gap-4 border-b border-slate-700 pb-4">
      <div>
        <div class="flex items-center gap-2 mb-1 flex-wrap" id="modalBadges"></div>
        <h3 class="text-xl font-bold" id="modalTitle"></h3>
        <a id="modalUrl" href="#" target="_blank" class="text-xs text-blue-400 hover:underline break-all block mt-1"></a>
      </div>
      <button onclick="closeModal()" class="p-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-700">✕</button>
    </div>

    <div class="grid grid-cols-4 gap-3 bg-slate-900/60 rounded-xl p-3 border border-slate-700">
      <div class="text-center"><div class="text-[10px] text-slate-400">Impresi<i class="th-info" data-tip="Total impresi halaman ini di Google Search Console sepanjang periode data.">i</i></div><div class="text-lg font-bold" id="mImpr">-</div></div>
      <div class="text-center"><div class="text-[10px] text-slate-400">Klik<i class="th-info" data-tip="Total klik organik Google ke halaman ini.">i</i></div><div class="text-lg font-bold text-blue-400" id="mClicks">-</div></div>
      <div class="text-center"><div class="text-[10px] text-slate-400">CTR<i class="th-info" data-tip="Click-Through Rate = Klik ÷ Impresi × 100%.">i</i></div><div class="text-lg font-bold text-emerald-400" id="mCtr">-</div></div>
      <div class="text-center"><div class="text-[10px] text-slate-400">Rank<i class="th-info" data-tip="Posisi rata-rata di Google pada minggu terakhir yang punya data.">i</i></div><div class="text-lg font-bold text-amber-400" id="mRank">-</div></div>
    </div>

    <div class="space-y-3">
      <div class="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4">
        <h5 class="text-xs font-bold text-rose-400 mb-1.5">🔴 MASALAH</h5>
        <ul class="text-xs space-y-1 list-disc list-inside" id="mMasalah"></ul>
      </div>
      <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
        <h5 class="text-xs font-bold text-emerald-400 mb-1.5">🟢 SOLUSI</h5>
        <ul class="text-xs space-y-1 list-disc list-inside" id="mSolusi"></ul>
      </div>
      <div class="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
        <h5 class="text-xs font-bold text-blue-400 mb-1.5">🎯 REKOMENDASI</h5>
        <ul class="text-xs space-y-1 list-disc list-inside" id="mRekomendasi"></ul>
      </div>
    </div>

    <div class="space-y-3">
      <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400">⚡ Perbaikan Langsung</h4>

      <div class="bg-slate-900 border border-slate-700 rounded-lg p-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[10px] font-semibold text-blue-400">META TITLE</span>
          <button class="copy-btn px-2 py-0.5 rounded border border-slate-600 hover:bg-slate-700" onclick="copyText('mMetaTitle',this)">Salin</button>
        </div>
        <div class="text-xs font-medium" id="mMetaTitle"></div>
        <div class="text-[10px] text-slate-500 mt-1" id="mMetaTitleLen"></div>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-lg p-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[10px] font-semibold text-emerald-400">META DESCRIPTION</span>
          <button class="copy-btn px-2 py-0.5 rounded border border-slate-600 hover:bg-slate-700" onclick="copyText('mMetaDesc',this)">Salin</button>
        </div>
        <div class="text-xs" id="mMetaDesc"></div>
        <div class="text-[10px] text-slate-500 mt-1" id="mMetaDescLen"></div>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-lg p-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[10px] font-semibold text-amber-400">OUTLINE H2</span>
          <button class="copy-btn px-2 py-0.5 rounded border border-slate-600 hover:bg-slate-700" onclick="copyText('mH2',this)">Salin</button>
        </div>
        <ol class="text-xs space-y-0.5 list-decimal list-inside" id="mH2"></ol>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-lg p-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[10px] font-semibold text-purple-400">FAQ SCHEMA (JSON-LD)</span>
          <button class="copy-btn px-2 py-0.5 rounded border border-slate-600 hover:bg-slate-700" onclick="copyText('mFaq',this)">Salin</button>
        </div>
        <pre class="snippet text-slate-300" id="mFaq"></pre>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-lg p-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-[10px] font-semibold text-slate-300">KIRIM KE WORDPRESS</span>
          <span class="text-[10px] text-slate-500" id="wpStatus">belum dikonfigurasi</span>
        </div>
        <div class="flex flex-wrap gap-2 mt-1">
          <button class="px-3 py-1.5 text-xs rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40" id="wpBtn" onclick="pushToWordPress()" disabled>Terapkan Meta ke WP</button>
          <span class="text-[10px] text-slate-500 self-center">Butuh Application Password WordPress (isi di wp_config.json)</span>
        </div>
      </div>
    </div>

    <div class="text-right pt-2 border-t border-slate-700">
      <button onclick="closeModal()" class="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-700 hover:bg-slate-600">Tutup</button>
    </div>
  </div>
</div>

<script>
const PRODUCTS = __PRODUCTS__;
const RECS = __RECS__;
const COMPETITORS = __COMPETITORS__;
const BRANDS = __BRANDS__;
const META = __META__;

let currentCategory = 'all', currentStatus = 'all', currentId = null;
let currentPeriod = 'weekly';   // daily | weekly | monthly
let currentBrand = 'all';       // brand filter drives every tab

// Rows in scope for the selected brand. All render functions read this, never
// PRODUCTS directly, so the whole dashboard follows one switch.
function brows(){
  return currentBrand==='all' ? PRODUCTS : PRODUCTS.filter(p=>p.brand===currentBrand);
}
function brandNames(){
  return [...new Set(PRODUCTS.map(p=>p.brand).filter(Boolean))];
}

const fmt = n => (n||0).toLocaleString('id-ID');
const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function rec(id){ return RECS[String(id)] || {masalah:[],solusi:[],rekomendasi:[],perbaikan:{},prioritas:1}; }

function init(){
  document.getElementById('dataStamp').textContent = META.stamp;
  document.getElementById('totalPortfolio').textContent = PRODUCTS.length + ' Program';
  renderBrandBar();
  const all = allDates();
  if (all.length){
    ['dateFrom','dateTo','cmpAFrom','cmpATo','cmpBFrom','cmpBTo'].forEach(id=>{
      const el = document.getElementById(id);
      el.min = all[0]; el.max = all[all.length-1];
    });
    setComparePreset(7);   // default: minggu ini vs minggu lalu
  }
  renderKPI(); renderMatrix(); renderAksi(); renderKompetitor(); renderTrends(); renderBrands();
}

function renderBrandBar(){
  const names = brandNames();
  const focus = {}; BRANDS.forEach(b=>focus[b.brand]=b.focus);
  document.getElementById('brandBar').innerHTML =
    '<span class="text-slate-400 mr-1">Brand:</span>' +
    ['all', ...names].map(b=>{
      const on = currentBrand===b;
      const label = b==='all' ? 'Semua Brand' : b;
      const n = b==='all' ? PRODUCTS.length : PRODUCTS.filter(p=>p.brand===b).length;
      return `<button onclick="setBrand('${esc(b)}')" class="pill-btn brand-btn px-3 py-1.5 rounded-lg border text-xs font-medium ${on?'active':'border-slate-700 text-slate-400 hover:bg-slate-700'}">${esc(label)} <span class="opacity-60">${n}</span></button>`;
    }).join('');
  const sub = currentBrand==='all'
    ? names.join(' • ') + ' • Matriks Impresi / Klik / CTR / Rank + Rekomendasi Aksi'
    : `${currentBrand} — ${focus[currentBrand]||''} • ${PRODUCTS.filter(p=>p.brand===currentBrand).length} LP`;
  document.getElementById('brandSubtitle').textContent = sub;
  document.getElementById('trendSubtitle').textContent =
    currentBrand==='all' ? 'Total impresi, klik & rata-rata posisi seluruh landing page'
                         : `Total impresi, klik & rata-rata posisi landing page ${currentBrand}`;
}

function setBrand(b){
  if (currentBrand===b) return;
  currentBrand = b;
  currentCategory = 'all';   // categories differ per brand
  renderBrandBar(); renderMatrix(); renderKPI(); renderAksi();
  renderKompetitor(); renderTrends(); renderCompare();
}

// Category pills follow the brand in scope — IPQI and GRC have different sets.
function renderCatPills(rows){
  const cats = [...new Set(rows.map(p=>p.category))].sort();
  document.getElementById('catPills').innerHTML =
    ['all', ...cats].map(c=>{
      const on = currentCategory===c;
      const label = c==='all' ? 'Semua' : c;
      return `<button onclick="setCategoryFilter('${esc(c).replace(/'/g,"\\'")}')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-slate-700 ${on?'active':'text-slate-400'}" data-cat="${esc(c)}">${esc(label)}</button>`;
    }).join('');
}

function renderKPI(){
  const P = brows();
  const impr = P.reduce((a,p)=>a+p.total_impr,0);
  const clicks = P.reduce((a,p)=>a+p.total_clicks,0);
  const ctr = impr ? (clicks/impr*100).toFixed(2) : 0;
  const aktif = P.filter(p=>p.status.toLowerCase()==='aktif').length;
  const top = [...P].sort((a,b)=>b.total_clicks-a.total_clicks)[0] || {};
  const needAction = P.filter(p=>rec(p.id).prioritas>=4).length;
  const cards = [
    ['Total Impresi Organik', fmt(impr), 'GSC kumulatif', 'text-slate-100',
     'Jumlah seluruh impresi organik dari Google Search Console, dijumlahkan untuk semua program dan semua minggu yang tersedia.'],
    ['Total Klik Organik', fmt(clicks), 'CTR rata-rata '+ctr+'%', 'text-blue-400',
     'Jumlah seluruh klik dari hasil pencarian organik Google. CTR rata-rata = total klik ÷ total impresi × 100%.'],
    ['Status Landing Page', aktif+' Aktif / '+(P.length-aktif)+' Draft', 'Target min 2 LP baru/mgg', 'text-slate-100',
     'Aktif = landing page sudah live dan terindeks Google. Draft = sudah dibuat tapi belum tayang. Target tim: minimal 2 LP baru per minggu.'],
    ['Perlu Tindakan', needAction+' Program', 'Prioritas aksi tinggi', 'text-amber-400',
     'Program dengan prioritas aksi 4 atau 5 — masalahnya paling mendesak (mis. impresi tinggi tapi CTR rendah, atau posisi masih di halaman 2+).'],
  ];
  document.getElementById('kpiRow').innerHTML = cards.map(([t,v,s,c,tip])=>`
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div class="text-xs font-medium text-slate-400 mb-1">${t}<i class="th-info" data-tip="${esc(tip)}">i</i></div>
      <div class="text-2xl sm:text-3xl font-extrabold ${c}">${v}</div>
      <div class="text-[10px] text-slate-500 mt-1">${s}</div>
    </div>`).join('') + `
    <div class="bg-slate-800 border border-emerald-500/30 rounded-xl p-4 col-span-2 lg:col-span-4">
      <div class="text-xs font-medium text-slate-400 mb-1">Top Star Performer<i class="th-info" data-tip="Program dengan klik organik terbanyak sepanjang periode data — tolok ukur yang bisa ditiru program lain.">i</i></div>
      <div class="text-base font-bold text-emerald-400">${esc(top.name||'-')}</div>
      <div class="text-xs text-slate-300 mt-1">${fmt(top.total_clicks)} Klik • CTR ${top.ctr||0}% • Rank #${top.latest_rank||'-'}</div>
    </div>`;
}

function sparkline(p){
  const w = p.weeks.filter(x=>x.impr||x.clicks);
  if (w.length < 2) return '<span class="text-slate-600 text-[10px]">—</span>';
  const W=80,H=22,pad=2;
  const maxI = Math.max(...w.map(x=>x.impr),1);
  const pts = w.map((x,i)=>{
    const px = pad + i/(w.length-1)*(W-pad*2);
    const py = H-pad - (x.impr/maxI)*(H-pad*2);
    return px.toFixed(1)+','+py.toFixed(1);
  }).join(' ');
  const last = w[w.length-1], prev = w[w.length-2];
  const up = last.impr >= prev.impr;
  return `<svg width="${W}" height="${H}" class="inline-block"><polyline fill="none" stroke="${up?'#34d399':'#fb7185'}" stroke-width="1.5" points="${pts}"/></svg>`;
}

function renderMatrix(){
  const q = document.getElementById('searchInput').value.toLowerCase().trim();
  const sortVal = document.getElementById('sortSelect').value;
  const tbody = document.getElementById('matrixBody');
  const empty = document.getElementById('matrixEmpty');

  const scoped = brows();
  renderCatPills(scoped);
  let rows = scoped.filter(p=>{
    const mc = currentCategory==='all' || p.category===currentCategory;
    const ms = currentStatus==='all' || p.status.toLowerCase()===currentStatus.toLowerCase();
    const mq = !q || [p.name,p.kw_utama,p.kw_target,p.kw_info].join(' ').toLowerCase().includes(q);
    return mc && ms && mq;
  });

  rows.sort((a,b)=>{
    const ra=rec(a.id), rb=rec(b.id);
    if (sortVal==='prio-desc') return rb.prioritas-ra.prioritas || b.total_impr-a.total_impr;
    if (sortVal==='impr-desc') return b.total_impr-a.total_impr;
    if (sortVal==='clicks-desc') return b.total_clicks-a.total_clicks;
    if (sortVal==='ctr-desc') return b.ctr-a.ctr;
    if (sortVal==='ctr-asc') return a.ctr-b.ctr;
    if (sortVal==='rank-asc') return (a.latest_rank||999)-(b.latest_rank||999);
    return a.name.localeCompare(b.name);
  });

  if (!rows.length){ tbody.innerHTML=''; empty.classList.remove('hidden'); document.getElementById('rowCountLabel').textContent='Menampilkan 0 program'; return; }
  empty.classList.add('hidden');
  document.getElementById('rowCountLabel').textContent = `Menampilkan ${rows.length} dari ${scoped.length} program`;

  tbody.innerHTML = rows.map(p=>{
    const live = p.status.toLowerCase()==='aktif';
    const badge = live
      ? '<span class="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Aktif</span>'
      : '<span class="badge bg-amber-500/10 text-amber-400 border border-amber-500/20">Draft</span>';
    let ctrColor='text-slate-400';
    if (p.ctr>=5) ctrColor='text-emerald-400 font-bold';
    else if (p.ctr>=2) ctrColor='text-blue-400 font-semibold';
    else if (p.total_impr>1000 && p.ctr<1) ctrColor='text-rose-400 font-semibold';
    const pr = rec(p.id).prioritas;
    const PR_TIP = 'Prioritas aksi: P5 = mendesak (impresi besar tapi CTR rendah / posisi halaman 3+), P4 = perlu perbaikan on-page, P3 = optimasi lanjutan, P1 = sehat, tidak ada tindakan mendesak.';
    const prBadge = pr>=5 ? `<span class="badge bg-rose-500/20 text-rose-300">P5<i class="th-info" data-tip="${PR_TIP}">i</i></span>`
                  : pr>=4 ? `<span class="badge bg-amber-500/20 text-amber-300">P4<i class="th-info" data-tip="${PR_TIP}">i</i></span>`
                  : pr>=3 ? `<span class="badge bg-blue-500/20 text-blue-300">P3<i class="th-info" data-tip="${PR_TIP}">i</i></span>`
                  : `<span class="badge bg-slate-600/40 text-slate-400">P1<i class="th-info" data-tip="${PR_TIP}">i</i></span>`;
    return `<tr class="hover:bg-slate-700/30">
      <td class="px-3 py-3 text-slate-500 font-mono text-xs">${p.id}</td>
      <td class="px-3 py-3">
        <div class="font-medium">${esc(p.name)}</div>
        ${p.url?`<a href="${esc(p.url)}" target="_blank" class="text-[11px] text-blue-400/80 hover:text-blue-300 truncate block max-w-xs">${esc(p.url)}</a>`:'<span class="text-[10px] text-amber-400/70 italic">Belum ada URL live</span>'}
      </td>
      <td class="px-3 py-3"><div class="text-xs text-slate-400">${esc(p.category)}</div>${currentBrand==='all'&&p.brand?`<div class="text-[10px] text-sky-400/80 font-semibold mt-0.5">${esc(p.brand)}</div>`:''}<div class="mt-1 flex gap-1">${badge}${prBadge}</div></td>
      <td class="px-3 py-3 text-right font-mono text-xs">${fmt(p.total_impr)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs font-semibold text-blue-400">${p.total_clicks}</td>
      <td class="px-3 py-3 text-right font-mono text-xs ${ctrColor}">${p.ctr}%</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${p.latest_rank>0?`<span class="text-amber-300">#${p.latest_rank}</span>`:'<span class="text-slate-500">-</span>'}</td>
      <td class="px-3 py-3 text-center">${sparkline(p)}</td>
      <td class="px-3 py-3 text-center">
        <button onclick="openModal(${p.id})" class="px-2.5 py-1 text-xs font-medium rounded border border-blue-500/40 text-blue-400 hover:bg-blue-500/10">Aksi</button>
      </td>
    </tr>`;
  }).join('');
}

function renderAksi(){
  const rows = [...brows()].sort((a,b)=>rec(b.id).prioritas-rec(a.id).prioritas || b.total_impr-a.total_impr);
  document.getElementById('aksiList').innerHTML = rows.map(p=>{
    const r = rec(p.id);
    const pr = r.prioritas;
    const border = pr>=5?'border-rose-500/40':pr>=4?'border-amber-500/40':pr>=3?'border-blue-500/40':'border-slate-700';
    return `<div class="bg-slate-800 border ${border} rounded-xl p-4 space-y-3">
      <div class="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="badge ${pr>=5?'bg-rose-500/20 text-rose-300':pr>=4?'bg-amber-500/20 text-amber-300':pr>=3?'bg-blue-500/20 text-blue-300':'bg-slate-600/40 text-slate-400'}">Prioritas ${pr}</span>
            <span class="badge bg-slate-700 text-slate-300">${esc(p.category)}</span>
            <span class="badge ${p.status.toLowerCase()==='aktif'?'bg-emerald-500/10 text-emerald-400':'bg-amber-500/10 text-amber-400'}">${esc(p.status)}</span>
          </div>
          <h4 class="font-bold mt-1.5">${esc(p.name)}</h4>
          <div class="text-[11px] text-slate-400 font-mono mt-0.5">Impr ${fmt(p.total_impr)} • Klik ${p.total_clicks} • CTR ${p.ctr}% • Rank #${p.latest_rank||'-'}</div>
        </div>
        <button onclick="openModal(${p.id})" class="px-3 py-1.5 text-xs rounded-lg bg-blue-600 hover:bg-blue-500">Buka Perbaikan</button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
        <div class="bg-rose-500/10 border border-rose-500/20 rounded-lg p-3">
          <div class="text-[10px] font-bold text-rose-400 mb-1">MASALAH</div>
          <ul class="space-y-1 list-disc list-inside text-slate-200">${r.masalah.map(m=>`<li>${esc(m)}</li>`).join('')}</ul>
        </div>
        <div class="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3">
          <div class="text-[10px] font-bold text-emerald-400 mb-1">SOLUSI</div>
          <ul class="space-y-1 list-disc list-inside text-slate-200">${r.solusi.map(m=>`<li>${esc(m)}</li>`).join('')}</ul>
        </div>
        <div class="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
          <div class="text-[10px] font-bold text-blue-400 mb-1">REKOMENDASI</div>
          <ul class="space-y-1 list-disc list-inside text-slate-200">${r.rekomendasi.length?r.rekomendasi.map(m=>`<li>${esc(m)}</li>`).join(''):'<li class="text-slate-500">—</li>'}</ul>
        </div>
      </div>
    </div>`;
  }).join('');
}

function renderKompetitor(){
  const el = document.getElementById('kompetitorList');
  const keys = Object.keys(COMPETITORS||{}).filter(k=>{
    if (currentBrand==='all') return true;
    const p = PRODUCTS.find(x=>String(x.id)===String(k));
    return (p||{}).brand===currentBrand || COMPETITORS[k].brand===currentBrand;
  });
  if (!keys.length){
    el.innerHTML = `<div class="bg-slate-800 border border-slate-700 rounded-xl p-6 text-center text-sm text-slate-400">
      Belum ada data kompetitor. Jalankan <code class="text-blue-400">python3 fetch_competitors.py</code>
      (Ubersuggest MCP + GSC) lalu bangun ulang dashboard.
    </div>`;
    return;
  }
  el.innerHTML = keys.map(k=>{
    const c = COMPETITORS[k];
    const p = PRODUCTS.find(x=>String(x.id)===String(k)) || {name:c.product_name||k};
    const rows = (c.competitor_keywords||[]).map(kw=>{
      const gap = kw.we_rank==null || (kw.top_position!=null && kw.we_rank>kw.top_position);
      return `<tr class="hover:bg-slate-700/30">
        <td class="px-3 py-2 text-xs">${esc(kw.keyword)}</td>
        <td class="px-3 py-2 text-right font-mono text-xs">${fmt(kw.volume)}</td>
        <td class="px-3 py-2 text-right font-mono text-xs text-slate-400">${kw.difficulty!=null?kw.difficulty:'-'}</td>
        <td class="px-3 py-2 text-xs text-slate-300">${esc(kw.top_competitor||'-')}${kw.top_position!=null?` <span class="text-slate-500">#${kw.top_position}</span>`:''}</td>
        <td class="px-3 py-2 text-right font-mono text-xs">${kw.we_rank!=null?`<span class="text-amber-300">#${kw.we_rank}</span>`:'<span class="text-rose-400 font-semibold">belum</span>'}</td>
        <td class="px-3 py-2 text-center">${gap?'<span class="badge bg-rose-500/20 text-rose-300">GAP<i class="th-info" data-tip="Kompetitor di atas kita, atau kita belum muncul di 10 besar. Ini celah yang harus diisi.">i</i></span>':'<span class="badge bg-emerald-500/10 text-emerald-400">unggul<i class="th-info" data-tip="Posisi kita di atas kompetitor teratas untuk keyword ini.">i</i></span>'}</td>
      </tr>`;
    }).join('');
    const gaps = (c.competitor_keywords||[]).filter(x=>x.we_rank==null || (x.top_position!=null && x.we_rank>x.top_position)).length;
    return `<div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <div class="p-4 border-b border-slate-700 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h4 class="font-bold">${esc(p.name)}</h4>
          <div class="text-[11px] text-slate-400">${esc(c.source||'Ubersuggest')} • ${(c.competitor_keywords||[]).length} keyword dianalisis</div>
        </div>
        <span class="badge ${gaps?'bg-rose-500/20 text-rose-300':'bg-emerald-500/10 text-emerald-400'}">${gaps} celah keyword</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-slate-900/70 text-slate-400 text-[11px] border-b border-slate-700">
            <tr>
              <th class="px-3 py-2 font-semibold">Keyword<i class="th-info" data-tip="Query yang muncul di Google untuk halaman ini. Sumber: GSC queries, dicek ulang lewat SERP Ubersuggest.">i</i></th>
              <th class="px-3 py-2 font-semibold text-right">Volume<i class="th-info" data-tip="Perkiraan pencarian rata-rata per bulan untuk keyword ini di Indonesia. Sumber: Ubersuggest.">i</i></th>
              <th class="px-3 py-2 font-semibold text-right">SD<i class="th-info" data-tip="SEO Difficulty 0–100: seberapa berat menembus halaman 1. Makin kecil makin mudah.">i</i></th>
              <th class="px-3 py-2 font-semibold">Peringkat Teratas<i class="th-info" data-tip="Domain kompetitor yang menempati hasil organik paling atas untuk keyword ini, beserta posisinya.">i</i></th>
              <th class="px-3 py-2 font-semibold text-right">Posisi Kita<i class="th-info" data-tip="Posisi halaman kita untuk keyword ini. 'belum' = kita tidak muncul sama sekali di 10 besar.">i</i></th>
              <th class="px-3 py-2 font-semibold text-center">Status<i class="th-info" data-tip="GAP = kompetitor di atas kita atau kita belum muncul → celah yang harus diisi. unggul = kita di atas kompetitor teratas.">i</i></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-700">${rows}</tbody>
        </table>
      </div>
    </div>`;
  }).join('');
}

const MONTHS = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];

// Bucket one product's rows into the selected period.
// daily rows (p.daily) drive daily + monthly; p.weeks drives weekly.
// Each bucket carries `ord`: a numeric index for weekly (p.weeks is already
// chronological, so ISO-week numbers that wrap at year end stay in order) and
// the ISO key itself for daily/monthly (string-sortable).
// Chronological order of the week keys present in the data. Keys are
// year-qualified ("2026W39"), so a plain string sort is chronological even
// when the series spans an ISO year boundary.
const WEEK_ORDER = (()=>{
  const seen = new Set();
  PRODUCTS.forEach(p=>(p.weeks||[]).forEach(w=>seen.add(w.w)));
  return new Map([...seen].sort().map((w,i)=>[w,i]));
})();

// Date-window filter ("" = open). Applied to rows before bucketing.
let dateFrom = '', dateTo = '';

// "2026W39" -> [mondayISO, sundayISO]; ISO-8601 week.
function weekRange(wk){
  const y = +wk.slice(0,4), n = +wk.slice(5);
  const jan4 = new Date(Date.UTC(y,0,4));
  const dow = jan4.getUTCDay() || 7;
  const mon = new Date(jan4); mon.setUTCDate(jan4.getUTCDate()-(dow-1)+(n-1)*7);
  const sun = new Date(mon); sun.setUTCDate(mon.getUTCDate()+6);
  return [mon.toISOString().slice(0,10), sun.toISOString().slice(0,10)];
}

// "2026-02" -> [first, last] day of month.
function monthRange(key){
  const [y,m] = key.split('-').map(Number);
  const last = new Date(Date.UTC(y, m, 0)).toISOString().slice(0,10);
  return [key + '-01', last];
}

function inWindow(a, b){
  if (dateFrom && b < dateFrom) return false;
  if (dateTo && a > dateTo) return false;
  return true;
}

function bucketProduct(p, period){
  const out = new Map();
  const add = (key,label,short,ord,impr,clicks,rank)=>{
    const e = out.get(key) || {key,label,short,ord,impr:0,clicks:0,_r:[],rank:null};
    e.impr += impr; e.clicks += clicks;
    if (rank!=null) e._r.push(rank);
    out.set(key,e);
  };
  if (period==='weekly'){
    (p.weeks||[]).forEach(w=>{
      const [a,b] = weekRange(w.w);
      if (!inWindow(a,b)) return;
      const lbl = w.w.slice(4);   // "2026W39" -> "W39"
      add(w.w, lbl, lbl, WEEK_ORDER.get(w.w), w.impr, w.clicks, w.rank);
    });
  } else {
    const rows = (p.daily&&p.daily.length) ? p.daily
      : (p.weeks||[]).map(w=>({d:null,w:w.w,impr:w.impr,clicks:w.clicks,rank:w.rank}));
    rows.forEach(r=>{
      if (period==='daily'){
        const d = r.d || r.w;
        if (!inWindow(d,d)) return;
        add(d, d, d.slice(5).replace('-','/'), d, r.impr, r.clicks, r.rank);
      } else { // monthly
        const d = r.d || r.w;
        const key = r.d ? r.d.slice(0,7) : 'W'+d;
        const [a,b] = r.d ? monthRange(key) : weekRange(r.w);
        if (!inWindow(a,b)) return;
        const label = r.d ? MONTHS[+r.d.slice(5,7)-1]+' '+r.d.slice(0,4) : d;
        add(key, label, r.d?MONTHS[+r.d.slice(5,7)-1]:d, key, r.impr, r.clicks, r.rank);
      }
    });
  }
  return [...out.values()].map(e=>{
    e.rank = e._r.length ? Math.round(e._r.reduce((a,b)=>a+b,0)/e._r.length*10)/10 : null;
    delete e._r; return e;
  }).sort((a,b)=>a.ord<b.ord?-1:a.ord>b.ord?1:0);
}

// Portfolio-wide series for the chart.
function bucketSeries(period){
  const totals = new Map();
  brows().forEach(p=>bucketProduct(p,period).forEach(b=>{
    const e = totals.get(b.key) || {key:b.key,label:b.label,short:b.short,ord:b.ord,impr:0,clicks:0,_r:[]};
    e.impr += b.impr; e.clicks += b.clicks;
    if (b.rank!=null) e._r.push(b.rank);
    totals.set(b.key,e);
  }));
  return [...totals.values()].map(e=>{
    e.rank = e._r.length ? Math.round(e._r.reduce((a,b)=>a+b,0)/e._r.length*10)/10 : null;
    delete e._r; return e;
  }).sort((a,b)=>a.ord<b.ord?-1:a.ord>b.ord?1:0);
}

// --- Compare two date ranges -------------------------------------------------
// Aggregate one product over [from,to] using daily rows where available.
// Weeks outside daily coverage are pro-rated by how many of their 7 days fall
// inside the window, so a partial week doesn't count double.
function windowAgg(p, from, to){
  let impr=0, clicks=0, rsum=0, rn=0;
  const days = (p.daily||[]).filter(r=>r.d>=from && r.d<=to);
  days.forEach(r=>{ impr+=r.impr; clicks+=r.clicks; if(r.rank!=null){rsum+=r.rank;rn++;} });
  const covered = days.length>0;
  (p.weeks||[]).forEach(w=>{
    if (covered) return;
    const [a,b] = weekRange(w.w);
    if (b < from || a > to) return;
    const ov = Math.min(b,to) >= Math.max(a,from)
      ? Math.round((Date.parse(Math.min(b,to)+'T00:00:00Z') - Date.parse(Math.max(a,from)+'T00:00:00Z'))/86400000)+1
      : 0;
    const f = ov/7;
    impr += w.impr*f; clicks += w.clicks*f;
    if (w.rank!=null){ rsum += w.rank*f; rn += f; }
  });
  return {impr:Math.round(impr), clicks:Math.round(clicks), rank: rn?Math.round(rsum/rn*10)/10:null};
}

function setComparePreset(days){
  const all = allDates(); if (!all.length) return;
  const last = all[all.length-1];
  const shift = (endISO, n)=>{ const d=new Date(endISO+'T00:00:00Z'); d.setUTCDate(d.getUTCDate()-n); return d.toISOString().slice(0,10); };
  const bFrom = shift(last, days-1);
  document.getElementById('cmpBFrom').value = bFrom < all[0] ? all[0] : bFrom;
  document.getElementById('cmpBTo').value = last;
  const aTo = shift(bFrom,1);
  document.getElementById('cmpATo').value = aTo;
  document.getElementById('cmpAFrom').value = shift(aTo, days-1);
  renderCompare();
}

function cmpPct(a,b){
  if (!a && !b) return '<span class="text-slate-600">—</span>';
  if (!a) return '<span class="text-emerald-400 font-semibold">▲ baru</span>';
  if (!b) return '<span class="text-rose-400 font-semibold">▼ -100%</span>';
  const d = Math.round((b-a)/a*100);
  if (d>0) return `<span class="text-emerald-400 font-semibold">▲ +${d}%</span>`;
  if (d<0) return `<span class="text-rose-400 font-semibold">▼ ${d}%</span>`;
  return '<span class="text-slate-500">0%</span>';
}
function cmpRank(a,b){
  if (a==null && b==null) return '<span class="text-slate-600">—</span>';
  if (a==null) return `<span class="text-slate-400">#${b} <span class="text-[10px]">(baru)</span></span>`;
  if (b==null) return `<span class="text-rose-400">#${a} → hilang</span>`;
  const d = Math.round((a-b)*10)/10;
  const t = d>0?`<span class="text-emerald-400 font-semibold">▲ ${d}</span>`
          : d<0?`<span class="text-rose-400 font-semibold">▼ ${Math.abs(d)}</span>`
          : '<span class="text-slate-500">—</span>';
  return `<span class="text-amber-300">#${a}</span> → <span class="text-amber-300">#${b}</span> ${t}`;
}

function renderCompare(){
  const body = document.getElementById('cmpBody');
  const foot = document.getElementById('cmpFoot');
  const g = id => document.getElementById(id).value;
  const aFrom=g('cmpAFrom'), aTo=g('cmpATo'), bFrom=g('cmpBFrom'), bTo=g('cmpBTo');
  if (!aFrom||!aTo||!bFrom||!bTo){
    body.innerHTML = `<tr><td colspan="10" class="px-3 py-6 text-center text-slate-400">Pilih kedua rentang tanggal, atau pakai preset di atas.</td></tr>`;
    foot.textContent = '—'; return;
  }
  if (aFrom>aTo || bFrom>bTo){ foot.textContent = 'Tanggal awal melebihi tanggal akhir.'; return; }

  const rows = brows().map(p=>{
    const A = windowAgg(p,aFrom,aTo), B = windowAgg(p,bFrom,bTo);
    return {p,A,B,dI:B.impr-A.impr,dC:B.clicks-A.clicks,
            dR:(A.rank!=null&&B.rank!=null)?A.rank-B.rank:null};
  }).filter(r=>r.A.impr||r.B.impr||r.A.clicks||r.B.clicks);

  const sort = document.getElementById('cmpSort').value;
  rows.sort((x,y)=>{
    if (sort==='dI') return y.dI-x.dI;
    if (sort==='dC') return y.dC-x.dC;
    if (sort==='dR') return (y.dR==null?-999:y.dR)-(x.dR==null?-999:x.dR);
    if (sort==='ib') return y.B.impr-x.B.impr;
    return x.p.name.localeCompare(y.p.name);
  });

  if (!rows.length){
    body.innerHTML = `<tr><td colspan="10" class="px-3 py-6 text-center text-slate-400">Tidak ada data di kedua rentang ini.</td></tr>`;
    foot.textContent = '—'; return;
  }
  const tA = rows.reduce((a,r)=>a+r.A.impr,0), tB = rows.reduce((a,r)=>a+r.B.impr,0);
  const cA = rows.reduce((a,r)=>a+r.A.clicks,0), cB = rows.reduce((a,r)=>a+r.B.clicks,0);
  const up = rows.filter(r=>r.dI>0).length, dn = rows.filter(r=>r.dI<0).length;
  foot.innerHTML = `${rows.length} program • Impresi: ${fmt(tA)} → <strong>${fmt(tB)}</strong> • Klik: ${cA} → <strong>${cB}</strong> • ${up} naik, ${dn} turun`;

  body.innerHTML = rows.map(r=>`
    <tr class="hover:bg-slate-700/30">
      <td class="px-3 py-3">
        <div class="font-medium">${esc(r.p.name)}</div>
        <div class="text-[11px] text-slate-500">${esc(r.p.kw_utama||'')}</div>
      </td>
      <td class="px-3 py-3 text-right font-mono text-xs text-slate-400">${fmt(r.A.impr)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${fmt(r.B.impr)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${cmpPct(r.A.impr,r.B.impr)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs text-slate-400">${fmt(r.A.clicks)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${fmt(r.B.clicks)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${cmpPct(r.A.clicks,r.B.clicks)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${cmpRank(r.A.rank,r.B.rank)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${r.B.rank!=null?`<span class="text-amber-300">#${r.B.rank}</span>`:'<span class="text-slate-600">—</span>'}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${r.dR==null?'<span class="text-slate-600">—</span>':(r.dR>0?`<span class="text-emerald-400 font-semibold">▲ ${r.dR}</span>`:r.dR<0?`<span class="text-rose-400 font-semibold">▼ ${Math.abs(r.dR)}</span>`:'<span class="text-slate-500">—</span>')}</td>
    </tr>`).join('');
}

function setPeriod(p){
  currentPeriod = p;
  document.querySelectorAll('.period-btn').forEach(b=>{
    const on = b.dataset.period===p;
    b.classList.toggle('active', on);
    b.classList.toggle('text-slate-400', !on);
  });
  renderTrends();
}

// Date-range controls. The window filters every bucket, so the chart, the rank
// table and the period label all narrow together.
function applyDateRange(){
  dateFrom = document.getElementById('dateFrom').value || '';
  dateTo = document.getElementById('dateTo').value || '';
  if (dateFrom && dateTo && dateFrom > dateTo){
    const t = dateFrom; dateFrom = dateTo; dateTo = t;
    document.getElementById('dateFrom').value = dateFrom;
    document.getElementById('dateTo').value = dateTo;
  }
  renderTrends();
}
function setDatePreset(days){
  const all = allDates();
  if (!all.length) return;
  const last = all[all.length-1];
  const start = new Date(last + 'T00:00:00Z');
  start.setUTCDate(start.getUTCDate() - (days-1));
  const from = start.toISOString().slice(0,10);
  document.getElementById('dateFrom').value = from < all[0] ? all[0] : from;
  document.getElementById('dateTo').value = last;
  applyDateRange();
}
function clearDateRange(){
  document.getElementById('dateFrom').value = '';
  document.getElementById('dateTo').value = '';
  applyDateRange();
}
// Every date the data covers, so presets anchor on real data, not today.
function allDates(){
  const s = new Set();
  PRODUCTS.forEach(p=>{
    (p.daily||[]).forEach(d=>s.add(d.d));
    (p.weeks||[]).forEach(w=>{ const [a,b]=weekRange(w.w); s.add(a); s.add(b); });
  });
  return [...s].sort();
}

// Per-program rank movement (first vs last bucket of the selected period).
function renderRankMove(series){
  const body = document.getElementById('rankMoveBody');
  const foot = document.getElementById('rankMoveFoot');
  const rows = brows().map(p=>{
    const b = bucketProduct(p,currentPeriod).filter(x=>x.rank!=null);
    if (b.length<2) return null;
    const first=b[0], last=b[b.length-1];
    const delta = Math.round((first.rank-last.rank)*10)/10;   // + = naik (posisi mengecil)
    const impr = b.reduce((a,x)=>a+x.impr,0), clicks = b.reduce((a,x)=>a+x.clicks,0);
    return {p,first,last,delta,impr,clicks,series:b};
  }).filter(Boolean).sort((a,b)=>b.delta-a.delta);

  if (!rows.length){
    body.innerHTML = `<tr><td colspan="7" class="px-3 py-6 text-center text-slate-400">Belum ada data posisi untuk periode ini.</td></tr>`;
    foot.textContent = '—';
    return;
  }
  const up = rows.filter(r=>r.delta>0).length, down = rows.filter(r=>r.delta<0).length;
  foot.textContent = `${rows.length} program punya data posisi • ${up} naik, ${down} turun, ${rows.length-up-down} stabil`;
  document.getElementById('rankPeriodLabel').textContent =
    series.length ? `${series[0].label} → ${series[series.length-1].label}` : '—';

  body.innerHTML = rows.map(r=>{
    const d = r.delta;
    const dTxt = d>0?`<span class="text-emerald-400 font-semibold">▲ ${d}</span>`
              : d<0?`<span class="text-rose-400 font-semibold">▼ ${Math.abs(d)}</span>`
              : '<span class="text-slate-400">—</span>';
    const spark = r.series.map(x=>x.rank);
    const W=80,H=22,pad=2;
    const maxR=Math.max(...spark,2), minR=1;
    const pts = spark.map((v,i)=>{
      const x=pad+i/(spark.length-1)*(W-pad*2);
      const y=pad+(v-minR)/(maxR-minR)*(H-pad*2);   // #1 di atas
      return x.toFixed(1)+','+y.toFixed(1);
    }).join(' ');
    const col = d>0?'#34d399':d<0?'#fb7185':'#94a3b8';
    return `<tr class="hover:bg-slate-700/30">
      <td class="px-3 py-3">
        <div class="font-medium">${esc(r.p.name)}</div>
        <div class="text-[11px] text-slate-500">${esc(r.p.kw_utama||'')}</div>
      </td>
      <td class="px-3 py-3 text-right font-mono text-xs text-slate-400">#${r.first.rank}</td>
      <td class="px-3 py-3 text-right font-mono text-xs text-amber-300">#${r.last.rank}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${dTxt}</td>
      <td class="px-3 py-3 text-right font-mono text-xs">${fmt(r.impr)}</td>
      <td class="px-3 py-3 text-right font-mono text-xs font-semibold text-blue-400">${r.clicks}</td>
      <td class="px-3 py-3 text-center"><svg width="${W}" height="${H}" class="inline-block"><polyline fill="none" stroke="${col}" stroke-width="1.5" points="${pts}"/></svg></td>
    </tr>`;
  }).join('');
}

function renderTrends(){
  const series = bucketSeries(currentPeriod);
  const el = document.getElementById('chartContainer');
  if (series.length<2){ el.innerHTML='<div class="text-slate-500 text-sm">Data periode ini belum cukup (&lt;2 titik). Coba periode Mingguan/Bulanan.</div>'; renderRankMove(series); return; }
  document.getElementById('periodLabel').textContent =
    `${series.length} titik: ${series[0].label} — ${series[series.length-1].label}`;
  const W=800,H=240,pad=40,cw=W-pad*2,ch=H-pad*2;
  const maxI=Math.max(...series.map(d=>d.impr),1), maxC=Math.max(...series.map(d=>d.clicks),1);
  const ranks = series.map(d=>d.rank).filter(r=>r!=null);
  const maxR=Math.max(...ranks,2), minR=1;
  const line=(key,max)=>series.map((d,i)=>{
    const x=pad+i/(series.length-1)*cw, y=pad+ch-(d[key]/max)*ch;
    return x.toFixed(1)+','+y.toFixed(1);
  }).join(' ');
  // rank axis inverted: #1 at top, worst at bottom
  const rankLine = series.map((d,i)=>{
    if (d.rank==null) return null;
    const x=pad+i/(series.length-1)*cw;
    const y=pad+ch-((d.rank-minR)/(maxR-minR))*ch;
    return x.toFixed(1)+','+y.toFixed(1);
  }).filter(Boolean).join(' ');
  const step = Math.max(1, Math.ceil(series.length/10));
  el.innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" class="w-full h-full">
      <line x1="${pad}" y1="${pad}" x2="${W-pad}" y2="${pad}" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="3,3"/>
      <line x1="${pad}" y1="${pad+ch/2}" x2="${W-pad}" y2="${pad+ch/2}" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="3,3"/>
      <line x1="${pad}" y1="${pad+ch}" x2="${W-pad}" y2="${pad+ch}" stroke="currentColor" stroke-opacity="0.2"/>
      <polyline fill="none" stroke="#3b82f6" stroke-width="2.5" points="${line('impr',maxI)}"/>
      <polyline fill="none" stroke="#34d399" stroke-width="2.5" stroke-dasharray="4,2" points="${line('clicks',maxC)}"/>
      <polyline fill="none" stroke="#fbbf24" stroke-width="2" points="${rankLine}"/>
      ${series.map((d,i)=>{
        const x=pad+i/(series.length-1)*cw, y=pad+ch-(d.impr/maxI)*ch;
        return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="#3b82f6"><title>${d.label}: ${fmt(d.impr)} impresi, ${d.clicks} klik${d.rank!=null?', posisi #'+d.rank:''}</title></circle>`;
      }).join('')}
      ${series.filter((_,i)=>i%step===0||i===series.length-1).map(d=>{
        const i=series.indexOf(d), x=pad+i/(series.length-1)*cw;
        return `<text x="${x.toFixed(1)}" y="${H-10}" fill="currentColor" opacity="0.6" font-size="10" text-anchor="middle">${d.short}</text>`;
      }).join('')}
    </svg>`;
  renderRankMove(series);

  const cats = {};
  brows().forEach(p=>{
    if (!cats[p.category]) cats[p.category]={n:0,clicks:0,impr:0};
    cats[p.category].n++; cats[p.category].clicks+=p.total_clicks; cats[p.category].impr+=p.total_impr;
  });
  const totalClicks = brows().reduce((a,p)=>a+p.total_clicks,0)||1;
  document.getElementById('categoryBars').innerHTML = Object.entries(cats).map(([c,v])=>{
    const pct = Math.round(v.clicks/totalClicks*100);
    return `<div>
      <div class="flex justify-between text-xs mb-1">
        <span class="font-medium">${esc(c)} (${v.n} program)</span>
        <span class="text-blue-400 font-semibold">${v.clicks} klik (${pct}%)</span>
      </div>
      <div class="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-700">
        <div class="bg-blue-500 h-2 rounded-full" style="width:${pct}%"></div>
      </div></div>`;
  }).join('');

  const top = [...brows()].sort((a,b)=>b.total_clicks-a.total_clicks).slice(0,5);
  document.getElementById('topKeywords').innerHTML = top.map((p,i)=>`
    <div class="py-2.5 flex items-center justify-between">
      <div><div class="font-semibold">${i+1}. ${esc(p.kw_utama)}</div>
      <div class="text-[11px] text-slate-400">${esc(p.name)}</div></div>
      <div class="text-right"><div class="font-bold text-emerald-400">${p.total_clicks} Klik</div>
      <div class="text-[10px] text-slate-400">CTR ${p.ctr}% • Posisi ${p.latest_rank||'-'}</div></div>
    </div>`).join('');
}

function renderBrands(){
  // Numbers are computed from products.json so the cross-brand table can never
  // drift from the detail tabs; brands.json only supplies the focus text.
  const focus = {}; (BRANDS||[]).forEach(b=>focus[b.brand]=b.focus);
  const byBrand = {};
  PRODUCTS.forEach(p=>{
    const b = p.brand || 'Lainnya';
    const e = byBrand[b] || (byBrand[b]={lp:0,aktif:0,impr:0,clicks:0,wks:new Set()});
    e.lp++; e.impr+=p.total_impr; e.clicks+=p.total_clicks;
    if (p.status.toLowerCase()==='aktif') e.aktif++;
    (p.weeks||[]).forEach(w=>{ if (w.impr||w.clicks) e.wks.add(w.w); });
  });
  const rows = Object.entries(byBrand).sort((a,b)=>b[1].impr-a[1].impr);
  const tot = rows.reduce((a,[,v])=>({lp:a.lp+v.lp,aktif:a.aktif+v.aktif,impr:a.impr+v.impr,clicks:a.clicks+v.clicks}),{lp:0,aktif:0,impr:0,clicks:0});
  document.getElementById('brandsBody').innerHTML = rows.map(([name,v])=>`
    <tr class="hover:bg-slate-700/30 cursor-pointer" onclick="setBrand('${esc(name)}')">
      <td class="px-4 py-3 font-semibold">${esc(name)}</td>
      <td class="px-4 py-3 text-xs text-slate-400">${esc(focus[name]||'—')}</td>
      <td class="px-4 py-3 text-center font-mono">${v.aktif}<span class="text-slate-500">/${v.lp}</span></td>
      <td class="px-4 py-3 text-right font-mono">${fmt(v.impr)}</td>
      <td class="px-4 py-3 text-right font-mono font-semibold text-blue-400">${fmt(v.clicks)}</td>
      <td class="px-4 py-3 text-right font-mono font-semibold text-emerald-400">${v.impr?(v.clicks/v.impr*100).toFixed(2)+'%':'0.00%'}</td>
    </tr>`).join('') + `
    <tr class="bg-slate-900/60 font-bold border-t border-slate-600">
      <td class="px-4 py-3" colspan="2">TOTAL</td>
      <td class="px-4 py-3 text-center font-mono">${tot.aktif}<span class="text-slate-500">/${tot.lp}</span></td>
      <td class="px-4 py-3 text-right font-mono">${fmt(tot.impr)}</td>
      <td class="px-4 py-3 text-right font-mono text-blue-400">${fmt(tot.clicks)}</td>
      <td class="px-4 py-3 text-right font-mono text-emerald-400">${tot.impr?(tot.clicks/tot.impr*100).toFixed(2)+'%':'0.00%'}</td>
    </tr>`;
}

function switchTab(t){
  ['matrix','aksi','kompetitor','tren','brands'].forEach(x=>{
    document.getElementById('view-'+x).classList.toggle('hidden', x!==t);
    const b = document.getElementById('btn-tab-'+x);
    b.classList.toggle('active', x===t);
    b.classList.toggle('text-slate-400', x!==t);
  });
}
function setCategoryFilter(c){
  currentCategory=c;
  document.querySelectorAll('.cat-btn').forEach(b=>{
    const on = b.dataset.cat===c;
    b.classList.toggle('active', on);
    b.classList.toggle('text-slate-400', !on);
  });
  renderMatrix();
}
function setStatusFilter(s){
  currentStatus=s;
  document.querySelectorAll('.status-btn').forEach(b=>{
    const on = b.dataset.status===s;
    b.classList.toggle('bg-blue-600', on);
    b.classList.toggle('text-white', on);
    b.classList.toggle('text-slate-400', !on);
  });
  renderMatrix();
}
function resetFilters(){
  document.getElementById('searchInput').value='';
  document.getElementById('sortSelect').value='prio-desc';
  setCategoryFilter('all'); setStatusFilter('all');
}

function openModal(id){
  const p = PRODUCTS.find(x=>x.id===id); if (!p) return;
  currentId = id;
  const r = rec(id), f = r.perbaikan||{};
  document.getElementById('modalTitle').textContent = p.name;
  document.getElementById('modalUrl').textContent = p.url || 'Belum ada URL live';
  document.getElementById('modalUrl').href = p.url || '#';
  document.getElementById('mImpr').textContent = fmt(p.total_impr);
  document.getElementById('mClicks').textContent = p.total_clicks;
  document.getElementById('mCtr').textContent = p.ctr+'%';
  document.getElementById('mRank').textContent = p.latest_rank>0?'#'+p.latest_rank:'-';
  document.getElementById('modalBadges').innerHTML =
    `<span class="badge ${p.status.toLowerCase()==='aktif'?'bg-emerald-500/10 text-emerald-400':'bg-amber-500/10 text-amber-400'}">${esc(p.status)}</span>
     <span class="badge bg-blue-500/10 text-blue-400">${esc(p.category)}</span>
     <span class="badge bg-slate-700 text-slate-300">Prioritas ${r.prioritas}</span>`;
  const ul = (id,arr) => document.getElementById(id).innerHTML =
    (arr&&arr.length?arr:['—']).map(x=>`<li>${esc(x)}</li>`).join('');
  ul('mMasalah', r.masalah); ul('mSolusi', r.solusi); ul('mRekomendasi', r.rekomendasi);
  document.getElementById('mMetaTitle').textContent = f.meta_title||'-';
  document.getElementById('mMetaTitleLen').textContent = (f.meta_title||'').length+' karakter (target ≤60)';
  document.getElementById('mMetaDesc').textContent = f.meta_description||'-';
  document.getElementById('mMetaDescLen').textContent = (f.meta_description||'').length+' karakter (target ≤155)';
  document.getElementById('mH2').innerHTML = (f.h2_outline||[]).map(h=>`<li>${esc(h)}</li>`).join('');
  document.getElementById('mFaq').textContent = f.faq_schema||'-';
  document.getElementById('detailModal').classList.remove('hidden');
  document.getElementById('detailModal').classList.add('flex');
}
function closeModal(){
  document.getElementById('detailModal').classList.add('hidden');
  document.getElementById('detailModal').classList.remove('flex');
}
function copyText(elId, btn){
  const t = document.getElementById(elId).textContent;
  navigator.clipboard.writeText(t).then(()=>{
    const o = btn.textContent; btn.textContent='Tersalin ✓';
    setTimeout(()=>btn.textContent=o, 1200);
  });
}
function pushToWordPress(){
  alert('Belum dikonfigurasi.\n\nIsi data/wp_config.json dengan:\n{\n  "base_url": "https://grc-indonesia.com",\n  "user": "USERNAME",\n  "app_password": "xxxx xxxx xxxx xxxx"\n}\n\nLalu jalankan: python3 push_wp.py --id ' + currentId);
}
document.getElementById('detailModal').addEventListener('click', function(e){ if (e.target===this) closeModal(); });

// --- Live refresh -----------------------------------------------------------
// The page is static, so "live" means: re-read the JSON the pipeline writes and
// re-render, without a reload. Only works when the page is served over http(s)
// from the same origin as data/ (GitHub Pages serves the repo root, so it does).
// Opened as a local file:// the fetch is blocked by the browser — the button
// then says so instead of failing silently.
const LIVE_MS = 5 * 60 * 1000;
let liveTimer = null, liveOn = false;

function liveSupported(){
  return location.protocol === 'http:' || location.protocol === 'https:';
}

function setLiveStatus(msg, cls){
  const el = document.getElementById('liveStatus');
  if (el){ el.textContent = msg; el.className = 'text-[11px] ' + (cls||'text-slate-500'); }
}

async function liveRefresh(manual){
  if (!liveSupported()){
    setLiveStatus('Live tidak tersedia saat file dibuka langsung (file://). Buka lewat URL GitHub Pages.', 'text-amber-400');
    return;
  }
  setLiveStatus('Memuat data terbaru…', 'text-slate-400');
  try {
    const bust = '?t=' + Date.now();
    const [pr, rc, cp, br] = await Promise.all([
      fetch('data/products.json' + bust).then(r=>r.ok?r.json():Promise.reject(r.status)),
      fetch('data/recommendations.json' + bust).then(r=>r.ok?r.json():Promise.reject(r.status)),
      fetch('data/competitors.json' + bust).then(r=>r.ok?r.json():Promise.reject(r.status)),
      fetch('data/brands.json' + bust).then(r=>r.ok?r.json():Promise.reject(r.status)),
    ]);
    if (!Array.isArray(pr) || !pr.length) throw new Error('products.json kosong');
    PRODUCTS.length = 0; PRODUCTS.push(...pr);
    Object.keys(RECS).forEach(k=>delete RECS[k]); Object.assign(RECS, rc);
    Object.keys(COMPETITORS).forEach(k=>delete COMPETITORS[k]); Object.assign(COMPETITORS, cp);
    BRANDS.length = 0; BRANDS.push(...br);
    const all = allDates();
    if (all.length){
      ['dateFrom','dateTo'].forEach(id=>{
        const el = document.getElementById(id);
        el.min = all[0]; el.max = all[all.length-1];
      });
    }
    renderBrandBar(); renderKPI(); renderMatrix(); renderAksi(); renderKompetitor(); renderTrends(); renderBrands(); renderCompare();
    setLiveStatus('Data terbaru dimuat ' + new Date().toLocaleTimeString('id-ID') +
                  (liveOn ? ' • auto tiap 5 menit' : ''), 'text-emerald-400');
  } catch (e) {
    setLiveStatus('Gagal memuat data terbaru (' + e + '). Menampilkan data yang tertanam.', 'text-rose-400');
  }
}

function toggleLive(){
  liveOn = !liveOn;
  const b = document.getElementById('liveBtn');
  if (liveOn){
    b.textContent = '⏸ Hentikan Live';
    b.classList.add('bg-emerald-600');
    liveRefresh(false);
    liveTimer = setInterval(()=>liveRefresh(false), LIVE_MS);
  } else {
    b.textContent = '▶ Live 5 menit';
    b.classList.remove('bg-emerald-600');
    clearInterval(liveTimer); liveTimer = null;
    setLiveStatus('Live dimatikan.', 'text-slate-500');
  }
}

// --- Shared tooltip ----------------------------------------------------------
// One #tip element, positioned fixed via event delegation. Delegation matters:
// table bodies and KPI cards are re-rendered by innerHTML constantly, so
// per-element listeners would leak or die after every refresh.
(function(){
  const tip = document.getElementById('tip');
  let cur = null;
  function place(el){
    const r = el.getBoundingClientRect();
    tip.textContent = el.dataset.tip;
    tip.classList.add('on');
    const tw = tip.offsetWidth, th = tip.offsetHeight, gap = 8;
    let x = r.left + r.width/2 - tw/2;
    let y = r.top - th - gap;
    if (y < gap) y = r.bottom + gap;                      // no room above
    x = Math.max(gap, Math.min(x, innerWidth - tw - gap)); // clamp horizontal
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  function hide(){ cur = null; tip.classList.remove('on'); }
  document.addEventListener('mouseover', e=>{
    const el = e.target.closest && e.target.closest('.th-info');
    if (el && el !== cur){ cur = el; place(el); }
  });
  document.addEventListener('mouseout', e=>{
    if (cur && e.target.closest && e.target.closest('.th-info') === cur) hide();
  });
  // touch: tap the i to show, tap anywhere else to dismiss
  document.addEventListener('click', e=>{
    const el = e.target.closest && e.target.closest('.th-info');
    if (el && el !== cur){ cur = el; place(el); e.stopPropagation(); }
    else if (!el) hide();
  }, true);
  addEventListener('scroll', hide, true);
  addEventListener('resize', hide);
})();

// --- Hermes AI chat widget ---------------------------------------------------
// Talks to the local Hermes API server (OpenAI-compatible, default :8642).
// Endpoint + key live in localStorage, never in this file — the repo is public.
(function(){
  const EP_KEY='hermes_ai_endpoint', K_KEY='hermes_ai_key', MSG_KEY='hermes_ai_msgs';
  const DEF_EP='http://127.0.0.1:8642/v1/chat/completions';
  // Proxy publik: nginx dashboard.digitalfinger.id -> FastAPI lokal -> 9router.
  // Key provider tidak pernah masuk repo. Token widget cuma remah biaya, bukan rahasia.
  const PROXY = 'https://dashboard.digitalfinger.id/keyword-ai/chat';
  const WIDGET_TOKEN = 'grc-widget-2026';
  const $ = id => document.getElementById(id);
  const LOCAL_HOST = /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
  const fab=$('aiFab'), panel=$('aiPanel'), log=$('aiLog'), input=$('aiInput'), dot=$('aiDot');
  let msgs = [];
  try { msgs = JSON.parse(localStorage.getItem(MSG_KEY) || '[]'); } catch(e){ msgs = []; }

  const ep  = () => localStorage.getItem(EP_KEY) || DEF_EP;
  const key = () => localStorage.getItem(K_KEY) || '';

  // Compact snapshot of the dashboard data so the model answers from real numbers.
  function context(){
    const L = [];
    L.push('KONTEKS DASHBOARD SEO: ' + brandNames().join(', '));
    L.push('Stamp: ' + (META.stamp||'-'));
    if (dateFrom || dateTo) L.push('Filter tanggal aktif: ' + (dateFrom||'awal') + ' s/d ' + (dateTo||'akhir'));
    L.push('');
    L.push('PROGRAM (' + PRODUCTS.length + '): nama | kategori | status | keyword utama (vol) | impresi | klik | CTR% | rank rata2 | rank terakhir');
    PRODUCTS.forEach(p=>{
      L.push([p.brand, p.name, p.category, p.status, (p.kw_utama||'-')+' ('+(p.vol_utama||'-')+')',
              p.total_impr, p.total_clicks, p.ctr, p.avg_rank, p.latest_rank].join(' | '));
    });
    // Weekly tail: without it the model cannot answer "what moved this week".
    const wk = p => (p.weeks||[]).filter(w=>w.impr||w.clicks||w.rank).slice(-4);
    const anyWk = PRODUCTS.some(p=>wk(p).length);
    if (anyWk){
      L.push('');
      L.push('SERI MINGGUAN TERAKHIR (4 minggu terakhir yang ada datanya) — nama | minggu: impr/klik/rank');
      PRODUCTS.forEach(p=>{
        const w = wk(p); if (!w.length) return;
        L.push(p.name + ' | ' + w.map(x=>x.w+': '+x.impr+'/'+x.clicks+'/'+(x.rank||'-')).join(' ; '));
      });
    }
    const byId = {}; PRODUCTS.forEach(p=>byId[p.id]=p);
    const recs = Object.entries(RECS||{}).map(([id,r])=>({p:byId[id], r}))
      .sort((a,b)=>(b.r.prioritas||0)-(a.r.prioritas||0));
    if (recs.length){
      L.push('');
      L.push('REKOMENDASI AKSI (prioritas tertinggi dulu):');
      recs.slice(0,15).forEach(({p,r})=>{
        L.push('- [P' + (r.prioritas||'-') + '] ' + (p?p.name:'?') +
               ' | MASALAH: ' + (r.masalah||[]).join(' ') +
               ' | SOLUSI: ' + (r.solusi||[]).join(' ') +
               ' | REKOMENDASI: ' + (r.rekomendasi||[]).join(' '));
      });
    }
    const comps = Object.entries(COMPETITORS||{}).map(([id,c])=>({p:byId[id], c}));
    if (comps.length){
      L.push('');
      L.push('CELAH KOMPETITOR:');
      comps.slice(0,12).forEach(({p,c})=>{
        (c.competitor_keywords||[]).slice(0,4).forEach(k=>{
          L.push('- ' + (p?p.name:(c.product_name||'?')) + ' | "' + k.keyword + '" vol ' + k.volume +
                 ' SD ' + k.difficulty + ' | teratas ' + k.top_competitor + ' #' + k.top_position +
                 ' | kita ' + (k.we_rank==null?'belum':('#'+k.we_rank)));
        });
      });
    }
    if ((BRANDS||[]).length){
      L.push('');
      L.push('BRAND: ' + BRANDS.map(b=>b.brand||b.name).join(', '));
    }
    return L.join('\n');
  }

  const SYS = () => 'Kamu analis SEO untuk ' + brandNames().join(' dan ') + '. Jawab dalam Bahasa Indonesia, ringkas, '
    + 'langsung ke angka. Pakai HANYA data di konteks; kalau tidak ada, bilang tidak ada. '
    + 'Format: poin pendek, angka pakai pemisah ribuan titik.\n\n' + context();

  function bubble(role, text){
    const wrap = document.createElement('div');
    wrap.className = role==='user' ? 'flex justify-end' : 'flex justify-start';
    const b = document.createElement('div');
    b.className = role==='user'
      ? 'max-w-[85%] rounded-2xl rounded-br-sm bg-blue-600 px-3 py-2 text-white whitespace-pre-wrap'
      : 'max-w-[90%] rounded-2xl rounded-bl-sm bg-slate-900 border border-slate-700 px-3 py-2 text-slate-200 whitespace-pre-wrap';
    b.textContent = text;
    wrap.appendChild(b); log.appendChild(wrap); log.scrollTop = log.scrollHeight;
    return b;
  }
  function repaint(){
    log.innerHTML = '';
    if (!msgs.length){
      bubble('assistant','Halo. Tanya apa saja soal data dashboard ini — misalnya program yang turun minggu ini, keyword volume besar tapi posisi masih jelek, atau bandingkan dua periode.');
    } else msgs.forEach(m=>bubble(m.role, m.content));
  }
  function status(state, text){
    dot.className = 'w-2.5 h-2.5 rounded-full ' +
      (state==='ok'?'bg-emerald-400':state==='err'?'bg-rose-500':state==='busy'?'bg-amber-400 animate-pulse':'bg-slate-500');
    if (text) dot.title = text;
  }

  async function send(text){
    if (!text.trim()) return;
    // Mode publik (github.io): lewat proxy publik, tanpa key di browser.
    // Mode lokal: langsung ke API server Hermes, butuh key.
    const viaProxy = !LOCAL_HOST;
    if (!viaProxy && !key()){
      bubble('assistant','Belum ada API key. Klik ⚙ di bawah untuk isi endpoint + key API server Hermes lokal.');
      return;
    }
    msgs.push({role:'user', content:text});
    bubble('user', text);
    input.value = '';
    const pending = bubble('assistant','…');
    status('busy','Menghubungi AI…');
    try {
      const url = viaProxy ? PROXY : ep();
      const headers = {'Content-Type':'application/json'};
      if (viaProxy) headers['X-Widget-Token'] = WIDGET_TOKEN;
      else headers['Authorization'] = 'Bearer ' + key();
      const res = await fetch(url, {
        method:'POST',
        headers,
        body: JSON.stringify({
          model:'hermes-agent',
          messages:[{role:'system',content:SYS()}].concat(msgs.slice(-12)),
          stream:false
        })
      });
      if (!res.ok){
        const t = await res.text();
        throw new Error('HTTP ' + res.status + ' — ' + t.slice(0,300));
      }
      const j = await res.json();
      const out = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || '(kosong)';
      pending.textContent = out;
      msgs.push({role:'assistant', content:out});
      status('ok','Terhubung');
    } catch(e){
      pending.textContent = 'Gagal menghubungi AI.\n\n' + e.message +
        (viaProxy
          ? '\n\nCek: proxy /keyword-ai/chat di dashboard.digitalfinger.id hidup (service keyword-ai).'
          : '\n\nCek: (1) gateway Hermes jalan, (2) API server aktif di ' + ep() +
            ', (3) origin diizinkan CORS, (4) API key benar.');
      status('err', String(e.message));
    }
    try { localStorage.setItem(MSG_KEY, JSON.stringify(msgs.slice(-20))); } catch(e){}
  }

  const QUICK = ['Program mana yang turun minggu ini?','Keyword volume besar tapi posisi kita masih jelek?',
                 'Ringkas kondisi 5 program teratas','Apa 3 aksi paling mendesak?'];
  QUICK.forEach(q=>{
    const b=document.createElement('button');
    b.className='px-2 py-1 rounded-full border border-slate-600 text-[11px] text-slate-300 hover:bg-slate-700';
    b.textContent=q; b.onclick=()=>send(q);
    $('aiQuick').appendChild(b);
  });

  fab.onclick = ()=>{ fab.classList.add('hidden'); panel.classList.remove('hidden'); panel.classList.add('flex'); input.focus(); };
  // Widget butuh endpoint yang bisa diakses dari origin manapun: proxy publik
  // (dashboard.digitalfinger.id, CORS *) atau API server Hermes lokal (localhost).
  // file:// tetap diblok — Origin: null, dan tidak ada proxy di sana.
  const SERVED = LOCAL_HOST || location.protocol.startsWith('http');
  if (!SERVED) fab.classList.add('hidden');
  $('aiClose').onclick = ()=>{ panel.classList.add('hidden'); panel.classList.remove('flex'); fab.classList.remove('hidden'); };
  $('aiClear').onclick = ()=>{ msgs=[]; localStorage.removeItem(MSG_KEY); repaint(); };
  $('aiCfg').onclick = ()=>{
    const e = prompt('Endpoint API server Hermes (OpenAI-compatible):', ep());
    if (e === null) return;
    const k = prompt('API key (API_SERVER_KEY). Disimpan hanya di browser ini:', key());
    if (k === null) return;
    localStorage.setItem(EP_KEY, e.trim());
    localStorage.setItem(K_KEY, k.trim());
    status(k.trim()?'ok':'idle', k.trim()?'Terhubung':'Belum ada API key');
    bubble('assistant','Pengaturan disimpan di browser ini. Endpoint: ' + e.trim());
  };
  $('aiSend').onclick = ()=>send(input.value);
  input.addEventListener('keydown', e=>{
    if (e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(input.value); }
  });
  repaint();
  if (!LOCAL_HOST) status('ok','Mode publik: lewat proxy dashboard.digitalfinger.id');
  else status(key()?'ok':'idle', key()?'Terhubung':'Belum ada API key');
})();

window.onload = init;
</script>
</body>
</html>
"""


TW_CDN = '<script src="https://cdn.tailwindcss.com"></script>'
TW_URL = "https://cdn.tailwindcss.com"


def tailwind_inline():
    """Tailwind source cached in data/ so the client copy works offline.
    Returns None when it can't be fetched (build falls back to the CDN tag)."""
    cache = os.path.join(DATA, "vendor-tailwind.js")
    if not os.path.exists(cache):
        try:
            with urllib.request.urlopen(TW_URL, timeout=60) as r:
                open(cache, "wb").write(r.read())
        except Exception as e:
            print(f"WARN: cannot fetch Tailwind for offline build ({e})")
            return None
    src = open(cache, encoding="utf-8").read()
    return None if len(src) < 100000 else src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--standalone", action="store_true",
                    help="also write a single-file copy for sending to a client")
    args = ap.parse_args()

    products = load("products.json", [])
    recs = load("recommendations.json", {})
    comps = load("competitors.json", {})
    brands = load("brands.json", [])
    meta = {
        "stamp": "Data per " + datetime.datetime.now().strftime("%d %b %Y %H:%M")
                + " • " + str(len(products)) + " program",
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    html = (HTML
            .replace("__PRODUCTS__", json.dumps(products, ensure_ascii=False))
            .replace("__RECS__", json.dumps(recs, ensure_ascii=False))
            .replace("__COMPETITORS__", json.dumps(comps, ensure_ascii=False))
            .replace("__BRANDS__", json.dumps(brands, ensure_ascii=False))
            .replace("__META__", json.dumps(meta, ensure_ascii=False)))
    with open(OUT, "w") as f:
        f.write(html)
    print(f"wrote {OUT} ({len(html):,} bytes)")
    print(f"products={len(products)} recs={len(recs)} competitors={len(comps)} brands={len(brands)}")

    if args.standalone:
        tw = tailwind_inline()
        if tw:
            html = html.replace(TW_CDN, "<script>\n" + tw + "\n</script>")
        else:
            print("WARN: standalone copy still needs the Tailwind CDN")
        out = os.path.join(HERE, "dashboard-standalone.html")
        with open(out, "w") as f:
            f.write(html)
        print(f"wrote {out} ({len(html):,} bytes) — kirim file ini ke klien")
        # GitHub Pages serves the repo root; index.html is the live copy and
        # uses the inlined Tailwind so it renders without the CDN.
        with open(os.path.join(HERE, "index.html"), "w") as f:
            f.write(html)
        print("wrote index.html (GitHub Pages entry point)")


if __name__ == "__main__":
    main()
