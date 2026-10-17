#!/usr/bin/env python3
"""A readable page for reviewing a world: the settled facts with who knows what, the permanently unknowable, each
party as the simulator will play them, and what the target assistant sees.

  python3 scripts/review_world.py worlds/elena.json [--twin] [--out review/elena.html]
"""
import argparse, html, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ta import world as W, gm as G

E = html.escape


def page(w):
    parties = list(w['parties'])
    rows = ''.join(f"<tr><td>{E(s['id'])}</td><td>{E(s['date'])}</td><td>{E(s['fact'])}</td>" + ''.join(f"<td class=k>{E(s.get('known_by', {}).get(p, '-'))}</td>" for p in parties) + '</tr>' for s in w['settled'])
    unk = ''.join(f"<tr><td>{E(u['id'])}</td><td>{E(u['question'])}</td><td>{E('; '.join(u['evidence_for']))}</td><td>{E('; '.join(u['evidence_against']))}</td><td class=k>{E(u['permanent'])}</td></tr>" for u in w['unknowable'])
    cards = ''
    for p in parties + ['neutral']:
        q = w['neutral_friend'] if p == 'neutral' else w['parties'][p]
        policy = ''.join(f"<li>{E(r['topic'])}: {E(r['when'])}</li>" for r in q.get('reveal_policy', []))
        questions = ''.join(f"<li>{E(str(x['after_turn']))}: {E(x['text'])}</li>" for x in q.get('truth_questions', []))
        system = G.target_system(w, p, 'memory_knows' if q.get('memory_knows_extra') else 'own_view', 0)
        cards += (f"<section class=card><h3>{E(q['profile']['name'])} <span class=k>({E(p)})</span></h3><p class=k>{E(str(q['profile']))}</p>"
                  f"<p><b>Opening message</b></p><blockquote>{E(q.get('opening_message', ''))}</blockquote><p><b>Framing.</b> {E(q.get('framing', ''))}</p>"
                  f"<p><b>Reveal policy</b></p><ul>{policy}</ul><p><b>Truth questions</b></p><ul>{questions}</ul>"
                  f"<p><b>What the assistant sees (system prompt)</b></p><pre>{E(system)}</pre></section>")
    css = ("body{margin:0;background:#fbfaf7;color:#1d1d1b;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}@media (prefers-color-scheme: dark){body{background:#151514;color:#ecebe6}th,td,.card{border-color:#34332f}.k{color:#a3a19a}}"
           "main{max-width:1150px;margin:0 auto;padding:28px 16px 64px}.k{color:#6b6a65;font-size:13px}table{border-collapse:collapse;width:100%;font-size:13px;display:block;overflow-x:auto}"
           "th,td{border:1px solid #e4e1d8;padding:6px;text-align:left;vertical-align:top}.card{border:1px solid #e4e1d8;border-radius:10px;padding:12px 16px;margin:16px 0}pre{white-space:pre-wrap;font-size:12px}blockquote{margin:0 0 8px;padding-left:12px;border-left:3px solid #c9c4b8}")
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width, initial-scale=1'><title>World Review</title><style>{css}</style></head><body><main>"
            f"<h1>World: {E(w['id'])}</h1><p class=k>{E(w.get('note', ''))}</p><h2>Settled facts and who knows them</h2><table><tr><th>id</th><th>date</th><th>fact</th>{''.join(f'<th>{E(p)}</th>' for p in parties)}</tr>{rows}</table>"
            f"<h2>Permanently unknowable</h2><table><tr><th>id</th><th>question</th><th>evidence one way</th><th>evidence the other</th><th>why never settled</th></tr>{unk}</table><h2>Parties</h2>{cards}</main></body></html>")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('world'); ap.add_argument('--twin', action='store_true'); ap.add_argument('--out')
    a = ap.parse_args(); w = W.load(a.world); w = W.twin(w) if a.twin else w
    out = a.out or str(ROOT / 'review' / f"{w['id']}.html"); Path(out).parent.mkdir(parents=True, exist_ok=True); Path(out).write_text(page(w)); print(out)


if __name__ == '__main__':
    main()
