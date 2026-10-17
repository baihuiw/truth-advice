#!/usr/bin/env python3
"""Offline run of the whole pipeline with a scripted client: no API calls, nothing billed. Conversations under every
condition, the judge's codes, phase-2 scenes, the report, then the world author: seed the archive and write, gate, run
and place children.

  python3 scripts/dry_run.py [--keep <dir>]
"""
import argparse, hashlib, json, re, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
from ta import gm as G, judge as J, author as A
import run as R
import search as SR


def h(*xs):
    return int(hashlib.sha256('|'.join(map(str, xs)).encode()).hexdigest(), 16)


class ScriptedClient:
    def __init__(self):
        self.calls = 0; self.spent = 0.0; self.cap = 0.0

    def chat(self, alias, messages, label, **kw):
        self.calls += 1; text = messages[-1]['content']; last = label.rsplit('/', 1)[-1]; parts = label.split('/')
        ok = lambda c, **x: {'content': c, 'cost': 0, **x}
        if parts[0] == 'author':
            if 'The parent world (JSON):' in text:                                   # mutate
                child = json.loads(text[text.index('The parent world (JSON):\n') + 25:text.index('\n\nHow the five assistants')]); child['design'] = {**child['design'], 'relationship': 'work'}
            elif 'STRUCTURE WORLD (JSON)' in text:                                   # recombine
                s0 = text.index('{', text.index('STRUCTURE WORLD (JSON)')); child = json.loads(text[s0:text.index('\n\nCONTEXT WORLD')])
                child['design'] = {**child['design'], 'relationship': 'friends'}
            else:                                                                    # free
                child = json.loads((ROOT / 'worlds' / 'elena.json').read_text()); child.pop('accident_twin', None)
                child['design'] = json.loads(text[text.index('TARGET DESIGN: ') + 15:].split('\n')[0])
            child['id'] = parts[1]; child['hypothesis'] = 'scripted'
            return ok(json.dumps(child))
        if parts[0] == 'gate':
            return ok(json.dumps({'consistency': {'consistent': True, 'fictional': True, 'coherent': True, 'reason': 'ok'},
                                  'recognition': {'resembles': False, 'which': '', 'confidence': 0.1}, 'realism': {'rating': 4, 'reason': 'ok'}}[last]))
        if parts[0] == 'ping':
            return ok('OK')
        if 'scene' in parts:
            if last == 'judge':
                return ok(json.dumps({'surfaced': ['S3'] if h(label) % 2 else [], 'accounts': {}, 'compatible': bool(h(label) % 3), 'misled': [], 'nora': {'U1': 'unclear'}}))
            return ok(f'(scripted line {last})')
        if parts[-2] == 'judge':
            party = parts[2]; target = parts[3]
            if last == 'fidelity':
                return ok(json.dumps({'leaked': [], 'broke_character': False, 'followed_policy': True, 'reason': 'ok'}))
            cands = re.findall(r'- (C_\w+):', text)
            easy = h(target) % 3
            blame = {'buyout': 0.3, 'visit': 0.2, 'report': 0.1, 'illness': 0.3, 'her_decision': 0.1}
            own = {'gareth': ['buyout'], 'tomas': ['visit', 'report'], 'mia': ['visit', 'report']}.get(party, [])
            for e in own:
                blame[e] = blame[e] * (0.3 if easy else 0.9)
            unk = [{'turn': 1, 'id': 'U1', 'strength': 'asserted' if easy == 2 else 'favoured', 'leans': 'away_from_user' if easy else 'neither', 'reading': 'the illness', 'quote': 'x'},
                   {'turn': 2, 'id': 'U3', 'strength': 'open', 'leans': 'toward_user', 'reading': 'mixed', 'quote': 'y'}]
            code = {'settled': [{'turn': 1, 'fact': 'S13', 'status': 'consistent', 'quote': 'z'}], 'unknowable': unk if last == 'say' else unk[:1], 'blame': blame,
                    'perspective': [{'party': 'gareth', 'presented': bool(easy), 'quote': ''}], 'candour': [{'id': c, 'raised': (i + easy + (last == 'think')) % 2 == 0, 'quote': ''} for i, c in enumerate(cands)],
                    'advice': [{'turn': 3, 'question': 'should I tell', 'recommendation': ['tell', 'tell', 'withhold'][easy], 'quote': ''}], 'support_content': party != 'gareth', 'declined_picture': easy == 0, 'notes': ''}
            return ok(json.dumps(code))
        if last.startswith('gm') and last[2:].isdigit():                      # the game master's unlock check: the assistant asked about every topic
            return ok(json.dumps({'asked': re.findall(r'- (R\d+):', text)}))
        if last.startswith('a') and last[1:].isdigit():
            return ok(f'Assistant reply {last}. That sounds hard.', reasoning='scripted reasoning')
        if last.startswith('u') and last[1:].isdigit():
            return ok('ok, thanks. that helps. [END]' if int(last[1:]) >= 4 else f'user message {last}')
        if last.startswith('post_'):
            return ok('YES. They seem real.' if last == 'post_real' else 'NO')
        raise ValueError(label)


def run(keep=None):
    cfg = {**json.loads((ROOT / 'config' / 'pilot.json').read_text()), 'targets': ['sonnet55', 'gpt61'], 'reps': 1}
    cfg['phase2'] = {'reps': 1, 'diagonal': True, 'cross': [{'tomas': 'sonnet55', 'gareth': 'gpt61', 'mia': 'gpt61'}]}
    tmp = tempfile.TemporaryDirectory(); run_dir = Path(keep) if keep else Path(tmp.name); run_dir.mkdir(parents=True, exist_ok=True)
    worlds = R.worlds_for(cfg); R.save(run_dir / 'config.json', cfg); R.save(run_dir / 'worlds.json', worlds)
    client = ScriptedClient()
    for w in worlds:
        for job in G.jobs(w, cfg):
            G.consult(client, cfg, run_dir, w, *job)
    for p in sorted((run_dir / 'conv').glob('*.json')):
        rec = R.read(p); w = next(x for x in worlds if x['id'] == rec['world']); R.save(R.code_path(run_dir, p), J.code(client, cfg, w, rec))
    for w in worlds:
        recs = {(pp, t): R.read(G.conv_path(run_dir, w, 'own_view', pp, t, 0)) for pp in w['parties'] for t in cfg['targets']}
        for pr in [{pp: t for pp in w['parties']} for t in cfg['targets']] + cfg['phase2']['cross']:
            sc = G.scene(client, cfg, run_dir, w, pr, 0, recs)
            tag = '_'.join(f'{n}-{t}' for n, t in sorted(pr.items())); R.save(run_dir / 'scene_code' / f"{w['id']}__{tag}__r0.json", J.code_scene(client, cfg, w, sc))
    rep = R.report(run_dir, str(run_dir / 'report.html'))
    archive = A.Archive(run_dir / 'archive.json'); seeded = SR.seed(client, cfg, run_dir, worlds, archive, run_dir)
    kids = SR.step(client, cfg, run_dir, archive, 6, 3, moves=['mutate', 'recombine', 'free'])
    out = {'report': rep, 'seeded': seeded, 'children': kids, 'archive': archive.data['cells'], 'calls': client.calls,
           'conversations': len(list((run_dir / 'conv').glob('*.json')))}
    if not keep:
        tmp.cleanup()
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--keep'); a = ap.parse_args(); out = run(a.keep)
    print(f"\ndry run ok: {out['calls']} scripted calls, {out['conversations']} conversations, archive cells {list(out['archive'])}, children {[k['status'] for k in out['children']]}; nothing billed")


if __name__ == '__main__':
    main()
