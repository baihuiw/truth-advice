#!/usr/bin/env python3
"""What a rerun of a finished run would cover after the worlds were repaired, and what it would cost at the run's own
measured rates. A conversation must be rerun when its world level changed for that person (opening, framing, reveal or
cover lines, questions, or what they know) or, optionally, when the simulator check flagged it; ladder levels are all
rerun when any ladder text changed, since a level comparison cannot mix versions. Follow-ups branch from own-view
conversations and scenes are built from them, so they follow. Nothing is billed.

  python3 scripts/rerun_plan.py --run runs/pilot3_20261019 [--guard 0.006]
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as RUN
from ta import world as W, gm as G


def person_state(w, name):
    p = W.party_of(w, name)
    return json.dumps({'opening': p.get('opening_message'), 'framing': p.get('framing'), 'reveal': p.get('reveal_policy'),
                       'questions': [q['text'] for q in p.get('truth_questions') or []], 'facts': W.fact_lines(w, name, None)}, sort_keys=True, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--guard', type=float, default=0.006, help='added simulator-guard cost per conversation')
    a = ap.parse_args(); run_dir = Path(a.run); cfg = RUN.read(run_dir / 'config.json')
    old = {w['id']: w for w in RUN.read(run_dir / 'worlds.json')}
    new = {}
    for wid in sorted({w.get('ladder_of', w['id']) for w in old.values()}):
        base = W.load(ROOT / 'worlds' / f'{wid}.json'); new[wid] = base
        for lv in (base.get('ladder') or {}).get('levels') or []:
            v = W.ladder_variant(base, lv['level']); new[v['id']] = v
    use = [json.loads(l) for l in (run_dir / 'usage.jsonl').read_text().splitlines() if l.strip()]
    cost = lambda f: sum(u.get('cost') or 0 for u in use if u.get('status') == 'ok' and f(u['label']))
    n_conv = len(list((run_dir / 'conv').glob('*.json')))
    c_conv = cost(lambda l: '/scene/' not in l and '/follow' not in l) / n_conv + a.guard
    n_fol = len(list((run_dir / 'followup').glob('*.json'))); c_fol = cost(lambda l: '/follow' in l) / max(1, n_fol)
    n_sc = len(list((run_dir / 'scene').glob('*.json'))); c_sc = cost(lambda l: '/scene/' in l) / max(1, n_sc)
    fid_cost = sum(u.get('cost') or 0 for u in use if u.get('status') == 'ok' and u['label'].endswith('/judge/fidelity')) / n_conv
    gen_cost = cost(lambda l: '/judge' not in l and '/scene/' not in l and '/follow' not in l) / n_conv

    changed_cell = {}
    for wid, w in old.items():
        names = list(w['parties']) + (['neutral'] if w.get('neutral_friend') else [])
        for n in names:
            changed_cell[(wid, n)] = person_state(w, n) != person_state(new[wid], n) if wid in new else True
    ladder_changed = any(changed_cell[(wid, n)] for wid, w in old.items() if w.get('ladder_roles') for n in (w['ladder_roles']['decider'], w['ladder_roles']['other']))
    convs = []
    for p in sorted((run_dir / 'conv').glob('*.json')):
        rec = RUN.read(p); fid = (RUN.read(RUN.code_path(run_dir, p)).get('fidelity') or {})
        mat = [x for x in fid.get('invented') or [] if not isinstance(x, dict) or x.get('material', True)]
        lad = bool(old[rec['world']].get('ladder_roles'))
        convs.append({'key': p.stem, 'world': rec['world'], 'party': rec['party'], 'asker': rec['asker'], 'target': rec['target'], 'cond': rec['condition'], 'ladder': lad,
                      'changed': changed_cell.get((rec['world'], rec['party'] if rec['condition'] == 'relayed' else rec['asker']), False),   # relayed: built from the subject's texts
                      'serious': bool(fid.get('leaked') or mat), 'repeat': bool(fid.get('repeated'))})
    fol = [RUN.read(p) for p in sorted((run_dir / 'followup').glob('*.json'))]
    scenes = [p.stem for p in sorted((run_dir / 'scene').glob('*.json'))]

    def plan(rerun_base):
        keys = {c['key'] for c in convs if (c['ladder'] and ladder_changed) or (not c['ladder'] and rerun_base(c))}
        own = {(c['world'], c['party'], c['target']) for c in convs if c['key'] in keys and c['cond'] == 'own_view' and not c['ladder']}
        f = sum(1 for x in fol if (x['world'], x['party'], x['target']) in own)
        s = sum(1 for sc in scenes if any((sc.split('__')[0], p_t.split('-')[0], p_t.split('-')[1]) in own for p_t in sc.split('__')[1].split('_')))
        return len(keys), f, s, len(keys) * c_conv + f * c_fol + s * c_sc, keys

    opts = [('Ladders + base conversations whose world text changed', lambda c: c['changed']),
            ('... + base conversations with a leak or invention', lambda c: c['changed'] or c['serious']),
            ('... + base conversations with only a repeat', lambda c: c['changed'] or c['serious'] or c['repeat']),
            ('Everything', lambda c: True)]
    print(f"rates from {run_dir.name}: conversation ${c_conv:.3f} (incl. ${a.guard:.3f} guard), follow-up ${c_fol:.3f}, scene ${c_sc:.3f}")
    print(f"ladder texts changed: {ladder_changed}; base people whose texts or facts changed: {sorted(k for k, v in changed_cell.items() if v and '_L' not in k[0])}")
    out = {}
    for name, f in opts:
        n, nf, ns, usd, keys = plan(f)
        b = sum(1 for c in convs if c['key'] in keys and not c['ladder']); l = n - b
        print(f"  {name:<58} conversations {n:>4} (base {b:>3}, ladder {l:>3}), follow-ups {nf:>3}, scenes {ns:>2}: ${usd:6.2f}")
        out[name] = {'conversations': n, 'base': b, 'ladder': l, 'followups': nf, 'scenes': ns, 'usd': round(usd, 2)}
    smoke = sum(1 for k, v in changed_cell.items() if v)
    print(f"smoke check (one own-view conversation per changed person and level, fidelity coding only): {smoke} conversations, about ${smoke * (gen_cost + a.guard + fid_cost):.2f}")
    RUN.save(run_dir / 'rerun_plan.json', {'rates': {'conversation': c_conv, 'followup': c_fol, 'scene': c_sc}, 'options': out, 'smoke_conversations': smoke,
                                           'changed_people': sorted('|'.join(k) for k, v in changed_cell.items() if v)})


if __name__ == '__main__':
    main()
