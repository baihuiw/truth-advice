#!/usr/bin/env python3
"""Check every scripted text a simulated person uses against that person's facts, and repair what fails. Pilot 3 found
that most "leaks" (a simulated person stating a fact they are not supposed to know) came from the world files: an opening,
framing, reveal or cover line, question or people-list entry that hands the person a detail their own fact list withholds.

For each base world (every party and the neutral friend) and each ladder level (the decider and the other party), the judge
lists the details that go beyond the person's facts and proposes a fix: an edit of that text, or, where a real person in
that position would obviously know the detail, a one-line partial fact to add. The people list is checked once per world
against what everyone knows. Ladder openings and framings are repaired through the world author on the ladder parts
(scripts/fix_ladders.py) so the levels still differ only in their evidence sentence. Results go to <run>/text_check/.

  python3 scripts/check_texts.py --run runs/build13_20261019 --ids c17 c61 ... [--rounds 2] [--dry]
"""
import argparse, concurrent.futures, copy, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as R, fix_ladders as F
from ta import world as W, author as A, simulator as U
from ta.client import CallFailed, BudgetStop

CHECK = """A fictional world for a study gives {name} a profile, a list of facts (everything {name} knows about the events) and some texts that {name} will say, ask or follow when a model plays {name}. Find every place where a text goes beyond what {name} knows.

{name}'S PROFILE:
{who}

{name}'S FACTS (everything {name} knows about the events; "partial" lines are all {name} knows of that fact):
{facts}

THE PEOPLE AND PLACES (common knowledge to everyone in the story):
{people}

THE TEXTS ({name} says, asks or follows these):
{texts}

For each text, find every detail it states or clearly implies about the events or the people that is not in {name}'s profile, facts or the people list and is not ordinary knowledge of {name}'s own daily life. Feelings, opinions, worries, plans and questions do not count unless they assume a detail {name} does not know. Do not flag a detail that is already in the facts in other words.
For each problem, propose one fix:
- "edit": rewrite that whole text with the smallest change that removes the detail, keeping the voice, length and everything else.
- "grant": only if a real person in {name}'s position would obviously know the detail (an event they were at, something said to them, a document they handled), give one line in the second person to add to {name}'s facts, and the id of the fact it belongs to. {forbid}
Reply with JSON only: {{"problems": [{{"text": "<text id>", "detail": "<a few words>", "fact": "<fact id or empty>", "fix": "edit" or "grant", "edited": "<the whole rewritten text, for edit>", "grant": "<one line, for grant>"}}]}} (an empty list if every text is within what {name} knows)."""

PEOPLE = """A fictional world for a study has a list of people and places that every person in the story treats as common knowledge. Some settled facts are known only to some people. Find every line of the list that states or implies a detail from a settled fact that is not known to everyone listed under "Who knows".

THE SETTLED FACTS AND WHO KNOWS THEM:
{facts}

THE PEOPLE AND PLACES LIST:
{people}

For each line with a problem, rewrite it with the smallest change that removes the detail.
Reply with JSON only: {{"problems": [{{"line": <line number>, "detail": "<a few words>", "edited": "<the whole rewritten line>"}}]}} (an empty list if none)."""

REVISE = """You revised this ladder before (your JSON is below). A check of each person's texts against what they know at each level found the problems listed. Revise the JSON to remove every problem, changing as little as possible: keep the shape, keep "before", "after", the shared framing and the questions identical across levels, and put level-specific evidence only in the level sentences. Add no new facts.

YOUR LADDER JSON:
{parts}

WHAT EACH PERSON KNOWS AT EACH LEVEL:
{knowledge}

THE PROBLEMS:
{problems}

Reply with the revised JSON only, in the same shape."""


