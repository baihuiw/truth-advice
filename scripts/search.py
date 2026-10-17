#!/usr/bin/env python3
"""The world author loop (autoresearch over worlds; see ta/author.py): mutate / recombine / free moves.

  python3 scripts/search.py seed --run runs/<name> [--from runs/<pilot>]   # place finished worlds in the archive
  python3 scripts/search.py step --run runs/<name> --n 6 --batch 2         # author, gate, run, code, place children
  python3 scripts/search.py report --run runs/<name>

The run directory is prepared with scripts/run.py prepare (same approval rules). Children are saved under
runs/<name>/worlds/; their conversations and codes go in the same conv/ and code/ folders as the seeds."""
import argparse, concurrent.futures, json, random, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
from ta import world as W, gm as G, judge as J, metrics as MX, author as A
from ta.client import BudgetStop, CallFailed
import run as R

LOCK = threading.Lock()


def world_summary(run_dir, w):
    rs = [r for r in R.rows(run_dir, [w]) if r['world'] == w['id']]
    return MX.summary(w, rs), rs


def examples(run_dir, w, k=3):
    out = []
    for p in sorted((run_dir / 'code').glob(f"{w['id']}__own_view__*.json"))[:12]:
        c = R.read(p); say = (c or {}).get('say') or {}
        for u in say.get('unknowable', []):
            if u.get('strength') == 'fact':
                out.append(f"{p.stem.split('__')[3]} told {p.stem.split('__')[2]}: \"{u.get('quote', '')[:160]}\" ({u['id']} asserted as fact)")
    return out[:k]


def evaluate(client, cfg, run_dir, w, conditions, reps):
    sub = {**cfg, 'conditions': conditions, 'reps': reps}
    for job in G.jobs(w, sub):
        G.consult(client, cfg, run_dir, w, *job)
    for p in sorted((run_dir / 'conv').glob(f"{w['id']}__*.json")):
        cp = R.code_path(run_dir, p)
        if not cp.exists():
            c = J.code(client, cfg, w, R.read(p))
            if c and c.get('say'):
                R.save(cp, c)
    summ, _ = world_summary(run_dir, w)
    return summ, A.fitness(summ)


def log(run_dir, row):
    with LOCK:
        with open(run_dir / 'children.jsonl', 'a') as f:
            f.write(json.dumps(row) + '\n')


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('seed'); s.add_argument('--run', required=True); s.add_argument('--from', dest='src')
    st = sub.add_parser('step'); st.add_argument('--run', required=True); st.add_argument('--n', type=int, default=4); st.add_argument('--batch', type=int, default=2)
    rp = sub.add_parser('report'); rp.add_argument('--run', required=True)
    a = ap.parse_args(); run_dir = Path(a.run); archive = A.Archive(run_dir / 'archive.json')
    if a.cmd == 'report':
        print(json.dumps(archive.data['cells'], indent=1))
        kids = [json.loads(l) for l in (run_dir / 'children.jsonl').read_text().splitlines()] if (run_dir / 'children.jsonl').exists() else []
        for k in kids:
            print(json.dumps(k)[:240])
        return
    cfg = R.read(run_dir / 'config.json'); worlds = R.authorized(run_dir); client = R.client_for(run_dir, cfg)
    if a.cmd == 'seed':
        seed(client, cfg, run_dir, worlds, archive, Path(a.src) if a.src else run_dir)
    if a.cmd == 'step':
        step(client, cfg, run_dir, archive, a.n, a.batch)
        print(f'spent ${client.spent:.2f} of ${client.cap:.2f}')


def seed(client, cfg, run_dir, worlds, archive, src):
    sc = cfg.get('search', {}); out = []
    for w in worlds:
        summ, _ = world_summary(src, w); fit = A.fitness(summ)
        if fit is None:
            summ, fit = evaluate(client, cfg, run_dir, w, sc.get('screen_conditions', ['own_view']), sc.get('screen_reps', 1))
        R.save(run_dir / 'worlds' / f"{w['id']}.json", w); R.save(run_dir / 'summaries' / f"{w['id']}.json", summ)
        res = archive.consider(w['id'], A.cell(w), fit) if fit is not None else 'unscored'; out.append((w['id'], fit, res)); print(w['id'], A.cell(w), fit, res)
    return out


def summary_of(run_dir, wid):
    sp = run_dir / 'summaries' / f'{wid}.json'
    return R.read(sp) if sp.exists() else {}


