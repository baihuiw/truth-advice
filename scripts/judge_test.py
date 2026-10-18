#!/usr/bin/env python3
"""Re-code a run's conversations (the reply coding only) with another judge reached at an OpenAI-compatible endpoint,
for example a model served on the cluster, into code_alt_<alias>/; scripts/judge_agreement.py then compares it with the
main judge. A self-hosted judge costs nothing; the run's ledger records zero-cost calls.

  python3 scripts/judge_test.py --run runs/<name> --alias gptoss --url http://127.0.0.1:8001/v1/chat/completions --model openai/gpt-oss-120b
"""
import argparse, concurrent.futures, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
from ta import judge as J
from ta.client import Client, CallFailed
import run as R


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--alias', required=True); ap.add_argument('--url', required=True); ap.add_argument('--model', required=True)
    ap.add_argument('--workers', type=int, default=8); a = ap.parse_args(); run_dir = Path(a.run)
    cfg = R.read(run_dir / 'config.json'); worlds = {w['id']: w for w in R.read(run_dir / 'worlds.json')}
    cfg = {**cfg, 'endpoints': {**(cfg.get('endpoints') or {}), a.alias: {'url': a.url, 'model': a.model}}}
    client = Client(run_dir, cfg, R.read(run_dir / 'catalog.json'), routes=R.read(run_dir / 'routes.json') if (run_dir / 'routes.json').exists() else None)
    out_dir = run_dir / f'code_alt_{a.alias}'; out_dir.mkdir(exist_ok=True)

    def one(p):
        if (out_dir / p.name).exists():
            return
        rec = R.read(p)
        if rec['target'] == a.alias:
            return                                           # never let a model judge its own conversations
        try:
            c = J.code_say(client, cfg, worlds[rec['world']], rec, a.alias)
        except CallFailed:
            return
        if c and c.get('say'):
            R.save(out_dir / p.name, c)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        list(pool.map(one, sorted((run_dir / 'conv').glob('*.json'))))
    print(f"coded with {a.alias}: {len(list(out_dir.glob('*.json')))}")


if __name__ == '__main__':
    main()
