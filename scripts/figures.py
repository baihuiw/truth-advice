#!/usr/bin/env python3
"""Paper figures from a finished run, drawn with matplotlib as PDF and PNG. Figure 1: the truth stance assistants recommend
(disclose / defer / withhold / deceive) across the information-asymmetry ladder, by assistant and by whose secret it is,
with the share that calls withholding dishonest. Intervals resample worlds (the unit of inference; one conversation per
cell). Nothing is billed.

  python3 scripts/figures.py --run runs/pilot3b_20261019 --out figures
"""
import argparse, collections, json, random, sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as RUN

T = ['sonnet55', 'gpt61', 'gemini38', 'deepseek4p', 'glm53']
NAME = {'sonnet55': 'Claude Sonnet 5.5', 'gpt61': 'GPT-6.1 Sol', 'gemini38': 'Gemini 3.8 Flash', 'deepseek4p': 'DeepSeek V4 Pro', 'glm53': 'GLM-5.3', 'all': 'All five assistants'}
MODEL_COLOR = {'sonnet55': '#2a78d6', 'gpt61': '#eb6834', 'gemini38': '#1baf7a', 'deepseek4p': '#eda100', 'glm53': '#6250d6', 'all': '#15191b'}
STANCES = ['disclose', 'defer', 'withhold', 'deceive']
STANCE_COLOR = {'disclose': '#1c5cab', 'defer': '#86b6ef', 'withhold': '#b8b6ad', 'deceive': '#d03b3b'}
STANCE_LABEL = {'disclose': 'Disclose', 'defer': 'Defer (tell later)', 'withhold': 'Withhold (say nothing false)', 'deceive': 'Deceive (say something false)'}
CODE2STANCE = {'tell': 'disclose', 'defer': 'defer', 'withhold': 'withhold', 'untruth': 'deceive'}
GROUPS = [("Own misstatement\nto an institution", ['c61', 'c69', 'c79']), ("Another person's\nown diagnosis", ['c74']), ("Family secret\nabout the dead", ['c17']),
          ("Institution's error\nthat hurts someone", ['c65', 'c66']), ("Own act, with\nretaliation risk", ['c71']), ("Another person's file\nor whereabouts", ['c62', 'c67', 'c72'])]
LEVELS = ['0\nthey know\nthe fact', '1\nstrong\nlead', '2\nweak\nlead', '3\nno\nlead']


def ladder_cells(run_dir):
    """Per (world, level, assistant): the stance on the disclosure question, the stance on the direct-denial question, and the
    honesty judgment of withholding (1 dishonest, 0.5 partly, 0 not), for the person holding the secret."""
    wl = RUN.read(run_dir / 'worlds.json'); worlds = {w['id']: w for w in wl}; out = []
    for r in RUN.rows(run_dir, wl):
        w = worlds[r['world']]; roles = w.get('ladder_roles')
        if not roles or r['party'] != roles['decider'] or not r['m']:
            continue
        dq = [q for q in w['parties'][roles['decider']]['truth_questions'] if q.get('choice')]
        ids = [q['choice']['id'] for q in dq]
        st = {a.get('choice'): CODE2STANCE.get(a['recommendation']) for a in r['m']['advice_items'] if a.get('choice') in ids and a['recommendation'] in CODE2STANCE}
        hj = [{'dishonest': 1.0, 'partly': 0.5, 'not_dishonest': 0.0}[v] for v in r['m'].get('honesty_judgment') or []]
        out.append({'world': w['ladder_of'], 'level': w['ladder_level'], 'model': r['target'], 'disclosure': st.get(ids[0]) if ids else None,
                    'deny': st.get(ids[1]) if len(ids) > 1 else None, 'dishonest': sum(hj) / len(hj) if hj else None})
    return out


def shares(cells, key='disclosure'):
    """Stance shares with each world weighted once (mean over the world's cells, then over worlds)."""
    by_world = collections.defaultdict(lambda: collections.Counter())
    for c in cells:
        if c[key]:
            by_world[c['world']][c[key]] += 1
    worlds = list(by_world)
    if not worlds:
        return {s: 0.0 for s in STANCES}, 0
    return {s: sum(by_world[w][s] / sum(by_world[w].values()) for w in worlds) / len(worlds) for s in STANCES}, sum(sum(v.values()) for v in by_world.values())


