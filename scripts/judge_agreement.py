#!/usr/bin/env python3
"""Does a cheaper judge agree with the main one? Compares code/ (main judge) with code_alt/ (judge_alt) on the reply
coding: the strongest strength each conversation gives each unknowable question, the side blame share, candour items
raised, and the advice recommendations.

  python3 scripts/judge_agreement.py --run runs/<name>
"""
import argparse, json, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ta import judge as J

ORDER = {s: i for i, s in enumerate(('open', 'favoured', 'asserted'))}


def strongest(say):
    out = {}
    for u in say.get('unknowable', []):
        out[u['id']] = max(out.get(u['id'], -1), ORDER[u['strength']])
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--alt-dir', default='code_alt'); a = ap.parse_args(); run_dir = Path(a.run)
    worlds = {w['id']: w for w in json.loads((run_dir / 'worlds.json').read_text())}
    unk_same, unk_n, blame_pairs, cand_same, cand_n, adv_same, adv_n, n = 0, 0, [], 0, 0, 0, 0, 0
    for p in sorted((run_dir / a.alt_dir).glob('*.json')):
        main_p = run_dir / 'code' / p.name
        if not main_p.exists():
            continue
        m = (json.loads(main_p.read_text()) or {}).get('say') or {}; x = (json.loads(p.read_text()) or {}).get('say') or {}
        world, cond, party = p.stem.split('__')[:3]; w = worlds[world]; n += 1
        sm, sx = strongest(m), strongest(x)
        for uid in set(sm) | set(sx):
            unk_n += 1; unk_same += sm.get(uid, -1) == sx.get(uid, -1)
        els = J.side(w, party)
        if els and m.get('blame') and x.get('blame'):
            blame_pairs.append((sum(m['blame'].get(e, 0) for e in els), sum(x['blame'].get(e, 0) for e in els)))
        cm = {c['id']: c['raised'] for c in m.get('candour', [])}; cx = {c['id']: c['raised'] for c in x.get('candour', [])}
        for cid in set(cm) & set(cx):
            cand_n += 1; cand_same += cm[cid] == cx[cid]
        am = sorted(r['recommendation'] for r in m.get('advice', [])); ax = sorted(r['recommendation'] for r in x.get('advice', []))
        if am or ax:
            adv_n += 1; adv_same += am == ax
    r = None
    if len(blame_pairs) > 2:
        xs, ys = zip(*blame_pairs); r = round(statistics.correlation(xs, ys), 3)
    print(f"conversations compared: {n}")
    print(f"unknowable, strongest strength per question: same {unk_same}/{unk_n}" + (f" ({unk_same / unk_n:.0%})" if unk_n else ''))
    print(f"side blame share: correlation {r} over {len(blame_pairs)}; mean abs difference "
          f"{round(statistics.mean(abs(a_ - b_) for a_, b_ in blame_pairs), 3) if blame_pairs else None}")
    print(f"candour items: same {cand_same}/{cand_n}" + (f" ({cand_same / cand_n:.0%})" if cand_n else ''))
    print(f"advice recommendations identical: {adv_same}/{adv_n}" + (f" ({adv_same / adv_n:.0%})" if adv_n else ''))


if __name__ == '__main__':
    main()
