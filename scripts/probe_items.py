#!/usr/bin/env python3
"""Items for the cluster replay (cluster/extract.py): every conversation of a run (with the assistant's reasoning and
the judge's quotes), plus a contrast set if given.

  python3 scripts/probe_items.py --run runs/<name> [--targets qwen32] [--contrast runs/<name>/contrast.jsonl] --out items.jsonl
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def conversation_items(run_dir, targets=None):
    out = []
    for p in sorted((run_dir / 'conv').glob('*.json')):
        rec = json.loads(p.read_text())
        if targets and rec['target'] not in targets:
            continue
        code = json.loads((run_dir / 'code' / p.name).read_text()) if (run_dir / 'code' / p.name).exists() else {}
        say = code.get('say') or {}
        quotes = [{'turn': u['turn'], 'text': u['quote'], 'label': f"{u['id']}:{u['strength']}:{u['leans']}"} for u in say.get('unknowable', []) if u.get('quote') and isinstance(u.get('turn'), int)]
        quotes += [{'turn': c['turn'], 'text': c['quote'], 'label': f"{c['id']}:raised"} for c in say.get('candour', []) if c.get('raised') and c.get('quote') and isinstance(c.get('turn'), int)]
        msgs = [{'role': 'system', 'content': rec['system']}] + [{k: v for k, v in m.items() if k in ('role', 'content', 'reasoning')} for m in rec['transcript']]
        out.append({'id': p.stem, 'kind': 'conversation', 'messages': msgs, 'quotes': quotes,
                    'labels': {k: rec[k] for k in ('world', 'condition', 'party', 'target', 'rep')}})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--targets', nargs='*'); ap.add_argument('--contrast'); ap.add_argument('--out', required=True)
    a = ap.parse_args(); items = conversation_items(Path(a.run), a.targets)
    if a.contrast:
        items += [json.loads(l) for l in open(a.contrast)]
    with open(a.out, 'w') as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + '\n')
    print(f'{len(items)} items -> {a.out}')


if __name__ == '__main__':
    main()
