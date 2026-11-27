/* Civ Italia: static app. Reads ./data/*.json written by scripts/export.py.
   Every number shown is computed here from counts (votes, electors, residents, euros, jobs) and
   the rules in meta.json; rates are recomputed, never averaged. */
(async function () {
'use strict';
const $ = s => document.querySelector(s);
const DATA = 'data/';
const get = async f => { const r = await fetch(DATA + f); if (!r.ok) throw new Error(f + ' ' + r.status); return r.json(); };

const FIRST = get('e_cam2022.json');  // the opening election downloads alongside the base files
const PREF_IT = (() => { try { const v = localStorage.getItem('civ-lang'); if (v) return v === 'it'; } catch (e) {} return (navigator.language || 'en').toLowerCase().startsWith('it'); })();
let IT_P = PREF_IT ? get('i18n_it.json').catch(() => null) : null;
const [T, BORDERS, CJ, META] = await Promise.all([get('tiles.json'), get('borders.json'), get('cities.json'), get('meta.json')]);
const N = T.n, R = T.d / Math.sqrt(3), C = {};
// ------------------------------------------------------------------ language
// English is the source; data/i18n_it.json maps each English string to Italian.
let LANG = (() => { try { const v = localStorage.getItem('civ-lang'); if (v === 'it' || v === 'en') return v; } catch (e) {} return (navigator.language || 'en').toLowerCase().startsWith('it') ? 'it' : 'en'; })();
let IT = null;
async function loadLang() { if (LANG === 'it' && !IT) IT = await (IT_P || (IT_P = get('i18n_it.json').catch(() => null))); if (LANG === 'it' && !IT) { LANG = 'en'; IT_P = null; } document.documentElement.lang = LANG; }
const tr = (str, v) => { let o = (LANG === 'it' && IT && IT.ui[str]) || str; if (v) o = o.replace(/\{(\w+)\}/g, (m, k) => v[k] ?? m); return o; };
const trm = (path, en) => { if (LANG !== 'it' || !IT) return en; let o = IT.meta; for (const p of path) o = o?.[p]; return o ?? en; };
const LOC = () => LANG === 'it' ? 'it-IT' : 'en-GB';
// land & people columns and city statistics arrive after the first paint
let lateGo; const LATE = new Promise(r => lateGo = r).then(() => Promise.all([get('tile_cols.json'), get('city_stats.json')])).then(([cols, cs]) => {
  const TN = { p: 'plains', h: 'hills', m: 'mountains', '': '' }, FN = { f: 'forest', m: 'marsh', '': '' };
  cols.terrain = cols.terrain.map(x => TN[x]); cols.feature = cols.feature.map(x => FN[x]);
  Object.assign(C, cols); cs.forEach((s, i) => Object.assign(CITIES[i], s));
});
const CITIES = CJ.cities, WONDERS = CJ.wonders;
const EL = {};                      // loaded elections
const ELIST = META.elections;
const COLS = META.columns;
const PARTY = ELIST.filter(e => e.kind !== 'referendum');

// ------------------------------------------------------------------ formatting
const nf = (x, d = 1) => x == null || !isFinite(x) ? '–' : x.toLocaleString(LOC(), { minimumFractionDigits: d, maximumFractionDigits: d });
const ni = x => x == null || !isFinite(x) ? '–' : Math.round(x).toLocaleString(LOC(), { useGrouping: 'always' });
const eur = x => x == null || !isFinite(x) ? '–' : '€' + Math.round(x).toLocaleString(LOC(), { useGrouping: 'always' });
const big = x => x == null || !isFinite(x) ? '–' : x >= 1e9 ? '€' + nf(x / 1e9, 2) + ' ' + tr('bn') : x >= 1e6 ? '€' + nf(x / 1e6, 1) + ' ' + tr('m') : eur(x);
const elabel = e => trm(['elections', e.id], e.label);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ymd = d => `${d.slice(6, 8)}/${d.slice(4, 6)}/${d.slice(0, 4)}`;

// ------------------------------------------------------------------ colour
const dark = () => { const t = document.documentElement.dataset.theme; return t ? t === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; };
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const hex2 = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
function ramp(stops, t) { t = Math.max(0, Math.min(1, t)) * (stops.length - 1); const i = Math.min(stops.length - 2, Math.floor(t)), f = t - i, a = hex2(stops[i]), b = hex2(stops[i + 1]); return `rgb(${a.map((x, k) => Math.round(x + (b[k] - x) * f)).join(',')})`; }
const PAL = () => dark()
  ? { yn: ['#c2a5cf', '#9970ab', '#6b4a7a', '#3b2f45', '#383838', '#2f4a36', '#3d8a52', '#5aae61', '#a6dba0'], div: ['#f39a8e', '#d55553', '#9a393b', '#5e2b2f', '#383838', '#213f69', '#1b64be', '#338ced', '#9dc8f7'], seq: ['#1a2a3c', '#17477f', '#1b64be', '#338ced', '#9dc8f7'], warm: ['#2a2622', '#5b3f1d', '#93611a', '#cf8f2a', '#f3c66b'], green: ['#1c2a22', '#20482f', '#2c6d40', '#4e9a5a', '#93cf8a'], terr: { plains: '#5d8a4e', hills: '#a8893f', mountains: '#8a7a6c', forest: '#2f6b3d', marsh: '#3f8f8a' } }
  : { yn: ['#762a83', '#9970ab', '#c2a5cf', '#e7d4e8', '#f2f2f2', '#d9f0d3', '#a6dba0', '#5aae61', '#1b7837'], div: ['#9e1f27', '#c9403f', '#e1756f', '#f0b3ad', '#efefef', '#b6d5f8', '#6aabf1', '#257de0', '#0e3d7e'], seq: ['#e4effc', '#9dc8f7', '#519ced', '#1b64be', '#0e3d7e'], warm: ['#fbf1dc', '#f3d38f', '#e0a43f', '#b8741c', '#7a4610'], green: ['#eef6e8', '#c4e2b4', '#86c07a', '#4b9152', '#22622f'], terr: { plains: '#b9d79a', hills: '#e2c886', mountains: '#b3a597', forest: '#5f9a5a', marsh: '#7cc2bc' } };
const PCOL = { FdI: '#2c52b3', PD: '#d8363a', M5S: '#d3a016', Lega: '#2f9a4c', FI: '#58b0ea', 'FI-NM': '#58b0ea', 'A-IV': '#b8419a', Az: '#b8419a', AVS: '#7c5a2e', LeU: '#a0442a', LS: '#a0442a', '+E': '#ef8f3a', SUE: '#ef8f3a', SVP: '#8d5fc0', NM: '#8fa3c8', NcI: '#8fa3c8', IC: '#e2a6a0', EV: '#4f9a5d', PTD: '#c46a6a', Lib: '#5e6e7a', Other: '#9aa5ad' };
const EXTRA = ['#6b8e23', '#008b8b', '#b5651d', '#7b68ee', '#c71585', '#20b2aa', '#cd853f', '#4682b4', '#9acd32', '#d2691e'];
const lcol = (l, i) => PCOL[l.short] || EXTRA[i % EXTRA.length];

// ------------------------------------------------------------------ election maths
async function loadE(id) { if (!EL[id]) EL[id] = prep(await (id === 'cam2022' ? FIRST : get('e_' + id + '.json'))); return EL[id]; }
function prep(E) {
  if (E.kind === 'referendum') {
    E.qs = E.questions.map((q, k) => ({ ...q, k }));
    return E;
  }
  E.lists.forEach((l, i) => { l.i = i; l.col = lcol(l, i); });
  E.T = stats(E, E.tiles, N); E.C = stats(E, E.cities, CITIES.length);
  E.NAT = stats(E, { electors: [E.nat.electors], voters: [E.nat.voters], valid: [E.nat.valid], v: E.nat.v.map(x => [x]) }, 1);
  E.hasCoal = E.lists.some(l => l.coal);
  return E;
}
function stats(E, B, n) {
  const L = E.lists, out = { lr: new Float32Array(n), econ: new Float32Array(n), gal: new Float32Array(n), cov: new Float32Array(n), lead: new Int16Array(n), margin: new Float32Array(n), turnout: new Float32Array(n), valid: B.valid, electors: B.electors, voters: B.voters, v: B.v };
  for (let i = 0; i < n; i++) {
    let sv = 0, a = 0, b = 0, c = 0, best = -1, bi = -1, cdx = 0, csx = 0, tot = 0;
    for (let k = 0; k < L.length; k++) {
      const v = B.v[k][i] || 0; tot += v;
      if (L[k].lr != null) { sv += v; a += v * L[k].lr; b += v * L[k].econ; c += v * L[k].gal; }
      if (L[k].id !== '__other__' && v > best) { best = v; bi = k; }
      if (L[k].coal === 'cdx') cdx += v; else if (L[k].coal === 'csx') csx += v;
    }
    const val = B.valid[i] || tot;
    out.lr[i] = sv > 0 ? a / sv : NaN; out.econ[i] = sv > 0 ? b / sv : NaN; out.gal[i] = sv > 0 ? c / sv : NaN;
    out.cov[i] = val > 0 ? sv / val : NaN; out.lead[i] = best > 0 ? bi : -1;
    out.margin[i] = val > 0 ? (cdx - csx) / val * 100 : NaN;
    out.turnout[i] = B.electors[i] > 20 ? B.voters[i] / B.electors[i] * 100 : NaN;
  }
  return out;
}
const refYes = (E, B, q, i) => { const y = B.yes[q][i], n = B.no[q][i]; return y + n > 0 ? y / (y + n) * 100 : NaN; };
const refTurn = (E, B, q, i) => B.electors[q][i] > 20 ? B.voters[q][i] / B.electors[q][i] * 100 : NaN;

// ------------------------------------------------------------------ yields (land & people)
const sum = a => a ? a.reduce((s, x) => s + (x || 0), 0) : NaN;
const rate = (num, den, sc = 1) => i => { const a = C[num]?.[i], b = C[den]?.[i]; return a != null && b > 0 ? a / b * sc : NaN; };
const natRate = (num, den, sc = 1) => C[num] && C[den] ? sum(C[num]) / sum(C[den]) * sc : NaN;
const cityRate = (c, num, den, sc = 1) => c[num] != null && c[den] > 0 ? c[num] / c[den] * sc : NaN;
const has = k => Array.isArray(C[k]);

// ------------------------------------------------------------------ lenses
const S = { eid: 'cam2022', lens: 'lr', share: null, swing: 'cam2018', q: 0, haz: 'landslide', sel: null, selKind: null };
const LENSES = [
  { id: 'lr', label: 'Ideology', grp: 'Politics', kind: 'party' },
  { id: 'lead', label: 'Leading list', grp: 'Politics', kind: 'party' },
  { id: 'margin', label: 'Coalition margin', grp: 'Politics', kind: 'camera' },
  { id: 'turnout', label: 'Loyalty (turnout)', grp: 'Politics', kind: 'any' },
  { id: 'share', label: 'List share', grp: 'Politics', kind: 'party' },
  { id: 'swing', label: 'Swing', grp: 'Politics', kind: 'party' },
  { id: 'econ', label: 'Economic axis', grp: 'Politics', kind: 'party' },
  { id: 'gal', label: 'Social axis', grp: 'Politics', kind: 'party' },
  { id: 'yes', label: 'Referendum Yes', grp: 'Politics', kind: 'ref' },
  { id: 'gold', label: 'Gold', grp: 'Land & people', kind: null, need: 'income' },
  { id: 'science', label: 'Science', grp: 'Land & people', kind: null, need: 'grad' },
  { id: 'prod', label: 'Production', grp: 'Land & people', kind: null, need: 'jobs_ind' },
  { id: 'food', label: 'Food', grp: 'Land & people', kind: null, need: 'farmland' },
  { id: 'terrain', label: 'Terrain', grp: 'Land & people', kind: null, need: 'terrain' },
  { id: 'age', label: 'Age 65+', grp: 'Land & people', kind: null, need: 'pop65' },
  { id: 'foreign', label: 'Foreign residents', grp: 'Land & people', kind: null, need: 'foreign' },
  { id: 'emp', label: 'Employment', grp: 'Land & people', kind: null, need: 'employed' },
  { id: 'density', label: 'Density', grp: 'Land & people', kind: null, need: 'pop_res' },
  { id: 'hazard', label: 'Hazards', grp: 'Land & people', kind: null, need: 'quakes' },
];
const curE = () => EL[S.eid];
const isRef = () => curE()?.kind === 'referendum';
function lensOK(l) {
  if (l.need && !has(l.need)) return false;
  const E = curE(); if (!E) return !l.kind;
  if (l.kind === 'party') return E.kind !== 'referendum';
  if (l.kind === 'camera') return E.kind === 'camera';
  if (l.kind === 'ref') return E.kind === 'referendum';
  return true;
}

// scale per lens: returns {val(i) tile value, cval(c) city value, color(v), legend html, fmt(v)}
let SC = null;
function q(arr, p) { const a = arr.filter(x => isFinite(x)).sort((x, y) => x - y); return a.length ? a[Math.min(a.length - 1, Math.floor(p * a.length))] : 0; }
function seqScale(vals, pal, lo, hi, fmt, label, rule) {
  if (lo == null) lo = q(vals, .02); if (hi == null) hi = q(vals, .98); if (hi <= lo) hi = lo + 1;
  return { color: v => isFinite(v) ? ramp(pal, (v - lo) / (hi - lo)) : null, legend: rampHTML(pal, fmt(lo), fmt((lo + hi) / 2), fmt(hi) + '+', label), fmt, rule };
}
function divScale(mid, half, pal, fmt, left, right, label, rule) {
  return { color: v => isFinite(v) ? ramp(pal, (v - (mid - half)) / (2 * half)) : null, legend: rampHTML(pal, `${fmt(mid - half)} ${left}`, fmt(mid), `${right} ${fmt(mid + half)}`, label), fmt, rule };
}
function rampHTML(stops, a, b, c, label) { return `<span>${label}</span><div class="ramp"><i style="background:linear-gradient(90deg,${stops.join(',')})"></i><div><span>${a}</span><span>${b}</span><span>${c}</span></div></div>`; }

async function buildScale() {
  const pal = PAL(), E = curE(), L = S.lens;
  const tv = new Float32Array(N), cv = new Float32Array(CITIES.length);
  let s;
  const fill = (fT, fC) => { for (let i = 0; i < N; i++) tv[i] = fT(i); for (let c = 0; c < CITIES.length; c++) cv[c] = fC(c); };
  if (['lr', 'econ', 'gal'].includes(L)) {
    fill(i => E.T[L][i], c => E.C[L][c]);
    const mid = E.NAT[L][0], half = L === 'lr' ? 1.6 : L === 'econ' ? 1.4 : 2.2;
    const lab = { lr: tr('Expert general left–right score (0–10), averaged over valid votes · Italy {v}', { v: nf(mid, 2) }), econ: tr('Expert economic left–right score (0–10), averaged over valid votes · Italy {v}', { v: nf(mid, 2) }), gal: tr('Expert social GAL–TAN score (0–10), averaged over valid votes · Italy {v}', { v: nf(mid, 2) }) }[L];
    s = divScale(mid, half, pal.div, x => nf(x, 2), L === 'gal' ? 'GAL' : tr('left'), L === 'gal' ? 'TAN' : tr('right'), lab, 'lr');
  } else if (L === 'lead') {
    fill(i => E.T.lead[i], c => E.C.lead[c]);
    const seen = [...new Set([...tv].filter(x => x >= 0))].sort((a, b) => a - b);
    s = { color: v => v >= 0 ? E.lists[v].col : null, fmt: v => v >= 0 ? E.lists[v].short : '–', categorical: true,
      legend: `<span>${tr('Largest list (all lists, scored or not)')}</span>` + seen.map(k => `<span class="sw"><b style="background:${E.lists[k].col}"></b>${esc(E.lists[k].short)}</span>`).join('') };
  } else if (L === 'margin') {
    fill(i => E.T.margin[i], c => E.C.margin[c]);
    s = divScale(0, 40, pal.div, x => nf(Math.abs(x), 0), tr('centre-left +'), tr('centre-right +'), tr('Centre-right minus centre-left, points of valid votes · Italy {v}', { v: nf(E.NAT.margin[0], 1) }), 'margin');
    s.fmt = x => isFinite(x) ? (x >= 0 ? tr('CDX +') : tr('CSX +')) + nf(Math.abs(x), 1) : '–';
  } else if (L === 'turnout') {
    if (isRef()) { fill(i => refTurn(E, E.tiles, S.q, i), c => refTurn(E, E.cities, S.q, c)); }
    else fill(i => E.T.turnout[i], c => E.C.turnout[c]);
    const nat = isRef() ? E.nat.voters[S.q] / E.nat.electors[S.q] * 100 : E.NAT.turnout[0];
    s = seqScale([...tv], pal.seq, isRef() ? 10 : 40, isRef() ? 70 : 85, x => nf(x, 0) + '%', tr('Voters as a share of electors · Italy {v}%', { v: nf(nat, 1) }), 'turnout');
    s.fmt = x => nf(x, 1) + '%';
  } else if (L === 'share') {
    const k = shareIdx(E);
    fill(i => E.T.valid[i] > 0 ? E.tiles.v[k][i] / E.T.valid[i] * 100 : NaN, c => E.C.valid[c] > 0 ? E.cities.v[k][c] / E.C.valid[c] * 100 : NaN);
    const pal2 = [pal.seq[0], E.lists[k].col];
    const hi = Math.max(5, Math.ceil(q([...tv], .97) / 5) * 5);
    s = seqScale([...tv], [mix(pal.seq[0], E.lists[k].col, 0), mix(pal.seq[0], E.lists[k].col, .45), E.lists[k].col, mix(E.lists[k].col, dark() ? '#ffffff' : '#000000', .35)], 0, hi, x => nf(x, 0) + '%',
      tr('{list}: share of valid votes · Italy {v}%', { list: esc(E.lists[k].label), v: nf(E.nat.v[k] / E.nat.valid * 100, 1) }), 'share');
    s.fmt = x => nf(x, 1) + '%';
  } else if (L === 'swing') {
    const P = await loadE(S.swing);
    fill(i => E.T.lr[i] - P.T.lr[i], c => E.C.lr[c] - P.C.lr[c]);
    const mid = E.NAT.lr[0] - P.NAT.lr[0];
    s = divScale(mid, .8, pal.div, x => (x > 0 ? '+' : '') + nf(x, 2), tr('left'), tr('right'), tr('Change in ideology score since {e} · Italy {v}', { e: esc(elabel(P)), v: (mid > 0 ? '+' : '') + nf(mid, 2) }), 'swing');
  } else if (L === 'yes') {
    fill(i => refYes(E, E.tiles, S.q, i), c => refYes(E, E.cities, S.q, c));
    const nat = E.nat.yes[S.q] / (E.nat.yes[S.q] + E.nat.no[S.q]) * 100;
    s = divScale(50, 30, pal.yn, x => nf(x, 0) + '%', tr('No'), tr('Yes'), tr('Yes as a share of Yes + No · Italy {v}% Yes', { v: nf(nat, 1) }), 'yes');
    s.fmt = x => tr('{v}% Yes', { v: nf(x, 1) });
  } else if (L === 'gold') {
    fill(rate('income', 'pop_res'), c => cityRate(CITIES[c], 'income', 'pop_res'));
    s = seqScale([...tv], pal.warm, null, null, x => eur(x), tr('Gold: declared taxable income per resident · Italy {v}', { v: eur(natRate('income', 'pop_res')) }), 'gold');
  } else if (L === 'science') {
    fill(rate('grad', 'pop25', 100), c => cityRate(CITIES[c], 'grad', 'pop25', 100));
    s = seqScale([...tv], pal.seq, null, null, x => nf(x, 0) + '%', tr('Science: residents aged 25+ with a degree · Italy {v}%', { v: nf(natRate('grad', 'pop25', 100), 1) }), 'science');
    s.fmt = x => nf(x, 1) + '%';
  } else if (L === 'prod') {
    fill(rate('jobs_ind', 'jobs_total', 100), c => cityRate(CITIES[c], 'jobs_ind', 'jobs_total', 100));
    s = seqScale([...tv], pal.warm, null, null, x => nf(x, 0) + '%', tr('Production: manufacturing + construction share of local jobs · Italy {v}%', { v: nf(natRate('jobs_ind', 'jobs_total', 100), 1) }), 'prod');
    s.fmt = x => nf(x, 1) + '%';
  } else if (L === 'food') {
    fill(i => C.farmland[i] * 100, c => cityAvgTiles(c, 'farmland') * 100);
    s = seqScale([...tv], pal.green, 0, 90, x => nf(x, 0) + '%', tr('Food: farmland as a share of land (land cover)'), 'food');
    s.fmt = x => nf(x, 1) + '%';
  } else if (L === 'age') {
    fill(rate('pop65', 'pop_cens', 100), c => cityRate(CITIES[c], 'pop65', 'pop_cens', 100));
    s = seqScale([...tv], pal.warm, null, null, x => nf(x, 0) + '%', tr('Residents aged 65 and over · Italy {v}%', { v: nf(natRate('pop65', 'pop_cens', 100), 1) }), 'age'); s.fmt = x => nf(x, 1) + '%';
  } else if (L === 'foreign') {
    fill(rate('foreign', 'pop_cens', 100), c => cityRate(CITIES[c], 'foreign', 'pop_cens', 100));
    s = seqScale([...tv], pal.seq, 0, null, x => nf(x, 0) + '%', tr('Residents with foreign citizenship · Italy {v}%', { v: nf(natRate('foreign', 'pop_cens', 100), 1) }), 'foreign'); s.fmt = x => nf(x, 1) + '%';
  } else if (L === 'emp') {
    fill(rate('employed', 'pop15', 100), c => cityRate(CITIES[c], 'employed', 'pop15', 100));
    s = seqScale([...tv], pal.green, null, null, x => nf(x, 0) + '%', tr('Employed residents per 100 residents aged 15+ · Italy {v}%', { v: nf(natRate('employed', 'pop15', 100), 1) }), 'emp'); s.fmt = x => nf(x, 1) + '%';
  } else if (L === 'density') {
    fill(rate('pop_res', 'land_km2'), c => { const ts = CITIES[c].tiles; let p = 0, a = 0; ts.forEach(t => { p += C.pop_res[t] || 0; a += C.land_km2[t] || 0; }); return a ? p / a : NaN; });
    const lt = [...tv].map(v => Math.log10(Math.max(1, v)));
    s = { color: v => isFinite(v) ? ramp(pal.seq, (Math.log10(Math.max(1, v)) - 1) / 3) : null, fmt: v => ni(v) + '/km²', rule: 'density',
      legend: rampHTML(pal.seq, '10', '300', tr('10,000+ per km²'), tr('Residents per km² of land (log scale)')) };
  } else if (L === 'terrain') {
    fill(i => i, c => NaN);
    const tc = pal.terr;
    s = { categorical: true, color: v => { const f = C.feature[v]; return f ? tc[f] : tc[C.terrain[v]] || null; }, fmt: v => terrName(v), rule: 'terrain',
      legend: `<span>${tr('Mean elevation of land, then land cover')}</span>` + ['Plains', 'Hills', 'Mountains', 'Forest', 'Marsh'].map(k => `<span class="sw"><b style="background:${tc[k.toLowerCase()]}"></b>${tr(k)}</span>`).join('') + `<span class="sw"><b style="background:transparent;border:2px solid ${css('--ink')}"></b>${tr('Coast')}</span>` };
  } else if (L === 'hazard') {
    const H = S.haz;
    if (H === 'quakes') { fill(i => C.quakes[i], c => sumTiles(c, 'quakes')); s = seqScale([...tv], pal.warm, 0, 6, x => ni(x), tr('Earthquakes of magnitude 4 or more since 1985, epicentre on the tile'), 'quakes'); }
    else if (H === 'landslide') { fill(i => C.land_km2[i] > 0 ? C.landslide_km2[i] / C.land_km2[i] * 100 : NaN, c => ratioTiles(c, 'landslide_km2', 'land_km2') * 100); s = seqScale([...tv], pal.warm, 0, 30, x => nf(x, 0) + '%', tr('Land in high or very high landslide hazard (ISPRA P3+P4)'), 'landslide'); s.fmt = x => nf(x, 1) + '%'; }
    else { fill(i => C.land_km2[i] > 0 ? C.flood_km2[i] / C.land_km2[i] * 100 : NaN, c => ratioTiles(c, 'flood_km2', 'land_km2') * 100); s = seqScale([...tv], pal.seq, 0, 40, x => nf(x, 0) + '%', tr('Land in medium-probability flood hazard (ISPRA P2)'), 'flood'); s.fmt = x => nf(x, 1) + '%'; }
    s.legend = `<label for="hz">${tr('Hazard')}</label><select id="hz"><option value="landslide"${H === 'landslide' ? ' selected' : ''}>${tr('Landslides')}</option><option value="flood"${H === 'flood' ? ' selected' : ''}>${tr('Floods')}</option><option value="quakes"${H === 'quakes' ? ' selected' : ''}>${tr('Earthquakes')}</option></select>` + s.legend;
  }
  s.tv = tv; s.cv = cv; SC = s;
  legend();
}
function mix(a, b, t) { const x = hex2(a), y = hex2(b); return '#' + x.map((v, k) => Math.round(v + (y[k] - v) * t).toString(16).padStart(2, '0')).join(''); }
const CAP = { plains: 'Plains', hills: 'Hills', mountains: 'Mountains', forest: 'forest', marsh: 'marsh' };
function terrName(i) { if (!C.terrain) return ''; const t = C.terrain[i], f = C.feature[i]; return t ? tr(CAP[t]) + (f ? ', ' + tr(CAP[f]) : '') + (C.coast[i] ? ', ' + tr('coast') : '') : '–'; }
const sumTiles = (c, k) => CITIES[c].tiles.reduce((s, t) => s + (C[k][t] || 0), 0);
const ratioTiles = (c, a, b) => { const x = sumTiles(c, a), y = sumTiles(c, b); return y ? x / y : NaN; };
function cityAvgTiles(c, k) { let s = 0, a = 0; CITIES[c].tiles.forEach(t => { if (C[k][t] != null) { s += C[k][t] * C.land_km2[t]; a += C.land_km2[t]; } }); return a ? s / a : NaN; }
function shareIdx(E) { let k = E.lists.findIndex(l => l.short === S.share || l.id === S.share); if (k < 0) { k = E.NAT.lead[0]; S.share = E.lists[k].short; } return k; }

// ------------------------------------------------------------------ legend & lens bar
function lensBar() {
  const box = $('#lenses'); let html = '', g = '';
  for (const l of LENSES) { if (!lensOK(l)) continue; if (l.grp !== g) { g = l.grp; html += `<span class="grp">${tr(g)}</span>`; } html += `<button type="button" data-l="${l.id}" aria-pressed="${l.id === S.lens}">${tr(l.label)}</button>`; }
  box.innerHTML = html;
  box.querySelectorAll('button').forEach(b => b.onclick = async () => { S.lens = b.dataset.l; lensBar(); await buildScale(); draw(); sheet(); });
}
function legend() {
  const E = curE(), Lg = $('#legend');
  let extra = '';
  if (S.lens === 'share') extra = `<label for="sp">${tr('List')}</label><select id="sp">${E.lists.filter(l => l.id !== '__other__').map(l => `<option value="${esc(l.short)}"${l.short === S.share ? ' selected' : ''}>${esc(l.label)}</option>`).join('')}</select>`;
  if (S.lens === 'swing') extra = `<label for="sw">${tr('Since')}</label><select id="sw">${PARTY.filter(e => e.id !== S.eid).map(e => `<option value="${e.id}"${e.id === S.swing ? ' selected' : ''}>${esc(elabel(e))}</option>`).join('')}</select>`;
  if (isRef() && (S.lens === 'yes' || S.lens === 'turnout') && E.qs.length > 1) extra = `<label for="rq">${tr('Question')}</label><select id="rq">${E.qs.map(x => `<option value="${x.k}"${x.k === S.q ? ' selected' : ''}>${x.q}. ${esc(x.text)}</option>`).join('')}</select>`;
  Lg.innerHTML = extra + SC.legend + `<span class="cue">${tr('· colour is never the only cue: tap any tile for its figures')}</span>`;
  const on = (id, f) => { const el = $(id); if (el) el.onchange = async () => { f(el.value); await buildScale(); draw(); sheet(); }; };
  on('#sp', v => S.share = v); on('#sw', v => S.swing = v); on('#rq', v => S.q = +v); on('#hz', v => S.haz = v);
}

// ------------------------------------------------------------------ canvas
const cv = $('#map'), ctx = cv.getContext('2d'); let W = 0, H = 0, s = 1, ox = 0, oy = 0;
const bx = Math.max(...T.x), by = Math.max(...T.y);
function fit() { const m = 14; s = Math.min((W - 2 * m) / (bx + T.d), (H - 2 * m) / (by + T.d)); ox = (W - bx * s) / 2; oy = (H - by * s) / 2; draw(); }
function resize() { const b = cv.getBoundingClientRect(), dpr = devicePixelRatio || 1; const first = !W; W = b.width; H = b.height; cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); first ? fit() : draw(); }
const HX = [0, 1, 2, 3, 4, 5].map(k => [Math.cos((60 * k + 30) * Math.PI / 180), Math.sin((60 * k + 30) * Math.PI / 180)]);
function hexPath(x, y, rr) { ctx.beginPath(); for (let k = 0; k < 6; k++) { const px = ox + (x + HX[k][0] * rr) * s, py = oy + (y + HX[k][1] * rr) * s; k ? ctx.lineTo(px, py) : ctx.moveTo(px, py); } ctx.closePath(); }
let raf = 0; function draw() { if (!raf) raf = requestAnimationFrame(paint); }
const nCities = () => s < 1.1 ? 12 : s < 2 ? 30 : s < 3.5 ? 80 : s < 6 ? 200 : CITIES.length;
function paint() {
  raf = 0; if (!SC) return;
  const sea = css('--sea'), ink = css('--ink'), panel = css('--panel'), nd = css('--nodata');
  ctx.fillStyle = sea; ctx.fillRect(0, 0, W, H);
  ctx.lineWidth = Math.min(1, s * .12); ctx.strokeStyle = sea;
  const hl = S.selKind === 'city' ? new Set(CITIES[S.sel].tiles) : null;
  for (let i = 0; i < N; i++) {
    const px = ox + T.x[i] * s, py = oy + T.y[i] * s; if (px < -20 || py < -20 || px > W + 20 || py > H + 20) continue;
    hexPath(T.x[i], T.y[i], R); ctx.fillStyle = SC.color(SC.tv[i]) || nd; ctx.fill(); ctx.stroke();
  }
  if (S.lens === 'terrain') { ctx.strokeStyle = ink; ctx.lineWidth = Math.max(1, s * .25); for (let i = 0; i < N; i++) if (C.coast[i]) { hexPath(T.x[i], T.y[i], R * .62); ctx.stroke(); } }
  ctx.strokeStyle = ink; ctx.globalAlpha = .45; ctx.lineWidth = 1; ctx.lineJoin = 'round';
  for (const b of BORDERS) { ctx.beginPath(); for (let i = 0; i < b.length; i += 2) { const px = ox + b[i] * s, py = oy + b[i + 1] * s; i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); } ctx.closePath(); ctx.stroke(); }
  ctx.globalAlpha = 1;
  if (hl) { ctx.lineWidth = 2; ctx.strokeStyle = ink; for (const i of hl) { hexPath(T.x[i], T.y[i], R * .92); ctx.stroke(); } }
  if (S.selKind === 'tile') { const i = S.sel; hexPath(T.x[i], T.y[i], R); ctx.lineWidth = 3; ctx.strokeStyle = panel; ctx.stroke(); ctx.lineWidth = 1.5; ctx.strokeStyle = ink; ctx.stroke(); }
  // cities: more appear as the reader zooms in; labels skip when they would collide
  const n = nCities(), boxes = [], vis = [];
  ctx.font = '600 11px "IBM Plex Sans",system-ui,sans-serif'; ctx.textBaseline = 'middle';
  for (let i = 0; i < n; i++) { const c = CITIES[i], px = ox + c.x * s, py = oy + c.y * s; if (px < 0 || py < 0 || px > W || py > H) continue; vis.push([i, px, py]); boxes.push([px - 6, py - 6, 12, 12]); }
  if (S.selKind === 'city' && !vis.some(v => v[0] === S.sel)) { const c = CITIES[S.sel]; vis.unshift([S.sel, ox + c.x * s, oy + c.y * s]); }
  for (const [i, px, py] of vis) {
    const name = CITIES[i].name, w = ctx.measureText(name).width + 10, bb = [px + 8, py - 9, w, 18];
    if (S.sel !== i && boxes.some(b => !(b[0] === px - 6 && b[1] === py - 6) && bb[0] < b[0] + b[2] && bb[0] + bb[2] > b[0] && bb[1] < b[1] + b[3] && bb[1] + bb[3] > b[1])) continue; boxes.push(bb);
    ctx.globalAlpha = .9; ctx.fillStyle = panel; ctx.beginPath(); ctx.roundRect(bb[0], bb[1], w, 18, 4); ctx.fill(); ctx.globalAlpha = 1; ctx.fillStyle = ink; ctx.fillText(name, px + 13, py + .5);
  }
  for (const [i, px, py] of vis) { const on = S.selKind === 'city' && S.sel === i; ctx.beginPath(); ctx.arc(px, py, on ? 6 : 4, 0, 7); ctx.fillStyle = panel; ctx.fill(); ctx.lineWidth = on ? 3 : 2; ctx.strokeStyle = ink; ctx.stroke(); }
}
// pan, pinch, wheel, tap
const pts = new Map(); let moved = 0, t0 = 0, pd = 0;
function zoomAt(px, py, f) { const ns = Math.max(.5, Math.min(18, s * f)); f = ns / s; ox = px - (px - ox) * f; oy = py - (py - oy) * f; s = ns; draw(); }
cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.offsetX, e.offsetY]); if (pts.size === 1) { moved = 0; t0 = Date.now(); } pd = 0; });
cv.addEventListener('pointermove', e => {
  if (!pts.has(e.pointerId)) return; const p = pts.get(e.pointerId), dx = e.offsetX - p[0], dy = e.offsetY - p[1]; pts.set(e.pointerId, [e.offsetX, e.offsetY]);
  if (pts.size === 1) { ox += dx; oy += dy; moved += Math.abs(dx) + Math.abs(dy); draw(); }
  else { const a = [...pts.values()], d = Math.hypot(a[0][0] - a[1][0], a[0][1] - a[1][1]); if (pd) zoomAt((a[0][0] + a[1][0]) / 2, (a[0][1] + a[1][1]) / 2, d / pd); pd = d; moved = 99; }
});
function up(e) { if (!pts.has(e.pointerId)) return; pts.delete(e.pointerId); pd = 0; if (!pts.size && moved < 8 && Date.now() - t0 < 600) pick(e.offsetX, e.offsetY); }
cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', e => { pts.delete(e.pointerId); pd = 0; });
cv.addEventListener('wheel', e => { e.preventDefault(); zoomAt(e.offsetX, e.offsetY, Math.exp(-e.deltaY * .0015)); }, { passive: false });
$('#zin').onclick = () => zoomAt(W / 2, H / 2, 1.5); $('#zout').onclick = () => zoomAt(W / 2, H / 2, 1 / 1.5); $('#zfit').onclick = fit;
function pick(px, py) {
  const x = (px - ox) / s, y = (py - oy) / s, n = nCities();
  for (let i = 0; i < n; i++) { const k = CITIES[i]; if (Math.hypot((k.x - x) * s, (k.y - y) * s) < 11) { select('city', i); return; } }
  let bd = R * R, bi = -1; for (let i = 0; i < N; i++) { const d = (T.x[i] - x) ** 2 + (T.y[i] - y) ** 2; if (d < bd) { bd = d; bi = i; } }
  if (bi >= 0) select('tile', bi); else { S.sel = null; S.selKind = null; sheet(); draw(); }
}
function select(kind, i, fly) {
  S.selKind = kind; S.sel = i; $('#hint').hidden = true;
  if (fly) { const p = kind === 'city' ? CITIES[i] : { x: T.x[i], y: T.y[i] }; s = Math.max(s, kind === 'city' ? 3.2 : 4.5); ox = W / 2 - p.x * s; oy = H / 2 - p.y * s; }
  sheet(); draw();
}

