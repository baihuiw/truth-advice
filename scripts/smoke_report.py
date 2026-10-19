#!/usr/bin/env python3
"""Score a smoke slice: the simulator check on each smoke conversation (leaks, material inventions, repeats, cover breaks),
the guard's send-backs, whether the ladder questions were asked and coded, and the same cells in an earlier run for
comparison. Nothing is billed.

  python3 scripts/smoke_report.py --run runs/pilot3b_20261019 --before runs/pilot3_20261019 [--threshold 0.9]
"""
import argparse, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as RUN
from ta import metrics as MX


def flags(run_dir, stem):
    cp = run_dir / 'code' / f'{stem}.json'
    if not cp.exists():
        return None
    fid = RUN.read(cp).get('fidelity') or {}
    mat = [x for x in fid.get('invented') or [] if not isinstance(x, dict) or x.get('material', True)]
    return {'leak': bool(fid.get('leaked')), 'material': bool(mat), 'repeat': bool(fid.get('repeated')), 'cover': bool(fid.get('cover_breaks')),
            'broke': bool(fid.get('broke_character')), 'detail': (fid.get('reason') or '')[:200], 'invented': [x.get('detail', x) if isinstance(x, dict) else x for x in mat][:3],
            'leaked': fid.get('leaked')}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--before'); ap.add_argument('--threshold', type=float, default=0.9)
    a = ap.parse_args(); run_dir = Path(a.run); jobs = RUN.read(run_dir / 'smoke_jobs.json')
    worlds = {w['id']: w for w in RUN.read(run_dir / 'worlds.json')}
    stems = [f'{wid}__{c}__{p}__{t}__r{r}' for wid, c, p, t, r in jobs]
    now = {s: flags(run_dir, s) for s in stems}; done = {s: f for s, f in now.items() if f}
    before = {s: flags(Path(a.before), s) for s in stems} if a.before else {}
    def rates(fs):
        n = len(fs)
        return {'n': n, **{k: round(sum(f[k] for f in fs) / n, 3) for k in ('leak', 'material', 'repeat', 'cover', 'broke')},
                'clean': round(sum(not (f['leak'] or f['material']) for f in fs) / n, 3), 'clean_no_repeat': round(sum(not (f['leak'] or f['material'] or f['repeat']) for f in fs) / n, 3)} if n else {'n': 0}
    print(f'smoke conversations coded: {len(done)} of {len(stems)}')
    r_now = rates(list(done.values())); print('pilot 3b smoke:', r_now)
    if before:
        b = [before[s] for s in done if before.get(s)]; print('same cells in the earlier run:', rates(b))
    lad = [s for s in done if '_L' in s.split('__')[0]]; base = [s for s in done if s not in lad]
    print('  ladder cells:', rates([done[s] for s in lad])); print('  base cells:', rates([done[s] for s in base]))
    g = Counter(); opened = 0; n = 0
    for s in done:
        rec = RUN.read(run_dir / 'conv' / f'{s}.json'); n += 1
        for x in rec.get('guard') or []:
            g[x['kind']] += 1
        w = worlds[rec['world']]; first = rec['transcript'][0]['content']
        if rec['condition'] != 'relayed':
            p = w['neutral_friend'] if rec['asker'] == 'neutral' else w['parties'][rec['asker']]
            opened += first.strip() == (p.get('opening_message') or '').strip()
    print(f"guard send-backs: {dict(g)} over {n} conversations ({sum(g.values()) / max(1, n):.1f} per conversation); scripted opening used in {opened} of {sum(1 for s in done if '__relayed__' not in s)}")
    rows = [r for r in RUN.rows(run_dir, list(worlds.values())) if f"{r['world']}__{r['condition']}__{r['party']}__{r['target']}__r{r['rep']}" in done]
    import pooled_report as PR
    print('ladder code coverage in the smoke slice:', PR.coverage(list(worlds.values()), rows))
    bad = [(s, f) for s, f in done.items() if f['leak'] or f['material']]
    print(f'\nconversations still flagged ({len(bad)}):')
    for s, f in bad:
        print(f"  {s}: leak {f['leaked']} invented {f['invented']} | {f['detail'][:160]}")
    verdict = r_now.get('clean', 0) >= a.threshold
    print(f"\nclean rate {r_now.get('clean')} vs threshold {a.threshold}: {'PASS' if verdict else 'BELOW THRESHOLD'}")
    RUN.save(run_dir / 'smoke_report.json', {'now': r_now, 'before': rates([before[s] for s in done if before.get(s)]) if before else None, 'guard': dict(g), 'pass': verdict,
                                            'flagged': [{'conv': s, **f} for s, f in bad]})


if __name__ == '__main__':
    main()
