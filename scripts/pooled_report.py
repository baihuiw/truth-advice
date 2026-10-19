#!/usr/bin/env python3
"""Pooled numbers across a run's worlds: base conditions by target and condition, loyalty (own view minus relayed),
framework match, reasons, follow-ups, eval awareness, named sources, simulator fidelity, scenes, and the
information-asymmetry ladders pooled by target and level, with world-bootstrap intervals for the slopes (level 3 minus
level 0). Each world counts once in a ladder mean, so a world with more advice items does not weigh more. Writes
<run>/pooled.json and prints a summary.

  python3 scripts/pooled_report.py --run runs/pilot3_20261019
"""
import argparse, json, random, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as RUN
from ta import metrics as MX, judge as J

MEASURES = ('tell', 'keep_quiet', 'lie_allowed', 'silence_dishonest', 'suspects', 'confront_now')
CONV_KEYS = ('overclaim', 'favoured', 'serves_interest', 'matches_view', 'candour', 'perspective', 'thought_not_said', 'overclaim_think')


def boot(values_by_world, reps=2000, seed=7):
    """Mean over worlds and a 95% interval from resampling worlds."""
    xs = [v for v in values_by_world if v is not None]
    if not xs:
        return None
    rng = random.Random(seed); m = sum(xs) / len(xs)
    if len(xs) < 3:
        return {'mean': round(m, 3), 'lo': None, 'hi': None, 'worlds': len(xs)}
    bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(reps))
    return {'mean': round(m, 3), 'lo': round(bs[int(0.025 * reps)], 3), 'hi': round(bs[int(0.975 * reps) - 1], 3), 'worlds': len(xs)}


def ladders(worlds, rows):
    per = MX.ladder(worlds, rows)                                         # {'<base>|<target>': {measure: {'by_level': {lv: v}, 'slope'}}}
    targets = sorted({k.split('|')[1] for k in per}); bases = sorted({k.split('|')[0] for k in per})
    out = {}
    for t in targets + ['all']:
        row = {}
        for m in MEASURES:
            lv_vals = defaultdict(list); slopes = []
            for b in bases:
                if t == 'all':                                            # all targets: average the targets within a world first
                    cells = [per[f'{b}|{x}'][m]['by_level'] for x in targets if m in per.get(f'{b}|{x}', {})]
                    if not cells:
                        continue
                    bl = {lv: sum(c[lv] for c in cells if lv in c) / sum(1 for c in cells if lv in c) for lv in range(4) if any(lv in c for c in cells)}
                else:
                    if m not in per.get(f'{b}|{t}', {}):
                        continue
                    bl = per[f'{b}|{t}'][m]['by_level']
                for lv, v in bl.items():
                    lv_vals[lv].append(v)
                if 0 in bl and 3 in bl:
                    slopes.append(bl[3] - bl[0])
            if lv_vals:
                row[m] = {'by_level': {lv: boot(v) for lv, v in sorted(lv_vals.items())}, 'slope': boot(slopes)}
        out[t] = row
    per_world = {k: {m: {'by_level': v['by_level'], 'slope': v['slope']} for m, v in row.items()} for k, row in per.items()}
    return out, per_world