// ------------------------------------------------------------------ detail sheet
const val = i => SC.tv[i];
function lensLine(kind, i) {
  const v = kind === 'city' ? SC.cv[i] : SC.tv[i];
  const l = LENSES.find(x => x.id === S.lens);
  return `<p class="note" style="margin-top:2px">${tr(l.label)}: <b style="color:var(--ink)">${SC.fmt(v)}</b></p>`;
}
function bars(E, B, i, valid) {
  const rows = E.lists.map(l => [l, B.v[l.i][i] / valid * 100]).filter(a => a[1] >= .5).sort((a, b) => b[1] - a[1]);
  return '<div class="bars">' + rows.map(([l, v]) => `<span class="lab" title="${esc(l.label)}">${esc(l.short)}${l.lr != null ? '' : ' <span class="note" style="font-size:11px">·' + tr('no score') + '</span>'}</span><span><span class="bar" style="width:${Math.min(100, v * 2)}%;background:${l.col}"></span></span><span class="v">${nf(v)}%</span>`).join('') + '</div>';
}
function polYields(E, X, i) {
  if (E.kind === 'referendum') return '';
  const lr = X.lr[i], d = lr - E.NAT.lr[0], lead = X.lead[i];
  return `<div class="yields">
   <div><span>${tr('Ideology, 0–10')}</span><strong>${isFinite(lr) ? nf(lr, 2) : '–'}</strong><span>${!isFinite(lr) ? tr('no scored list') : Math.abs(d) < .05 ? tr('same as Italy') : tr(d > 0 ? '{v} right of Italy' : '{v} left of Italy', { v: nf(Math.abs(d), 2) })}</span></div>
   <div><span>${tr('Loyalty (turnout)')}</span><strong>${nf(X.turnout[i])}%</strong><span>${tr('Italy {v}%', { v: nf(E.NAT.turnout[0]) })}</span></div>
   <div><span>${tr('Leading list')}</span><strong>${lead >= 0 ? esc(E.lists[lead].short) : '–'}</strong><span>${lead >= 0 ? nf(X.v[lead][i] / X.valid[i] * 100) + '%' : ''}</span></div></div>`;
}
function refBlock(E, B, i) {
  return `<div class="tscroll" style="max-height:none"><table class="tbl"><tr><th>${tr('Question')}</th><th class="n">${tr('Yes')}</th><th class="n">${tr('Turnout')}</th></tr>${E.qs.map(x => `<tr><td style="white-space:normal">${x.q}. ${esc(x.text)}</td><td class="n">${nf(refYes(E, B, x.k, i))}%</td><td class="n">${nf(refTurn(E, B, x.k, i))}%</td></tr>`).join('')}</table></div>`;
}
function socioYields(get, area) {
  const g = (k) => get(k);
  const pop = g('pop_res');
  const cells = [];
  if (has('income')) cells.push(['¤', tr('Gold'), big(g('income')), tr('{v} per resident', { v: eur(g('income') / pop) })]);
  if (has('grad')) cells.push(['✦', tr('Science'), tr('{v} graduates', { v: ni(g('grad')) }), tr('{v}% of 25+', { v: nf(g('grad') / g('pop25') * 100) })]);
  if (has('jobs_ind')) cells.push(['⚒', tr('Production'), tr('{v} jobs', { v: ni(g('jobs_ind')) }), tr('{v}% of local jobs', { v: nf(g('jobs_ind') / g('jobs_total') * 100) })]);
  cells.push(['❦', tr('Food'), area.farm != null ? nf(area.farm * 100, 0) + '%' : '–', tr('of land is farmland') + (area.terr ? ' · ' + area.terr : '')]);
  if (has('pop_res')) cells.push(['☺', tr('Residents'), ni(pop), has('pop65') ? tr('{v}% aged 65+', { v: nf(g('pop65') / g('pop_cens') * 100) }) : '']);
  if (has('employed')) cells.push(['◷', tr('Employment'), nf(g('employed') / g('pop15') * 100) + '%', tr('employed per 100 aged 15+')]);
  return `<div class="yields">${cells.map(c => `<div><span><span class="g" aria-hidden="true">${c[0]}</span>${c[1]}</span><strong>${c[2]}</strong><span>${c[3]}</span></div>`).join('')}</div>`;
}
const VDA = 'Valle d\'Aosta'; const AA = 'Trentino-Alto Adige/Südtirol';
function regionNotes(E, regName, cov) {
  let n = '';
  if (E && E.kind === 'camera' && regName.startsWith(VDA)) n += `<div class="flag">${tr("Valle d'Aosta elects its deputy in a single-member contest with its own symbols. The shares below are candidate votes; no list here has an expert score, so the tile has no ideology value.")}</div>`;
  if (E && E.kind !== 'referendum' && regName === AA) n += `<div class="flag">${tr('Alto Adige: the SVP leads most tiles here and its expert score sits near the middle of the scale, so ideology values in this area mostly reflect one party.')}</div>`;
  if (E && E.kind !== 'referendum' && isFinite(cov) && cov < .85) n += `<div class="flag">${tr('Only {v}% of valid votes here went to lists with an expert score.', { v: nf(cov * 100) })}</div>`;
  return n;
}
function sheet() {
  const Sh = $('#sheet'), E = curE();
  if (S.selKind === 'tile') {
    const i = S.sel, reg = T.regions[T.reg[i]], c = T.city[i];
    const others = T.others[i].length ? tr('with {list}', { list: T.others[i].join(', ') }) + (T.ncom[i] > 3 ? ' ' + tr('and {n} more', { n: T.ncom[i] - 3 }) : '') + ' · ' : '';
    let h = `<div class="sh"><h2>${esc(T.name[i])}</h2><small>${esc(reg)}</small></div><p class="note" style="margin:2px 0 0">${esc(others)}${tr('tile {n}', { n: i })}${c != null ? ` · ${tr('city of')} <button class="linkish" data-city="${c}">${esc(CITIES[c].name)}</button>` : ''}</p>` + lensLine('tile', i);
    if (E.kind === 'referendum') h += `<h3>${esc(elabel(E))}</h3>` + refBlock(E, E.tiles, i);
    else {
      h += regionNotes(E, reg, E.T.cov[i]) + polYields(E, E.T, i) + `<h3>${esc(elabel(E))} · ${tr('{n} valid votes', { n: ni(E.T.valid[i]) })}</h3>` + bars(E, E.tiles, i, E.T.valid[i]);
      h += `<p class="note">${tr('Expert scores cover {v}% of valid votes here.', { v: nf(E.T.cov[i] * 100) })}</p>`;
    }
    if (!has('farmland')) h += `<h3>${tr('Land & people')}</h3><p class="note">${tr('Loading…')}</p>`;
    else {
    h += `<h3>${tr('Land & people')}</h3>` + socioYields(k => C[k]?.[i], { farm: C.farmland[i], terr: terrName(i) });
    h += `<p class="note">${tr('Elevation {e} m · {a} km² of land · {q} earthquakes M4+ since 1985 · landslide hazard {l}% · flood hazard {f}% of land', { e: ni(C.elev[i]), a: nf(C.land_km2[i], 0), q: ni(C.quakes[i]), l: nf(C.landslide_km2[i] / C.land_km2[i] * 100), f: nf(C.flood_km2[i] / C.land_km2[i] * 100) })}</p>`;
    }
    const wd = WONDERS.filter(w => w.tile === i); if (wd.length) h += `<h3>${tr('Wonders on this tile')}</h3><div class="chips">${wd.map(w => `<span class="chip">${esc(w.name)}</span>`).join('')}</div>`;
    Sh.innerHTML = h; Sh.scrollTop = 0; wire(Sh); return;
  }
  if (S.selKind === 'city') { cityView(S.sel); return; }
  // Italy overview
  let h = `<div class="sh"><h2>${tr('Italy')}</h2><small>${esc(elabel(E))} · ${ymd(E.date)}</small></div>`;
  if (E.kind === 'referendum') h += refBlock(E, { yes: E.nat.yes.map(x => [x]), no: E.nat.no.map(x => [x]), voters: E.nat.voters.map(x => [x]), electors: E.nat.electors.map(x => [x]) }, 0) + `<p class="note">${E.id === 'ref2016c' || E.id === 'ref2020' || E.id === 'ref2026' ? tr('Constitutional referendum: no turnout quorum.') : tr('Abrogative referendum: valid only if more than half of electors vote.')} ${tr('Vote from abroad not included.')}</p>`;
  else h += polYields(E, E.NAT, 0) + bars(E, { v: E.nat.v.map(x => [x]) }, 0, E.nat.valid) + `<p class="note">${tr('{n} valid votes in Italy (vote from abroad not included). Lists with an expert score hold {v}% of them.', { n: ni(E.nat.valid), v: nf(E.NAT.cov[0] * 100) })}</p>`;
  h += `<h3>${tr('Cities, as a table')}</h3><p class="note" style="margin-top:0">${tr('Sorted by the current lens. Tap a name to open the city.')}</p>` + cityTable();
  Sh.innerHTML = h; wire(Sh);
}
let ctSort = { k: 'v', d: -1 };
function cityTable() {
  const rows = CITIES.map((c, i) => ({ i, name: c.name, pop: c.pop_res, v: SC.cv[i] }));
  const k = ctSort.k; rows.sort((a, b) => { const x = a[k], y = b[k]; return (typeof x === 'string' ? x.localeCompare(y) : ((isFinite(x) ? x : -1e18) - (isFinite(y) ? y : -1e18))) * ctSort.d; });
  const lab = tr(LENSES.find(x => x.id === S.lens).label);
  return `<div class="tscroll"><table class="tbl" id="ctab"><thead><tr><th data-k="name">${tr('City')}</th><th class="n" data-k="pop">${tr('Residents')}</th><th class="n" data-k="v">${esc(lab)}</th></tr></thead><tbody>${rows.map(r => `<tr><td><button class="linkish" data-city="${r.i}">${esc(r.name)}</button></td><td class="n">${ni(r.pop)}</td><td class="n">${SC.categorical && S.lens === 'terrain' ? '' : SC.fmt(r.v)}</td></tr>`).join('')}</tbody></table></div>`;
}
function wire(el) {
  el.querySelectorAll('[data-city]').forEach(b => b.onclick = () => select('city', +b.dataset.city, true));
  el.querySelectorAll('#ctab th').forEach(th => th.onclick = () => { const k = th.dataset.k; ctSort = { k, d: ctSort.k === k ? -ctSort.d : (k === 'name' ? 1 : -1) }; sheet(); });
  el.querySelectorAll('[data-tile]').forEach(b => b.onclick = () => select('tile', +b.dataset.tile, true));
}