def boot_mean(cells, key, reps=2000, seed=7):
    by_world = collections.defaultdict(list)
    for c in cells:
        if c[key] is not None:
            by_world[c['world']].append(c[key])
    ws = [sum(v) / len(v) for v in by_world.values()]
    if not ws:
        return None, None, None
    rng = random.Random(seed); m = sum(ws) / len(ws)
    if len(ws) < 3:
        return m, None, None
    bs = sorted(sum(rng.choice(ws) for _ in ws) / len(ws) for _ in range(reps))
    return m, bs[int(0.025 * reps)], bs[int(0.975 * reps) - 1]


def stacked(ax, dists, labels, title, show_n=True):
    x = range(len(dists)); bottom = [0.0] * len(dists)
    for s in STANCES:
        vals = [d[0][s] for d in dists]
        ax.bar(x, vals, bottom=bottom, color=STANCE_COLOR[s], width=0.78, edgecolor='white', linewidth=0.6)
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v >= 0.12:
                ax.text(i, b + v / 2, f'{100 * v:.0f}', ha='center', va='center', fontsize=6.5, color='white' if s in ('disclose', 'deceive') else '#15191b')
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=6.5); ax.set_ylim(0, 1); ax.set_yticks([0, 0.5, 1]); ax.set_yticklabels(['0', '50', '100%'], fontsize=6.5)
    ax.set_title(title, fontsize=8, loc='left', pad=4)
    if show_n:
        ax.text(1.0, 1.02, 'n=' + ','.join(str(d[1]) for d in dists), transform=ax.transAxes, ha='right', va='bottom', fontsize=5.5, color='#5b6367')
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    ax.spines['left'].set_color('#b8b6ad'); ax.spines['bottom'].set_color('#b8b6ad'); ax.tick_params(length=2, color='#b8b6ad')


def figure1(run_dir, out_dir):
    cells = ladder_cells(run_dir); deny = shares(cells, 'deny')
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'], 'font.size': 7, 'axes.titleweight': 'normal'})
    fig = plt.figure(figsize=(7.2, 6.6))
    gs = fig.add_gridspec(2, 6, height_ratios=[1, 1.2], hspace=0.5, wspace=0.3, left=0.075, right=0.985, top=0.855, bottom=0.11)
    # Row A: stances by evidence level, per assistant and pooled
    for i, t in enumerate(T + ['all']):
        ax = fig.add_subplot(gs[0, i]); sub = [c for c in cells if t == 'all' or c['model'] == t]
        dists = [shares([c for c in sub if c['level'] == lv]) for lv in range(4)]
        stacked(ax, dists, ['0', '1', '2', '3'], NAME[t], show_n=False)
        if i:
            ax.set_yticklabels([])
        if i == 0:
            ax.set_ylabel('Share of recommendations', fontsize=7)
    fig.text(0.075, 0.955, "A  Which truth stance does the assistant recommend to the person holding the secret, as the other person's evidence thins?", fontsize=8.5, weight='bold', ha='left')
    fig.text(0.075, 0.925, "Other person's evidence: level 0, they know the key fact but not its meaning; 1, a strong lead; 2, a weak lead; 3, no lead. Eleven worlds, one conversation per cell, weighted by world.", fontsize=6.0, color='#5b6367')
    fig.text(0.075, 0.905, f"Deception never appears on this question; on the direct one (\"if they ask me outright, can I say no?\") it is recommended in {100 * deny[0]['deceive']:.1f}% of {deny[1]} answers, all by Gemini.", fontsize=6.0, color='#5b6367')
    fig.text(0.53, 0.528, "Other person's evidence level", fontsize=6.8, ha='center')
    # Row B left: stances by whose secret it is (pooled over levels and assistants)
    axb = fig.add_subplot(gs[1, 0:4])
    dists = [shares([c for c in cells if c['world'] in ws]) for _, ws in GROUPS]
    order = sorted(range(len(GROUPS)), key=lambda i: -(dists[i][0]['disclose'] + dists[i][0]['defer']))
    stacked(axb, [dists[i] for i in order], [GROUPS[i][0] + '\n' + ', '.join(GROUPS[i][1]) + f'\nn={dists[i][1]}' for i in order], 'B  The same, by whose secret it is (all levels and assistants pooled)', show_n=False)
    axb.set_ylabel('Share of recommendations', fontsize=7); axb.tick_params(axis='x', labelsize=6)
    # Row B right: withholding judged dishonest, by level
    axc = fig.add_subplot(gs[1, 4:6])
    for t in T + ['all']:
        sub = [c for c in cells if t == 'all' or c['model'] == t]; ys = []; lo = []; hi = []
        for lv in range(4):
            m, l, h = boot_mean([c for c in sub if c['level'] == lv], 'dishonest'); ys.append(m); lo.append(l); hi.append(h)
        if t == 'all':
            axc.fill_between(range(4), [l if l is not None else y for l, y in zip(lo, ys)], [h if h is not None else y for h, y in zip(hi, ys)], color='#15191b', alpha=0.08, linewidth=0)
        axc.plot(range(4), ys, color=MODEL_COLOR[t], linewidth=2.2 if t == 'all' else 1.2, marker='o', markersize=3.5 if t == 'all' else 2.5, label=NAME[t], zorder=3 if t == 'all' else 2)
    axc.set_ylim(0, 1); axc.set_yticks([0, 0.5, 1]); axc.set_yticklabels(['0', '0.5', '1'], fontsize=6.5); axc.set_xticks(range(4)); axc.set_xticklabels(['0', '1', '2', '3'], fontsize=6.5)
    axc.set_xlabel("Other person's evidence level", fontsize=6.5, labelpad=2); axc.set_ylabel('Dishonesty of withholding (0 no, 0.5 partly, 1 yes)', fontsize=6.5)
    axc.set_title('C  Is the withholding called dishonest?', fontsize=8, loc='left', pad=4)
    for sp in ('top', 'right'):
        axc.spines[sp].set_visible(False)
    axc.spines['left'].set_color('#b8b6ad'); axc.spines['bottom'].set_color('#b8b6ad'); axc.tick_params(length=2, color='#b8b6ad')
    axc.legend(fontsize=5.6, frameon=False, loc='lower left', ncol=2, handlelength=1.4, columnspacing=0.8)
    fig.legend(handles=[Patch(color=STANCE_COLOR[s], label=STANCE_LABEL[s]) for s in STANCES], loc='lower center', ncol=4, frameon=False, fontsize=7, bbox_to_anchor=(0.5, 0.0))
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(out_dir / f'fig1_stances.{ext}', dpi=300)
    dec = collections.Counter(c['model'] for c in cells if c['deny'] == 'deceive')
    print('saved', out_dir / 'fig1_stances.pdf', '| direct denial: deceive share', round(deny[0]['deceive'], 3), 'n', deny[1], 'by model', dict(dec))
    print('cells', len(cells), 'pooled by level:', [{s: round(v, 2) for s, v in shares([c for c in cells if c['level'] == lv])[0].items()} for lv in range(4)])


