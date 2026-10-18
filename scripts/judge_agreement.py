#!/usr/bin/env python3
"""Does a cheaper judge agree with the main one? Compares code/ (main judge) with an alternate judge's directory on the
reply coding, at three levels:

  items         each unknowable question both judges coded (same strength, same lean); candour items; advice turns
  conversations the per-conversation measures the report uses (any asserted, any lean toward the user, picture
                declined, any advice to withhold or say something untrue, side blame share, perspective)
  cells         target x condition means of those measures: does the cheap judge give the same model ranking?

Agreement on binary measures is reported with Cohen's kappa next to raw agreement, since most of them are rare.

  python3 scripts/judge_agreement.py --run runs/<name> [--alt-dir code_alt_gptoss]
"""
import argparse, json, statistics, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ta import metrics as M

ORDER = {s: i for i, s in enumerate(('open', 'favoured', 'asserted'))}


def kappa(pairs):
    """Cohen's kappa for two binary raters; None when one rater is constant and the other agrees."""
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return round((po - pe) / (1 - pe), 2) if pe < 1 else None


def corr(pairs):
    if len(pairs) < 3:
        return None
    xs, ys = zip(*pairs)
    try:
        return round(statistics.correlation(xs, ys), 2)
    except statistics.StatisticsError:
        return None


def strongest(say):
    out = {}
    for u in say.get('unknowable') or []:
        if u.get('strength') in ORDER and u.get('id'):
            prev = out.get(u['id'])
            if prev is None or ORDER[u['strength']] > ORDER[prev['strength']]:
                out[u['id']] = u
    return out


def per_conv(w, rec, c):
    m = M.conv(w, rec, c)
    if m is None:
        return None
    say = c['say']; unk = say.get('unknowable') or []
    return {'any_asserted': any(u['strength'] == 'asserted' for u in unk),
            'any_toward_user': any(u.get('leans') == 'toward_user' for u in unk),
            'picture_declined': m['picture_declined'],
            'any_withhold_or_untruth': any(a in ('withhold', 'untruth') for a in m['advice']),
            'side_blame': m['side_blame'], 'perspective': m['perspective'], 'contradictions': m['contradictions'],
            'serves_interest': m.get('serves_interest'), 'matches_view': m.get('matches_view'),
            'overclaim': m['overclaim'], 'candour': m['candour']}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--alt-dir', default='code_alt'); a = ap.parse_args()
    run_dir = Path(a.run); worlds = {w['id']: w for w in json.loads((run_dir / 'worlds.json').read_text())}
    q_both = q_same = q_lean_same = q_main_only = q_alt_only = 0
    cand, adv = [], []
    conv_pairs = defaultdict(list); cells = defaultdict(lambda: defaultdict(lambda: ([], [])))
    n = 0
    for p in sorted((run_dir / a.alt_dir).glob('*.json')):
        main_p, rec_p = run_dir / 'code' / p.name, run_dir / 'conv' / p.name
        if not main_p.exists() or not rec_p.exists():
            continue
        cm, cx, rec = json.loads(main_p.read_text()) or {}, json.loads(p.read_text()) or {}, json.loads(rec_p.read_text())
        m, x = cm.get('say'), cx.get('say')
        if not m or not x:
            continue
        w = worlds[rec['world']]; n += 1
        sm, sx = strongest(m), strongest(x)
        for uid in set(sm) | set(sx):
            if uid in sm and uid in sx:
                q_both += 1; q_same += sm[uid]['strength'] == sx[uid]['strength']
                key = 'reading' if 'leans' not in sm[uid] and 'leans' not in sx[uid] else 'leans'      # reading ids, or the old lean label
                q_lean_same += sm[uid].get(key) == sx[uid].get(key)
            elif uid in sm:
                q_main_only += 1
            else:
                q_alt_only += 1
        km = {c['id']: bool(c['raised']) for c in m.get('candour') or [] if 'id' in c}; kx = {c['id']: bool(c['raised']) for c in x.get('candour') or [] if 'id' in c}
        cand += [(km[i], kx[i]) for i in set(km) & set(kx)]
        am = {r.get('turn'): r['recommendation'] for r in m.get('advice') or []}; ax = {r.get('turn'): r['recommendation'] for r in x.get('advice') or []}
        adv += [(am[t], ax[t]) for t in set(am) & set(ax)]
        vm, vx = per_conv(w, rec, cm), per_conv(w, rec, cx)
        if not vm or not vx:
            continue
        cell = (rec['target'], rec['condition'])
        for k in vm:
            if vm[k] is not None and vx[k] is not None:
                conv_pairs[k].append((float(vm[k]), float(vx[k])))
                cells[k][cell][0].append(float(vm[k])); cells[k][cell][1].append(float(vx[k]))
    pct = lambda s, t: f"{s}/{t} ({s / t:.0%})" if t else '0/0'
    print(f"alternate judge: {a.alt_dir}; conversations compared: {n}\n")
    print("ITEMS")
    print(f"  unknowable questions coded by both: {q_both}; only main: {q_main_only}; only alternate: {q_alt_only}")
    print(f"    same strength: {pct(q_same, q_both)}; same reading (or lean, for old codes): {pct(q_lean_same, q_both)}")
    print(f"  candour items raised: same {pct(sum(u == v for u, v in cand), len(cand))}; kappa {kappa(cand)}")
    print(f"  advice on the same turn: same {pct(sum(u == v for u, v in adv), len(adv))}")
    print("\nCONVERSATIONS  (binary: agreement, kappa, rate main vs alternate; continuous: r, mean abs difference)")
    for k, ps in conv_pairs.items():
        if k in ('any_asserted', 'any_toward_user', 'picture_declined', 'any_withhold_or_untruth'):
            bp = [(bool(u), bool(v)) for u, v in ps]
            print(f"  {k:<24} {pct(sum(u == v for u, v in bp), len(bp)):<14} kappa {kappa(bp)!s:<5} "
                  f"rate {sum(u for u, _ in bp) / len(bp):.2f} vs {sum(v for _, v in bp) / len(bp):.2f}")
        else:
            print(f"  {k:<24} n {len(ps):<4} r {corr(ps)!s:<5} mad {statistics.mean(abs(u - v) for u, v in ps):.3f} "
                  f"mean {statistics.mean(u for u, _ in ps):.2f} vs {statistics.mean(v for _, v in ps):.2f}")
    print("\nCELLS  (target x condition means; r across cells, and whether the two judges rank the targets the same way)")
    for k, by in cells.items():
        pts = [(statistics.mean(u), statistics.mean(v)) for u, v in by.values() if u]
        tgt = defaultdict(lambda: ([], []))
        for (t, _), (u, v) in by.items():
            tgt[t][0].extend(u); tgt[t][1].extend(v)
        rank_m = [t for t, _ in sorted(tgt.items(), key=lambda kv: -statistics.mean(kv[1][0]))]
        rank_x = [t for t, _ in sorted(tgt.items(), key=lambda kv: -statistics.mean(kv[1][1]))]
        print(f"  {k:<24} cells {len(pts):<3} r {corr(pts)!s:<5} target order main {' > '.join(rank_m)}")
        print(f"  {'':<24} {'':<9} {'':<7} target order alt  {' > '.join(rank_x)}")


if __name__ == '__main__':
    main()
