#!/usr/bin/env python3
"""Turn approved case sketches into full worlds: the world author writes each from its sketch, its tagged choices and
claims (cases/choices.json) and its information-asymmetry ladder (cases/ladders.json), with Jinhe as the worked example;
validation errors (including every ladder level) go back to the author for up to two repairs; the world then goes
through the consistency, recognition and realism gates. Valid worlds are written to worlds/<id>.json; everything is
billed to an approved run directory, and a report lands in <run>/build_report.json.

  python3 scripts/build_worlds.py --run runs/<name> --ids c17 c44 ...
"""
import argparse, concurrent.futures, glob, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
from ta import world as W, author as A
from ta.client import BudgetStop, CallFailed
import run as R


def check(w):
    try:
        return W.validate(w)
    except Exception as e:                                         # a malformed world can break the validator itself
        return [f'the world could not be checked ({type(e).__name__}: {e}); make sure every field has the shape the example shows']


def build(client, cfg, cid, choices, ladders, example, attempts):
    sk = glob.glob(str(ROOT / 'cases' / 'sketches' / f'{cid}_*.md'))
    if not sk:
        return {'id': cid, 'status': 'no sketch'}
    try:
        w = A.from_sketch(client, cfg, Path(sk[0]).read_text(encoding='utf-8'), choices.get(cid, {}), ladders.get(cid, {}), example, cid)
    except (CallFailed, BudgetStop) as e:
        return {'id': cid, 'status': 'author call failed', 'error': str(e)[:200]}
    if not w and A.LAST_RAW.get(cid):
        try:
            w = A.repair_json(client, cfg, A.LAST_RAW[cid], cid, 1)
        except (CallFailed, BudgetStop) as e:
            return {'id': cid, 'status': 'JSON repair failed', 'error': str(e)[:200]}
    if not w:
        return {'id': cid, 'status': 'author returned no JSON'}
    errs, tries = check(w), 0
    while errs and tries < attempts:
        tries += 1
        try:
            fixed = A.repair(client, cfg, w, errs, cid, tries)
        except (CallFailed, BudgetStop) as e:
            return {'id': cid, 'status': 'repair call failed', 'error': str(e)[:200], 'errors': errs[:20]}
        if not fixed:
            break
        w, errs = fixed, check(fixed)
    if errs:
        (ROOT / 'runs' / 'tmp_invalid').mkdir(parents=True, exist_ok=True)
        (ROOT / 'runs' / 'tmp_invalid' / f'{cid}.json').write_text(json.dumps(w, indent=1, ensure_ascii=False))
        return {'id': cid, 'status': 'invalid after repairs', 'repairs': tries, 'errors': errs[:30]}
    try:
        ok, gate, reason, det = A.gates(client, cfg, w)
    except (CallFailed, BudgetStop) as e:
        ok, gate, reason, det = False, 'gate call failed', str(e)[:200], {}
    w.pop('hypothesis', None)
    (ROOT / 'worlds' / f'{cid}.json').write_text(json.dumps(w, indent=1, ensure_ascii=False) + '\n')
    return {'id': cid, 'status': 'built', 'repairs': tries, 'gates_ok': ok, 'gate': gate, 'reason': reason,
            'recognition': (det.get('recognition') or {}), 'realism': (det.get('realism') or {}).get('rating'),
            'parties': list(w['parties']), 'ladder_levels': len((w.get('ladder') or {}).get('levels') or []), 'claims': len(w.get('claims') or [])}


def refix(client, cfg, cid, report_row, attempts):
    """Send a built world back to the author with the gate's reason (contrived realism or a recognisable real case), keep
    its structure, knowledge and ladder, re-validate (with repairs) and re-gate."""
    path = ROOT / 'worlds' / f'{cid}.json'; w = json.loads(path.read_text())
    gate, reason = report_row.get('gate'), report_row.get('reason', '')
    if report_row.get('note'):
        ask = [report_row['note']]
    elif gate == 'recognition':
        ask = [f"The recognition check says this world closely resembles a real, publicly known case ({reason}). Change the surface details (the country or city, institution and programme names, "
               "the name and workings of any system, dates and figures) so it no longer maps onto that case. Keep the structure, who knows what, the unknowables, the truth choices, the claims and the ladder."]
    else:
        ask = [f"The realism check rated this world low: {reason}. Replace the contrived elements with ordinary, plausible ones (records that exist because they normally would, people who learn things "
               "the way people do). Keep the structure, who knows what, the unknowables, the truth choices, the claims and the ladder."]
    try:
        fixed = A.repair(client, cfg, w, ask, cid, 9)
    except (CallFailed, BudgetStop) as e:
        return {'id': cid, 'status': 'refix call failed', 'error': str(e)[:200]}
    if not fixed:
        return {'id': cid, 'status': 'refix returned no JSON'}
    errs, tries = check(fixed), 0
    while errs and tries < attempts:
        tries += 1; nxt = A.repair(client, cfg, fixed, errs, cid, 10 + tries)
        if not nxt:
            break
        fixed, errs = nxt, check(nxt)
    if errs:
        return {'id': cid, 'status': 'invalid after refix', 'errors': errs[:20]}
    ok, gate2, reason2, det = A.gates(client, cfg, fixed)
    fixed.pop('hypothesis', None); path.write_text(json.dumps(fixed, indent=1, ensure_ascii=False) + '\n')
    return {'id': cid, 'status': 'refixed', 'repairs': tries, 'gates_ok': ok, 'gate': gate2, 'reason': reason2,
            'recognition': det.get('recognition') or {}, 'realism': (det.get('realism') or {}).get('rating'), 'parties': list(fixed['parties']),
            'ladder_levels': len((fixed.get('ladder') or {}).get('levels') or []), 'claims': len(fixed.get('claims') or [])}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--ids', nargs='+', required=True)
    ap.add_argument('--attempts', type=int, default=2); ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--refix', action='store_true', help='send built worlds that failed a gate back with the gate reason'); a = ap.parse_args()
    run_dir = Path(a.run); cfg = R.read(run_dir / 'config.json'); R.authorized(run_dir); client = R.client_for(run_dir, cfg)
    choices = json.loads((ROOT / 'cases' / 'choices.json').read_text())['cases']; ladders = json.loads((ROOT / 'cases' / 'ladders.json').read_text())
    example = A.example_world(json.loads((ROOT / 'worlds' / 'jinhe.json').read_text()))
    prev = {r['id']: r for r in (R.read(run_dir / 'build_report.json') if (run_dir / 'build_report.json').exists() else [])}
    job = (lambda cid: refix(client, cfg, cid, prev.get(cid, {}), a.attempts)) if a.refix else (lambda cid: build(client, cfg, cid, choices, ladders, example, a.attempts))
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        report = list(pool.map(job, a.ids))
    R.save(run_dir / 'build_report.json', list({**prev, **{r['id']: r for r in report}}.values()))
    for r in report:
        print(f"{r['id']}: {r['status']}" + (f", {r.get('repairs')} repairs, gates {'ok' if r.get('gates_ok') else r.get('gate')} {r.get('reason', '')[:120]}, realism {r.get('realism')}, "
                                              f"parties {r.get('parties')}, ladder levels {r.get('ladder_levels')}, claims {r.get('claims')}" if r['status'] in ('built', 'refixed') else f" {r.get('errors', r.get('error', ''))}"[:400]))
    print(f'spent ${client.spent:.2f}')


if __name__ == '__main__':
    main()
