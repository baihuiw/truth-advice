#!/usr/bin/env python3
"""Summary of the effect coding (scripts/code_effect.py): on the teller side, the acts recommended and whether they leave the
other person misled, knowingly or not; on the seeker side, what the assistant tells the person in the dark about the
hidden truth, what it tells them to do, and where they end up. By assistant, by evidence level (ladder conversations),
and by whose secret it is. Each world is weighted once. Writes <run>/effect_summary.json. Nothing is billed.

  python3 scripts/effect_report.py --run runs/pilot3b_20261019
"""
import argparse, collections, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as RUN

T = ['sonnet55', 'gpt61', 'gemini38', 'deepseek4p', 'glm53']
ACTS = ['plain', 'tactful', 'partial', 'defer', 'withhold', 'deceive']
STANCES = ['states_truth', 'leans_truth', 'cant_tell', 'leans_false', 'states_false', 'none']
COURSES = ['ask_directly', 'gather_evidence', 'wait', 'drop_it', 'accept_denial', 'none']
GROUPS = {'c61': 'own misstatement', 'c69': 'own misstatement', 'c79': 'own misstatement', 'c74': "another's diagnosis", 'c17': 'family secret',
          'c65': "institution's error", 'c66': "institution's error", 'c71': 'own act, retaliation risk', 'c62': "another's file", 'c67': "another's file", 'c72': "another's file"}


def load(run_dir):
    worlds = {w['id']: w for w in RUN.read(run_dir / 'worlds.json')}; tell, seek = [], []
    for p in sorted((run_dir / 'effect').glob('*.json')):
        e = RUN.read(p); wid, cond, party, model, rep = p.stem.split('__'); w = worlds[wid]; base = w.get('ladder_of', wid)
        roles = w.get('ladder_roles') or {}; role = 'decider' if party == roles.get('decider') else 'other' if party == roles.get('other') else 'base'
        meta = {'conv': p.stem, 'world': base, 'level': w.get('ladder_level'), 'model': model, 'cond': cond, 'role': role, 'group': GROUPS.get(base, '?')}
        tell += [{**meta, **it} for it in e.get('tell_items') or [] if it.get('act') and it['act'] != 'none']
        seek += [{**meta, **it} for it in e.get('seek_items') or [] if it.get('stance')]
    return tell, seek


def share(items, key, values, by='world'):
    """Distribution of `key` over `values`, each world weighted once."""
    per = collections.defaultdict(collections.Counter)
    for it in items:
        per[it[by]][it.get(key)] += 1
    ws = [w for w in per if sum(per[w].values())]
    if not ws:
        return {v: None for v in values}, 0
    return {v: round(sum(per[w][v] / sum(per[w].values()) for w in ws) / len(ws), 3) for v in values}, len(items)


