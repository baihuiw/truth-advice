#!/usr/bin/env python3
"""Two worked examples as one page: a world (its people, settled facts with who knows them, what nobody can settle, and each
person's opening and questions at the level shown) followed by one real conversation from the run. No commentary.

  python3 scripts/examples_page.py --run runs/pilot3b_20261019 --out examples.html --cases c17_L1__own_view__thandeka__sonnet55__r0 c66_L1__own_view__anan__gemini38__r0
"""
import argparse, csv, html, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as RUN, conversation_page as CP
from ta import world as W

E = html.escape
MODEL = CP.MODEL


def who_knows(s, w):
    out = []
    for n, v in (s.get('known_by') or {}).items():
        name = W.party_of(w, n)['profile']['name'] if (n in w['parties'] or n == 'neutral') else n
        out.append(E(name) + (' <span class="partial">(partly)</span>' if str(v).startswith('partial') else ''))
    return ', '.join(out) or 'nobody'


def world_html(w, titles):
    base = w.get('ladder_of', w['id']); lad = w.get('ladder_roles') or {}
    people = ''.join(f'<li>{E(x)}</li>' for x in w.get('people') or [])
    facts = ''.join(f'<tr><td class="id">{E(s["id"])}</td><td>{E(s["fact"])}</td><td class="kb">{who_knows(s, w)}</td></tr>' for s in w['settled'])
    unk = ''.join(f'<li><b>{E(u["id"])}</b> {E(u["question"])}' + (('<ul>' + ''.join(f'<li>{E(k)}: {E(v)}</li>' for k, v in (u.get("readings") or {}).items()) + '</ul>') if u.get('readings') else '') + '</li>' for u in w.get('unknowable') or [])
    parties = ''
    for n, p in w['parties'].items():
        if p.get('relay_of'):
            continue
        pr = p['profile']; role = ' · holds the secret' if n == lad.get('decider') else ' · knows less' if n == lad.get('other') else ''
        qs = ''.join(f'<li>{E(q["text"])}</li>' for q in p.get('truth_questions') or [])
        parties += (f'<div class="party"><h4>{E(pr["name"])}<span class="role">{E(pr.get("occupation", ""))}{E(role)}</span></h4>'
                    f'<p class="opening">“{E(p.get("opening_message", ""))}”</p><ol class="qs">{qs}</ol></div>')
    level = f' · ladder level {w["ladder_level"]}: {E(lad.get("label", ""))}' if lad else ''
    return (f'<section class="world"><h2><span class="wid">{E(base)}</span> {E(titles.get(base, base))}{level}</h2>'
            f'<div class="grid"><div><h3>People and places</h3><ul class="people">{people}</ul></div>'
            f'<div><h3>What nobody in the world can settle</h3><ul class="unk">{unk or "<li>none</li>"}</ul></div></div>'
            f'<h3>Settled facts and who knows them</h3><div class="scroll"><table><thead><tr><th></th><th>Fact</th><th>Known by</th></tr></thead><tbody>{facts}</tbody></table></div>'
            f'<h3>Each person\'s opening message and questions at this level</h3><div class="parties">{parties}</div></section>')


