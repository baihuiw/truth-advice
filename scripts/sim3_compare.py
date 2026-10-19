#!/usr/bin/env python3
"""Compare the arms of the simulator test on the same cells: the coded advice on the disclosure and denial questions, the
ladder codes (keeping quiet dishonest, suspicion, confront), candour and overclaiming; how often each arm's codes agree
with the live arm's; the simulator check per arm; conversation length; cost. Nothing is billed.

  python3 scripts/sim3_compare.py --arms fixed=runs/sim3_fixed_20261019 bounded=runs/sim3_bounded_20261019 live=runs/sim3_live_20261019
"""
import argparse, json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as RUN, smoke_report as SR
from ta import judge as J, metrics as MX


def cell_codes(run_dir, worlds, stem):
    cp = run_dir / 'code' / f'{stem}.json'; conv = run_dir / 'conv' / f'{stem}.json'
    if not cp.exists():
        return None
    rec = RUN.read(conv); c = RUN.read(cp); say = J.norm_code(c['say']); w = worlds[rec['world']]
    m = MX.conv(w, rec, c) or {}
    dq = [q for q in w['parties'][rec['party']]['truth_questions'] if q.get('choice')]
    ids = [q['choice']['id'] for q in dq]
    adv = {a['choice']: a['recommendation'] for a in say.get('advice') or [] if a.get('choice') and a['recommendation'] != 'none'}
    first = lambda xs, k: (xs[0].get(k) if xs else None)
    return {'disclosure': adv.get(ids[0]) if ids else None, 'deny': adv.get(ids[1]) if len(ids) > 1 else None,
            'silence': first(say.get('honesty_judgment') or [], 'verdict'), 'suspicion': first(say.get('suspicion') or [], 'verdict'),
            'confront': first(say.get('confront') or [], 'recommendation'), 'candour': m.get('candour'), 'overclaim': m.get('overclaim'),
            'untruth': any(a['recommendation'] == 'untruth' for a in say.get('advice') or []),
            'user_turns': rec.get('user_turns'), 'assistant_questions': sum(x['content'].count('?') for x in rec['transcript'] if x['role'] == 'assistant'),
            'flags': SR.flags(run_dir, stem)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--arms', nargs='+', required=True); a = ap.parse_args()
    arms = dict(x.split('=', 1) for x in a.arms); runs = {k: Path(v) for k, v in arms.items()}
    jobs = RUN.read(next(iter(runs.values())) / 'jobs.json'); stems = [f'{w}__{c}__{p}__{t}__r{r}' for w, c, p, t, r in jobs]
    worlds = {k: {w['id']: w for w in RUN.read(r / 'worlds.json')} for k, r in runs.items()}
    codes = {k: {s: cell_codes(r, worlds[k], s) for s in stems} for k, r in runs.items()}
    ref = 'live' if 'live' in codes else list(codes)[0]
    print('cells coded per arm:', {k: sum(v is not None for v in d.values()) for k, d in codes.items()})
    keys = ('disclosure', 'deny', 'silence', 'suspicion', 'confront')
    print(f'\nagreement with the {ref} arm, cell by cell (same code), and the distribution of each code:')
    for key in keys:
        line = f'  {key:<11}'
        for k, d in codes.items():
            vals = [v[key] for v in d.values() if v and v[key] is not None]
            dist = ', '.join(f'{x} {n}' for x, n in Counter(vals).most_common())
            if k != ref:
                pairs = [(d[s][key], codes[ref][s][key]) for s in stems if d.get(s) and codes[ref].get(s) and d[s][key] is not None and codes[ref][s][key] is not None]
                agree = sum(x == y for x, y in pairs) / len(pairs) if pairs else None
                line += f' | {k}: agree {agree:.0%} (n{len(pairs)}) [{dist}]' if agree is not None else f' | {k}: [{dist}]'
            else:
                line += f' | {k}: [{dist}]'
        print(line)
    print('\nmeans per arm:')
    for k, d in codes.items():
        vs = [v for v in d.values() if v]
        fl = [v['flags'] for v in vs if v['flags']]
        clean = sum(not (f['leak'] or f['material']) for f in fl) / len(fl) if fl else None
        print(f"  {k:<8} candour {MX.mean([v['candour'] for v in vs]):.2f}  overclaim {MX.mean([v['overclaim'] for v in vs]):.2f}  lies advised {sum(v['untruth'] for v in vs)}  "
              f"user turns {MX.mean([v['user_turns'] for v in vs]):.1f}  assistant question marks {MX.mean([v['assistant_questions'] for v in vs]):.1f}  simulator clean {clean:.0%}" if clean is not None else f'  {k}: no codes')
    print('\ncost per arm (conversations + coding):')
    for k, r in runs.items():
        use = [json.loads(l) for l in (r / 'usage.jsonl').read_text().splitlines() if l.strip()] if (r / 'usage.jsonl').exists() else []
        n = sum(v is not None for v in codes[k].values())
        print(f"  {k:<8} ${sum(u.get('cost') or 0 for u in use if u.get('status') == 'ok'):.2f} for {n} conversations")
    RUN.save(runs[ref].parent / 'sim3_compare.json', {k: {s: v for s, v in d.items()} for k, d in codes.items()})


if __name__ == '__main__':
    main()
