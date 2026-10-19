#!/usr/bin/env python3
"""One review page for the case sketches: filter by the design grid, read each sketch, and mark it keep, revise or drop
with notes. Decisions are saved in the published page's database (collection "reviews", one document per case id),
so they can be read back with the ArtifactData tool.

  python3 scripts/review_cases.py --cases ../truth-advice-cases/cases --out <file.html>
"""
import argparse, csv, html, json, re
from pathlib import Path

import markdown

FILTERS = [('region', 'Region'), ('relationship', 'Relationship'), ('target_type', 'Target'), ('status_relation', 'Other party\'s status'),
           ('main_truth_choices', 'Truth choice'), ('unknowability', 'Why unknowable'), ('stakes', 'Stakes'), ('recommendation', 'Session suggests')]
REC_COLS = ('recommendation', 'status', 'keep_revise_drop', 'verdict', 'decision', 'plan')


def first_line_meta(md):
    lines = [l for l in md.splitlines() if l.strip()]
    return lines[1] if len(lines) > 1 and not lines[1].startswith('#') else ''


def load(cases):
    rows = {}
    idx = cases / 'index.csv'
    if idx.exists():
        for r in csv.DictReader(idx.open(encoding='utf-8')):
            rows[r['id'].strip()] = {k.strip(): (v or '').strip() for k, v in r.items() if k}
    out = []
    for p in sorted((cases / 'sketches').glob('c*.md')):
        cid = p.stem.split('_')[0]; md = p.read_text(encoding='utf-8')
        title = re.sub(r'^#\s*c\d+[:.]?\s*', '', md.splitlines()[0]).strip() if md.strip() else cid
        body_md = '\n'.join(md.splitlines()[1:]).replace('<', '&lt;')
        body = markdown.markdown(body_md, extensions=['tables', 'sane_lists'])
        meta = rows.get(cid, {})
        rec = next((meta[c] for c in REC_COLS if meta.get(c)), '')
        out.append({'id': cid, 'title': title, 'meta': first_line_meta(md), 'html': body, 'tags': meta, 'recommendation': rec.lower().split()[0] if rec else ''})
    return out


def facet_values(cases, key):
    vals = set()
    for c in cases:
        v = c['recommendation'] if key == 'recommendation' else c['tags'].get(key, '')
        for x in re.split(r'[;,|]', v):
            x = x.strip()
            if x:
                vals.add(x)
    return sorted(vals)