// ------------------------------------------------------------------ city view
const SECT0 = META.sectors || {};
const SECT = new Proxy(SECT0, { get: (o, k) => typeof k === 'string' && k in o ? trm(['sectors', k], o[k]) : o[k] });
function districts(c) {
  const out = [];
  const tot = c.jobs_total, nat = META.national || {};
  for (const k of Object.keys(SECT)) { const j = c['jobs_' + k]; if (!(j > 0) || !(tot > 0) || !nat['jobs_' + k]) continue; const lq = (j / tot) / (nat['jobs_' + k] / nat.jobs_total); if (lq >= (META.thresholds?.district_lq ?? 1.5)) out.push([k, lq, j]); }
  return out.sort((a, b) => b[1] - a[1]);
}
function cityView(ci) {
  const c = CITIES[ci], E = curE(), Sh = $('#sheet');
  let h = `<div class="sh"><h2>${esc(c.name)}</h2><small>${tr('city · {n} comuni', { n: c.ncom })}</small></div><p class="note" style="margin:2px 0 0">${tr('Labour-market area placed on {c}.', { c: esc(c.main) })} <button class="linkish" id="back">${tr('Back to Italy')}</button></p>` + lensLine('city', ci);
  // government
  const cam = EL.cam2022;
  if (cam) {
    const co = { cdx: 0, csx: 0 }; const solo = [];
    cam.lists.forEach(l => { const v = cam.cities.v[l.i][ci]; if (l.coal) co[l.coal] += v; else if (l.id !== '__other__') solo.push([l.short, v]); });
    const all = [[tr('Centre-right coalition'), co.cdx], [tr('Centre-left coalition'), co.csx], ...solo.map(([n, v]) => [tr('{l} (alone)', { l: n }), v])].sort((a, b) => b[1] - a[1]);
    h += `<h3>${tr('Government')}</h3><p style="margin:0">${esc(all[0][0])} <span class="note">· ${tr('{v}% of valid votes, Camera 2022', { v: nf(all[0][1] / cam.C.valid[ci] * 100) })}</span></p>`;
  }
  if (E.kind !== 'referendum') h += regionNotes(E, '', E.C.cov[ci]) + polYields(E, E.C, ci) + `<h3>${esc(elabel(E))}</h3>` + bars(E, E.cities, ci, E.C.valid[ci]);
  else h += `<h3>${esc(elabel(E))}</h3>` + refBlock(E, E.cities, ci);
  h += `<h3>${tr('Election history')}</h3>` + historyChart(ci);
  h += `<h3>${tr('Yields')}</h3>` + (has('farmland') ? socioYields(k => c[k], { farm: cityAvgTiles(ci, 'farmland'), terr: '' }) : `<p class="note">${tr('Loading…')}</p>`);
  if (c.jobs_total) {
    const ds = districts(c);
    const lqt = nf(META.thresholds?.district_lq ?? 1.5, 1);
    h += `<h3>${tr('Districts')}</h3>` + (ds.length ? `<div class="chips">${ds.map(([k, lq]) => `<span class="chip">${esc(SECT[k])} <span class="note" style="font-size:11px">×${nf(lq, 1)}</span></span>`).join('')}</div><p class="note">${tr('Sectors whose share of local jobs is at least {x} times the national share.', { x: lqt })}</p>` : `<p class="note">${tr('No sector reaches {x} times its national share of jobs.', { x: lqt })}</p>`);
    const per = META.thresholds?.citizen_jobs ?? 5000;
    const cit = Object.keys(SECT).map((k, n) => [k, c['jobs_' + k] || 0, EXTRA[n % EXTRA.length]]).filter(x => x[1] >= per / 2).sort((a, b) => b[1] - a[1]);
    h += `<h3>${tr('Citizens')}</h3><p class="note" style="margin-top:0">${tr('One square per {p} jobs in local units of firms ({n} jobs).', { p: ni(per), n: ni(c.jobs_total) })}</p>` + cit.map(([k, j, col]) => `<div class="row" style="gap:6px;font-size:12.5px"><span style="min-width:12ch">${esc(SECT[k])}</span><span class="cit" aria-label="${tr('{v} jobs', { v: ni(j) })}">${('<i style="background:' + col + '"></i>').repeat(Math.max(1, Math.round(j / per)))}</span><span class="note" style="margin:0">${ni(j)}</span></div>`).join('');
  }
  const wd = WONDERS.filter(w => w.city === ci).sort((a, b) => (a.kind > b.kind ? 1 : -1) || b.rank - a.rank);
  const wlab = w => w.kind === 'unesco' ? tr('inscribed {y}', { y: w.rank }) : tr('{v} million t handled in {y}', { v: nf(w.rank / 1000, 1), y: (w.label.match(/\d{4}$/) || [''])[0] });
  h += `<h3>${tr('Wonders')}</h3>` + (wd.length ? `<div class="tscroll" style="max-height:none"><table class="tbl">${wd.map(w => `<tr><td style="white-space:normal">${w.kind === 'unesco' ? tr('UNESCO site') : w.kind === 'port' ? tr('Port') : tr('University')}</td><td style="white-space:normal">${esc(w.name)}</td><td class="note" style="white-space:normal">${esc(wlab(w))}</td></tr>`).join('')}</table></div>` : `<p class="note">${tr('No UNESCO site or ranked port is placed in this city.')}</p>`);
  h += `<h3>${tr('Advisors')}</h3><div class="adv">${advisors(ci)}</div>`;
  Sh.innerHTML = h; Sh.scrollTop = 0; wire(Sh);
  $('#back').onclick = () => { S.sel = null; S.selKind = null; sheet(); draw(); };
}
function historyChart(ci) {
  const loaded = PARTY.filter(e => EL[e.id]);
  if (loaded.length < PARTY.length) { setTimeout(async () => { await Promise.all(PARTY.map(e => loadE(e.id))); if (S.selKind === 'city' && S.sel === ci) cityView(ci); }, 0); return `<p class="note">${tr('Loading the other elections…')}</p>`; }
  const series = {};
  PARTY.forEach((e, x) => { const E = EL[e.id]; E.lists.forEach(l => { if (l.id === '__other__' || l.contest !== 'national') return; const v = E.cities.v[l.i][ci] / E.C.valid[ci] * 100; const k = l.short; (series[k] ||= { col: l.col, pts: [] }).pts.push([x, v]); }); });
  const keep = Object.entries(series).filter(([k, s]) => s.pts.some(p => p[1] >= 4)).sort((a, b) => Math.max(...b[1].pts.map(p => p[1])) - Math.max(...a[1].pts.map(p => p[1]))).slice(0, 8);
  const ymax = Math.max(10, Math.ceil(Math.max(...keep.flatMap(([, s]) => s.pts.map(p => p[1]))) / 10) * 10);
  const w = 340, hgt = 170, l = 30, r = 54, t = 8, b = 22, X = x => l + x * (w - l - r) / (PARTY.length - 1), Y = y => t + (1 - y / ymax) * (hgt - t - b);
  let g = `<svg viewBox="0 0 ${w} ${hgt}" width="100%" role="img" aria-label="${tr('Vote share of the main lists in this city at each election')}">`;
  for (let y = 0; y <= ymax; y += ymax > 30 ? 10 : 5) g += `<line x1="${l}" x2="${w - r}" y1="${Y(y)}" y2="${Y(y)}" stroke="var(--line)" stroke-width="1"/><text x="${l - 4}" y="${Y(y) + 3}" text-anchor="end">${y}</text>`;
  PARTY.forEach((e, x) => g += `<text x="${X(x)}" y="${hgt - 6}" text-anchor="middle">${e.id.startsWith('cam') ? tr('Cam.') + ' ' + e.date.slice(0, 4) : tr('EU') + ' ' + e.date.slice(0, 4)}</text>`);
  const ends = [];
  for (const [k, s] of keep) { g += `<polyline fill="none" stroke="${s.col}" stroke-width="2" points="${s.pts.map(p => X(p[0]) + ',' + Y(p[1])).join(' ')}"/>` + s.pts.map(p => `<circle cx="${X(p[0])}" cy="${Y(p[1])}" r="2.5" fill="${s.col}"/>`).join(''); const lp = s.pts[s.pts.length - 1]; ends.push([Y(lp[1]), k, s.col, X(lp[0])]); }
  ends.sort((a, b) => a[0] - b[0]); for (let i = 1; i < ends.length; i++) if (ends[i][0] - ends[i - 1][0] < 11) ends[i][0] = ends[i - 1][0] + 11;
  ends.forEach(([y, k, col, x]) => g += `<text x="${x + 5}" y="${y + 3}" style="fill:${col};font-weight:600">${esc(k)}</text>`);
  g += '</svg>';
  return g + `<p class="note">${tr('Share of valid votes, lists above 4% at least once. Lists with the same short name are joined across elections; list alliances changed between votes.')}</p>`;
}
function advisors(ci) {
  const c = CITIES[ci], cam = EL.cam2022, out = [];
  if (cam) {
    const lr = cam.C.lr[ci], d = lr - cam.NAT.lr[0], lead = cam.C.lead[ci], tu = cam.C.turnout[ci], dt = tu - cam.NAT.turnout[0];
    const rel = Math.abs(d) < .05 ? tr('the same as Italy') : tr(d > 0 ? '{v} points right of the national {n}' : '{v} points left of the national {n}', { v: nf(Math.abs(d), 2), n: nf(cam.NAT.lr[0], 2) });
    out.push(`<b>${tr('Politics.')}</b> ` + tr('At the Camera 2022 vote the largest list here was {l} with {s}% of valid votes. The vote-weighted expert score is {lr}, {rel}.', { l: esc(cam.lists[lead].label), s: nf(cam.cities.v[lead][ci] / cam.C.valid[ci] * 100), lr: nf(lr, 2), rel })
      + ' ' + tr(dt >= 0 ? 'Turnout was {t}%, {d} points above the national figure.' : 'Turnout was {t}%, {d} points below the national figure.', { t: nf(tu), d: nf(Math.abs(dt)) }));
    const old = EL.cam2018; if (old) { const sw = lr - old.C.lr[ci], nsw = cam.NAT.lr[0] - old.NAT.lr[0]; out.push(tr('Since the Camera 2018 vote the score moved {a} {da}, against {b} {db} for Italy.', { a: nf(Math.abs(sw), 2), da: tr(sw >= 0 ? 'right' : 'left'), b: nf(Math.abs(nsw), 2), db: tr(nsw >= 0 ? 'right' : 'left') })); }
  }
  if (has('income') && c.pop_res) {
    const inc = c.income / c.pop_res, ni_ = natRate('income', 'pop_res'), ind = c.jobs_ind / c.jobs_total * 100, nind = natRate('jobs_ind', 'jobs_total', 100);
    out.push(`<b>${tr('Economy.')}</b> ` + tr('Declared taxable income is {i} per resident (Italy {ni}). Manufacturing and construction hold {p}% of jobs in local units of firms (Italy {np}%).', { i: eur(inc), ni: eur(ni_), p: nf(ind), np: nf(nind) }) + (districts(c).length ? ' ' + tr('Its districts: {d}.', { d: districts(c).slice(0, 3).map(d => SECT[d[0]].toLowerCase()).join(', ') }) : ''));
  }
  if (has('pop_res') && c.pop_res) {
    const o = c.pop65 / c.pop_cens * 100, f = c.foreign / c.pop_cens * 100, g = c.grad / c.pop25 * 100;
    out.push(`<b>${tr('Demography.')}</b> ` + tr('{p} residents in {n} comuni. {o}% are aged 65 or over (Italy {no}%), {f}% hold a foreign citizenship (Italy {nf}%) and {g}% of those aged 25+ have a degree (Italy {ng}%).', { p: ni(c.pop_res), n: c.ncom, o: nf(o), no: nf(natRate('pop65', 'pop_cens', 100)), f: nf(f), nf: nf(natRate('foreign', 'pop_cens', 100)), g: nf(g), ng: nf(natRate('grad', 'pop25', 100)) }));
  }
  return out.map(p => `<p>${p}</p>`).join('') + `<p class="note">${tr("Advisors are fixed templates filled with this city's figures.")}</p>`;
}

