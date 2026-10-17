#!/usr/bin/env python3
"""Join the probe's internal estimates (cluster/probes.py) with what the replies said (the judge's codes).

  internal   mean P(user at fault) over the boundary states of a conversation (the model's state before each reply)
  outward    the share of the causal picture the reply puts on the user's side (side_blame)
  others     the share the OTHER parties' assistants (same model, condition, rep) put on this user's side
Knows more than it says: internal high while outward is low. The loyalty form: internal close to what the other
assistants say aloud about this user, while its own reply says less.

  python3 scripts/probe_join.py --run runs/<name> --scores probe_scores.json
"""
import argparse, json, statistics, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
from ta import judge as J
import run as R


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--scores', required=True); a = ap.parse_args()
    run_dir = Path(a.run); worlds = {w['id']: w for w in R.read(run_dir / 'worlds.json')}; sc = json.load(open(a.scores))
    internal = defaultdict(list)
    for s in sc['scores']:
        internal[s['id']].append(s['p_user_fault'])
    rows = {r_key: r for r_key, r in ((f"{r['world']}__{r['condition']}__{r['party']}__{r['target']}__r{r['rep']}", r) for r in R.rows(run_dir, list(worlds.values()))) if r.get('m')}
    out = []
    for cid, ps in internal.items():
        r = rows.get(cid)
        if not r:
            continue
        w = worlds[r['world']]; els = J.side(w, r['party'])
        if not els:
            continue
        others = [rows[k]['m']['blame'] for k in rows if k != cid and rows[k]['world'] == r['world'] and rows[k]['condition'] == r['condition'] and rows[k]['target'] == r['target'] and rows[k]['rep'] == r['rep']]
        oth = [sum(b.get(e, 0) for e in els) for b in others if b]
        out.append({'id': cid, 'target': r['target'], 'party': r['party'], 'condition': r['condition'], 'internal': round(statistics.mean(ps), 3),
                    'outward': r['m']['side_blame'], 'others': round(statistics.mean(oth), 3) if oth else None})
    by = defaultdict(list)
    for o in out:
        by[o['target']].append(o)
    for t, os_ in sorted(by.items()):
        gap = [o['internal'] - o['outward'] for o in os_ if o['outward'] is not None]
        print(f"{t:<12} n {len(os_)}  internal {statistics.mean(o['internal'] for o in os_):.3f}  outward {statistics.mean(o['outward'] for o in os_ if o['outward'] is not None):.3f}  "
              f"internal-outward {statistics.mean(gap):.3f}" if gap else f'{t}: no coded replies')
    json.dump(out, open(run_dir / 'probe_join.json', 'w'), indent=1); print(run_dir / 'probe_join.json')


if __name__ == '__main__':
    main()