def figure2(run_dir, out_dir):
    """The effect of the advice on the other person: teller side (acts flat across the ladder, misled share rising, awareness by
    assistant) and seeker side (what the person in the dark is told and where they end up, by level and by assistant)."""
    import effect_report as ER
    tell, seek = ER.load(run_dir); ACTS = ER.ACTS
    ACT_COLOR = {'plain': '#1c5cab', 'tactful': '#5598e7', 'partial': '#d9a441', 'defer': '#b7d3f6', 'withhold': '#b8b6ad', 'deceive': '#d03b3b'}
    ACT_LABEL = {'plain': 'Disclose plainly', 'tactful': 'Disclose tactfully', 'partial': 'Partial truth', 'defer': 'Defer', 'withhold': 'Withhold', 'deceive': 'Deceive'}
    ST_COLOR = {'truth': '#1c5cab', 'cant': '#b8b6ad', 'false': '#d03b3b', 'none': '#e8e6df'}
    ST_LABEL = {'truth': 'States or leans to the truth', 'cant': "Says it can't be known", 'false': 'Leans to or states something false', 'none': 'Does not address it'}
    OUT_COLOR = {'truth': '#1c5cab', 'uncertain': '#b8b6ad', 'false': '#d03b3b'}
    OUT_LABEL = {'truth': 'At the truth', 'uncertain': 'Still uncertain', 'false': 'Believing something false'}

    def stack(ax, dists, labels, keys, colors, title):
        x = range(len(dists)); bottom = [0.0] * len(dists)
        for k in keys:
            vals = [d.get(k) or 0.0 for d in dists]
            ax.bar(x, vals, bottom=bottom, color=colors[k], width=0.78, edgecolor='white', linewidth=0.6)
            for i, (v, b) in enumerate(zip(vals, bottom)):
                if v >= 0.1:
                    ax.text(i, b + v / 2, f'{100 * v:.0f}', ha='center', va='center', fontsize=6.3, color='white' if k in ('plain', 'truth', 'false', 'deceive') else '#15191b')
            bottom = [b + v for b, v in zip(bottom, vals)]
        ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=6.5); ax.set_ylim(0, 1); ax.set_yticks([0, 0.5, 1]); ax.set_yticklabels(['0', '50', '100%'], fontsize=6.5)
        ax.set_title(title, fontsize=7.8, loc='left', pad=4)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        ax.spines['left'].set_color('#b8b6ad'); ax.spines['bottom'].set_color('#b8b6ad'); ax.tick_params(length=2, color='#b8b6ad')

    def lines(ax, items, pred, title, ylabel):
        for t in T + ['all']:
            ys, lo, hi = [], [], []
            for lv in range(4):
                sub = [{'world': it['world'], 'v': float(pred(it))} for it in items if (t == 'all' or it['model'] == t) and it['level'] == lv]
                m, l, h = boot_mean(sub, 'v'); ys.append(m); lo.append(l); hi.append(h)
            if t == 'all':
                ax.fill_between(range(4), [l if l is not None else y for l, y in zip(lo, ys)], [h if h is not None else y for h, y in zip(hi, ys)], color='#15191b', alpha=0.08, linewidth=0)
            ax.plot(range(4), ys, color=MODEL_COLOR[t], linewidth=2.2 if t == 'all' else 1.1, marker='o', markersize=3.5 if t == 'all' else 2.5, label=NAME[t], zorder=3 if t == 'all' else 2)
        ax.set_ylim(0, 1); ax.set_yticks([0, 0.5, 1]); ax.set_yticklabels(['0', '50', '100%'], fontsize=6.5); ax.set_xticks(range(4)); ax.set_xticklabels(['0', '1', '2', '3'], fontsize=6.5)
        ax.set_title(title, fontsize=7.8, loc='left', pad=4); ax.set_ylabel(ylabel, fontsize=6.5)
        for sp in ('top', 'right'):
            ax.spines[sp].set_visible(False)
        ax.spines['left'].set_color('#b8b6ad'); ax.spines['bottom'].set_color('#b8b6ad'); ax.tick_params(length=2, color='#b8b6ad')

    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'], 'font.size': 7})
    fig = plt.figure(figsize=(7.2, 7.2))
    gs = fig.add_gridspec(2, 3, hspace=0.7, wspace=0.42, left=0.075, right=0.985, top=0.865, bottom=0.175)
    dec = [it for it in tell if it['role'] == 'decider']
    # A1 acts by level
    ax = fig.add_subplot(gs[0, 0]); dists = [ER.share([it for it in dec if it['level'] == lv], 'act', ACTS)[0] for lv in range(4)]
    stack(ax, dists, ['0', '1', '2', '3'], ACTS, ACT_COLOR, 'A1  The advised act, by level'); ax.set_xlabel("Other person's evidence level", fontsize=6.5, labelpad=2); ax.set_ylabel('Share of recommendations', fontsize=6.5)
    # A2 misled by level
    ax = fig.add_subplot(gs[0, 1]); notalready = [it for it in dec if it.get('misled') != 'already']
    lines(ax, notalready, lambda it: it.get('misled') == 'yes', 'A2  Share leaving the other person misled', 'Misled if the advice is followed'); ax.set_xlabel("Other person's evidence level", fontsize=6.5, labelpad=2)
    ax.legend(fontsize=5.4, frameon=False, loc='upper left', ncol=2, handlelength=1.3, columnspacing=0.7)
    # A3 acknowledged when misled, by assistant
    ax = fig.add_subplot(gs[0, 2]); vals = []
    for t in T:
        m, l, h = boot_mean([{'world': it['world'], 'v': float(it.get('acknowledged') == 'yes')} for it in tell if it['model'] == t and it.get('misled') == 'yes'], 'v'); vals.append((m or 0, l, h))
    ax.barh(range(len(T)), [v[0] for v in vals], color=[MODEL_COLOR[t] for t in T], height=0.62)
    for i, (m, l, h) in enumerate(vals):
        if l is not None:
            ax.plot([l, h], [i, i], color='#15191b', linewidth=0.9)
        ax.text(0.02, i, f'{100 * m:.0f}%', va='center', fontsize=6.3, color='white')
    ax.set_yticks(range(len(T))); ax.set_yticklabels([NAME[t] for t in T], fontsize=6.3); ax.invert_yaxis(); ax.set_xlim(0, 1); ax.set_xticks([0, 0.5, 1]); ax.set_xticklabels(['0', '50', '100%'], fontsize=6.5)
    ax.set_title('A3  When misleading, says so', fontsize=7.8, loc='left', pad=4)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    ax.spines['left'].set_color('#b8b6ad'); ax.spines['bottom'].set_color('#b8b6ad'); ax.tick_params(length=2, color='#b8b6ad')
    # B1 stance by level (the person who knows less)
    oth = [it for it in seek if it['role'] == 'other']
    coll = lambda it: 'truth' if it.get('stance') in ('states_truth', 'leans_truth') else 'cant' if it.get('stance') == 'cant_tell' else 'false' if it.get('stance') in ('leans_false', 'states_false') else 'none'
    for it in oth:
        it['_st'] = coll(it)
    ax = fig.add_subplot(gs[1, 0]); dists = [ER.share([it for it in oth if it['level'] == lv], '_st', ['truth', 'cant', 'false', 'none'])[0] for lv in range(4)]
    stack(ax, dists, ['0', '1', '2', '3'], ['truth', 'cant', 'false', 'none'], ST_COLOR, 'B1  What they are told, by level'); ax.set_xlabel("Their evidence level", fontsize=6.5, labelpad=2); ax.set_ylabel('Share of answers', fontsize=6.5)
    # B2 outcome by level
    ax = fig.add_subplot(gs[1, 1]); dists = [ER.share([it for it in oth if it['level'] == lv and it.get('outcome') != 'na'], 'outcome', ['truth', 'uncertain', 'false'])[0] for lv in range(4)]
    stack(ax, dists, ['0', '1', '2', '3'], ['truth', 'uncertain', 'false'], OUT_COLOR, 'B2  Where they end up, by level'); ax.set_xlabel("Their evidence level", fontsize=6.5, labelpad=2)
    # B3 outcome by assistant (all seeking questions)
    ax = fig.add_subplot(gs[1, 2]); dists = [ER.share([it for it in seek if it['model'] == t and it.get('outcome') != 'na'], 'outcome', ['truth', 'uncertain', 'false'])[0] for t in T]
    stack(ax, dists, [NAME[t].replace(' ', '\n', 1) for t in T], ['truth', 'uncertain', 'false'], OUT_COLOR, 'B3  Where they end up, by assistant'); ax.tick_params(axis='x', labelsize=5.6)
    fig.text(0.075, 0.955, 'A  The person holding the secret: the advised act is the same at every level, so its effect on the other person grows with the gap', fontsize=8.3, weight='bold')
    fig.text(0.075, 0.930, "A1: what they are advised to say. A2: share of that advice that would leave the other person believing something false or unable to understand their situation,", fontsize=6.0, color='#5b6367')
    fig.text(0.075, 0.913, "judged from the facts, excluding cases where they already know; band = 95% world bootstrap. A3: of the misleading advice, the share where the assistant says so.", fontsize=6.0, color='#5b6367')
    fig.text(0.075, 0.515, 'B  The person who knows less: mostly kept uncertain, and led to a false belief more often as their evidence thins', fontsize=8.3, weight='bold')
    fig.text(0.075, 0.49, "B1: what the assistant tells them about the hidden matter. B2, B3: where they most likely end up on it if they follow the advice and believe what it says (judged from the facts).", fontsize=6.0, color='#5b6367')
    h1 = [Patch(color=ACT_COLOR[k], label=ACT_LABEL[k]) for k in ACTS]; h2 = [Patch(color=ST_COLOR[k], label=ST_LABEL[k]) for k in ('truth', 'cant', 'false', 'none')]
    h3 = [Patch(color=OUT_COLOR[k], label=OUT_LABEL[k]) for k in ('truth', 'uncertain', 'false')]
    fig.legend(handles=h1, loc='lower center', ncol=6, frameon=False, fontsize=6.2, bbox_to_anchor=(0.5, 0.082), handlelength=1.2, columnspacing=1.0, title='A1, acts', title_fontsize=6.2)
    fig.legend(handles=h2, loc='lower center', ncol=4, frameon=False, fontsize=6.2, bbox_to_anchor=(0.5, 0.041), handlelength=1.2, columnspacing=1.0, title='B1, what they are told', title_fontsize=6.2)
    fig.legend(handles=h3, loc='lower center', ncol=3, frameon=False, fontsize=6.2, bbox_to_anchor=(0.5, 0.0), handlelength=1.2, columnspacing=1.0, title='B2, B3, where they end up', title_fontsize=6.2)
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ('pdf', 'png'):
        fig.savefig(out_dir / f'fig2_effect.{ext}', dpi=300)
    print('saved', out_dir / 'fig2_effect.pdf')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--out', default='figures'); ap.add_argument('--only', choices=['1', '2']); a = ap.parse_args()
    if a.only != '2':
        figure1(Path(a.run), Path(a.out))
    if a.only != '1':
        figure2(Path(a.run), Path(a.out))


if __name__ == '__main__':
    main()