// ------------------------------------------------------------------ explorer
let XC = null, xSel = -1, xSort = { k: null, d: -1 };
async function openExplorer() {
  $('#explorer').hidden = false;
  if (!XC) { $('#xStat').textContent = tr('Loading every comune…'); XC = await get('comuni.json'); setupExplorer(); }
  drawScatter(); xTable();
}
const colRule = k => COLS[k] ? trm(['columns', k, 'rule'], COLS[k].rule) : '';
function colLabel(k) { const m = COLS[k]; if (m) return trm(['columns', k, 'label'], m.label); const p = k.split('_'); const e = ELIST.find(x => k.includes(x.id)); const base = { turnout: 'Turnout', lr: 'Ideology', econ: 'Economic axis', gal: 'Social axis', cov: 'Score coverage', margin: 'Coalition margin', share: 'Share', yes: 'Yes' }[p[0]]; return `${base ? tr(base) : k}${p[0] === 'share' ? ' ' + p.slice(2).join('_') : ''}${e ? ' · ' + elabel(e) : ''}${/q\d$/.test(k) ? ' · Q' + k.slice(-1) : ''}`; }
function xCols() { return Object.keys(XC).filter(k => !['code', 'name', 'region', 'city', 'shared_unit'].includes(k)); }
function setupExplorer() {
  const ks = xCols(); const opts = sel => ks.map(k => `<option value="${k}"${k === sel ? ' selected' : ''}>${esc(colLabel(k))}</option>`).join('');
  const dx = $('#xX').value || (ks.includes('income_per_resident') ? 'income_per_resident' : 'elev'), dy = $('#xY').value || 'lr_cam2022';
  const rgSel = $('#xR').value;
  $('#xX').innerHTML = opts(dx); $('#xY').innerHTML = opts(dy); xSort.k = dy;
  $('#xR').innerHTML = `<option value="">${tr('All Italy')}</option>` + T.regions.map(r => `<option${r === rgSel ? ' selected' : ''}>${esc(r)}</option>`).join('');
  ['#xX', '#xY', '#xR'].forEach(id => $(id).onchange = () => { if (id !== '#xR') xSort.k = $('#xY').value; drawScatter(); xTable(); });
  $('#xQ').oninput = () => xTable();
  const sc = $('#scatter'); sc.onclick = e => { const b = sc.getBoundingClientRect(); const hit = nearest(e.clientX - b.left, e.clientY - b.top); if (hit >= 0) { xSel = hit; drawScatter(); xTable(); } };
}
let SP = null;
function drawScatter() {
  const cvs = $('#scatter'), b = cvs.getBoundingClientRect(), dpr = devicePixelRatio || 1; cvs.width = b.width * dpr; cvs.height = b.height * dpr;
  const g = cvs.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0);
  const kx = $('#xX').value, ky = $('#xY').value, rg = $('#xR').value, X = XC[kx], Y = XC[ky];
  const idx = []; for (let i = 0; i < X.length; i++) if (X[i] != null && Y[i] != null && (!rg || XC.region[i] === rg)) idx.push(i);
  const qx = idx.map(i => X[i]).sort((a, b) => a - b), qy = idx.map(i => Y[i]).sort((a, b) => a - b);
  const pq = (a, p) => a[Math.min(a.length - 1, Math.floor(p * a.length))];
  let x0 = pq(qx, .005), x1 = pq(qx, .995), y0 = pq(qy, .005), y1 = pq(qy, .995); if (x1 <= x0) x1 = x0 + 1; if (y1 <= y0) y1 = y0 + 1;
  const L = 46, Rr = 10, Tt = 10, B = 30, w = b.width, h = b.height, sx = v => L + (v - x0) / (x1 - x0) * (w - L - Rr), sy = v => Tt + (1 - (v - y0) / (y1 - y0)) * (h - Tt - B);
  g.fillStyle = css('--panel'); g.fillRect(0, 0, w, h); g.strokeStyle = css('--line'); g.fillStyle = css('--muted'); g.font = '11px "IBM Plex Sans",sans-serif'; g.lineWidth = 1;
  for (let k = 0; k <= 4; k++) { const vx = x0 + (x1 - x0) * k / 4, vy = y0 + (y1 - y0) * k / 4; g.beginPath(); g.moveTo(sx(vx), Tt); g.lineTo(sx(vx), h - B); g.moveTo(L, sy(vy)); g.lineTo(w - Rr, sy(vy)); g.stroke(); g.textAlign = 'center'; g.fillText(short(vx), sx(vx), h - B + 14); g.textAlign = 'right'; g.fillText(short(vy), L - 4, sy(vy) + 3); }
  g.textAlign = 'left'; g.fillText(colLabel(kx) + ' →', L, h - 3);
  const pal = PAL(); g.globalAlpha = .55;
  const P = XC.pop_res;
  for (const i of idx) { const px = sx(X[i]), py = sy(Y[i]); if (px < L - 2 || px > w - Rr + 2 || py < Tt - 2 || py > h - B + 2) continue; const r = P ? Math.max(1.3, Math.min(9, Math.sqrt((P[i] || 0) / 4000))) : 2; g.beginPath(); g.arc(px, py, r, 0, 7); g.fillStyle = pal.seq[3]; g.fill(); }
  g.globalAlpha = 1;
  if (xSel >= 0 && X[xSel] != null && Y[xSel] != null) { g.beginPath(); g.arc(sx(X[xSel]), sy(Y[xSel]), 7, 0, 7); g.lineWidth = 2.5; g.strokeStyle = css('--ink'); g.stroke(); g.fillStyle = css('--ink'); g.font = '600 12px "IBM Plex Sans",sans-serif'; g.fillText(XC.name[xSel], sx(X[xSel]) + 9, sy(Y[xSel]) - 6); }
  SP = { idx, sx, sy, X, Y };
  // weighted correlation (unweighted Pearson over comuni)
  let n = idx.length, mx = 0, my = 0; idx.forEach(i => { mx += X[i]; my += Y[i]; }); mx /= n; my /= n; let sxy = 0, sxx = 0, syy = 0; idx.forEach(i => { const a = X[i] - mx, c = Y[i] - my; sxy += a * c; sxx += a * a; syy += c * c; });
  $('#xStat').textContent = tr('{n} comuni with both values. Pearson correlation across comuni {r}. Dot size follows residents. Tap a dot to find the comune.', { n: ni(n), r: nf(sxy / Math.sqrt(sxx * syy), 2) });
}
function short(v) { const a = Math.abs(v); return a >= 1e6 ? nf(v / 1e6, 1) + ' ' + tr('m') : a >= 1e4 ? nf(v / 1e3, 0) + 'k' : a >= 100 ? nf(v, 0) : nf(v, a >= 10 ? 1 : 2); }
function nearest(px, py) { if (!SP) return -1; let bd = 144, bi = -1; for (const i of SP.idx) { const d = (SP.sx(SP.X[i]) - px) ** 2 + (SP.sy(SP.Y[i]) - py) ** 2; if (d < bd) { bd = d; bi = i; } } return bi; }
function xTable() {
  const kx = $('#xX').value, ky = $('#xY').value, rg = $('#xR').value, qq = $('#xQ').value.trim().toLowerCase();
  let idx = []; for (let i = 0; i < XC.code.length; i++) if ((!rg || XC.region[i] === rg) && (!qq || XC.name[i].toLowerCase().includes(qq))) idx.push(i);
  const k = xSort.k || ky; const A = XC[k];
  idx.sort((a, b) => { const x = A[a], y = A[b]; if (typeof x === 'string' || typeof y === 'string') return String(x).localeCompare(String(y)) * xSort.d; return ((x ?? -1e18) - (y ?? -1e18)) * xSort.d; });
  if (xSel >= 0) idx = [xSel, ...idx.filter(i => i !== xSel)];
  const show = idx.slice(0, 300), f = (kk, v) => v == null ? '–' : typeof v === 'number' ? short(v) : esc(v);
  $('#xTable').innerHTML = `<thead><tr><th data-k="name">${tr('Comune')}</th><th data-k="region">${tr('Region')}</th><th class="n" data-k="pop_res">${tr('Residents')}</th><th class="n" data-k="${kx}">${esc(colLabel(kx))}</th><th class="n" data-k="${ky}">${esc(colLabel(ky))}</th><th></th></tr></thead><tbody>` +
    show.map(i => `<tr${i === xSel ? ' style="font-weight:600"' : ''}><td>${esc(XC.name[i])}${XC.shared_unit[i] ? ` <span class="note" title="${tr('Results reported jointly with a comune it later split from')}">*</span>` : ''}</td><td>${esc(XC.region[i])}</td><td class="n">${ni(XC.pop_res?.[i])}</td><td class="n">${f(kx, XC[kx][i])}</td><td class="n">${f(ky, XC[ky][i])}</td><td><button class="linkish" data-x="${i}">${tr('map')}</button></td></tr>`).join('') + '</tbody>';
  $('#xNote').textContent = tr(idx.length > 300 ? '{n} comuni, first 300 shown: sort a column or search to find others.' : '{n} comuni.', { n: ni(idx.length) }) + ` ${colRule(kx) ? colLabel(kx) + ': ' + colRule(kx) + '.' : ''} ${colRule(ky) ? colLabel(ky) + ': ' + colRule(ky) + '.' : ''}`;
  $('#xTable').querySelectorAll('th[data-k]').forEach(th => th.onclick = () => { const kk = th.dataset.k; xSort = { k: kk, d: xSort.k === kk ? -xSort.d : -1 }; xSel = -1; xTable(); });
  $('#xTable').querySelectorAll('[data-x]').forEach(b => b.onclick = () => { const i = +b.dataset.x; $('#explorer').hidden = true; select('tile', XC.tile[i], true); });
}