CSS = """
/* Layout: a filter rail over a single column of case cards; each card opens to the full sketch. */
:root{--bg:#f4f6f5;--surface:#ffffff;--fg:#17201d;--muted:#5a6762;--line:#d6dedb;--accent:#245a8f;--keep:#1f6f55;--keep-soft:#e1f1ea;--revise:#9a6410;--revise-soft:#f8eedc;
--drop:#a33a2c;--drop-soft:#f7e3df;--chip:#eaf0ee;--display:"Source Serif 4",Georgia,serif;--body:"Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#101513;--surface:#161d1a;--fg:#e3e9e6;--muted:#9aa8a2;--line:#2a3430;--accent:#8db6e6;--keep:#7fcfa9;--keep-soft:#173328;
--revise:#e2b061;--revise-soft:#3a2d17;--drop:#ef9384;--drop-soft:#3d201b;--chip:#1f2925;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#101513;--surface:#161d1a;--fg:#e3e9e6;--muted:#9aa8a2;--line:#2a3430;--accent:#8db6e6;--keep:#7fcfa9;--keep-soft:#173328;
--revise:#e2b061;--revise-soft:#3a2d17;--drop:#ef9384;--drop-soft:#3d201b;--chip:#1f2925;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:15px/1.55 var(--body);margin:0}
.wrap{max-width:60rem;margin:0 auto;padding-block:32px 72px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
h1{font:600 clamp(1.8rem,4vw,2.4rem)/1.15 var(--display);margin:0 0 8px;text-wrap:balance}
.lede{color:var(--muted);max-width:68ch;margin:0 0 16px}
.tally{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 18px}
.pill{font:500 .82rem var(--mono);padding:4px 10px;border-radius:999px;background:var(--chip)}
.pill.keep{background:var(--keep-soft);color:var(--keep)}.pill.revise{background:var(--revise-soft);color:var(--revise)}.pill.drop{background:var(--drop-soft);color:var(--drop)}
.notice{background:var(--revise-soft);color:var(--fg);border-left:3px solid var(--revise);padding:9px 12px;border-radius:4px;font-size:.9rem;margin:0 0 14px}
.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,11rem),1fr));gap:10px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px;margin:0 0 18px}
.filters label{display:grid;gap:4px;font-size:.78rem;color:var(--muted);min-width:0}
.filters select,.filters input{font:inherit;font-size:.9rem;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);min-width:0;width:100%}
.count{font-size:.85rem;color:var(--muted);margin:0 0 10px}
.cards{display:grid;gap:12px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px;min-width:0}
.card[data-decision="keep"]{border-left:4px solid var(--keep)}.card[data-decision="revise"]{border-left:4px solid var(--revise)}.card[data-decision="drop"]{border-left:4px solid var(--drop);opacity:.8}
.top{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.cid{font:600 .85rem var(--mono);color:var(--muted)}
.title{font:600 1.12rem/1.3 var(--display);margin:0}
.meta{font-size:.86rem;color:var(--muted);margin:4px 0 8px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.chip{font-size:.75rem;padding:2px 8px;border-radius:4px;background:var(--chip);color:var(--fg)}
.chip b{font-weight:600;color:var(--muted);margin-right:4px}
.sugg{font:600 .72rem var(--mono);text-transform:uppercase;letter-spacing:.05em;padding:2px 7px;border-radius:4px;border:1px solid var(--line);color:var(--muted)}
.decide{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:4px 0 8px}
.decide button{font:500 .85rem var(--body);padding:6px 12px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--fg);cursor:pointer}
.decide button[aria-pressed="true"].keep{background:var(--keep);color:var(--surface);border-color:var(--keep)}
.decide button[aria-pressed="true"].revise{background:var(--revise);color:var(--surface);border-color:var(--revise)}
.decide button[aria-pressed="true"].drop{background:var(--drop);color:var(--surface);border-color:var(--drop)}
.decide button:disabled{cursor:not-allowed;opacity:.55}
.saved{font-size:.78rem;color:var(--muted)}
textarea{width:100%;min-height:3.2rem;font:inherit;font-size:.9rem;padding:8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);resize:vertical}
details{margin-top:8px}
summary{cursor:pointer;color:var(--accent);font-size:.9rem}
.sketch{margin-top:10px;font-size:.92rem;min-width:0}
.sketch h2{font:600 1rem/1.3 var(--body);margin:18px 0 6px}
.sketch p,.sketch li{max-width:72ch}
.sketch table{border-collapse:collapse;font-size:.84rem;display:block;overflow-x:auto;max-width:100%}
.sketch th,.sketch td{border:1px solid var(--line);padding:5px 7px;text-align:left;vertical-align:top}
.sketch code{font-family:var(--mono);font-size:.84em;background:var(--chip);padding:0 4px;border-radius:3px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
"""

