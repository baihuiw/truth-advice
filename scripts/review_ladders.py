#!/usr/bin/env python3
"""One review page for the information-asymmetry ladders: for each case, what the other party has at each level, how the
decider knows it, whether the other party could find out later, and both sides' questions. Decisions (keep, revise,
drop) and notes save to the page's database, collection "ladder_reviews".

  python3 scripts/review_ladders.py --ladders cases/ladders_worlds.json ../truth-advice-cases/cases/ladders.json --out <file.html>
"""
import argparse, html, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import review_cases as RC

E = html.escape
WORLD_TITLES = {'jinhe': 'Jinhe: the missing 60,000 yuan', 'marlow': "Marlow: the solicitor's letter"}


def cfo(v):
    if isinstance(v, dict):
        return f"{v.get('answer', '')}: {v.get('device', '')}".strip(': ')
    if isinstance(v, bool):
        return 'yes' if v else 'no'
    return str(v or '')


def card_html(cid, L):
    D, O = str(L['decider']).title(), str(L['other']).title()
    rows = ''.join(f"<tr><td><b>{E(str(l['level']))}</b> {E(l.get('label', ''))}</td><td>{E(l.get('o_has', ''))}</td><td>{E(l.get('d_knows', ''))}</td><td>{E(cfo(l.get('could_find_out')))}</td></tr>"
                   for l in L['levels'])
    qs = ''
    for l in L['levels']:
        dq, oq = l.get('d_questions') or {}, l.get('o_questions') or {}
        qs += (f"<h3>Level {E(str(l['level']))}: {E(l.get('label', ''))}</h3>"
               f"<p class='keeps'><b>What {E(D)} can still keep back:</b> {E(l.get('d_keeps_back', ''))} <code>{E(l.get('d_choice_type', ''))}</code></p>"
               f"<div class='qgrid'><div><p class='qh'>{E(D)} asks</p><ul>" + ''.join(f"<li>{E(dq.get(k, ''))}</li>" for k in ('disclosure', 'deny', 'judgment') if dq.get(k)) + "</ul></div>"
               f"<div><p class='qh'>{E(O)} asks</p><ul>" + ''.join(f"<li>{E(oq.get(k, ''))}</li>" for k in ('verdict', 'right_to_ask', 'believe_denial') if oq.get(k)) + "</ul></div></div>"
               + (f"<p class='delta'><b>Facts changed:</b> {E('; '.join(l.get('fact_delta') or []) or 'none (as written)')}</p>"))
    notes = ''.join(f"<p><b>{E(k)}:</b> {E(str(v))}</p>" for k, v in (('The key fact', L.get('key_fact')), ('What stays unknowable', L.get('stays_open')),
                                                                        ('Could they find out later', L.get('could_find_out_note')), ('Literal-truth trap', L.get('literal_truth_trap')),
                                                                        ('Slopes it can tell apart', L.get('slopes')), ('Twin', L.get('twin')), ('Caveat', L.get('caveat'))) if v)
    return (f"{notes}<div class='tw'><table><thead><tr><th>Level</th><th>What {E(O)} has</th><th>How {E(D)} knows</th><th>Could {E(O)} find out later</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>{qs}")


def load(paths):
    out = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding='utf-8'))
        for cid, L in data.items():
            if not isinstance(L, dict) or 'levels' not in L:
                continue
            D, O = str(L['decider']).title(), str(L['other']).title()
            role = lambda r: f" ({L[r]})" if L.get(r) else ''
            out.append({'id': cid, 'title': L.get('title') or WORLD_TITLES.get(cid, cid),
                        'meta': f"{D}{role('decider_role')} holds something; {O}{role('other_role')} knows less. Choice: {L.get('choice_id', '')}.",
                        'html': card_html(cid, L),
                        'tags': {'other_type': L.get('other_type', 'person'), 'status_relation': L.get('status', 'equal'),
                                 'base_level': str(L.get('base_level', '')), 'source': 'built world' if cid in WORLD_TITLES else 'sketch'},
                        'recommendation': ''})
    return sorted(out, key=lambda c: (c['tags']['source'] != 'built world', c['id']))


CSS_EXTRA = """
.sketch h3{font:600 .95rem var(--body);margin:16px 0 4px}
.qgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr));gap:10px}
.qgrid ul{margin:2px 0 6px;padding-left:1.1rem}.qh{font:600 .76rem var(--mono);text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:6px 0 2px}
.keeps,.delta{font-size:.86rem;margin:4px 0}.delta{color:var(--muted)}
.tw{overflow-x:auto}.tw table{border-collapse:collapse;font-size:.84rem;min-width:560px}.tw th,.tw td{border:1px solid var(--line);padding:5px 7px;text-align:left;vertical-align:top}
"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--ladders', nargs='+', required=True); ap.add_argument('--out', required=True); ap.add_argument('--start')
    a = ap.parse_args(); cases = load(a.ladders)
    RC.FILTERS = [('source', 'Source'), ('other_type', 'Other party is'), ('status_relation', "Other party's status"), ('base_level', 'Sketch as written sits at level')]
    lede = ("The information-asymmetry ladders, the study's main axis. In each case one person holds something the other lacks; the four levels change only how much "
            "the other party has, from knowing the key fact (level 0) to having no lead (level 3). Open a case to see each level and both sides' questions, then mark it "
            "keep, revise or drop with a note. Your decisions save as you make them.")
    groups = json.loads(a.start) if a.start else None
    page = RC.page(cases, 'Ladder Review', lede, groups).replace("collection('reviews')", "collection('ladder_reviews')")
    page = page.replace('</style>', CSS_EXTRA + '</style>', 1).replace("'Notes for this case (what to change, why to drop it)'", "'Notes for this ladder (a level that feels contrived, a question to change)'")
    Path(a.out).write_text(page, encoding='utf-8'); print(f'{a.out}: {len(cases)} ladders')


if __name__ == '__main__':
    main()