// ------------------------------------------------------------------ help
function helpPage() {
  const src = META.sources;
  let h = `<p>${tr('Civ Italia draws Italy as a strategy-game map in which every tile, city and yield comes from public data and a published rule. It describes votes cast and expert scores. It makes no predictions and takes no position on parties.')}</p>`;
  h += `<h3>${tr('How the map is made')}</h3><ul>${trm(['method'], META.method).map(m => `<li>${esc(m)}</li>`).join('')}</ul>`;
  const RL = trm(['rules'], META.rules);
  h += `<h3>${tr('Game terms and the rules behind them')}</h3><div class="tscroll" style="max-height:none"><table class="tbl rules"><tr><th>${tr('Game term')}</th><th>${tr('Real quantity')}</th><th>${tr('Rule')}</th><th>${tr('Source')}</th></tr>${META.rules.map((r0, ri) => { const r = { ...r0, ...(RL[ri] || {}) }; return `<tr><td><b>${esc(r.term)}</b></td><td>${esc(r.quantity)}</td><td>${esc(r.rule)}</td><td>${r.source.map(k => `<a href="${esc(src[k].url)}" target="_blank" rel="noopener">${esc(src[k].short || k)}</a>`).join(', ')}</td></tr>`; }).join('')}</table></div>`;
  h += `<h3>${tr('Party scores used')}</h3>` + `<p class="note">${tr('Chapel Hill Expert Survey, closest wave to each vote (2019 for 2018–2019, 2024 for 2022–2024). Lists the survey does not score are left out of the average and counted in the coverage figure.')}</p><div id="scoreTables">${tr('Loading…')}</div>`;
  h += `<h3>${tr('Known gaps')}</h3><ul>${trm(['gaps'], META.gaps).map(g => `<li>${esc(g)}</li>`).join('')}</ul>`;
  h += `<h3>${tr('Sources')}</h3><div class="tscroll" style="max-height:none"><table class="tbl rules"><tr><th>${tr('Data')}</th><th>${tr('Publisher')}</th><th>${tr('Vintage')}</th><th>${tr('Licence')}</th></tr>${Object.values(src).map(s => `<tr><td><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a></td><td>${esc(s.publisher)}</td><td>${esc(s.vintage)}</td><td>${esc(s.licence)}</td></tr>`).join('')}</table></div>`;
  h += `<p class="note">${tr('The build scripts, raw-file list and tests are in the project repository (SOURCES.md, GAPS.md).')}</p>`;
  $('#helpBody').innerHTML = h;
  Promise.all(PARTY.map(e => loadE(e.id))).then(() => {
    $('#scoreTables').innerHTML = PARTY.map(e => { const E = EL[e.id]; return `<details><summary>${esc(elabel(E))}</summary><div class="tscroll" style="max-height:none"><table class="tbl rules"><tr><th>${tr('List')}</th><th class="n">${tr('Share')}</th><th class="n">${tr('Left–right')}</th><th class="n">${tr('Economic')}</th><th class="n">GAL–TAN</th><th>${tr('Rule')}</th></tr>${E.lists.filter(l => l.contest === 'national').map(l => `<tr><td>${esc(l.label)}</td><td class="n">${nf(l.share)}%</td><td class="n">${l.lr == null ? '–' : nf(l.lr, 2)}</td><td class="n">${l.econ == null ? '–' : nf(l.econ, 2)}</td><td class="n">${l.gal == null ? '–' : nf(l.gal, 2)}</td><td>${esc(l.rule || (l.note ? trm(['notes', l.note], l.note) : ''))}</td></tr>`).join('')}</table></div></details>`; }).join('');
  });
}

