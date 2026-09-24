#!/usr/bin/env python3
"""Build dashboard.html from data/*.json (single self-contained file).

Run: python3 build_dashboard.py
"""
import json, os, datetime

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
        <p class="text-sm text-slate-400 mt-1">GRC Indonesia • Proxsis Academy • Matriks Impresi / Klik / CTR / Rank + Rekomendasi Aksi</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="text-right hidden sm:block">
          <div class="text-xs text-slate-400">Total Portofolio</div>
          <div class="text-lg font-bold" id="totalPortfolio">—</div>
        </div>
        <button onclick="resetFilters()" class="px-3 py-2 text-xs font-medium rounded-lg border border-slate-700 hover:bg-slate-700">Reset Filter</button>
      </div>
    </div>
  </header>

  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4" id="kpiRow"></div>

  <div class="flex flex-wrap items-center gap-2 border-b border-slate-700 pb-3">
    <button onclick="switchTab('matrix')" id="btn-tab-matrix" class="tab-btn active px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700">📊 Matriks Kinerja</button>
    <button onclick="switchTab('aksi')" id="btn-tab-aksi" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700 text-slate-400">🛠️ Aksi &amp; Perbaikan</button>
    <button onclick="switchTab('kompetitor')" id="btn-tab-kompetitor" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700 text-slate-400">🥊 Keyword Kompetitor</button>
    <button onclick="switchTab('tren')" id="btn-tab-tren" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-slate-700 text-slate-400">📈 Tren Mingguan</button>
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
          <button onclick="setCategoryFilter('all')" class="pill-btn active cat-btn px-2.5 py-1 rounded-md border border-slate-700" data-cat="all">Semua</button>
          <button onclick="setCategoryFilter('Sertifikasi BNSP / Profesi')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-slate-700 text-slate-400" data-cat="Sertifikasi BNSP / Profesi">Sertifikasi BNSP</button>
          <button onclick="setCategoryFilter('Standar ISO & Kepatuhan')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-slate-700 text-slate-400" data-cat="Standar ISO & Kepatuhan">Standar ISO</button>
          <button onclick="setCategoryFilter('Audit, Fraud & Forensik')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-slate-700 text-slate-400" data-cat="Audit, Fraud & Forensik">Audit &amp; Fraud</button>
          <button onclick="setCategoryFilter('Tata Kelola & BUMN')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-slate-700 text-slate-400" data-cat="Tata Kelola & BUMN">Tata Kelola</button>
          <button onclick="setCategoryFilter('AI & Data Governance')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-slate-700 text-slate-400" data-cat="AI & Data Governance">AI &amp; Data</button>
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
              <th class="px-3 py-3 font-semibold w-10">#</th>
              <th class="px-3 py-3 font-semibold min-w-[230px]">Program Layanan</th>
              <th class="px-3 py-3 font-semibold min-w-[150px]">Kategori / Status</th>
              <th class="px-3 py-3 font-semibold text-right">Impresi</th>
              <th class="px-3 py-3 font-semibold text-right">Klik</th>
              <th class="px-3 py-3 font-semibold text-right">CTR</th>
              <th class="px-3 py-3 font-semibold text-right">Rank</th>
              <th class="px-3 py-3 font-semibold text-center min-w-[90px]">Tren</th>
              <th class="px-3 py-3 font-semibold text-center w-24">Aksi</th>
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
          <h2 class="text-lg font-bold">Tren Trafik Organik Mingguan</h2>
          <p class="text-xs text-slate-400">Total impresi &amp; klik seluruh landing page GRC Indonesia</p>
        </div>
        <div class="flex items-center gap-4 text-xs">
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-blue-500"></span> Impresi</span>
          <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-400"></span> Klik</span>
        </div>
      </div>
      <div class="w-full overflow-x-auto pt-4"><div class="min-w-[700px] h-72" id="chartContainer"></div></div>
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
      <h2 class="text-lg font-bold">🌐 Snapshot Kinerja Unit Bisnis Proxsis Academy</h2>
      <p class="text-xs text-slate-400 mt-1">Perbandingan performa organik mingguan antar brand.</p>
    </div>
    <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <table class="w-full text-left text-xs sm:text-sm">
        <thead class="bg-slate-900/70 text-slate-400 border-b border-slate-700">
          <tr>
            <th class="px-4 py-3 font-semibold">Brand / Unit Bisnis</th>
            <th class="px-4 py-3 font-semibold">Fokus</th>
            <th class="px-4 py-3 font-semibold text-center">LP Aktif</th>
            <th class="px-4 py-3 font-semibold text-right">Impresi/Mgg</th>
            <th class="px-4 py-3 font-semibold text-right">Klik/Mgg</th>
            <th class="px-4 py-3 font-semibold text-right">Avg CTR</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-700" id="brandsBody"></tbody>
      </table>
    </div>
  </div>

</div>

