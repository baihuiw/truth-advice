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


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--ids', nargs='+', required=True)
    ap.add_argument('--attempts', type=int, default=2); ap.add_argument('--workers', type=int, default=4); a = ap.parse_args()
    run_dir = Path(a.run); cfg = R.read(run_dir / 'config.json'); R.authorized(run_dir); client = R.client_for(run_dir, cfg)
    choices = json.loads((ROOT / 'cases' / 'choices.json').read_text())['cases']; ladders = json.loads((ROOT / 'cases' / 'ladders.json').read_text())
    example = A.example_world(json.loads((ROOT / 'worlds' / 'jinhe.json').read_text()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        report = list(pool.map(lambda cid: build(client, cfg, cid, choices, ladders, example, a.attempts), a.ids))
    R.save(run_dir / 'build_report.json', report)
    for r in report:
        print(f"{r['id']}: {r['status']}" + (f", {r.get('repairs')} repairs, gates {'ok' if r.get('gates_ok') else r.get('gate')} {r.get('reason', '')[:120]}, realism {r.get('realism')}, "
                                              f"parties {r.get('parties')}, ladder levels {r.get('ladder_levels')}, claims {r.get('claims')}" if r['status'] == 'built' else f" {r.get('errors', r.get('error', ''))}"[:400]))
    print(f'spent ${client.spent:.2f}')


if __name__ == '__main__':
    main()
