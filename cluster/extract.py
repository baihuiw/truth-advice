#!/usr/bin/env python3
"""Replay conversations (and contrast items) through an open-weight model by teacher forcing and save mean residual-
stream activations, at a set of layers, for three kinds of span:

  boundary  the end of each user message plus the assistant header that follows it: the model's state just before it
            replies (what it represents about the situation when it starts to answer)
  reply     each assistant reply
  quote     sentences of a reply that the judge quoted (with the judge's label)

Items (one JSON per line): {"id", "kind": "conversation"|"contrast", "messages": [...], "labels": {...},
"quotes": [{"turn": n, "text": "...", "label": "..."}]}. Assistant messages may carry "reasoning", which the chat
template renders before the reply. Output: <out>/<kind>.npy (float16, [n_spans, n_layers, d]) and <out>/<kind>.rows.jsonl.

  python cluster/extract.py --items items.jsonl --model Qwen/Qwen3-32B --out <dir> [--layers 8,12,...]
"""
import argparse, json, time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def render(tok, messages, add_generation_prompt=False):
    msgs = []
    for m in messages:
        x = {'role': m['role'], 'content': m['content']}
        if m['role'] == 'assistant' and m.get('reasoning'):
            x['reasoning_content'] = m['reasoning']
        msgs.append(x)
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=add_generation_prompt)


def spans(full, messages, add_generation_prompt):
    """Character spans of every message's content in the rendered text, in order."""
    out, pos = [], 0
    for i, m in enumerate(messages):
        core = (m['content'] or '').strip()
        j = full.find(core, pos) if core else -1
        out.append((j, j + len(core)) if j >= 0 else None)
        if j >= 0:
            pos = j + len(core)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--items', required=True); ap.add_argument('--model', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--layers', default='8,12,16,20,24,28,32,36,40,44,48,52,56,60'); ap.add_argument('--tail', type=int, default=8); ap.add_argument('--max-tokens', type=int, default=24000)
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True); layers = [int(x) for x in a.layers.split(',')]
    items = [json.loads(l) for l in open(a.items)]
    tok = AutoTokenizer.from_pretrained(a.model); model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16).to('cuda'); model.eval()
    layers = [l for l in layers if 1 <= l < model.config.num_hidden_layers]
    # Capture only the probed layers with forward hooks (hidden_states[l] is the output of decoder layer l-1) and run the
    # base model without the LM head: all 65 hidden states plus 150k-vocab logits for a 12k-token conversation do not fit
    # next to Qwen3-32B's 64 GB of weights on one 80 GB card.
    captured = {}

    def hook(l):
        def f(_mod, _inp, output):
            captured[l] = (output[0] if isinstance(output, tuple) else output)[0].detach()
        return f
    handles = [model.model.layers[l - 1].register_forward_hook(hook(l)) for l in layers]
    acts, rows, skipped, t0 = defaultdict(list), defaultdict(list), defaultdict(int), time.time()
    for n, it in enumerate(items):
        gen = it['kind'] == 'contrast'; msgs = it['messages']
        full = render(tok, msgs, add_generation_prompt=gen); sp = spans(full, msgs, gen)
        enc = tok(full, return_offsets_mapping=True, add_special_tokens=False); ids, offs = enc['input_ids'], enc['offset_mapping']
        if len(ids) > a.max_tokens:
            skipped['too long'] += 1; continue
        captured.clear()
        with torch.no_grad():
            model.model(input_ids=torch.tensor([ids], device='cuda'), use_cache=False)
        H = torch.stack([captured[l] for l in layers])

        def toks(lo, hi):
            return [i for i, (s, e) in enumerate(offs) if e > s and e > lo and s < hi]

        def keep(idx, row):
            if idx:
                acts[it['kind']].append(H[:, idx, :].float().mean(dim=1).to(torch.float16).cpu().numpy())
                rows[it['kind']].append({'id': it['id'], **(it.get('labels') or {}), **row, 'n_tokens': len(idx)})
            else:
                skipped['empty span'] += 1
        a_turn = 0
        for i, m in enumerate(msgs):
            if sp[i] is None:
                continue
            if m['role'] == 'user':
                nxt = next((sp[k][0] for k in range(i + 1, len(msgs)) if sp[k] is not None), len(full)) if not gen else len(full)
                tail = toks(sp[i][0], sp[i][1])[-a.tail:]
                keep(tail + toks(sp[i][1], nxt), {'span': 'boundary', 'before_turn': a_turn + 1})
            elif m['role'] == 'assistant':
                a_turn += 1; keep(toks(*sp[i]), {'span': 'reply', 'turn': a_turn})
                for q in [q for q in it.get('quotes', []) if q.get('turn') == a_turn]:
                    j = full.find(q['text'].strip(), sp[i][0], sp[i][1] + 1)
                    if j >= 0:
                        keep(toks(j, j + len(q['text'].strip())), {'span': 'quote', 'turn': a_turn, 'label': q.get('label')})
        if n % 25 == 0:
            print(f'{n}/{len(items)} items, {time.time() - t0:.0f}s, last {len(ids)} tokens', flush=True)
    for kind, xs in acts.items():
        np.save(out / f'{kind}.npy', np.stack(xs))
        with open(out / f'{kind}.rows.jsonl', 'w') as f:
            for r in rows[kind]:
                f.write(json.dumps(r) + '\n')
        print(f'{kind}: {len(xs)} spans', flush=True)
    for h in handles:
        h.remove()
    json.dump({'layers': layers, 'model': a.model, 'skipped': dict(skipped)}, open(out / 'meta.json', 'w')); print('skipped', dict(skipped), f'{time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