<!-- MODAL -->
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
      <div class="text-center"><div class="text-[10px] text-slate-400">Impresi</div><div class="text-lg font-bold" id="mImpr">-</div></div>
      <div class="text-center"><div class="text-[10px] text-slate-400">Klik</div><div class="text-lg font-bold text-blue-400" id="mClicks">-</div></div>
      <div class="text-center"><div class="text-[10px] text-slate-400">CTR</div><div class="text-lg font-bold text-emerald-400" id="mCtr">-</div></div>
      <div class="text-center"><div class="text-[10px] text-slate-400">Rank</div><div class="text-lg font-bold text-amber-400" id="mRank">-</div></div>
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

const fmt = n => (n||0).toLocaleString('id-ID');
const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function rec(id){ return RECS[String(id)] || {masalah:[],solusi:[],rekomendasi:[],perbaikan:{},prioritas:1}; }

function init(){
  document.getElementById('dataStamp').textContent = META.stamp;
  document.getElementById('totalPortfolio').textContent = PRODUCTS.length + ' Program';
  renderKPI(); renderMatrix(); renderAksi(); renderKompetitor(); renderTrends(); renderBrands();
}

function renderKPI(){
  const impr = PRODUCTS.reduce((a,p)=>a+p.total_impr,0);
  const clicks = PRODUCTS.reduce((a,p)=>a+p.total_clicks,0);
  const ctr = impr ? (clicks/impr*100).toFixed(2) : 0;
  const aktif = PRODUCTS.filter(p=>p.status.toLowerCase()==='aktif').length;
  const top = [...PRODUCTS].sort((a,b)=>b.total_clicks-a.total_clicks)[0] || {};
  const needAction = PRODUCTS.filter(p=>rec(p.id).prioritas>=4).length;
  const cards = [
    ['Total Impresi Organik', fmt(impr), 'GSC kumulatif', 'text-slate-100'],
    ['Total Klik Organik', fmt(clicks), 'CTR rata-rata '+ctr+'%', 'text-blue-400'],
    ['Status Landing Page', aktif+' Aktif / '+(PRODUCTS.length-aktif)+' Draft', 'Target min 2 LP baru/mgg', 'text-slate-100'],
    ['Perlu Tindakan', needAction+' Program', 'Prioritas aksi tinggi', 'text-amber-400'],
  ];
  document.getElementById('kpiRow').innerHTML = cards.map(([t,v,s,c])=>`
    <div class="bg-slate-800 border border-slate-700 rounded-xl p-4">
      <div class="text-xs font-medium text-slate-400 mb-1">${t}</div>
      <div class="text-2xl sm:text-3xl font-extrabold ${c}">${v}</div>
      <div class="text-[10px] text-slate-500 mt-1">${s}</div>
    </div>`).join('') + `
    <div class="bg-slate-800 border border-emerald-500/30 rounded-xl p-4 col-span-2 lg:col-span-4">
      <div class="text-xs font-medium text-slate-400 mb-1">Top Star Performer</div>
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

  let rows = PRODUCTS.filter(p=>{
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
  document.getElementById('rowCountLabel').textContent = `Menampilkan ${rows.length} dari ${PRODUCTS.length} program`;

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
    const prBadge = pr>=5 ? '<span class="badge bg-rose-500/20 text-rose-300">P5</span>'
                  : pr>=4 ? '<span class="badge bg-amber-500/20 text-amber-300">P4</span>'
                  : pr>=3 ? '<span class="badge bg-blue-500/20 text-blue-300">P3</span>'
                  : '<span class="badge bg-slate-600/40 text-slate-400">P1</span>';
    return `<tr class="hover:bg-slate-700/30">
      <td class="px-3 py-3 text-slate-500 font-mono text-xs">${p.id}</td>
      <td class="px-3 py-3">
        <div class="font-medium">${esc(p.name)}</div>
        ${p.url?`<a href="${esc(p.url)}" target="_blank" class="text-[11px] text-blue-400/80 hover:text-blue-300 truncate block max-w-xs">${esc(p.url)}</a>`:'<span class="text-[10px] text-amber-400/70 italic">Belum ada URL live</span>'}
      </td>
      <td class="px-3 py-3"><div class="text-xs text-slate-400">${esc(p.category)}</div><div class="mt-1 flex gap-1">${badge}${prBadge}</div></td>
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
  const rows = [...PRODUCTS].sort((a,b)=>rec(b.id).prioritas-rec(a.id).prioritas || b.total_impr-a.total_impr);
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
  const keys = Object.keys(COMPETITORS||{});
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
        <td class="px-3 py-2 text-center">${gap?'<span class="badge bg-rose-500/20 text-rose-300">GAP</span>':'<span class="badge bg-emerald-500/10 text-emerald-400">unggul</span>'}</td>
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
              <th class="px-3 py-2 font-semibold">Keyword</th>
              <th class="px-3 py-2 font-semibold text-right">Volume</th>
              <th class="px-3 py-2 font-semibold text-right">SD</th>
              <th class="px-3 py-2 font-semibold">Peringkat Teratas</th>
              <th class="px-3 py-2 font-semibold text-right">Posisi Kita</th>
              <th class="px-3 py-2 font-semibold text-center">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-700">${rows}</tbody>
        </table>
      </div>
    </div>`;
  }).join('');
}

function renderTrends(){
  const totals = {};
  PRODUCTS.forEach(p=>p.weeks.forEach(w=>{
    if (!totals[w.w]) totals[w.w] = {w:w.w, impr:0, clicks:0};
    totals[w.w].impr += w.impr; totals[w.w].clicks += w.clicks;
  }));
  const data = Object.values(totals).sort((a,b)=>parseInt(a.w.slice(1))-parseInt(b.w.slice(1)));
  if (data.length<2){ document.getElementById('chartContainer').innerHTML='<div class="text-slate-500 text-sm">Data mingguan belum cukup.</div>'; return; }
  const W=800,H=240,pad=40,cw=W-pad*2,ch=H-pad*2;
  const maxI=Math.max(...data.map(d=>d.impr),1), maxC=Math.max(...data.map(d=>d.clicks),1);
  const line=(key,max)=>data.map((d,i)=>{
    const x=pad+i/(data.length-1)*cw, y=pad+ch-(d[key]/max)*ch;
    return x.toFixed(1)+','+y.toFixed(1);
  }).join(' ');
  document.getElementById('chartContainer').innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" class="w-full h-full">
      <line x1="${pad}" y1="${pad}" x2="${W-pad}" y2="${pad}" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="3,3"/>
      <line x1="${pad}" y1="${pad+ch/2}" x2="${W-pad}" y2="${pad+ch/2}" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="3,3"/>
      <line x1="${pad}" y1="${pad+ch}" x2="${W-pad}" y2="${pad+ch}" stroke="currentColor" stroke-opacity="0.2"/>
      <polyline fill="none" stroke="#3b82f6" stroke-width="2.5" points="${line('impr',maxI)}"/>
      <polyline fill="none" stroke="#34d399" stroke-width="2.5" stroke-dasharray="4,2" points="${line('clicks',maxC)}"/>
      ${data.map((d,i)=>{
        const x=pad+i/(data.length-1)*cw, y=pad+ch-(d.impr/maxI)*ch;
        return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="#3b82f6"><title>${d.w}: ${fmt(d.impr)} impresi, ${d.clicks} klik</title></circle>`;
      }).join('')}
      ${data.filter((_,i)=>i%4===0||i===data.length-1).map(d=>{
        const i=data.indexOf(d), x=pad+i/(data.length-1)*cw;
        return `<text x="${x.toFixed(1)}" y="${H-10}" fill="currentColor" opacity="0.6" font-size="10" text-anchor="middle">${d.w}</text>`;
      }).join('')}
    </svg>`;

  const cats = {};
  PRODUCTS.forEach(p=>{
    if (!cats[p.category]) cats[p.category]={n:0,clicks:0,impr:0};
    cats[p.category].n++; cats[p.category].clicks+=p.total_clicks; cats[p.category].impr+=p.total_impr;
  });
  const totalClicks = PRODUCTS.reduce((a,p)=>a+p.total_clicks,0)||1;
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

  const top = [...PRODUCTS].sort((a,b)=>b.total_clicks-a.total_clicks).slice(0,5);
  document.getElementById('topKeywords').innerHTML = top.map((p,i)=>`
    <div class="py-2.5 flex items-center justify-between">
      <div><div class="font-semibold">${i+1}. ${esc(p.kw_utama)}</div>
      <div class="text-[11px] text-slate-400">${esc(p.name)}</div></div>
      <div class="text-right"><div class="font-bold text-emerald-400">${p.total_clicks} Klik</div>
      <div class="text-[10px] text-slate-400">CTR ${p.ctr}% • Posisi ${p.latest_rank||'-'}</div></div>
    </div>`).join('');
}

function renderBrands(){
  document.getElementById('brandsBody').innerHTML = (BRANDS||[]).map(b=>`
    <tr class="hover:bg-slate-700/30">
      <td class="px-4 py-3 font-semibold">${esc(b.brand)}</td>
      <td class="px-4 py-3 text-xs text-slate-400">${esc(b.focus)}</td>
      <td class="px-4 py-3 text-center font-mono">${b.active_lp}</td>
      <td class="px-4 py-3 text-right font-mono">${fmt(b.impr)}</td>
      <td class="px-4 py-3 text-right font-mono font-semibold text-blue-400">${b.clicks}</td>
      <td class="px-4 py-3 text-right font-mono font-semibold text-emerald-400">${b.ctr}</td>
    </tr>`).join('');
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
window.onload = init;
</script>
</body>
</html>
"""


def main():
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


if __name__ == "__main__":
    main()