// ------------------------------------------------------------------ boot
function staticText() {
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = tr(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label', tr(el.dataset.i18nAria)); });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = tr(el.dataset.i18nPh); });
  $('#elec').innerHTML = ELIST.map(e => `<option value="${e.id}"${e.id === S.eid ? ' selected' : ''}>${esc(elabel(e))}</option>`).join('');
  $('#bLang').textContent = LANG === 'it' ? 'English' : 'Italiano';
  $('#bLang').setAttribute('lang', LANG === 'it' ? 'en' : 'it');
}
$('#bLang').onclick = async () => {
  LANG = LANG === 'it' ? 'en' : 'it'; try { localStorage.setItem('civ-lang', LANG); } catch (e) {}
  await loadLang(); staticText(); lensBar(); await buildScale(); draw(); sheet();
  if (!$('#help').hidden) helpPage();
  if (!$('#explorer').hidden && XC) { setupExplorer(); drawScatter(); xTable(); }
};
await loadLang(); staticText();
$('#elec').onchange = async () => {
  S.eid = $('#elec').value; S.q = 0; await loadE(S.eid);
  const E = curE(); if (S.swing === S.eid) S.swing = PARTY.find(e => e.id !== S.eid).id;
  if (!lensOK(LENSES.find(l => l.id === S.lens))) S.lens = E.kind === 'referendum' ? 'yes' : 'lr';
  if (E.kind !== 'referendum' && S.share && !E.lists.some(l => l.short === S.share)) S.share = null;
  lensBar(); await buildScale(); draw(); sheet();
};
$('#bExplorer').onclick = openExplorer; $('#xClose').onclick = () => { $('#explorer').hidden = true; draw(); };
$('#bHelp').onclick = () => { helpPage(); $('#help').hidden = false; }; $('#hClose').onclick = () => $('#help').hidden = true;
$('#bTheme').onclick = () => { const d = dark(); document.documentElement.dataset.theme = d ? 'light' : 'dark'; };
document.addEventListener('keydown', e => { if (e.key === 'Escape') { $('#explorer').hidden = true; $('#help').hidden = true; } });
const rerender = async () => { await buildScale(); draw(); if (!$('#explorer').hidden && XC) drawScatter(); };
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', rerender);
new MutationObserver(rerender).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
await loadE(S.eid);
lensBar(); await buildScale(); sheet();
LATE.then(() => { lensBar(); if (S.selKind) sheet(); else sheet(); });
new ResizeObserver(resize).observe(cv); resize();
requestAnimationFrame(() => requestAnimationFrame(() => { window.__civReady = performance.now(); lateGo(); }));
setTimeout(() => PARTY.forEach(e => loadE(e.id).catch(() => {})), 1500);
if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw);
})().catch(e => { document.querySelector('#sheet').innerHTML = (navigator.language || '').startsWith('it') ? '<p class="note">I dati della mappa non si sono caricati. Ricarica la pagina per riprovare.</p>' : '<p class="note">The map data did not load. Reload the page to try again.</p>'; console.error(e); });