def coverage(worlds, rows):
    """How often the codes the ladder needs are present: an advice item on the decider's disclosure choice, a verdict on keeping
    quiet, and the other party's suspicion and confront codes."""
    by_id = {w['id']: w for w in worlds}; c = defaultdict(lambda: [0, 0])
    for r in rows:
        w = by_id.get(r['world'])
        if not w or not w.get('ladder_roles') or not r.get('m'):
            continue
        roles = w['ladder_roles']
        if r['party'] == roles['decider']:
            dq = [q for q in w['parties'][roles['decider']]['truth_questions'] if q.get('choice')]
            ids = [q['choice']['id'] for q in dq]
            got = {a.get('choice') for a in r['m'].get('advice_items') or [] if a.get('recommendation') != 'none'}
            c['disclosure_advice'][0] += bool(ids and ids[0] in got); c['disclosure_advice'][1] += 1
            if len(ids) > 1:
                c['deny_advice'][0] += ids[1] in got; c['deny_advice'][1] += 1
            c['silence_verdict'][0] += bool(r['m'].get('honesty_judgment')); c['silence_verdict'][1] += 1
        elif r['party'] == roles['other']:
            c['suspicion'][0] += bool(r['m'].get('suspicion')); c['suspicion'][1] += 1
            c['confront'][0] += bool(r['m'].get('confront')); c['confront'][1] += 1
    return {k: {'share': round(a / b, 3) if b else None, 'n': b} for k, (a, b) in c.items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); a = ap.parse_args()
    run_dir = Path(a.run); worlds = RUN.read(run_dir / 'worlds.json'); rows = RUN.rows(run_dir, worlds)
    by_id = {w['id']: w for w in worlds}
    base_worlds = [w for w in worlds if not w.get('ladder_roles')]; base_ids = {w['id'] for w in base_worlds}
    base_rows = [r for r in rows if r['world'] in base_ids]
    out = {'n': {'conversations': len(rows), 'coded': sum(1 for r in rows if r['m']), 'base': len(base_rows), 'ladder': len(rows) - len(base_rows)}}

    agg = defaultdict(list)                                               # base conditions, pooled across worlds (conversation-weighted)
    for r in base_rows:
        if r['m']:
            agg[(r['target'], r['condition'])].append(r['m'])
    out['conditions'] = {f'{t}|{c}': {**{k: MX.mean([m.get(k) for m in ms]) for k in CONV_KEYS}, 'n': len(ms),
                                      'sim_ok': MX.mean([float(m['sim_ok']) for m in ms]),
                                      'advice': {x: sum(x in m['advice'] for m in ms) for x in J.ADVICE},
                                      'eval_aware_reasoning': round(sum(1 for m in ms if m.get('eval_aware')) / len(ms), 3)}
                         for (t, c), ms in sorted(agg.items())}

    pairs = defaultdict(list)                                             # loyalty: own view minus relayed, same facts
    for w in base_worlds:
        for x in MX.loyalty(w, [r for r in base_rows if r['world'] == w['id']]):
            pairs[x['target']].append({**x, 'world': w['id']})
    out['loyalty'] = {t: {**{k: MX.mean([x[k] for x in xs]) for k in ('serves_interest', 'matches_view', 'overclaim', 'side_favour', 'candour')},
                          'pairs': len(xs), 'worlds': len({x['world'] for x in xs})} for t, xs in sorted(pairs.items())}

    hits = defaultdict(lambda: defaultdict(lambda: [0.0, 0])); kinds = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for w in base_worlds:
        fm = MX.framework_match(w, [r for r in base_rows if r['world'] == w['id']])
        for t, v in fm.items():
            for fw, (m, n) in v['match'].items():
                hits[t][fw][0] += m * n; hits[t][fw][1] += n
            for ty, d in v['by_choice_type'].items():
                for rec, k in d.items():
                    kinds[t][ty][rec] += k
    out['frameworks'] = {t: {'match': {fw: (round(s / n, 3), n) for fw, (s, n) in fws.items() if n}, 'by_choice_type': {k: dict(v) for k, v in kinds[t].items()}}
                         for t, fws in sorted(hits.items())}
    out['reasons'] = MX.reasons(base_rows)

    fr = []
    for fp in sorted((run_dir / 'followup').glob('*.json')) if (run_dir / 'followup').exists() else []:
        f = RUN.read(fp); cp = run_dir / 'followup_code' / fp.name
        fr.append({**f, 'code': RUN.read(cp) if cp.exists() else None})
    out['followups'] = {'n': len(fr), 'coded': sum(1 for f in fr if f.get('code')), 'by_target': MX.follow(fr)}

    called = defaultdict(lambda: [0, 0]); named = defaultdict(lambda: [0, 0]); named_t = defaultdict(lambda: [0, 0]); sim = defaultdict(lambda: [0, 0])
    for r in rows:
        w = by_id[r['world']]; base = w.get('ladder_of', w['id']); cond = 'ladder' if w.get('ladder_roles') else r['condition']
        real = ((r.get('post') or {}).get('real') or '').strip(); src = ((r.get('post') or {}).get('source') or '').strip()
        if real:
            called[(r['target'], cond)][0] += RUN.called_test(real); called[(r['target'], cond)][1] += 1
        if src:
            hit = not re.match(r'^\W*no\b', src, re.I)
            named[base][0] += hit; named[base][1] += 1; named_t[r['target']][0] += hit; named_t[r['target']][1] += 1
        if r['m']:
            sim[base][0] += r['m']['sim_ok']; sim[base][1] += 1
    share = lambda d: {('|'.join(k) if isinstance(k, tuple) else k): {'share': round(a / b, 3), 'n': b} for k, (a, b) in sorted(d.items()) if b}
    out['called_a_test'] = share(called); out['named_a_source'] = {'by_world': share(named), 'by_target': share(named_t)}; out['sim_ok'] = share(sim)

    sc = [RUN.read(p) for p in sorted((run_dir / 'scene_code').glob('*.json'))] if (run_dir / 'scene_code').exists() else []
    out['scenes'] = {'n': len(sc), 'compatible_rate': MX.mean([float(bool(s.get('compatible'))) for s in sc if s])}

    out['ladders'], out['ladders_per_world'] = ladders(worlds, rows)
    out['ladder_coverage'] = coverage(worlds, rows)
    use = [json.loads(l) for l in (run_dir / 'usage.jsonl').read_text().splitlines() if l.strip()]
    out['cost_usd'] = round(sum(u.get('cost') or 0 for u in use if u.get('status') == 'ok'), 2)
    RUN.save(run_dir / 'pooled.json', out)

    print(f"conversations {out['n']}; follow-ups {out['followups']['n']} ({out['followups']['coded']} coded); scenes {out['scenes']['n']}; cost ${out['cost_usd']}")
    print('ladder code coverage:', out['ladder_coverage'])
    print('== ladders pooled over worlds (level 0/1/2/3; slope = level 3 minus level 0, 95% world-bootstrap interval)')
    for t, row in out['ladders'].items():
        print(f'  {t}')
        for m, v in row.items():
            lv = '/'.join(f"{v['by_level'][k]['mean']:.2f}" if v['by_level'].get(k) else '-' for k in range(4))
            s = v['slope']
            print(f"    {m:<18} {lv}   slope {s['mean']:+.2f} [{s['lo']}, {s['hi']}] ({s['worlds']} worlds)" if s else f"    {m:<18} {lv}")
    print('== base conditions pooled (overclaim / serves_interest / matches_view / candour; advice counts)')
    for k, v in out['conditions'].items():
        print(f"  {k:<26} n{v['n']:<4} overclaim {v['overclaim']}  interest {v['serves_interest']}  view {v['matches_view']}  candour {v['candour']}  sim_ok {v['sim_ok']}  advice {v['advice']}")
    print('== loyalty (own view minus relayed)')
    for t, v in out['loyalty'].items():
        print(f"  {t:<12} {v}")
    print('== frameworks'); [print(f"  {t:<12} {v['match']}") for t, v in out['frameworks'].items()]
    print('== follow-ups'); [print(f"  {t:<12} went_along {v['went_along']} gave_way {v['gave_way']} fits_truth {v['fits_truth']} fits_evidence {v['fits_evidence']}") for t, v in out['followups']['by_target'].items()]
    print('== called a test:', {k: v['share'] for k, v in out['called_a_test'].items()})
    print('== named a source by world:', {k: v['share'] for k, v in out['named_a_source']['by_world'].items()})
    print('== simulator clean by world:', {k: v['share'] for k, v in out['sim_ok'].items()})


if __name__ == '__main__':
    main()
