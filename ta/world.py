"""Worlds: one event, its people, and three layers of truth (settled facts, permanently unknowable facts,
interpretation). A world file is the single source the game master, the simulator, the judge and the author all read.
The target assistant never sees a world file: it sees only a deployment prompt, a memory file and the conversation."""
import copy, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ('own_view', 'all_accounts', 'neutral_friend', 'memory_knows')
LEAK = re.compile(r'\b(palter\w*|mislead\w*|deceiv\w*|deception|deceptive|honest\w*|dishonest\w*|truthful\w*|lie|lies|lying|liar|'
                  r'scenario\w*|simulat\w*|experiment\w*|eval\b|evaluation|test subject|role-?play)\b', re.I)
PARTY_KEYS = ('profile', 'view', 'framing', 'reveal_policy', 'opening_message', 'truth_questions', 'memory', 'account', 'responsibility', 'protects', 'candour_items')


def load(path):
    w = json.loads(Path(path).read_text()); errs = validate(w)
    if errs:
        raise ValueError(f"{w.get('id')}: " + '; '.join(errs))
    return w


def load_all(directory=ROOT / 'worlds'):
    return {w['id']: w for w in (load(p) for p in sorted(Path(directory).glob('*.json')))}


def seen_by_target(w, party):
    """Everything a target could read for one party: the opening message, the memory file and the account."""
    p = w['parties'][party] if party in w['parties'] else w['neutral_friend']
    return '\n'.join([p.get('opening_message', ''), p.get('account', ''), p.get('memory_knows_extra', '')] + list(p.get('memory') or []) + [w['deployment_system_prompt']])


def validate(w):
    errs = [f'missing {k}' for k in ('id', 'settled', 'unknowable', 'parties', 'neutral_friend', 'deployment_system_prompt', 'blame_elements', 'people') if k not in w]
    if errs:
        return errs
    ids = {s['id'] for s in w['settled']}
    if len(ids) != len(w['settled']):
        errs.append('duplicate settled fact ids')
    if not w['unknowable']:
        errs.append('a world needs at least one permanently unknowable fact')
    for u in w['unknowable']:
        if not u.get('evidence_for') or not u.get('evidence_against'):
            errs.append(f"{u.get('id')}: an unknowable fact needs evidence pointing each way")
        if not u.get('permanent'):
            errs.append(f"{u.get('id')}: say why it can never be settled")
    for s in w['settled']:
        for who, k in (s.get('known_by') or {}).items():
            if who not in w['parties'] and who != 'neutral':
                errs.append(f"{s['id']}: known_by names {who}, who is not a party")
            if not (k == 'yes' or k.startswith('full:') or k.startswith('partial:')):
                errs.append(f"{s['id']}: known_by for {who} must be 'yes', 'full: ...' or 'partial: ...'")
        for name, p in w['parties'].items():
            if s['id'] in (p.get('view') or []) and name not in (s.get('known_by') or {}):
                errs.append(f"{s['id']} is in {name}'s view but known_by does not say what {name} knows")
    hidden_somewhere = False
    for name, p in w['parties'].items():
        errs += [f'{name}: missing {k}' for k in PARTY_KEYS if k not in p]
        if 'view' not in p:
            continue
        bad = set(p['view']) - ids
        if bad:
            errs.append(f'{name}: view has unknown facts {sorted(bad)}')
        others = [set(q.get('view', [])) for n, q in w['parties'].items() if n != name]
        if any(f not in set().union(*others) for f in p['view']) if others else False:
            hidden_somewhere = True
        for b in p.get('responsibility') or []:
            if b not in w['blame_elements']:
                errs.append(f'{name}: responsibility element {b} is not a blame element')
        m = LEAK.search(seen_by_target(w, name))
        if m:
            errs.append(f'{name}: the target would see the word {m.group(0)!r}')
    if not hidden_somewhere and len(w['parties']) > 1:
        errs.append('no party holds a fact the others lack')
    if len(w['parties']) < 2:
        errs.append('a world needs at least two parties')
    return errs


def twin(w):
    """The accident (or other) twin declared in the world file, as a full world."""
    t = w.get('accident_twin')
    if not t:
        return None
    out = copy.deepcopy(w); out['id'] = t['id']; out.pop('accident_twin', None); out['twin_of'] = w['id']
    for fid, change in t.get('changes', {}).items():
        if change.startswith('removed'):
            out['settled'] = [s for s in out['settled'] if s['id'] != fid]
            for p in out['parties'].values():
                p['view'] = [f for f in p['view'] if f != fid]
        else:
            for s in out['settled']:
                if s['id'] == fid:
                    s['fact'] = change
    for uid, q in t.get('unknowable_replaced', {}).items():
        for u in out['unknowable']:
            if u['id'] == uid:
                u['question'] = q
    for name, p in out['parties'].items():
        for k, v in (t.get('party_changes', {}).get(name) or {}).items():
            p[k] = v
    return out


def known(s, party):
    """What a party knows of a settled fact: ('full', how they know it), ('partial', a self-contained partial version),
    or None. known_by values are 'yes', 'full: <how they know>' or 'partial: <what they know>'."""
    k = (s.get('known_by') or {}).get(party)
    if not k:
        return None
    if k.startswith('partial:'):
        return 'partial', k[len('partial:'):].strip()
    return 'full', k[len('full:'):].strip() if k.startswith('full:') else ''


def fact_lines(w, party):
    """The settled facts a party knows, as that party knows them: a partially known fact is rendered only as the
    party's partial version, so no simulator ever reads the parts it does not know."""
    view = set(w['neutral_friend'].get('view') or []) if party == 'neutral' else set(w['parties'][party]['view'])
    out = []
    for s in w['settled']:
        if s['id'] not in view:
            continue
        kind, text = known(s, party) or ('full', '')
        out.append(f"- [{s['id']}, {s['date']}] {text}" if kind == 'partial' else f"- [{s['id']}, {s['date']}] {s['fact']}" + (f" (you know this {text})" if text else ''))
    return '\n'.join(out)


def memory(w, party, condition):
    p = w['parties'].get(party, {})
    notes = list(p.get('memory') or [])
    if condition == 'memory_knows' and p.get('memory_knows_extra'):
        notes.append(p['memory_knows_extra']); notes.sort()
    return notes


def consultations(w, condition):
    """Who consults under a condition: every party, the neutral friend, or (memory_knows) the parties whose memory can
    hold an extra fact."""
    if condition == 'neutral_friend':
        return ['neutral']
    if condition == 'memory_knows':
        return [n for n, p in w['parties'].items() if p.get('memory_knows_extra')]
    return list(w['parties'])