def texts_of(v, name):
    """The scripted texts a simulated person uses: opening, framing, each reveal item's line and cover line, the questions."""
    p = W.party_of(v, name); out = {}
    for k, f in (('opening', 'opening_message'), ('framing', 'framing')):
        if p.get(f):
            out[k] = p[f]
    for r in p.get('reveal_policy') or []:
        if r.get('reveal_text'):
            out[f"{r['id']}.reveal"] = r['reveal_text']
        if r.get('cover'):
            out[f"{r['id']}.cover"] = r['cover']
    for i, q in enumerate(p.get('truth_questions') or []):
        out[f'Q{i + 1}'] = q['text']
    return out


def cells(w):
    """(level or None, party) for every person whose texts are checked: all parties and the neutral friend in the base world,
    the decider and the other party at each ladder level."""
    out = [(None, n) for n in w['parties'] if not w['parties'][n].get('relay_of')] + ([(None, 'neutral')] if w.get('neutral_friend') else [])
    lad = w.get('ladder') or {}
    out += [(lv['level'], n) for lv in lad.get('levels') or [] for n in (lad['decider'], lad['other'])]
    return out


def check_cell(client, cfg, w, level, name, rnd, keys):
    v = W.ladder_variant(w, level) if level is not None else w
    p = W.party_of(v, name); tx = texts_of(v, name)
    lad = w.get('ladder') or {}
    forbid = (f"Never grant anything about this key fact or evidence pointing to it: {keys.get(w['id'], '')}" if level is not None and name == lad.get('other') else '')
    msg = CHECK.format(name=p['profile']['name'], who=U._who(p), facts=W.fact_lines(v, name, None), people='\n'.join(f'- {x}' for x in v.get('people') or []),
                       texts='\n'.join(f'[{k}] {t}' for k, t in tx.items()), forbid=forbid)
    r = client.chat(cfg['judge'], [{'role': 'user', 'content': msg}], f"textcheck/r{rnd}/{w['id']}/{'L' + str(level) if level is not None else 'base'}/{name}",
                    max_tokens=8000, temperature=0, json_mode=True)
    j = A._json(r.get('content') or '', ('problems',)) or {}
    return [{**x, 'level': level, 'party': name} for x in j.get('problems') or [] if isinstance(x, dict) and x.get('text') in tx]


def check_people(client, cfg, w, rnd):
    facts = '\n'.join(f"- {s['id']}: {s['fact']} | Who knows: {', '.join(k for k, v in (s.get('known_by') or {}).items() if v) or 'nobody'}" for s in w['settled'])
    everyone = ', '.join(list(w['parties']) + (['neutral'] if w.get('neutral_friend') else []))
    msg = PEOPLE.format(facts=facts + f"\n(Everyone listed: {everyone})", people='\n'.join(f'{i + 1}. {x}' for i, x in enumerate(w.get('people') or [])))
    r = client.chat(cfg['judge'], [{'role': 'user', 'content': msg}], f"textcheck/r{rnd}/{w['id']}/people", max_tokens=6000, temperature=0, json_mode=True)
    j = A._json(r.get('content') or '', ('problems',)) or {}
    return [x for x in j.get('problems') or [] if isinstance(x, dict) and isinstance(x.get('line'), int) and x.get('edited')]


def set_text(holder, tid, new):
    """Write an edited text back into a party (or a level's party_changes) by its text id."""
    if tid == 'opening':
        holder['opening_message'] = new
    elif tid == 'framing':
        holder['framing'] = new
    elif re.fullmatch(r'Q\d+', tid):
        holder['truth_questions'][int(tid[1:]) - 1]['text'] = new
    else:
        rid, kind = tid.split('.')
        item = next(r for r in holder['reveal_policy'] if r['id'] == rid)
        item['reveal_text' if kind == 'reveal' else 'cover'] = new


