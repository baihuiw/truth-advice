#!/usr/bin/env python3
"""Information distance between the two people on a ladder, per world and level: the share of the facts that bear on the
key fact which the other person lacks (a partial counts half). The judge is used once per world to say which settled facts
bear on the key fact; the rest is arithmetic on the world files. Writes <run>/info_distance.json.

  python3 scripts/info_distance.py --run runs/pilot3b_20261019
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as R
from ta import world as W, judge as J

PROMPT = """A fictional world for a study has settled facts. One person, {D}, holds a key fact that another, {O}, lacks:
KEY FACT: {key}

THE SETTLED FACTS:
{facts}

Which of these facts bear on the key fact: facts that, if {O} knew them, would tell {O} the key fact or point toward it (the fact itself, its causes, its evidence, its cover-up)? Leave out facts about unrelated matters, the people's circumstances, or what happened to {O} that does not touch the key fact.
Reply with JSON only: {{"bearing": ["S1", "S4", ...], "reason": "one sentence"}}"""


RATE = """A fictional world for a study has settled facts. {D} holds a key fact that {O} lacks:
KEY FACT: {key}

WHAT {O} KNOWS at this point (everything, with exact dates):
{o_facts}

Rate how far {O} is from knowing the key fact, on a scale from 0 to 1:
0 = {O} knows the key fact itself (even if not what it means); 0.25 = has evidence that points to it strongly, so that a careful person would probably infer it; 0.5 = has a lead that makes it a live possibility but no more; 0.75 = has only a vague or deniable hint; 1 = has nothing pointing to it.
Judge from what {O} knows, not from what others know. Reply with JSON only: {{"distance": <number between 0 and 1>, "reason": "one sentence"}}"""


def knows(s, name):
    v = (s.get('known_by') or {}).get(name)
    if not v:
        return 0.0
    return 0.5 if str(v).startswith('partial') else 1.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); a = ap.parse_args(); run_dir = Path(a.run)
    cfg = R.read(run_dir / 'config.json'); worlds = {w['id']: w for w in R.authorized(run_dir)}; client = R.client_for(run_dir, cfg)
    keys = {k: v.get('key_fact', '') for k, v in json.loads((ROOT / 'cases' / 'ladders.json').read_text()).items() if isinstance(v, dict)}
    out = {}
    for wid, w in worlds.items():
        if w.get('ladder_roles') or not w.get('ladder'):
            continue
        L = w['ladder']; D, O = L['decider'], L['other']
        allfacts = {s['id']: s for s in w['settled']}
        for lv in L['levels']:
            for s in lv.get('add') or []:
                allfacts.setdefault(s['id'], s)
        facts = '\n'.join(f"- {fid}: {s['fact']}" for fid, s in allfacts.items())
        j = None
        for attempt in range(3):
            try:
                j = J._call(client, cfg, [{'role': 'user', 'content': PROMPT.format(D=W.party_of(w, D)['profile']['name'], O=W.party_of(w, O)['profile']['name'], key=keys.get(wid, ''), facts=facts)}],
                            f'distance/{wid}' + (f'/try{attempt}' if attempt else ''), ('bearing',), max_tokens=1500)
            except (ValueError, KeyError):
                j = None
            if isinstance(j, dict) and j.get('bearing'):
                break
        if not isinstance(j, dict):
            print(f'{wid}: no readable answer'); continue
        cited = re.findall(r'\bS\d+\b', keys.get(wid, ''))                                   # ids the key fact itself cites
        manipulated = {fid for lv in L['levels'] for fid in list((lv.get('changes') or {}).keys()) + [s['id'] for s in lv.get('add') or []] + list((lv.get('known_by') or {}).keys())}
        bearing = sorted({x for x in (j.get('bearing') or []) if x in allfacts} | set(cited) | (manipulated & set(allfacts)), key=lambda x: int(x[1:]))
        levels = {}
        for lv in L['levels']:
            v = W.ladder_variant(w, lv['level']); vf = {s['id']: s for s in v['settled']}
            rel = [fid for fid in bearing if fid in vf]
            d_know = [knows(vf[f], D) for f in rel]; o_know = [knows(vf[f], O) for f in rel]
            gap = [max(0.0, dk - ok) for dk, ok in zip(d_know, o_know)]          # what the decider knows that the other lacks, on the bearing facts
            rated = None
            for attempt in range(2):
                try:
                    jr = J._call(client, cfg, [{'role': 'user', 'content': RATE.format(D=W.party_of(w, D)['profile']['name'], O=W.party_of(w, O)['profile']['name'], key=keys.get(wid, ''), o_facts=W.fact_lines(v, O, None) or '- nothing')}],
                                 f"distance/{wid}/L{lv['level']}/rate" + (f'/try{attempt}' if attempt else ''), ('distance',), max_tokens=400)
                    rated = float(jr.get('distance')) if isinstance(jr, dict) and jr.get('distance') is not None else None
                except (ValueError, KeyError, TypeError):
                    rated = None
                if rated is not None:
                    break
            levels[lv['level']] = {'bearing_in_level': rel, 'judged_distance': rated, 'other_lacks': round(sum(1 - o for o in o_know) / len(rel), 3) if rel else None,
                                   'distance': round(sum(gap) / max(1e-9, sum(d_know)), 3) if rel and sum(d_know) else None,
                                   'all_facts_gap': round(sum(max(0.0, knows(s, D) - knows(s, O)) for s in vf.values()) / max(1, len(vf)), 3)}
        out[wid] = {'decider': D, 'other': O, 'key_fact': keys.get(wid, ''), 'bearing': bearing, 'reason': j.get('reason', ''), 'levels': levels}
        print(f"{wid}: count distance " + ' / '.join(f"{levels[l]['distance']}" for l in sorted(levels)) + " | judged distance " + ' / '.join(f"{levels[l]['judged_distance']}" for l in sorted(levels)))
    R.save(run_dir / 'info_distance.json', out); print(f'spent ${client.spent:.2f}')


if __name__ == '__main__':
    main()
