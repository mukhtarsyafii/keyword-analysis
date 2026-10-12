import urllib.error
import sys, json, urllib.request, urllib.parse, datetime, re
sys.path.insert(0, '/Users/mukhtarsyafii/Projects/keyword-analysis')
import fetch_gsc as F

SID = '1qJ6neAJ4OL98qjSHTTz5QL6TMa0Q4iYbxIJp3dnYz4I'
TAB = "'LP PROXSIS STRATEGY'"
BASE = 'https://proxsis-strategy.framer.ai'
DRY = '--write' not in sys.argv

CAT = {'business-strategy': 'Business Strategy', 'productivity-quality': 'Productivity & Quality',
       'governance-risk-compliance': 'Governance, Risk & Compliance', 'business-resillience': 'Business Resillience'}
NAME = {
    '/services': 'Services (index)',
    'business-strategy': 'Business Strategy', 'productivity-quality': 'Productivity & Quality',
    'governance-risk-compliance': 'Governance, Risk & Compliance', 'business-resillience': 'Business Resillience',
    'enterprise-strategic-planning': 'Enterprise Strategic Planning',
    'business-restructuring': 'Business Restructuring',
    'balanced-scorecard-performance-management': 'Balanced Scorecard & Performance Management',
    'merger-acquisition-due-dilligence': 'Merger & Acquisition Due Diligence',
    'feasibility-study': 'Feasibility Study', 'project-management-office': 'Project Management Office',
    'business-process-management': 'Business Process Management',
    'standard-operating-procedure-(sop)-development': 'SOP Development',
    'corporate-policy-guideline-development': 'Corporate Policy & Guideline Development',
    'integrated-governance-risk-management-compliance': 'Integrated Governance Risk Management Compliance',
    'enterprise-risk-management': 'Enterprise Risk Management', 'regulatory-compliance': 'Regulatory Compliance',
    'business-continuity-management-system': 'Business Continuity Management System',
    'business-contingency-plan': 'Business Contingency Plan',
}
SLUG2CAT = {
    'enterprise-strategic-planning': 'business-strategy', 'business-restructuring': 'business-strategy',
    'balanced-scorecard-performance-management': 'business-strategy',
    'merger-acquisition-due-dilligence': 'business-strategy', 'feasibility-study': 'business-strategy',
    'project-management-office': 'business-strategy',
    'business-process-management': 'productivity-quality', 'standard-operating-procedure-(sop)-development': 'productivity-quality',
    'corporate-policy-guideline-development': 'productivity-quality',
    'integrated-governance-risk-management-compliance': 'governance-risk-compliance',
    'enterprise-risk-management': 'governance-risk-compliance', 'regulatory-compliance': 'governance-risk-compliance',
    'business-continuity-management-system': 'business-resillience', 'business-contingency-plan': 'business-resillience',
}
# inbound click-path (href nyata): homepage -> /services -> kategori -> expertise tertentu saja
PATHWAY = {
    '/services': 'homepage → /services',
    '/services/business-strategy': 'homepage → /services',
    '/services/productivity-quality': 'homepage → /services',
    '/services/governance-risk-compliance': 'homepage → /services',
    '/services/business-resillience': 'homepage → /services',
    '/services/expertise/balanced-scorecard-performance-management': 'homepage → /services → business-strategy',
    '/services/expertise/merger-acquisition-due-dilligence': 'homepage → /services → business-strategy',
    '/services/expertise/business-continuity-management-system': 'homepage → /services → business-resillience',
}

pq = json.load(open('/Users/mukhtarsyafii/.hermes/cache/scratch/synergy/strat_gsc_pq.json'))
def gsc_kw(path):
    arr = pq.get('https://strategy.proxsisgroup.com' + path, [])
    qs = [q for _, q, _ in arr if not q.lower().startswith('site:') and 'proxsis' not in q.lower() and 'proxis' not in q.lower()
          and len(q) > 5 and re.search(r'[a-z]{4}', q) and not re.search(r'\d', q)]
    return qs[0] if qs else ''

rows_src = []
PATHS = [('/services', '/services')] + [(f'/services/{c}', c) for c in CAT] + \
        [(f'/services/expertise/{s}', s) for s in NAME if s not in CAT and not s.startswith('/')]
for path, slug in PATHS:
    name = NAME[slug]
    kw = gsc_kw(path)
    if not kw:
        kw = {'/services': 'business consulting services indonesia'}.get(path, name.lower())
    sec = []
    if path in SLUG2CAT.values() or False:
        pass
    # sekunder: nama kategori + nama alt
    cat_key = SLUG2CAT.get(slug)
    if cat_key: sec.append(CAT[cat_key].lower() + ' consulting')
    sec.append('konsultan ' + name.lower())
    pathway = PATHWAY.get(path, '')
    rows_src.append([name, kw, '; '.join(sec[:2]), BASE + path, '-', '-', 'Aktif',
                     pathway or 'tidak ada link internal (hanya sitemap + teks)'])

# urutkan: pathway dulu, lalu non-pathway
rows_src.sort(key=lambda r: (r[7].startswith('homepage'), r[0]))
print('rows', len(rows_src))
for r in rows_src: print(' ', r[7][:30] or '(none)', '|', r[0], '|', r[1])

if DRY: sys.exit(0)

tok = F.access_token()
vals = [[str(i + 1)] + r for i, r in enumerate(rows_src)]
# header baru: tandai kolom pathway di H3
n = len(vals)
rng = f'{TAB}!A5:I{4 + n}'
body = {'values': vals}
req = urllib.request.Request(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/{urllib.parse.quote(rng)}?valueInputOption=RAW',
                             data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}, method='PUT')
try:
    d = json.load(urllib.request.urlopen(req))
except urllib.error.HTTPError as e:
    print('ERR', e.read().decode()); raise
print('updatedCells', d['updatedCells'])
# header
req2 = urllib.request.Request(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/{urllib.parse.quote(TAB+"!A1:I4")}?valueInputOption=RAW',
                              data=json.dumps({'values': [
                                  ['LP TRACKER — PROXSIS STRATEGY 2026'],
                                  ['Brand: Proxsis Strategy | Sumber: crawl sitemap + GSC strategy.proxsisgroup.com (19 halaman services; 14 expertise; site consulting, tanpa halaman training berdiri sendiri)'],
                                  ['No', 'Nama LP / Halaman', 'Keyword Utama', 'Keyword Sekunder', 'URL', 'Tanggal Live', 'PIC Buat', 'Status LP', 'Pathway dari Homepage'],
                                  ['', '', '', '', '', '', '', '', ''],
                              ]}).encode(), headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}, method='PUT')
d2 = json.load(urllib.request.urlopen(req2))
print('headerCells', d2['updatedCells'])
# readback
rng2 = urllib.parse.quote(f'{TAB}!A5:I{4+n}')
req3 = urllib.request.Request(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/{rng2}', headers={'Authorization': 'Bearer ' + tok})
back = json.load(urllib.request.urlopen(req3))['values']
mis = sum(1 for a, b in zip(vals, back) if a[:6] != (b + [''] * 9)[:6])
print('readback rows', len(back), 'mismatch', mis)
