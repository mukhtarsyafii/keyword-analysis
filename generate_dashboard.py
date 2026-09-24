import json

with open('/Users/mukhtarsyafii/.gemini/antigravity/scratch/data_prepared.json') as f:
    data = json.load(f)

products_json = json.dumps(data["products"])
brands_json = json.dumps(data["brands"])
audits_json = json.dumps(data["audits"])
weekly_json = json.dumps(data["weekly_chart"])

html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Kinerja Keyword & Produk — GRC Indonesia (Proxsis)</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    /* Custom scrollbar */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(150, 150, 150, 0.3); border-radius: 9999px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(150, 150, 150, 0.5); }}
    
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 0.125rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 500;
    }}
    .tab-btn.active {{
      background-color: var(--primary, #3b82f6);
      color: var(--primary-foreground, #ffffff);
      border-color: transparent;
    }}
    .pill-btn.active {{
      background-color: var(--primary, #3b82f6);
      color: #ffffff;
    }}
  </style>
</head>
<body class="bg-[var(--background,#0f172a)] text-[var(--foreground,#f8fafc)] antialiased p-4 sm:p-6 min-h-screen">

  <div class="max-w-7xl mx-auto space-y-6">
    
    <!-- Top Header -->
    <header class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-2xl p-5 shadow-sm">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Live Intel GSC Tracker
            </span>
            <span class="text-xs text-[var(--muted-foreground,#94a3b8)]">Tahun 2026 • Periode W1 – W36</span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--foreground,#f8fafc)]">
            Dashboard Kinerja Keyword & Produk Layanan
          </h1>
          <p class="text-sm text-[var(--muted-foreground,#94a3b8)] mt-1">
            GRC Indonesia • Proxsis Academy • Pemantauan Posisi Organik & Evaluasi Landing Page
          </p>
        </div>
        
        <div class="flex items-center gap-3">
          <div class="text-right hidden sm:block">
            <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">Total Portofolio</div>
            <div class="text-lg font-bold text-[var(--foreground,#f8fafc)]">54 Program Pelatihan</div>
          </div>
          <button onclick="resetFilters()" class="px-3 py-2 text-xs font-medium rounded-lg border border-[var(--border,#334155)] hover:bg-[var(--secondary,#334155)] transition-colors">
            Reset Filter
          </button>
        </div>
      </div>
    </header>

    <!-- KPI Summary Stats -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- KPI 1 -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div class="text-xs font-medium text-[var(--muted-foreground,#94a3b8)] mb-1">Total Impresi Organik</div>
        <div class="text-2xl sm:text-3xl font-extrabold text-[var(--foreground,#f8fafc)]">36.952</div>
        <div class="flex items-center gap-1.5 mt-2 text-xs text-emerald-400">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
          <span>Puncak di W6 (1.937/mgg)</span>
        </div>
        <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)] mt-0.5">Google Search Console W1–W36</div>
      </div>

      <!-- KPI 2 -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div class="text-xs font-medium text-[var(--muted-foreground,#94a3b8)] mb-1">Total Klik Organik</div>
        <div class="text-2xl sm:text-3xl font-extrabold text-blue-400">835 <span class="text-sm font-medium text-[var(--muted-foreground,#94a3b8)]">Klik</span></div>
        <div class="flex items-center gap-1.5 mt-2 text-xs text-[var(--muted-foreground,#94a3b8)]">
          <span class="font-semibold text-emerald-400">CTR Rata-rata 2.26%</span>
        </div>
        <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)] mt-0.5">Rasio kunjungan nyata dari pencarian</div>
      </div>

      <!-- KPI 3 -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div class="text-xs font-medium text-[var(--muted-foreground,#94a3b8)] mb-1">Status Landing Page</div>
        <div class="text-2xl sm:text-3xl font-extrabold text-[var(--foreground,#f8fafc)]">25 <span class="text-sm font-normal text-emerald-400">Aktif</span> / <span class="text-sm font-normal text-amber-400">29 Draft</span></div>
        <div class="flex items-center gap-1.5 mt-2 text-xs text-[var(--muted-foreground,#94a3b8)]">
          <span>Target: Min 2 LP Baru / Minggu</span>
        </div>
        <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)] mt-0.5">54 Total silabus terpetakan</div>
      </div>

      <!-- KPI 4 -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div class="text-xs font-medium text-[var(--muted-foreground,#94a3b8)] mb-1">Top Star Performer</div>
        <div class="text-base sm:text-lg font-bold text-emerald-400 truncate" title="ICoFR Intensive Training">ICoFR Intensive Training</div>
        <div class="text-xs font-semibold text-[var(--foreground,#f8fafc)] mt-1">
          233 Klik • CTR 9.64%
        </div>
        <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)] mt-1">Peringkat ~9 Google • Search Intent Tinggi</div>
      </div>

    </div>

    <!-- Navigation Tabs -->
    <div class="flex flex-wrap items-center gap-2 border-b border-[var(--border,#334155)] pb-3">
      <button onclick="switchTab('tracker')" id="btn-tab-tracker" class="tab-btn active px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-[var(--border,#334155)] transition-all">
        📊 Katalog & Keyword Tracker
      </button>
      <button onclick="switchTab('trends')" id="btn-tab-trends" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-[var(--border,#334155)] transition-all text-[var(--muted-foreground,#94a3b8)] hover:text-[var(--foreground,#f8fafc)]">
        📈 Tren Performa Mingguan
      </button>
      <button onclick="switchTab('opportunities')" id="btn-tab-opportunities" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-[var(--border,#334155)] transition-all text-[var(--muted-foreground,#94a3b8)] hover:text-[var(--foreground,#f8fafc)]">
        ⚡ Peluang Cepat (High Imp, Low CTR)
      </button>
      <button onclick="switchTab('audit')" id="btn-tab-audit" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-[var(--border,#334155)] transition-all text-[var(--muted-foreground,#94a3b8)] hover:text-[var(--foreground,#f8fafc)]">
        ⚠️ Audit Kesesuaian Konten
      </button>
      <button onclick="switchTab('brands')" id="btn-tab-brands" class="tab-btn px-4 py-2 text-xs sm:text-sm font-medium rounded-lg border border-[var(--border,#334155)] transition-all text-[var(--muted-foreground,#94a3b8)] hover:text-[var(--foreground,#f8fafc)]">
        🌐 Komparasi Lintas Brand Proxsis
      </button>
    </div>

    <!-- VIEW 1: KATALOG & KEYWORD TRACKER -->
    <div id="view-tracker" class="space-y-4">
      
      <!-- Filters and Controls -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm space-y-4">
        <div class="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          
          <!-- Search input -->
          <div class="relative flex-1">
            <svg class="w-4 h-4 absolute left-3 top-3 text-[var(--muted-foreground,#94a3b8)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            <input type="text" id="searchInput" oninput="renderTable()" placeholder="Cari nama produk, keyword utama, atau target keyword..." class="w-full pl-9 pr-4 py-2 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs sm:text-sm text-[var(--foreground,#f8fafc)] placeholder-[var(--muted-foreground,#94a3b8)] focus:outline-none focus:ring-2 focus:ring-blue-500">
          </div>

          <!-- Sort dropdown -->
          <div class="flex items-center gap-2">
            <span class="text-xs text-[var(--muted-foreground,#94a3b8)] whitespace-nowrap">Urutkan:</span>
            <select id="sortSelect" onchange="renderTable()" class="px-3 py-2 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)] text-xs text-[var(--foreground,#f8fafc)] focus:outline-none">
              <option value="clicks-desc">Klik Organik (Tertinggi)</option>
              <option value="impr-desc">Impresi (Tertinggi)</option>
              <option value="ctr-desc">CTR (Tertinggi)</option>
              <option value="rank-asc">Ranking Terbaik (Google SERP)</option>
              <option value="name-asc">Nama Program (A-Z)</option>
            </select>
          </div>

        </div>

        <!-- Filter Pills -->
        <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[var(--border,#334155)]">
          <!-- Categories -->
          <div class="flex flex-wrap items-center gap-1.5 text-xs">
            <span class="text-[var(--muted-foreground,#94a3b8)] mr-1">Kategori:</span>
            <button onclick="setCategoryFilter('all')" class="pill-btn active cat-btn px-2.5 py-1 rounded-md border border-[var(--border,#334155)] hover:bg-[var(--secondary,#334155)]" data-cat="all">Semua</button>
            <button onclick="setCategoryFilter('Sertifikasi BNSP / Profesi')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-[var(--border,#334155)] hover:bg-[var(--secondary,#334155)] text-[var(--muted-foreground,#94a3b8)]" data-cat="Sertifikasi BNSP / Profesi">Sertifikasi BNSP</button>
            <button onclick="setCategoryFilter('Standar ISO & Kepatuhan')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-[var(--border,#334155)] hover:bg-[var(--secondary,#334155)] text-[var(--muted-foreground,#94a3b8)]" data-cat="Standar ISO & Kepatuhan">Standar ISO</button>
            <button onclick="setCategoryFilter('Audit, Fraud & Forensik')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-[var(--border,#334155)] hover:bg-[var(--secondary,#334155)] text-[var(--muted-foreground,#94a3b8)]" data-cat="Audit, Fraud & Forensik">Audit & Fraud</button>
            <button onclick="setCategoryFilter('Tata Kelola & BUMN')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-[var(--border,#334155)] hover:bg-[var(--secondary,#334155)] text-[var(--muted-foreground,#94a3b8)]" data-cat="Tata Kelola & BUMN">Tata Kelola & BUMN</button>
            <button onclick="setCategoryFilter('AI & Data Governance')" class="pill-btn cat-btn px-2.5 py-1 rounded-md border border-[var(--border,#334155)] hover:bg-[var(--secondary,#334155)] text-[var(--muted-foreground,#94a3b8)]" data-cat="AI & Data Governance">AI & Data</button>
          </div>

          <!-- Status -->
          <div class="flex items-center gap-1.5 text-xs">
            <span class="text-[var(--muted-foreground,#94a3b8)] mr-1">Status:</span>
            <button onclick="setStatusFilter('all')" class="status-btn px-2 py-1 rounded border border-[var(--border,#334155)] bg-blue-600 text-white" data-status="all">Semua</button>
            <button onclick="setStatusFilter('Aktif')" class="status-btn px-2 py-1 rounded border border-[var(--border,#334155)] text-[var(--muted-foreground,#94a3b8)]" data-status="Aktif">Aktif (25)</button>
            <button onclick="setStatusFilter('Draft')" class="status-btn px-2 py-1 rounded border border-[var(--border,#334155)] text-[var(--muted-foreground,#94a3b8)]" data-status="Draft">Draft (29)</button>
          </div>
        </div>

      </div>

      <!-- Products Table -->
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs sm:text-sm">
            <thead class="bg-[var(--background,#0f172a)]/70 text-[var(--muted-foreground,#94a3b8)] border-b border-[var(--border,#334155)]">
              <tr>
                <th class="px-4 py-3 font-semibold w-12">#</th>
                <th class="px-4 py-3 font-semibold min-w-[240px]">Program Layanan Pelatihan</th>
                <th class="px-4 py-3 font-semibold min-w-[160px]">Kategori & Status</th>
                <th class="px-4 py-3 font-semibold min-w-[200px]">Keyword Utama (Est. Vol)</th>
                <th class="px-4 py-3 font-semibold min-w-[180px]">Target Keyword</th>
                <th class="px-4 py-3 font-semibold text-right">Impresi</th>
                <th class="px-4 py-3 font-semibold text-right">Klik</th>
                <th class="px-4 py-3 font-semibold text-right">CTR</th>
                <th class="px-4 py-3 font-semibold text-right">Rank</th>
                <th class="px-4 py-3 font-semibold text-center w-24">Aksi</th>
              </tr>
            </thead>
            <tbody id="productsTableBody" class="divide-y divide-[var(--border,#334155)]">
              <!-- Rendered via JS -->
            </tbody>
          </table>
        </div>
        <div id="tableEmptyState" class="hidden p-8 text-center text-sm text-[var(--muted-foreground,#94a3b8)]">
          Tidak ditemukan produk yang cocok dengan pencarian atau filter Anda.
        </div>
        <div class="px-4 py-3 border-t border-[var(--border,#334155)] bg-[var(--background,#0f172a)]/40 flex items-center justify-between text-xs text-[var(--muted-foreground,#94a3b8)]">
          <span id="rowCountLabel">Menampilkan 54 program</span>
          <span>Klik tombol "Detail" untuk membuka breakdown mingguan & rekomendasi SEO</span>
        </div>
      </div>

    </div>

    <!-- VIEW 2: TREN KINERJA MINGGUAN -->
    <div id="view-trends" class="hidden space-y-6">
      
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 class="text-lg font-bold text-[var(--foreground,#f8fafc)]">Tren Trafik Organik Mingguan (W1 – W36)</h2>
            <p class="text-xs text-[var(--muted-foreground,#94a3b8)]">Pergerakan total Impresi dan Klik organik dari seluruh Landing Page GRC Indonesia</p>
          </div>
          <div class="flex items-center gap-4 text-xs">
            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-blue-500"></span> Impresi</span>
            <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-400"></span> Klik</span>
          </div>
        </div>

        <!-- SVG Interactive Chart Container -->
        <div class="w-full overflow-x-auto pt-4">
          <div class="min-w-[700px] h-72 relative" id="chartContainer">
            <!-- Chart rendered via JS -->
          </div>
        </div>
        <div class="text-[11px] text-[var(--muted-foreground,#94a3b8)] text-center">
          💡 Catatan: Lonjakan impresi tertinggi terjadi pada W5 – W9 (hingga 1.937 impresi/minggu), kemudian mengalami penyesuaian seiring rotasi indeks Google.
        </div>
      </div>

      <!-- Category Performance Summary -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm space-y-3">
          <h3 class="text-sm font-bold text-[var(--foreground,#f8fafc)]">Distribusi Klik per Kategori Program</h3>
          <div class="space-y-3 pt-2" id="categoryDistributionBars">
            <!-- Rendered by JS -->
          </div>
        </div>

        <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm space-y-3">
          <h3 class="text-sm font-bold text-[var(--foreground,#f8fafc)]">Top 5 Keyword dengan Konversi Klik Tertinggi</h3>
          <div class="divide-y divide-[var(--border,#334155)] text-xs" id="topKeywordsList">
            <!-- Rendered by JS -->
          </div>
        </div>

      </div>

    </div>

    <!-- VIEW 3: PELUANG CEPAT / QUICK WINS -->
    <div id="view-opportunities" class="hidden space-y-4">
      
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm">
        <h2 class="text-lg font-bold text-amber-400 flex items-center gap-2">
          <span>⚡</span> Peluang Cepat: Halaman Tinggi Impresi Namun Rendah CTR
        </h2>
        <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1">
          Halaman-halaman berikut telah memiliki visibilitas sangat tinggi di Google (SERP rank bagus), namun rasio kliknya masih rendah. Mengoptimasi <strong>Meta Title</strong> dan <strong>Meta Description</strong> pada halaman ini akan memberikan lonjakan klik tercepat tanpa perlu backlink baru.
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="opportunityCards">
        <!-- Rendered by JS -->
      </div>

    </div>

    <!-- VIEW 4: AUDIT KESESUAIAN KONTEN -->
    <div id="view-audit" class="hidden space-y-4">
      
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-rose-400 flex items-center gap-2">
              <span>⚠️</span> Temuan Audit Kesesuaian Konten (Content Mismatch)
            </h2>
            <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1">
              Catatan anomali dari tab <em>Content Mismatch Audit</em> yang membutuhkan perbaikan segera dari PIC Web & SEO.
            </p>
          </div>
          <span class="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            Perlu Tindakan
          </span>
        </div>
      </div>

      <div class="space-y-3" id="auditListContainer">
        <!-- Rendered by JS -->
      </div>

    </div>

    <!-- VIEW 5: KOMPARASI LINTAS BRAND PROXSIS -->
    <div id="view-brands" class="hidden space-y-4">
      
      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-5 shadow-sm">
        <h2 class="text-lg font-bold text-[var(--foreground,#f8fafc)] flex items-center gap-2">
          <span>🌐</span> Snapshot Kinerja Unit Bisnis Proxsis Academy (Minggu W33)
        </h2>
        <p class="text-xs text-[var(--muted-foreground,#94a3b8)] mt-1">
          Perbandingan performa organik mingguan antar brand di lingkungan Proxsis Academy berdasarkan tab Dashboard utama.
        </p>
      </div>

      <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl shadow-sm overflow-hidden">
        <table class="w-full text-left text-xs sm:text-sm">
          <thead class="bg-[var(--background,#0f172a)]/70 text-[var(--muted-foreground,#94a3b8)] border-b border-[var(--border,#334155)]">
            <tr>
              <th class="px-4 py-3 font-semibold">Nama Brand / Unit Bisnis</th>
              <th class="px-4 py-3 font-semibold">Fokus Pelatihan & Layanan</th>
              <th class="px-4 py-3 font-semibold text-center">LP Aktif</th>
              <th class="px-4 py-3 font-semibold text-right">Impresi / Mgg</th>
              <th class="px-4 py-3 font-semibold text-right">Klik / Mgg</th>
              <th class="px-4 py-3 font-semibold text-right">Avg CTR</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--border,#334155)]" id="brandsTableBody">
            <!-- Rendered by JS -->
          </tbody>
        </table>
      </div>

    </div>

  </div>

  <!-- Detail Modal Drawer -->
  <div id="detailModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
    <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
      
      <div class="flex items-start justify-between gap-4 border-b border-[var(--border,#334155)] pb-4">
        <div>
          <div class="flex items-center gap-2 mb-1" id="modalBadges"></div>
          <h3 class="text-xl font-bold text-[var(--foreground,#f8fafc)]" id="modalTitle"></h3>
          <a id="modalUrl" href="#" target="_blank" class="text-xs text-blue-400 hover:underline flex items-center gap-1 mt-1 break-all">
            <svg class="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
            <span id="modalUrlText"></span>
          </a>
        </div>
        <button onclick="closeModal()" class="p-1.5 rounded-lg border border-[var(--border,#334155)] text-[var(--muted-foreground,#94a3b8)] hover:text-white hover:bg-[var(--secondary,#334155)]">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <!-- Performance Stats inside Modal -->
      <div class="grid grid-cols-4 gap-3 bg-[var(--background,#0f172a)]/60 rounded-xl p-3 border border-[var(--border,#334155)]">
        <div class="text-center">
          <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)]">Total Impresi</div>
          <div class="text-lg font-bold text-[var(--foreground,#f8fafc)]" id="modalImpr">-</div>
        </div>
        <div class="text-center">
          <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)]">Total Klik</div>
          <div class="text-lg font-bold text-blue-400" id="modalClicks">-</div>
        </div>
        <div class="text-center">
          <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)]">CTR Kumulatif</div>
          <div class="text-lg font-bold text-emerald-400" id="modalCtr">-</div>
        </div>
        <div class="text-center">
          <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)]">Posisi Rank SERP</div>
          <div class="text-lg font-bold text-amber-400" id="modalRank">-</div>
        </div>
      </div>

      <!-- Keyword Architecture -->
      <div class="space-y-2">
        <h4 class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground,#94a3b8)]">Arsitektur Kata Kunci & Search Volume</h4>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
          <div class="p-3 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)]">
            <span class="text-[10px] font-semibold text-blue-400">KEYWORD UTAMA</span>
            <div class="font-medium text-[var(--foreground,#f8fafc)] mt-0.5" id="modalKwUtama">-</div>
            <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)] mt-1">Est. Volume: <span class="font-semibold text-white" id="modalVolUtama">-</span> / bln</div>
          </div>
          <div class="p-3 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)]">
            <span class="text-[10px] font-semibold text-emerald-400">TARGET TRANSAKSIONAL</span>
            <div class="font-medium text-[var(--foreground,#f8fafc)] mt-0.5" id="modalKwTarget">-</div>
            <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)] mt-1">Est. Volume: <span class="font-semibold text-white" id="modalVolTarget">-</span> / bln</div>
          </div>
          <div class="p-3 rounded-lg bg-[var(--background,#0f172a)] border border-[var(--border,#334155)]">
            <span class="text-[10px] font-semibold text-amber-400">INFORMASIONAL (TOP FUNNEL)</span>
            <div class="font-medium text-[var(--foreground,#f8fafc)] mt-0.5" id="modalKwInfo">-</div>
            <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)] mt-1">Est. Volume: <span class="font-semibold text-white" id="modalVolInfo">-</span> / bln</div>
          </div>
        </div>
      </div>

      <!-- Actionable Advice -->
      <div class="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 space-y-1.5">
        <h5 class="text-xs font-bold text-blue-400 flex items-center gap-1.5">
          <span>🎯</span> Rekomendasi Optimasi SEO & Lead Conversion
        </h5>
        <p class="text-xs text-[var(--foreground,#f8fafc)]" id="modalAdvice">
          -
        </p>
      </div>

      <!-- Close Button -->
      <div class="text-right pt-2 border-t border-[var(--border,#334155)]">
        <button onclick="closeModal()" class="px-4 py-2 text-xs font-semibold rounded-lg bg-[var(--secondary,#334155)] text-white hover:bg-slate-600 transition-colors">
          Tutup Rincian
        </button>
      </div>

    </div>
  </div>

  <!-- Raw Data Injection -->
  <script>
    const productsData = {products_json};
    const brandsData = {brands_json};
    const auditsData = {audits_json};
    const weeklyData = {weekly_json};

    let currentCategory = 'all';
    let currentStatus = 'all';

    function init() {{
      renderTable();
      renderTrends();
      renderOpportunities();
      renderAudits();
      renderBrands();
    }}

    function switchTab(tabId) {{
      const tabs = ['tracker', 'trends', 'opportunities', 'audit', 'brands'];
      tabs.forEach(t => {{
        const el = document.getElementById('view-' + t);
        const btn = document.getElementById('btn-tab-' + t);
        if (t === tabId) {{
          el.classList.remove('hidden');
          btn.classList.add('active');
          btn.classList.remove('text-[var(--muted-foreground,#94a3b8)]');
        }} else {{
          el.classList.add('hidden');
          btn.classList.remove('active');
          btn.classList.add('text-[var(--muted-foreground,#94a3b8)]');
        }}
      }});
    }}

    function setCategoryFilter(cat) {{
      currentCategory = cat;
      document.querySelectorAll('.cat-btn').forEach(btn => {{
        if (btn.dataset.cat === cat) {{
          btn.classList.add('active');
          btn.classList.remove('text-[var(--muted-foreground,#94a3b8)]');
        }} else {{
          btn.classList.remove('active');
          btn.classList.add('text-[var(--muted-foreground,#94a3b8)]');
        }}
      }});
      renderTable();
    }}

    function setStatusFilter(status) {{
      currentStatus = status;
      document.querySelectorAll('.status-btn').forEach(btn => {{
        if (btn.dataset.status === status) {{
          btn.classList.add('bg-blue-600', 'text-white');
          btn.classList.remove('text-[var(--muted-foreground,#94a3b8)]');
        }} else {{
          btn.classList.remove('bg-blue-600', 'text-white');
          btn.classList.add('text-[var(--muted-foreground,#94a3b8)]');
        }}
      }});
      renderTable();
    }}

    function resetFilters() {{
      document.getElementById('searchInput').value = '';
      document.getElementById('sortSelect').value = 'clicks-desc';
      setCategoryFilter('all');
      setStatusFilter('all');
    }}

    function renderTable() {{
      const query = document.getElementById('searchInput').value.toLowerCase().trim();
      const sortVal = document.getElementById('sortSelect').value;
      const tbody = document.getElementById('productsTableBody');
      const emptyState = document.getElementById('tableEmptyState');
      const rowCountLabel = document.getElementById('rowCountLabel');

      let filtered = productsData.filter(p => {{
        const matchCat = currentCategory === 'all' || p.category === currentCategory;
        const matchStatus = currentStatus === 'all' || p.status.toLowerCase() === currentStatus.toLowerCase();
        const matchQuery = !query || 
          p.name.toLowerCase().includes(query) ||
          p.kw_utama.toLowerCase().includes(query) ||
          p.kw_target.toLowerCase().includes(query) ||
          p.kw_info.toLowerCase().includes(query);
        return matchCat && matchStatus && matchQuery;
      }});

      // Sorting
      filtered.sort((a, b) => {{
        if (sortVal === 'clicks-desc') return b.total_clicks - a.total_clicks;
        if (sortVal === 'impr-desc') return b.total_impr - a.total_impr;
        if (sortVal === 'ctr-desc') return b.ctr - a.ctr;
        if (sortVal === 'rank-asc') {{
          const rA = a.latest_rank || 999;
          const rB = b.latest_rank || 999;
          return rA - rB;
        }}
        if (sortVal === 'name-asc') return a.name.localeCompare(b.name);
        return 0;
      }});

      if (filtered.length === 0) {{
        tbody.innerHTML = '';
        emptyState.classList.remove('hidden');
        rowCountLabel.innerText = 'Menampilkan 0 program';
        return;
      }}

      emptyState.classList.add('hidden');
      rowCountLabel.innerText = `Menampilkan ${{filtered.length}} dari ${{productsData.length}} program`;

      tbody.innerHTML = filtered.map(p => {{
        const isLive = p.status.toLowerCase() === 'aktif';
        const statusBadge = isLive 
          ? `<span class="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Aktif</span>`
          : `<span class="badge bg-amber-500/10 text-amber-400 border border-amber-500/20">Draft</span>`;

        let ctrColor = 'text-[var(--muted-foreground,#94a3b8)]';
        if (p.ctr >= 5.0) ctrColor = 'text-emerald-400 font-bold';
        else if (p.ctr >= 2.0) ctrColor = 'text-blue-400 font-semibold';
        else if (p.total_impr > 1000 && p.ctr < 1.0) ctrColor = 'text-rose-400 font-semibold';

        const rankDisplay = p.latest_rank > 0 
          ? `<span class="font-medium text-amber-300">#${{p.latest_rank}}</span>`
          : `<span class="text-[var(--muted-foreground,#94a3b8)]">-</span>`;

        return `
          <tr class="hover:bg-[var(--secondary,#1e293b)]/30 transition-colors">
            <td class="px-4 py-3 text-[var(--muted-foreground,#94a3b8)] font-mono text-xs">${{p.id}}</td>
            <td class="px-4 py-3">
              <div class="font-medium text-[var(--foreground,#f8fafc)]">${{p.name}}</div>
              ${{p.url ? `<a href="${{p.url}}" target="_blank" class="text-[11px] text-blue-400/80 hover:text-blue-300 truncate block max-w-xs">${{p.url}}</a>` : '<span class="text-[10px] text-amber-400/70 italic">Belum ada URL live</span>'}}
            </td>
            <td class="px-4 py-3">
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">${{p.category}}</div>
              <div class="mt-1">${{statusBadge}}</div>
            </td>
            <td class="px-4 py-3">
              <div class="font-medium text-[var(--foreground,#f8fafc)]">${{p.kw_utama}}</div>
              <div class="text-[11px] text-[var(--muted-foreground,#94a3b8)]">Vol: <span class="font-medium text-white">${{p.vol_utama}}</span></div>
            </td>
            <td class="px-4 py-3">
              <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">${{p.kw_target}}</div>
              <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)]">Vol: ${{p.vol_target}}</div>
            </td>
            <td class="px-4 py-3 text-right font-mono text-xs text-[var(--foreground,#f8fafc)]">${{p.total_impr.toLocaleString('id-ID')}}</td>
            <td class="px-4 py-3 text-right font-mono text-xs font-semibold text-blue-400">${{p.total_clicks}}</td>
            <td class="px-4 py-3 text-right font-mono text-xs ${{ctrColor}}">${{p.ctr}}%</td>
            <td class="px-4 py-3 text-right font-mono text-xs">${{rankDisplay}}</td>
            <td class="px-4 py-3 text-center">
              <button onclick="openModal(${{p.id}})" class="px-2.5 py-1 text-xs font-medium rounded border border-blue-500/40 text-blue-400 hover:bg-blue-500/10 transition-colors">
                Detail
              </button>
            </td>
          </tr>
        `;
      }}).join('');
    }}

    function renderTrends() {{
      const container = document.getElementById('chartContainer');
      const maxImpr = Math.max(...weeklyData.map(w => w.impr));
      const maxClicks = Math.max(...weeklyData.map(w => w.clicks));
      
      const width = 800;
      const height = 240;
      const padding = 40;
      const chartW = width - padding * 2;
      const chartH = height - padding * 2;

      const ptsImpr = weeklyData.map((d, i) => {{
        const x = padding + (i / (weeklyData.length - 1)) * chartW;
        const y = padding + chartH - (d.impr / maxImpr) * chartH;
        return `${{x}},${{y}}`;
      }}).join(' ');

      const ptsClicks = weeklyData.map((d, i) => {{
        const x = padding + (i / (weeklyData.length - 1)) * chartW;
        const y = padding + chartH - (d.clicks / maxClicks) * chartH;
        return `${{x}},${{y}}`;
      }}).join(' ');

      const svgHtml = `
        <svg viewBox="0 0 ${{width}} ${{height}}" class="w-full h-full">
          <!-- Grid lines -->
          <line x1="${{padding}}" y1="${{padding}}" x2="${{width - padding}}" y2="${{padding}}" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="3,3" />
          <line x1="${{padding}}" y1="${{padding + chartH/2}}" x2="${{width - padding}}" y2="${{padding + chartH/2}}" stroke="currentColor" stroke-opacity="0.1" stroke-dasharray="3,3" />
          <line x1="${{padding}}" y1="${{padding + chartH}}" x2="${{width - padding}}" y2="${{padding + chartH}}" stroke="currentColor" stroke-opacity="0.2" />

          <!-- Impression line (Blue) -->
          <polyline fill="none" stroke="#3b82f6" stroke-width="2.5" points="${{ptsImpr}}" />

          <!-- Clicks line (Emerald) -->
          <polyline fill="none" stroke="#34d399" stroke-width="2.5" stroke-dasharray="4,2" points="${{ptsClicks}}" />

          <!-- Dots for impressions -->
          ${{weeklyData.map((d, i) => {{
            const x = padding + (i / (weeklyData.length - 1)) * chartW;
            const y = padding + chartH - (d.impr / maxImpr) * chartH;
            return `<circle cx="${{x}}" cy="${{y}}" r="3" fill="#3b82f6"><title>${{d.week}}: ${{d.impr}} Impresi, ${{d.clicks}} Klik</title></circle>`;
          }}).join('')}}

          <!-- X axis labels (sampled) -->
          ${{weeklyData.filter((_, i) => i % 4 === 0 || i === weeklyData.length - 1).map((d, idx, arr) => {{
            const origIndex = weeklyData.indexOf(d);
            const x = padding + (origIndex / (weeklyData.length - 1)) * chartW;
            return `<text x="${{x}}" y="${{height - 10}}" fill="currentColor" opacity="0.6" font-size="10" text-anchor="middle">${{d.week}}</text>`;
          }}).join('')}}
        </svg>
      `;
      container.innerHTML = svgHtml;

      // Category breakdown
      const catCounts = {{}};
      productsData.forEach(p => {{
        if (!catCounts[p.category]) catCounts[p.category] = {{ count: 0, clicks: 0, impr: 0 }};
        catCounts[p.category].count++;
        catCounts[p.category].clicks += p.total_clicks;
        catCounts[p.category].impr += p.total_impr;
      }});

      const catBars = document.getElementById('categoryDistributionBars');
      catBars.innerHTML = Object.entries(catCounts).map(([cat, val]) => {{
        const pct = Math.round((val.clicks / 835) * 100);
        return `
          <div>
            <div class="flex justify-between text-xs mb-1">
              <span class="font-medium text-[var(--foreground,#f8fafc)]">${{cat}} (${{val.count}} program)</span>
              <span class="text-blue-400 font-semibold">${{val.clicks}} klik (${{pct}}%)</span>
            </div>
            <div class="w-full bg-[var(--background,#0f172a)] rounded-full h-2 overflow-hidden border border-[var(--border,#334155)]">
              <div class="bg-blue-500 h-2 rounded-full" style="width: ${{pct}}%"></div>
            </div>
          </div>
        `;
      }}).join('');

      // Top 5 keywords
      const topKws = [...productsData].sort((a,b) => b.total_clicks - a.total_clicks).slice(0, 5);
      const topKwList = document.getElementById('topKeywordsList');
      topKwList.innerHTML = topKws.map((p, idx) => `
        <div class="py-2.5 flex items-center justify-between">
          <div>
            <div class="font-semibold text-[var(--foreground,#f8fafc)]">${{idx+1}}. ${{p.kw_utama}}</div>
            <div class="text-[11px] text-[var(--muted-foreground,#94a3b8)]">${{p.name}}</div>
          </div>
          <div class="text-right">
            <div class="font-bold text-emerald-400">${{p.total_clicks}} Klik</div>
            <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)]">CTR ${{p.ctr}}% • Posisi ${{p.latest_rank || '-'}}</div>
          </div>
        </div>
      `).join('');
    }}

    function renderOpportunities() {{
      const opps = productsData
        .filter(p => p.total_impr >= 800 && p.ctr < 2.0 && p.status.toLowerCase() === 'aktif')
        .sort((a,b) => b.total_impr - a.total_impr);

      const container = document.getElementById('opportunityCards');
      container.innerHTML = opps.map(p => `
        <div class="bg-[var(--card,#1e293b)] border border-amber-500/30 rounded-xl p-4 shadow-sm flex flex-col justify-between">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="badge bg-amber-500/10 text-amber-400 border border-amber-500/30 font-mono">Peringkat #${{p.latest_rank || 'Top 10'}}</span>
              <span class="text-xs text-rose-400 font-bold">CTR Rendah: ${{p.ctr}}%</span>
            </div>
            <h4 class="font-bold text-[var(--foreground,#f8fafc)]">${{p.name}}</h4>
            <div class="text-xs text-[var(--muted-foreground,#94a3b8)]">
              Keyword: <span class="text-white font-medium">"${{p.kw_utama}}"</span> (Vol: ${{p.vol_utama}})
            </div>
            <div class="grid grid-cols-2 gap-2 p-2 bg-[var(--background,#0f172a)] rounded-lg text-center text-xs mt-2">
              <div>
                <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)]">Impresi Terbuang</div>
                <div class="font-bold text-amber-400 text-sm">${{p.total_impr.toLocaleString('id-ID')}}</div>
              </div>
              <div>
                <div class="text-[10px] text-[var(--muted-foreground,#94a3b8)]">Klik Terkumpul</div>
                <div class="font-bold text-white text-sm">${{p.total_clicks}}</div>
              </div>
            </div>
          </div>
          <div class="mt-4 pt-3 border-t border-[var(--border,#334155)] flex items-center justify-between text-xs">
            <span class="text-[11px] text-[var(--muted-foreground,#94a3b8)]">Solusi: Rombak Meta Title & CTA</span>
            <button onclick="openModal(${{p.id}})" class="text-blue-400 hover:underline font-semibold">Buka Rencana</button>
          </div>
        </div>
      `).join('');
    }}

    function renderAudits() {{
      const container = document.getElementById('auditListContainer');
      container.innerHTML = auditsData.map(a => `
        <div class="bg-[var(--card,#1e293b)] border border-[var(--border,#334155)] rounded-xl p-4 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="badge ${{a.status === 'MISMATCH' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'}}">${{a.status}}</span>
              <span class="text-xs text-[var(--muted-foreground,#94a3b8)]">Tingkat Urgensi: <strong class="text-rose-400">${{a.severity}}</strong></span>
            </div>
            <span class="text-xs text-[var(--muted-foreground,#94a3b8)] font-mono">${{a.brand}} • Row #${{a.row}}</span>
          </div>
          <div>
            <h4 class="font-bold text-[var(--foreground,#f8fafc)]">${{a.name}}</h4>
            <a href="${{a.url}}" target="_blank" class="text-xs text-blue-400 hover:underline break-all block mt-0.5">${{a.url}}</a>
          </div>
          <div class="bg-[var(--background,#0f172a)]/80 rounded-lg p-3 text-xs space-y-1">
            <div class="text-rose-300 font-medium">Masalah: ${{a.issue}}</div>
            <div class="text-emerald-400 font-medium mt-1">Solusi Direkomendasikan: ${{a.action}}</div>
          </div>
        </div>
      `).join('');
    }}

    function renderBrands() {{
      const tbody = document.getElementById('brandsTableBody');
      tbody.innerHTML = brandsData.map(b => `
        <tr class="hover:bg-[var(--secondary,#1e293b)]/30 transition-colors">
          <td class="px-4 py-3 font-semibold text-[var(--foreground,#f8fafc)]">${{b.brand}}</td>
          <td class="px-4 py-3 text-xs text-[var(--muted-foreground,#94a3b8)]">${{b.focus}}</td>
          <td class="px-4 py-3 text-center font-mono font-medium">${{b.active_lp}}</td>
          <td class="px-4 py-3 text-right font-mono font-medium text-[var(--foreground,#f8fafc)]">${{b.impr.toLocaleString('id-ID')}}</td>
          <td class="px-4 py-3 text-right font-mono font-semibold text-blue-400">${{b.clicks}}</td>
          <td class="px-4 py-3 text-right font-mono font-semibold text-emerald-400">${{b.ctr}}</td>
        </tr>
      `).join('');
    }}

    function openModal(id) {{
      const p = productsData.find(item => item.id === id);
      if (!p) return;

      document.getElementById('modalTitle').innerText = p.name;
      document.getElementById('modalUrlText').innerText = p.url || 'Belum memiliki tautan landing page live';
      document.getElementById('modalUrl').href = p.url || '#';
      document.getElementById('modalImpr').innerText = p.total_impr.toLocaleString('id-ID');
      document.getElementById('modalClicks').innerText = p.total_clicks;
      document.getElementById('modalCtr').innerText = p.ctr + '%';
      document.getElementById('modalRank').innerText = p.latest_rank > 0 ? '#' + p.latest_rank : '-';

      document.getElementById('modalKwUtama').innerText = p.kw_utama;
      document.getElementById('modalVolUtama').innerText = p.vol_utama;
      document.getElementById('modalKwTarget').innerText = p.kw_target;
      document.getElementById('modalVolTarget').innerText = p.vol_target;
      document.getElementById('modalKwInfo').innerText = p.kw_info;
      document.getElementById('modalVolInfo').innerText = p.vol_info;

      const isLive = p.status.toLowerCase() === 'aktif';
      document.getElementById('modalBadges').innerHTML = `
        <span class="badge ${{isLive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}}">${{p.status}}</span>
        <span class="badge bg-blue-500/10 text-blue-400 border border-blue-500/20">${{p.category}}</span>
      `;

      let advice = '';
      if (!isLive) {{
        advice = 'Halaman ini masih dalam tahap DRAFT / PIPELINE. Prioritaskan penerbitan konten sesuai silabus dan daftarkan ke Google Search Console untuk mulai menangkap volume pencarian bulanan sebesar ' + p.vol_utama + '.';
      }} else if (p.total_clicks >= 50 && p.ctr >= 5.0) {{
        advice = '🌟 Halaman Bintang (Top Performer). Pertahankan posisi ranking SERP dengan memperbarui jadwal training terkini, menambah testimoni alumni korporat, dan pastikan form registrasi / CTA WhatsApp berkonversi optimal.';
      }} else if (p.total_impr >= 800 && p.ctr < 2.0) {{
        advice = '⚡ Peluang Quick Win. Impresi tinggi namun CTR rendah. Segera ganti Meta Title dengan format: "[Nama Pelatihan] 2026 Bersertifikat BNSP / ISO - GRC Indonesia" dan perjelas manfaat utama di meta description untuk memicu klik.';
      }} else {{
        advice = 'Halaman memiliki potensi stabil. Tingkatkan internal linking dari artikel blog informasional terkait topik "' + p.kw_info + '" menuju landing page transaksional ini.';
      }}
      document.getElementById('modalAdvice').innerText = advice;

      document.getElementById('detailModal').classList.remove('hidden');
    }}

    function closeModal() {{
      document.getElementById('detailModal').classList.add('hidden');
    }}

    // Close on backdrop click
    document.getElementById('detailModal').addEventListener('click', function(e) {{
      if (e.target === this) closeModal();
    }});

    window.onload = init;
  </script>
</body>
</html>
"""

with open('/Users/mukhtarsyafii/.gemini/antigravity/brain/c6c68bbe-3cc9-4b15-b1f6-efcac2aafc9c/dashboard.html', 'w') as f:
    f.write(html_content)

print("Dashboard successfully generated.")
