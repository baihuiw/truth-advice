#!/usr/bin/env python3
"""One conversation as a readable page: what the assistant saw before the first message, every turn (with the
assistant's reasoning folded away), the game master's unlocks, the post-conversation answers, and the judge's codes.

  python3 scripts/show_conv.py runs/<name>/conv/<file>.json [--out review/conv.html]
"""
import argparse, html, json
from pathlib import Path

E = html.escape


def page(rec, code):
    turns = ''; a = 0
    for m in rec['transcript']:
        if m['role'] == 'user':
            turns += f"<div class='msg user'><div class=who>{E(rec['party'].title())} (simulated user)</div>{E(m['content']).replace(chr(10), '<br>')}</div>"
        else:
            a += 1
            reasoning = f"<details><summary>reasoning</summary><pre>{E(m.get('reasoning') or '')}</pre></details>" if (m.get('reasoning') or '').strip() else ''
            turns += f"<div class='msg bot'><div class=who>{E(rec['target'])}, turn {a}</div>{E(m['content']).replace(chr(10), '<br>')}{reasoning}</div>"
    unl = ', '.join(f"{u['item']} after turn {u['after_assistant_turn']}" for u in rec.get('unlocks') or []) or 'none'
    post = ''.join(f"<p><b>{E(k)}:</b> {E(v)}</p>" for k, v in (rec.get('post') or {}).items())
    say = (code or {}).get('say') or {}
    codes = (f"<h2>Judge's codes</h2><pre>{E(json.dumps({k: say.get(k) for k in ('unknowable', 'blame', 'declined_picture', 'candour', 'advice', 'perspective', 'support_content')}, indent=1, ensure_ascii=False))}</pre>"
             f"<h3>Simulated-user check</h3><pre>{E(json.dumps((code or {}).get('fidelity'), indent=1, ensure_ascii=False))}</pre>") if code else ''
    css = ("body{margin:0;background:#fbfaf7;color:#1d1d1b;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}@media (prefers-color-scheme: dark){body{background:#151514;color:#ecebe6}.user{background:#1f2633!important}.bot{background:#232220!important}pre{background:#1c1b19!important}}"
           "main{max-width:860px;margin:0 auto;padding:24px 16px 64px}.msg{border-radius:10px;padding:12px 14px;margin:12px 0}.user{background:#eef3fb}.bot{background:#f3f1ea}.who{font-size:12px;opacity:.7;margin-bottom:4px}"
           "pre{white-space:pre-wrap;font-size:12px;background:#f3f1ea;padding:10px;border-radius:8px}summary{cursor:pointer;font-size:13px;opacity:.8}")
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width, initial-scale=1'><title>Conversation</title><style>{css}</style></head><body><main>"
            f"<h1>{E(rec['world'])}: {E(rec['party'])} with {E(rec['target'])}</h1><p>Condition: <b>{E(rec['condition'])}</b>, rep {rec['rep']}. Locked topics opened by the game master: {E(unl)}.</p>"
            f"<details><summary><b>What the assistant saw before the first message</b></summary><pre>{E(rec['system'])}</pre></details>{turns}<h2>After the conversation</h2>{post}{codes}</main></body></html>")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('conv'); ap.add_argument('--out'); a = ap.parse_args()
    p = Path(a.conv); rec = json.loads(p.read_text()); cp = p.parent.parent / 'code' / p.name
    code = json.loads(cp.read_text()) if cp.exists() else None
    if code is None and (p.parent.parent / 'code' / 'smoke_code.json').exists():
        code = json.loads((p.parent.parent / 'code' / 'smoke_code.json').read_text())
    out = Path(a.out or f'review/conv_{p.stem}.html'); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(page(rec, code)); print(out)


if __name__ == '__main__':
    main()