def rate(items, pred, by='world'):
    per = collections.defaultdict(list)
    for it in items:
        per[it[by]].append(float(pred(it)))
    ws = [sum(v) / len(v) for v in per.values()]
    return (round(sum(ws) / len(ws), 3), len(items)) if ws else (None, 0)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); a = ap.parse_args(); run_dir = Path(a.run)
    tell, seek = load(run_dir); out = {'n_tell': len(tell), 'n_seek': len(seek), 'conversations': len(list((run_dir / 'effect').glob('*.json')))}
    print(f"{out['conversations']} conversations coded: {len(tell)} telling items, {len(seek)} seeking items")
    misled = lambda it: it.get('misled') == 'yes'
    print('\n== TELLER SIDE: acts recommended (share, worlds weighted equally) and the share of each act that leaves the other person misled')
    out['tell'] = {}
    for t in T + ['all']:
        its = [it for it in tell if t == 'all' or it['model'] == t]; d, n = share(its, 'act', ACTS)
        per_act = {act: rate([it for it in its if it['act'] == act], misled)[0] for act in ACTS}
        know = rate([it for it in its if misled(it)], lambda it: it.get('acknowledged') == 'yes')
        out['tell'][t] = {'acts': d, 'n': n, 'misled_by_act': per_act, 'misled_overall': rate(its, misled)[0], 'acknowledged_when_misled': know[0], 'n_misled': know[1]}
        print(f"  {t:<11} n{n:<4} " + '  '.join(f"{act} {100 * (d[act] or 0):.0f}%" for act in ACTS) + f"  | misled {100 * (out['tell'][t]['misled_overall'] or 0):.0f}%; of those acknowledged {100 * (know[0] or 0):.0f}% (n{know[1]})")
    print('  misled share by act (all assistants):', {act: out['tell']['all']['misled_by_act'][act] for act in ACTS})
    print('\n== TELLER SIDE by whose secret it is (all assistants)')
    out['tell_by_group'] = {}
    for g in sorted(set(GROUPS.values())):
        its = [it for it in tell if it['group'] == g]; d, n = share(its, 'act', ACTS); m = rate(its, misled); k = rate([it for it in its if misled(it)], lambda it: it.get('acknowledged') == 'yes')
        out['tell_by_group'][g] = {'acts': d, 'n': n, 'misled': m[0], 'acknowledged_when_misled': k[0]}
        print(f"  {g:<28} n{n:<4} " + '  '.join(f"{act} {100 * (d[act] or 0):.0f}%" for act in ACTS) + f"  | misled {100 * (m[0] or 0):.0f}%, acknowledged {100 * (k[0] or 0):.0f}%")
    print('\n== TELLER SIDE by evidence level (ladder, person holding the secret; all assistants)')
    out['tell_by_level'] = {}
    for lv in range(4):
        its = [it for it in tell if it['role'] == 'decider' and it['level'] == lv]; d, n = share(its, 'act', ACTS); m = rate(its, misled); k = rate([it for it in its if misled(it)], lambda it: it.get('acknowledged') == 'yes')
        out['tell_by_level'][lv] = {'acts': d, 'n': n, 'misled': m[0], 'acknowledged_when_misled': k[0]}
        print(f"  level {lv} n{n:<4} " + '  '.join(f"{act} {100 * (d[act] or 0):.0f}%" for act in ACTS) + f"  | misled {100 * (m[0] or 0):.0f}%, acknowledged {100 * (k[0] or 0):.0f}%")
    print('\n== SEEKER SIDE: what the assistant tells the person in the dark (share), what it tells them to do, and where they end up')
    out['seek'] = {}
    for t in T + ['all']:
        its = [it for it in seek if t == 'all' or it['model'] == t]; st, n = share(its, 'stance', STANCES); co, _ = share(its, 'course', COURSES); oc, _ = share(its, 'outcome', ['truth', 'uncertain', 'false', 'na'])
        acc_false = rate([it for it in its if it.get('course') == 'accept_denial'], lambda it: it.get('outcome') == 'false')
        out['seek'][t] = {'stance': st, 'course': co, 'outcome': oc, 'n': n, 'accept_denial_false': acc_false[0], 'n_accept_denial': acc_false[1]}
        print(f"  {t:<11} n{n:<4} stance: " + ' '.join(f"{s} {100 * (st[s] or 0):.0f}%" for s in STANCES) + f"\n{'':<17} course: " + ' '.join(f"{c} {100 * (co[c] or 0):.0f}%" for c in COURSES)
              + f"\n{'':<17} outcome: truth {100 * (oc['truth'] or 0):.0f}%  uncertain {100 * (oc['uncertain'] or 0):.0f}%  false {100 * (oc['false'] or 0):.0f}%   | told to accept a denial {acc_false[1]} times, of which the denial would be false in {100 * (acc_false[0] or 0):.0f}%")
    print('\n== SEEKER SIDE by evidence level (ladder, the person who knows less; all assistants)')
    out['seek_by_level'] = {}
    for lv in range(4):
        its = [it for it in seek if it['role'] == 'other' and it['level'] == lv]; st, n = share(its, 'stance', STANCES); oc, _ = share(its, 'outcome', ['truth', 'uncertain', 'false', 'na']); co, _ = share(its, 'course', COURSES)
        out['seek_by_level'][lv] = {'stance': st, 'outcome': oc, 'course': co, 'n': n}
        print(f"  level {lv} n{n:<4} states/leans truth {100 * ((st['states_truth'] or 0) + (st['leans_truth'] or 0)):.0f}%  can't tell {100 * (st['cant_tell'] or 0):.0f}%  leans/states false {100 * ((st['leans_false'] or 0) + (st['states_false'] or 0)):.0f}%  | ends at truth {100 * (oc['truth'] or 0):.0f}% uncertain {100 * (oc['uncertain'] or 0):.0f}% false {100 * (oc['false'] or 0):.0f}%  | ask directly {100 * (co['ask_directly'] or 0):.0f}% accept denial {100 * (co['accept_denial'] or 0):.0f}%")
    RUN.save(run_dir / 'effect_summary.json', out)


if __name__ == '__main__':
    main()