def conv_html(w, rec):
    who = W.party_of(w, rec['asker'])['profile']['name']
    msgs = ''.join((f'<div class="msg person"><span class="who">{E(who)}</span><div class="body">{E(m["content"]).replace(chr(10), "<br>")}</div></div>' if m['role'] == 'user'
                    else f'<div class="msg assistant"><span class="who">{E(MODEL.get(rec["target"], rec["target"]))}</span><div class="body">{CP.md(m["content"])}</div></div>') for m in rec['transcript'])
    return f'<section class="conv"><h3>{E(who)} and {E(MODEL.get(rec["target"], rec["target"]))}</h3><div class="thread">{msgs}</div></section>'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--out', required=True); ap.add_argument('--cases', nargs='+', required=True); a = ap.parse_args()
    run_dir = Path(a.run); worlds = {w['id']: w for w in RUN.read(run_dir / 'worlds.json')}
    titles = {r['id']: r['title'] for r in csv.DictReader(open(ROOT / 'cases' / 'index.csv'))}
    body = ''
    for stem in a.cases:
        rec = RUN.read(run_dir / 'conv' / f'{stem}.json'); w = worlds[rec['world']]
        ww = W.relayed(w, rec['party']) if rec['condition'] == 'relayed' else w
        body += world_html(w, titles) + conv_html(ww, rec)
    page = f"""<title>Two Worlds, Two Conversations</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&family=IBM+Plex+Sans:wght@400;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap">
<style>
:root{{--bg:#f4f6f5;--surface:#ffffff;--fg:#16191b;--muted:#5b6367;--line:#dbe1df;--accent:#2a78d6;--person:#eef2f7;--display:"Source Serif 4",Georgia,serif;--body:"IBM Plex Sans",system-ui,sans-serif;--data:"IBM Plex Mono",ui-monospace,Menlo,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#101416;--surface:#171c1f;--fg:#e7ecec;--muted:#9aa4a8;--line:#2a3136;--accent:#5a9be8;--person:#1d2730;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#101416;--surface:#171c1f;--fg:#e7ecec;--muted:#9aa4a8;--line:#2a3136;--accent:#5a9be8;--person:#1d2730;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:15px/1.55 var(--body);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
main{{max-width:900px;margin:0 auto;padding-block:32px 72px;display:grid;gap:40px}}
h2,h3,h4{{font-family:var(--display);font-weight:600;line-height:1.2;margin:0}} h2{{font-size:1.45rem}} h3{{font-size:1.05rem;margin-top:18px;margin-bottom:8px}} h4{{font-size:.98rem}}
.wid{{font:500 .8rem var(--data);color:var(--muted);margin-right:6px}} .role{{font:400 .8rem var(--body);color:var(--muted);margin-left:8px}}
.world{{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:18px 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:0 24px}}
ul.people,ul.unk{{margin:0;padding-left:1.1rem;font-size:.9rem}} ul.unk ul{{padding-left:1rem;color:var(--muted);font-size:.85rem}}
.scroll{{overflow-x:auto}} table{{border-collapse:collapse;font-size:.88rem;width:100%}} th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}
thead th{{font:600 .72rem var(--data);letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}} td.id{{font:500 .8rem var(--data);color:var(--muted);white-space:nowrap}} td.kb{{font-size:.82rem;color:var(--muted);min-width:9rem}} .partial{{color:var(--muted)}}
.parties{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:14px}} .party{{border:1px solid var(--line);border-radius:6px;padding:10px 12px;min-width:0}}
.opening{{font-size:.88rem;margin:6px 0;color:var(--fg)}} ol.qs{{margin:0;padding-left:1.1rem;font-size:.84rem;color:var(--muted)}}
.conv{{display:grid;gap:8px}} .thread{{display:grid;gap:10px}} .msg{{display:grid;gap:3px;min-width:0}} .msg .who{{font:500 .74rem var(--data);color:var(--muted)}}
.msg .body{{border-radius:8px;padding:9px 12px;overflow-wrap:anywhere}} .person .body{{background:var(--person)}} .assistant .body{{background:var(--surface);border:1px solid var(--line)}}
.body p{{margin:0 0 8px}} .body p:last-child{{margin-bottom:0}} .body ul,.body ol{{margin:0 0 8px;padding-left:1.2rem}} .body p.h{{font-weight:600}} .body blockquote{{margin:0 0 8px;padding-left:10px;border-left:3px solid var(--line);color:var(--muted)}}
</style>
<main>{body}</main>
"""
    Path(a.out).write_text(page, encoding='utf-8'); print(a.out, len(page), 'chars')


if __name__ == '__main__':
    main()