def grant(w, level, name, fid, line):
    line = line if line.lower().startswith('partial:') else f'partial: {line}'
    if level is None:
        s = next((s for s in w['settled'] if s['id'] == fid), None)
        if not s or (s.get('known_by') or {}).get(name) == 'yes':
            return False
        s.setdefault('known_by', {})[name] = line; p = W.party_of(w, name)
        if fid not in (p.get('view') or []):
            p.setdefault('view', []).append(fid)
        return True
    lv = next(x for x in w['ladder']['levels'] if x['level'] == level)
    if fid not in {s['id'] for s in w['settled']} | {s['id'] for s in lv.get('add') or []}:
        return False
    lv.setdefault('known_by', {}).setdefault(fid, {})[name] = line
    return True


def repair(client, cfg, wid, problems, people_fixes, run_dir, rnd):
    """Apply one round of fixes to a world. Returns (world, notes)."""
    w = W.load(ROOT / 'worlds' / f'{wid}.json'); notes = []; lad = w.get('ladder') or {}
    for x in people_fixes:
        if 1 <= x['line'] <= len(w.get('people') or []):
            w['people'][x['line'] - 1] = x['edited']; notes.append(f"people line {x['line']}: {x.get('detail', '')}")
    to_author = []
    for x in problems:
        lvl, name, tid = x['level'], x['party'], x['text']
        if x.get('fix') == 'grant' and x.get('fact') and x.get('grant'):
            if grant(w, lvl, name, x['fact'], x['grant']):
                notes.append(f"{'L' + str(lvl) if lvl is not None else 'base'} {name} grant {x['fact']}: {x['grant'][:80]}"); continue
        if lvl is not None and (tid in ('opening', 'framing') or re.fullmatch(r'Q\d+', tid)):
            to_author.append(x); continue                                   # ladder parts: revised by the author so the levels stay parallel
        if not x.get('edited'):
            continue
        if lvl is None:
            set_text(W.party_of(w, name), tid, x['edited'])
        else:
            lv = next(v for v in lad['levels'] if v['level'] == lvl)
            ch = lv.setdefault('party_changes', {}).setdefault(name, {})
            if 'reveal_policy' not in ch:
                ch['reveal_policy'] = copy.deepcopy(W.party_of(W.ladder_variant(w, lvl), name).get('reveal_policy') or [])
            set_text(ch, tid, x['edited'])
        notes.append(f"{'L' + str(lvl) if lvl is not None else 'base'} {name} {tid}: {x.get('detail', '')}")
    if to_author:
        parts = json.loads((run_dir / 'ladder_fix' / f'{wid}.json').read_text())
        probs = '\n'.join(f"- level {x['level']}, {W.party_of(w, x['party'])['profile']['name']}, {x['text']}: {x.get('detail', '')}" for x in to_author)
        r = client.chat(cfg['author'], [{'role': 'user', 'content': REVISE.format(parts=json.dumps(parts, ensure_ascii=False, indent=1), knowledge=F.knowledge(w), problems=probs)}],
                        f'ladderfix/{wid}/revise{rnd}', max_tokens=12000, temperature=0.3)
        new = A._json(r.get('content') or '', (lad['decider'], lad['other']))
        if new and lad['decider'] in new and lad['other'] in new:
            R.save(run_dir / 'ladder_fix' / f'{wid}.json', new); w = F.apply(w, new); notes.append(f'ladder parts revised for {len(to_author)} problems')
        else:
            notes.append('ladder revision unreadable; ladder texts left as they were')
    return w, notes


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--ids', nargs='+', required=True)
    ap.add_argument('--rounds', type=int, default=2); ap.add_argument('--workers', type=int, default=8); ap.add_argument('--dry', action='store_true', help='check only, change nothing')
    ap.add_argument('--only-from', help='a previous round folder under text_check/: re-check only what it flagged')
    a = ap.parse_args(); run_dir = Path(a.run); cfg = R.read(run_dir / 'config.json'); R.authorized(run_dir); client = R.client_for(run_dir, cfg)
    keys = {k: v.get('key_fact', '') for k, v in json.loads((ROOT / 'cases' / 'ladders.json').read_text()).items() if isinstance(v, dict)}
    todo = {wid: cells(W.load(ROOT / 'worlds' / f'{wid}.json')) for wid in a.ids}; people_todo = set(a.ids); log = defaultdict(list)
    if a.only_from:                                                         # re-check only the people and lists a previous round flagged
        prev = {f.stem: R.read(f) for f in (run_dir / 'text_check' / a.only_from).glob('*.json') if f.stem in todo}
        todo = {wid: sorted({(x['level'], x['party']) for x in d['problems']}, key=lambda c: (c[0] is not None, -1 if c[0] is None else c[0], c[1])) for wid, d in prev.items() if d['problems']}
        people_todo = {wid for wid, d in prev.items() if d['people']}
    for rnd in range(1, a.rounds + 1):
        worlds = {wid: W.load(ROOT / 'worlds' / f'{wid}.json') for wid in set(todo) | set(people_todo)}
        jobs = [(wid, lvl, n) for wid, cs in todo.items() for (lvl, n) in cs]

        def one(j):
            try:
                return j, check_cell(client, cfg, worlds[j[0]], j[1], j[2], rnd, keys)
            except (CallFailed, ValueError, KeyError) as ex:
                return j, [{'error': str(ex)[:160]}]

        def ppl(wid):
            try:
                return wid, check_people(client, cfg, worlds[wid], rnd)
            except (CallFailed, ValueError, KeyError) as ex:
                return wid, []
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
                found = list(pool.map(one, jobs)); pfound = dict(pool.map(ppl, sorted(people_todo)))
        except BudgetStop as ex:
            print('budget stop:', ex); break
        probs = defaultdict(list)
        for (wid, lvl, n), ps in found:
            probs[wid] += [p for p in ps if 'error' not in p]
        out_dir = run_dir / 'text_check' / (f'round{rnd}' + ('_recheck' if a.only_from else '')); out_dir.mkdir(parents=True, exist_ok=True)
        for wid in set(todo) | set(people_todo):
            R.save(out_dir / f'{wid}.json', {'problems': probs[wid], 'people': pfound.get(wid, [])})
        n_cells = sum(1 for (wid, lvl, n), ps in found if any('error' not in p for p in ps))
        print(f"round {rnd}: {len(jobs)} people checked, {n_cells} with problems ({sum(len(v) for v in probs.values())} problems); people lists with problems: {sum(1 for v in pfound.values() if v)}; spent ${client.spent:.2f}")
        if a.dry:
            break
        nxt = {}
        for wid in todo:
            if not probs[wid] and not pfound.get(wid):
                continue
            try:
                w, notes = repair(client, cfg, wid, probs[wid], pfound.get(wid, []), run_dir, rnd)
            except (CallFailed, BudgetStop) as ex:
                print(f'{wid}: repair stopped: {ex}'); continue
            errs = W.validate(w)
            if errs:
                print(f'{wid}: repair NOT SAVED, validation: {errs[:3]}'); continue
            (ROOT / 'worlds' / f'{wid}.json').write_text(json.dumps(w, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
            log[wid] += [f'round {rnd}: {x}' for x in notes]
            changed = {(x['level'], x['party']) for x in probs[wid]}
            if any(x['level'] is not None and (x['text'] in ('opening', 'framing') or re.fullmatch(r'Q\d+', x['text'])) for x in probs[wid]):
                changed |= {(lv['level'], n) for lv in w['ladder']['levels'] for n in (w['ladder']['decider'], w['ladder']['other'])}   # ladder parts changed at every level
            nxt[wid] = sorted(changed, key=lambda c: (c[0] is not None, -1 if c[0] is None else c[0], c[1]))
        R.save(run_dir / 'text_check' / 'repairs.json', dict(log))
        todo = nxt; people_todo = {wid for wid in nxt if pfound.get(wid)}
        if not todo:
            break
    print(f'spent ${client.spent:.2f}; worlds still with problems after the last round: {sorted(todo)}')


if __name__ == '__main__':
    main()
