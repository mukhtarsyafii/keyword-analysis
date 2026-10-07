// Smoke test: run every render function of the dashboard JS against a stub DOM.
// Catches ReferenceError / undefined-element bugs without a browser.
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/)[1];

const store = {};
function el(id) {
  if (!store[id]) store[id] = {
    id, innerHTML: '', textContent: '', value: '', className: '', style: {},
    classList: { add(){}, remove(){}, toggle(){}, contains(){return false;} },
    addEventListener(){}, appendChild(){}, querySelectorAll(){ return []; },
    getBoundingClientRect(){ return {left:0,top:0,width:0,height:0}; },
    dataset: {}, offsetWidth: 10, offsetHeight: 10, focus(){},
  };
  return store[id];
}
global.document = {
  getElementById: el,
  querySelectorAll: () => [],
  createElement: () => el('tmp' + Math.random()),
  addEventListener(){},
  body: el('body'),
};
global.location = { protocol: 'file:', hostname: 'x', href: 'file://x' };
global.localStorage = { getItem: () => null, setItem(){}, removeItem(){} };
global.navigator = { clipboard: { writeText: async () => {} } };
global.window = { onload: null, addEventListener(){} };
global.addEventListener = () => {};
global.setInterval = () => 0; global.clearInterval = () => {};
global.fetch = async () => { throw new Error('no net'); };

const vm = require('vm');
vm.createContext(global);
vm.runInContext(js + '\n;globalThis.__api = {PRODUCTS, RECS, BRANDS, renderBrandBar, renderKPI, renderMatrix, renderAksi, renderKompetitor, renderTrends, renderBrands, renderCompare, setBrand, brows, brandNames, allDates};', global);
const A = global.__api;

function check(label, fn) {
  try { fn(); console.log('ok  ', label); }
  catch (e) { console.log('FAIL', label, '-', e.message); process.exitCode = 1; }
}

check('init()', () => window.onload());
check('brandNames has both brands', () => {
  const n = A.brandNames();
  if (!n.includes('GRC Indonesia') || !n.includes('IPQI') || !n.includes('ITGID')) throw new Error(n.join(','));
});
check('brandBar rendered', () => {
  if (!el('brandBar').innerHTML.includes('IPQI')) throw new Error('no IPQI pill');
});
check('matrix rows include IPQI when all', () => {
  if (!el('matrixBody').innerHTML.includes('ipqi.org')) throw new Error('no ipqi row');
});
check('brands table computed', () => {
  const b = el('brandsBody').innerHTML;
  if (!b.includes('TOTAL')) throw new Error('no total row');
  if (!b.includes('IPQI')) throw new Error('no IPQI row');
});
check('setBrand(IPQI) scopes everything', () => {
  A.setBrand('IPQI');
  if (A.brows().some(p => p.brand !== 'IPQI')) throw new Error('scope leak');
  if (el('matrixBody').innerHTML.includes('grc-indonesia.com')) throw new Error('GRC row leaked');
  if (!el('brandSubtitle').textContent.includes('IPQI')) throw new Error('subtitle stale');
});
check('setBrand(ITGID) scopes everything', () => {
  A.setBrand('ITGID');
  if (A.brows().length !== A.PRODUCTS.filter(p => p.brand === 'ITGID').length) throw new Error('scope leak');
  if (A.brows().some(p => p.brand !== 'ITGID')) throw new Error('non-ITGID row');
  const m = el('matrixBody').innerHTML;
  if (!m.includes('itgid.org')) throw new Error('no itgid row');
  if (m.includes('grc-indonesia.com') || m.includes('ipqi.org')) throw new Error('other brand leaked');
  A.setBrand('all');
});
check('setBrand back to all', () => {
  A.setBrand('all');
  if (A.brows().length !== A.PRODUCTS.length) throw new Error('scope not restored');
});
check('trends weekly series for IPQI', () => {
  A.setBrand('IPQI');
  const before = el('chartContainer').innerHTML;
  A.renderTrends();
  if (!el('chartContainer').innerHTML.length) throw new Error('empty chart');
  A.setBrand('all');
});
check('compare table renders', () => { A.renderCompare(); });
check('competitor tab renders', () => { A.renderKompetitor(); });
check('aksi tab renders', () => { A.renderAksi(); });