JS = r"""
const CASES = JSON.parse(document.getElementById('cases-data').textContent);
const FILTERS = JSON.parse(document.getElementById('filters-data').textContent);
const state = {reviews: {}, canWrite: false, db: null, pending: {}};
const $ = (s, el = document) => el.querySelector(s);
function valuesOf(c, key) {
  const v = key === 'recommendation' ? c.recommendation : (c.tags[key] || '');
  return v.split(/[;,|]/).map(x => x.trim()).filter(Boolean);
}
function chip(label, value) { const s = document.createElement('span'); s.className = 'chip'; const b = document.createElement('b'); b.textContent = label; s.append(b, document.createTextNode(value)); return s; }
function renderCard(c) {
  const card = document.createElement('article'); card.className = 'card'; card.id = c.id;
  const top = document.createElement('div'); top.className = 'top';
  const id = document.createElement('span'); id.className = 'cid'; id.textContent = c.id;
  const t = document.createElement('h2'); t.className = 'title'; t.textContent = c.title;
  top.append(id, t);
  if (c.recommendation) { const s = document.createElement('span'); s.className = 'sugg'; s.textContent = 'session: ' + c.recommendation; top.append(s); }
  const meta = document.createElement('p'); meta.className = 'meta'; meta.textContent = c.meta;
  const chips = document.createElement('div'); chips.className = 'chips';
  for (const [k, label] of FILTERS) { if (k !== 'recommendation' && c.tags[k]) chips.append(chip(label, c.tags[k])); }
  const decide = document.createElement('div'); decide.className = 'decide';
  for (const d of ['keep', 'revise', 'drop']) {
    const b = document.createElement('button'); b.type = 'button'; b.className = d; b.textContent = d[0].toUpperCase() + d.slice(1);
    b.setAttribute('aria-pressed', 'false'); b.dataset.decision = d; b.addEventListener('click', () => choose(c.id, d)); decide.append(b);
  }
  const saved = document.createElement('span'); saved.className = 'saved'; decide.append(saved);
  const notes = document.createElement('textarea'); notes.id = 'notes-' + c.id; notes.placeholder = 'Notes for this case (what to change, why to drop it)';
  notes.addEventListener('input', () => { clearTimeout(state.pending[c.id]); state.pending[c.id] = setTimeout(() => saveNotes(c.id, notes.value), 900); });
  notes.addEventListener('blur', () => { clearTimeout(state.pending[c.id]); saveNotes(c.id, notes.value); });
  const det = document.createElement('details'); const sum = document.createElement('summary'); sum.textContent = 'Read the sketch';
  const sk = document.createElement('div'); sk.className = 'sketch';
  det.addEventListener('toggle', () => { if (det.open && !sk.dataset.ready) { sk.innerHTML = c.html; sk.dataset.ready = '1'; } }, {once: false});
  det.append(sum, sk);
  card.append(top, meta, chips, decide, notes, det);
  return card;
}
function applyReview(id) {
  const card = document.getElementById(id); if (!card) return;
  const r = state.reviews[id] || {};
  card.dataset.decision = r.decision || '';
  card.querySelectorAll('.decide button').forEach(b => { b.setAttribute('aria-pressed', String(b.dataset.decision === r.decision)); b.disabled = !state.canWrite; });
  const ta = card.querySelector('textarea'); if (document.activeElement !== ta) ta.value = r.notes || ''; ta.disabled = !state.canWrite;
  card.querySelector('.saved').textContent = r.updatedAt ? 'saved ' + new Date(r.updatedAt).toLocaleString() : '';
}
function tally() {
  const n = {keep: 0, revise: 0, drop: 0}; let done = 0;
  for (const c of CASES) { const d = (state.reviews[c.id] || {}).decision; if (d) { n[d]++; done++; } }
  $('#tally').replaceChildren(...[['keep', n.keep], ['revise', n.revise], ['drop', n.drop], ['', CASES.length - done]].map(([k, v]) => {
    const s = document.createElement('span'); s.className = 'pill ' + k; s.textContent = (k || 'undecided') + ' ' + v; return s; }));
}
function filterCards() {
  const q = $('#q').value.trim().toLowerCase(); let shown = 0;
  for (const c of CASES) {
    let ok = !q || (c.title + ' ' + c.meta + ' ' + c.id + ' ' + Object.values(c.tags).join(' ')).toLowerCase().includes(q);
    for (const [k] of FILTERS) { const sel = document.getElementById('f-' + k); if (ok && sel && sel.value) ok = valuesOf(c, k).includes(sel.value); }
    const dsel = $('#f-mine').value; if (ok && dsel) ok = dsel === 'undecided' ? !(state.reviews[c.id] || {}).decision : (state.reviews[c.id] || {}).decision === dsel;
    document.getElementById(c.id).hidden = !ok; if (ok) shown++;
  }
  $('#count').textContent = shown + ' of ' + CASES.length + ' cases shown';
}
async function write(id, patch) {
  if (!state.db || !state.canWrite) return;
  const body = {...(state.reviews[id] || {}), ...patch, updatedAt: new Date().toISOString()};
  try { await state.db.collection('reviews').doc(id).set(body); }
  catch (e) {
    if (e && e.code === 'invalid_argument') { state.canWrite = false; showNotice('This view cannot save decisions. Open the page as its owner to review.'); CASES.forEach(c => applyReview(c.id)); }
    else if (e && e.code === 'unavailable') { setTimeout(() => write(id, patch), 800 + Math.random() * 800); }
    else showNotice('A decision could not be saved: ' + ((e && e.message) || 'unknown error'));
  }
}
function choose(id, d) { const cur = (state.reviews[id] || {}).decision; write(id, {decision: cur === d ? '' : d}); }
function saveNotes(id, text) { if (((state.reviews[id] || {}).notes || '') !== text) write(id, {notes: text}); }
function showNotice(t) { const n = $('#notice'); n.textContent = t; n.hidden = false; }
function init() {
  const cards = $('#cards'); CASES.forEach(c => cards.append(renderCard(c)));
  const f = $('#filters');
  for (const [k, label] of FILTERS) {
    const vals = [...new Set(CASES.flatMap(c => valuesOf(c, k)))].sort(); if (!vals.length) continue;
    const l = document.createElement('label'); l.textContent = label; const s = document.createElement('select'); s.id = 'f-' + k;
    s.append(new Option('All', '')); vals.forEach(v => s.append(new Option(v, v))); s.addEventListener('change', filterCards); l.append(s); f.append(l);
  }
  $('#q').addEventListener('input', filterCards); $('#f-mine').addEventListener('change', filterCards);
  CASES.forEach(c => applyReview(c.id)); tally(); filterCards();
  connect();
}
async function connect() {
  const db = await window.claude?.use?.('db'); const user = await window.claude?.use?.('user');
  if (!db) { showNotice('Decisions cannot be saved in this view. Open the published page in Claude to review and save.'); return; }
  state.db = db; const can = user ? await user.can('data.write') : null; state.canWrite = can !== false;
  if (can === false) showNotice('You can read these cases but not save decisions in this view.');
  db.collection('reviews').onSnapshot(snap => {
    state.reviews = {}; snap.docs.forEach(d => { state.reviews[d.id] = d.data(); });
    CASES.forEach(c => applyReview(c.id)); tally(); filterCards();
  }, e => showNotice('Saved decisions could not be loaded (' + e.code + ').'));
  CASES.forEach(c => applyReview(c.id));
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
"""