def archive_digest(run_dir, archive, k=3):
    """What the archive's best worlds show, for free moves."""
    best = sorted(archive.data['cells'].values(), key=lambda v: -(v['fitness'] or 0))[:k]
    return '\n'.join(f"world {v['world']} (fitness {v['fitness']}):\n{A.digest(summary_of(run_dir, v['world']))}" for v in best) or '- nothing yet'


def step(client, cfg, run_dir, archive, n, batch, moves=None):
    """n new worlds in batches; each is a mutate, recombine or free move (config search.move_shares; `moves` forces a
    repeating sequence, used by the dry run)."""
    sc = cfg.get('search', {}); rows = []
    pool_worlds = {p.stem: R.read(p) for p in (run_dir / 'worlds').glob('*.json')}
    done = len((run_dir / 'children.jsonl').read_text().splitlines()) if (run_dir / 'children.jsonl').exists() else 0
    rng = random.Random(cfg.get('seed', 0) + done); weights = sc.get('operator_weights', {})
    example = next(iter(pool_worlds.values()))
    for b0 in range(0, n, batch):
        jobs = []
        for j in range(min(batch, n - b0)):
            parents = archive.parents(); k = done + b0 + j
            move = moves[k % len(moves)] if moves else A.choose_move(rng, sc.get('move_shares'), len(parents))
            if move == 'recombine' and len(parents) < 2:
                move = 'mutate'
            if move == 'mutate':
                parent = pool_worlds[rng.choice(parents)]; ops = list(A.OPERATORS)
                op = rng.choices(ops, weights=[float(weights.get(o, 1.0)) for o in ops], k=1)[0]
                jobs.append({'move': move, 'id': f'w{k:03d}_{op}', 'parents': [parent], 'op': op})
            elif move == 'recombine':
                a_id, b_id = rng.sample(parents, 2)
                jobs.append({'move': move, 'id': f'w{k:03d}_recombine', 'parents': [pool_worlds[a_id], pool_worlds[b_id]]})
            else:
                jobs.append({'move': move, 'id': f'w{k:03d}_free', 'parents': [], 'design': A.target_design(rng, archive), 'templates': rng.sample(A.TEMPLATES, 2)})

        def go(job):
            cid = job['id']; row = {'id': cid, 'move': job['move'], 'parents': [w['id'] for w in job['parents']], 'op': job.get('op')}
            try:
                if job['move'] == 'mutate':
                    par = job['parents'][0]; child = A.write_child(client, cfg, par, job['op'], cid, A.digest(summary_of(run_dir, par['id']), examples(run_dir, par)))
                elif job['move'] == 'recombine':
                    a_, b_ = job['parents']
                    child = A.recombine(client, cfg, a_, b_, cid, A.digest(summary_of(run_dir, a_['id'])), A.digest(summary_of(run_dir, b_['id'])))
                else:
                    child = A.free(client, cfg, job['design'], job['templates'], cid, example, archive_digest(run_dir, archive)); row['design_target'] = job['design']
                if not child:
                    row.update(status='rejected', gate='author'); return row
                ok, gate, why, det = A.gates(client, cfg, child)
                if not ok:
                    R.save(run_dir / 'rejected' / f'{cid}.json', {'world': child, 'gate': gate, 'reason': why}); row.update(status='rejected', gate=gate, reason=why); return row
                R.save(run_dir / 'worlds' / f'{cid}.json', child)
                summ, fit = evaluate(client, cfg, run_dir, child, sc.get('screen_conditions', ['own_view']), sc.get('screen_reps', 1))
                R.save(run_dir / 'summaries' / f'{cid}.json', summ)
                row.update(status='evaluated', cell=A.cell(child), fitness=fit, attributable=child['search']['attributable'], hypothesis=str(child.get('hypothesis', ''))[:200],
                           archive=archive.consider(cid, A.cell(child), fit) if fit is not None else 'unscored')
            except BudgetStop as ex:
                row.update(status='budget_stop', reason=str(ex)[:200])
            except CallFailed as ex:
                row.update(status='call_failed', reason=str(ex)[:200])
            return row
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch) as ex:
            for row in ex.map(go, jobs):
                log(run_dir, row); rows.append(row); print(json.dumps(row)[:300], flush=True)
        pool_worlds = {p.stem: R.read(p) for p in (run_dir / 'worlds').glob('*.json')}
        if any(r['status'] == 'budget_stop' for r in rows):
            break
    return rows


if __name__ == '__main__':
    main()
