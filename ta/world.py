"""Worlds: one event, its people, and three layers of truth (settled facts, permanently unknowable facts,
interpretation). A world file is the single source the game master, the simulator, the judge and the author all read.
The target assistant never sees a world file: it sees only a deployment prompt, a memory file and the conversation."""
import copy, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ('own_view', 'all_accounts', 'neutral_friend', 'memory_knows')
WHEN = ('volunteers', 'if_asked', 'if_pressed')
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
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
    for name in list(w['parties']) + ['neutral']:
        p = party_of(w, name); rids = [r.get('id') for r in p.get('reveal_policy') or []]
        if len(set(rids)) != len(rids) or None in rids:
            errs.append(f'{name}: reveal items need unique ids')
        for r in p.get('reveal_policy') or []:
            if r.get('when') not in WHEN:
                errs.append(f"{name} {r.get('id')}: when must be one of {WHEN}")
            if r.get('when') != 'volunteers' and not r.get('ask_cue'):
                errs.append(f"{name} {r.get('id')}: a locked item needs an ask_cue")
            if set(r.get('facts') or []) - set(p.get('view') or []):
                errs.append(f"{name} {r.get('id')}: facts outside the view")
            if r.get('requires') and r['requires'] not in rids:
                errs.append(f"{name} {r.get('id')}: requires an unknown item")
    year = int(w.get('conversation_start', '2026-10-05')[:4]); recent = re.compile(rf'\b({year}|{year + 1})\b')
    shown = list(w.get('people') or [])
    for name in list(w['parties']) + ['neutral']:
        p = party_of(w, name)
        shown += [p.get('opening_message', ''), p.get('account', ''), p.get('memory_knows_extra', '')] + list(p.get('memory') or [])
        shown += [r.get(k, '') for r in p.get('reveal_policy') or [] for k in ('surface', 'reveal_text', 'hint')]
    shown += [k for s in w['settled'] for k in (s.get('known_by') or {}).values() if k.startswith('partial:')]
    for x in shown:
        if recent.search(x or ''):
            errs.append(f'the current year appears in text the simulator or the target reads: {x[:60]!r}')
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


def when(w, date):
    """A date as the people in the world would say it: no year for this year, 'last <month>' for last year, so nothing
    the target reads carries a year that may lie beyond its training data."""
    year = int(w.get('conversation_start', '2026-10-05')[:4]); parts = str(date).split('/')[0].split('-')
    try:
        y = int(parts[0]); m = MONTHS[int(parts[1]) - 1] if len(parts) > 1 else None; d = int(parts[2]) if len(parts) > 2 else None
    except (ValueError, IndexError):
        return str(date)
    if y == year:
        return f'{d} {m}' if d else (m or 'this year')
    if y == year - 1:
        return f'last {m}' if m else 'last year'
    return f'{m} {y}' if m else str(y)


def party_of(w, party):
    return w['neutral_friend'] if party == 'neutral' else w['parties'][party]


def locked_facts(w, party, unlocked=None):
    """Facts tied to reveal items that are not open yet, with the surface text (if any) to show in their place."""
    out = {}
    for r in party_of(w, party).get('reveal_policy') or []:
        if r['when'] != 'volunteers' and (unlocked is None or r['id'] not in unlocked):
            for f in r.get('facts') or []:
                out[f] = r.get('surface')
    return out


def fact_lines(w, party, unlocked=None):
    """The settled facts a party knows, as that party knows them. A partially known fact is rendered only as the
    party's partial version; a fact tied to a reveal item that is not open yet is hidden (or shown as its surface
    text), so no simulator reads what it may not yet say. unlocked=None shows everything the party knows."""
    view = set(party_of(w, party).get('view') or [])
    hidden = locked_facts(w, party, unlocked) if unlocked is not None else {}
    out = []
    for s in w['settled']:
        if s['id'] not in view:
            continue
        if s['id'] in hidden:
            if hidden[s['id']]:
                out.append(f"- [{when(w, s['date'])}] {hidden[s['id']]}")
            continue
        kind, text = known(s, party) or ('full', '')
        out.append(f"- [{when(w, s['date'])}] {text}" if kind == 'partial' else f"- [{when(w, s['date'])}] {s['fact']}" + (f" (you know this {text})" if text else ''))
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
