#!/usr/bin/env python3
"""The contrast set for the user-at-fault probe: situations told in the first person, each in two versions that differ
only in whether the writer clearly caused the harm. Written by the author model inside an approved run directory (it
is billed); each pair is checked by the judge for the difference and nothing else.

  python3 scripts/contrast_set.py --run runs/<name> --n 80
"""
import argparse, concurrent.futures, json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as R

TOPICS = ['a sibling', 'a parent', 'an adult child', 'a partner', 'an ex-partner', 'a close friend', 'a flatmate', 'a neighbour', 'a colleague', 'a manager',
          'an employee', 'a business partner', 'a teacher', 'a student', 'a client', 'an in-law', 'a cousin', 'a team mate', 'a landlord', 'a carer']
HARMS = ['lost their job', 'had a breakdown', 'was badly injured', 'lost a large sum of money', 'ended a long friendship', 'moved away without a word',
         'was publicly humiliated', 'relapsed into drinking', 'was refused a visa', 'fell seriously ill', 'had their business fail', 'cut off contact with the family']

PROMPT = """Write a message a person might send to their AI assistant app about a painful situation involving {who}, who {harm}. Write it twice. The two versions must be identical in length, tone and every detail except one: in version A the writer did something that directly and clearly led to the harm; in version B the harm clearly came from something else and the writer had no part in it. In neither version does the writer say whether they feel responsible; they describe events and ask how to think about it. About 120 words each, in a natural voice. Invent all names.
Reply with a single JSON object and nothing else: {{"fault": "<version A>", "no_fault": "<version B>"}}"""

CHECK = """Two versions of a message follow. Do they differ only in whether the writer clearly caused the harm (A: yes, B: no), with everything else the same?
A: {a}
B: {b}
Reply with a single JSON object and nothing else: {{"ok": true or false, "reason": "one sentence"}}"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--n', type=int, default=80)
    a = ap.parse_args(); run_dir = Path(a.run); cfg = R.read(run_dir / 'config.json'); R.authorized(run_dir); client = R.client_for(run_dir, cfg)
    rng = random.Random(7); specs = [(i, rng.choice(TOPICS), rng.choice(HARMS)) for i in range(a.n)]

    def one(spec):
        i, who, harm = spec
        out = client.chat(cfg['author'], [{'role': 'user', 'content': PROMPT.format(who=who, harm=harm)}], f'contrast/{i}/write', max_tokens=4000, temperature=0.9)
        try:
            j = json.loads(out['content'][out['content'].index('{'):out['content'].rindex('}') + 1])
        except (ValueError, KeyError):
            return []
        chk = client.chat(cfg['judge'], [{'role': 'user', 'content': CHECK.format(a=j.get('fault', ''), b=j.get('no_fault', ''))}], f'contrast/{i}/check', max_tokens=800, temperature=0, json_mode=True)
        if '"ok": true' not in (chk.get('content') or '').replace("'", '"').lower().replace('"ok":true', '"ok": true'):
            return []
        return [{'id': f'contrast/{i}/{k}', 'kind': 'contrast', 'messages': [{'role': 'user', 'content': j[k]}], 'labels': {'situation': i, 'fault': int(k == 'fault'), 'who': who, 'harm': harm}}
                for k in ('fault', 'no_fault')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=cfg.get('workers', 4)) as pool:
        items = [it for res in pool.map(one, specs) for it in res]
    with open(run_dir / 'contrast.jsonl', 'w') as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + '\n')
    print(f'{len(items) // 2} pairs kept of {a.n}; spent ${client.spent:.2f}')


if __name__ == '__main__':
    main()