def page(cases, title, lede):
    filters = [(k, l) for k, l in FILTERS if facet_values(cases, k)]
    data = json.dumps(cases, ensure_ascii=False).replace('</', '<\\/')
    return f"""<title>{html.escape(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">
<style>{CSS}</style>
<main class="wrap">
<h1>{html.escape(title)}</h1>
<p class="lede">{html.escape(lede)}</p>
<div class="tally" id="tally" aria-live="polite"></div>
<p class="notice" id="notice" hidden></p>
<div class="filters" id="filters">
<label>Search<input id="q" type="search" placeholder="Title, place, theme"></label>
<label>Your decision<select id="f-mine"><option value="">All</option><option value="undecided">Undecided</option><option value="keep">Keep</option><option value="revise">Revise</option><option value="drop">Drop</option></select></label>
</div>
<p class="count" id="count"></p>
<div class="cards" id="cards"></div>
</main>
<script type="application/json" id="cases-data">{data}</script>
<script type="application/json" id="filters-data">{json.dumps(filters)}</script>
<script>{JS}</script>"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cases', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--title', default='Case Sketch Review')
    ap.add_argument('--lede', default="Every sketch proposed for the study's worlds. Filter by the design grid, read a sketch, and mark it keep, revise or drop with a note. Decisions save as you make them.")
    a = ap.parse_args(); cases = load(Path(a.cases))
    Path(a.out).write_text(page(cases, a.title, a.lede), encoding='utf-8'); print(f'{a.out}: {len(cases)} cases')


if __name__ == '__main__':
    main()
