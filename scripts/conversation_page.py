#!/usr/bin/env python3
"""A reading page for a set of conversations in a run: each conversation in full (the simulated person's messages and the
assistant's replies), grouped by world, with the simulator check's verdict, the guard's send-backs and how the judge coded
the advice. Filters for verdict, world and kind. Nothing is billed.

  python3 scripts/conversation_page.py --run runs/pilot3b_20261019 --jobs runs/pilot3b_20261019/smoke_jobs.json --out page.html
"""
import argparse, csv, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import run as RUN
from ta import world as W, judge as J

E = html.escape
MODEL = {'sonnet55': 'Claude Sonnet 5.5', 'gpt61': 'GPT-6.1 Sol', 'gemini38': 'Gemini 3.8 Flash', 'deepseek4p': 'DeepSeek V4 Pro', 'glm53': 'GLM-5.3'}
LEVEL = {0: 'Level 0: they know the key fact', 1: 'Level 1: strong lead', 2: 'Level 2: weak lead', 3: 'Level 3: no lead'}


def md(text):
    """A small Markdown subset for assistant replies: paragraphs, bold, italics, bullet and numbered lists, quotes, headings."""
    out, lst = [], None
    inline = lambda s: re.sub(r'(?<!\*)\*(?!\s)([^*]+?)\*(?!\*)', r'<em>\1</em>', re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', E(s)))
    for line in (text or '').split('\n'):
        s = line.rstrip(); m_ul = re.match(r'^\s*[-*•]\s+(.*)', s); m_ol = re.match(r'^\s*\d+[.)]\s+(.*)', s)
        kind = 'ul' if m_ul else 'ol' if m_ol else None
        if lst and kind != lst:
            out.append(f'</{lst}>'); lst = None
        if kind:
            if not lst:
                out.append(f'<{kind}>'); lst = kind
            out.append(f'<li>{inline((m_ul or m_ol).group(1))}</li>')
        elif s.startswith('>'):
            out.append(f'<blockquote>{inline(s.lstrip("> "))}</blockquote>')
        elif re.match(r'^#{1,4}\s', s):
            head = re.sub(r'^#+\s*', '', s)
            out.append(f'<p class="h">{inline(head)}</p>')
        elif s.strip():
            out.append(f'<p>{inline(s)}</p>')
    if lst:
        out.append(f'</{lst}>')
    return ''.join(out)


def verdict(fid):
    mat = [x for x in fid.get('invented') or [] if not isinstance(x, dict) or x.get('material', True)]
    tags = (['leak'] if fid.get('leaked') else []) + (['invented'] if mat else []) + (['repeat'] if fid.get('repeated') else [])
    return tags, [x.get('detail', x) if isinstance(x, dict) else x for x in mat]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', required=True); ap.add_argument('--jobs', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--title', default='Smoke Conversations'); ap.add_argument('--lede', default=''); ap.add_argument('--eyebrow', default='Truth-advice study · pilot 3b smoke check')
    a = ap.parse_args(); run_dir = Path(a.run)
    worlds = {w['id']: w for w in RUN.read(run_dir / 'worlds.json')}
    titles = {r['id']: r['title'] for r in csv.DictReader(open(ROOT / 'cases' / 'index.csv'))}
    rep = RUN.read(run_dir / 'smoke_report.json') if (run_dir / 'smoke_report.json').exists() else {}
    cards, by_world = [], {}
    for wid, cond, party, target, r in RUN.read(Path(a.jobs)):
        stem = f'{wid}__{cond}__{party}__{target}__r{r}'; cp = run_dir / 'conv' / f'{stem}.json'
        if not cp.exists():
            continue
        rec = RUN.read(cp); code = RUN.read(run_dir / 'code' / f'{stem}.json') if (run_dir / 'code' / f'{stem}.json').exists() else {}
        w = worlds[wid]; base = w.get('ladder_of', wid); roles = (worlds[base].get('ladder') or {})
        who = W.party_of(w, rec['asker'])['profile']['name']; subj = W.party_of(w, party)['profile']['name']
        role = 'holds the secret' if party == roles.get('decider') else 'knows less' if party == roles.get('other') else 'another person'
        where = LEVEL.get(w.get('ladder_level')) if w.get('ladder_roles') else ('Relayed by a friend' if cond == 'relayed' else 'Base world, own view')
        kind = 'ladder' if w.get('ladder_roles') else 'relayed' if cond == 'relayed' else 'base'
        tags, inv = verdict(code.get('fidelity') or {})
        say = J.norm_code(code['say']) if code.get('say') else {}
        advice = '; '.join(f"{x.get('recommendation')}" + (f" ({x['choice']})" if x.get('choice') and x['choice'] != 'none' else '') for x in say.get('advice') or [])
        extra = '; '.join(f'{k.replace("_", " ")}: ' + ', '.join(str(v.get('verdict') or v.get('recommendation')) for v in say.get(k) or []) for k in ('honesty_judgment', 'suspicion', 'confront') if say.get(k))
        guard = rec.get('guard') or []
        br = lambda t: E(t).replace(chr(10), '<br>')
        msgs = ''.join((f'<div class="msg person"><span class="who">{E(who)}</span><div class="body">{br(m["content"])}</div></div>' if m['role'] == 'user'
                        else f'<div class="msg assistant"><span class="who">{E(MODEL.get(target, target))}</span><div class="body">{md(m["content"])}</div></div>') for m in rec['transcript'])
        chips = ''.join(f'<span class="chip {t}">{t}</span>' for t in tags) or '<span class="chip clean">clean</span>'
        notes = ''
        if inv:
            notes += f'<p class="note"><b>Invented:</b> {E("; ".join(map(str, inv)))}</p>'
        if (code.get('fidelity') or {}).get('leaked'):
            notes += f'<p class="note"><b>Stated a fact they should not know:</b> {E(", ".join(map(str, code["fidelity"]["leaked"])))}</p>'
        if (code.get('fidelity') or {}).get('reason'):
            notes += f'<p class="note"><b>Check:</b> {E(code["fidelity"]["reason"])}</p>'
        if guard:
            notes += '<p class="note"><b>Guard sent back:</b> ' + E('; '.join(f"message {g['turn']} ({g['kind'].replace('_', ' ')}: {g['detail'][:120]})" for g in guard)) + '</p>'
        if advice or extra:
            notes += f'<p class="note"><b>Coded:</b> {E(advice)}{"; " if advice and extra else ""}{E(extra)}</p>'
        label = f"{subj} ({role})" + (f", told by {who}" if cond == 'relayed' else '')
        cards.append((base, f'<details class="conv" data-world="{E(base)}" data-kind="{kind}" data-flag="{"flagged" if set(tags) & {"leak", "invented"} else "clean"}">'
                            f'<summary><span class="where">{E(where)}</span><span class="label">{E(label)}</span>{chips}<span class="turns">{sum(m["role"] == "user" for m in rec["transcript"])} messages</span></summary>'
                            f'<div class="notes">{notes}</div><div class="thread">{msgs}</div></details>'))
        by_world.setdefault(base, 0); by_world[base] += 1
    order = sorted(by_world)
    sections = ''.join(f'<section class="world" data-world="{E(b)}"><h2><span class="wid">{E(b)}</span> {E(titles.get(b, b))}</h2>'
                       + ''.join(c for wb, c in cards if wb == b) + '</section>' for b in order)
    now = rep.get('now') or {}; before = rep.get('before') or {}
    pct = lambda v: '–' if v is None else f'{int(100 * v + 0.5)}%'
    stats = (f'<div class="stats"><div><b>{now.get("n", len(cards))}</b><span>conversations</span></div><div><b>{pct(now.get("clean"))}</b><span>clean (no leak, no invented fact)</span></div>'
             f'<div><b>{pct(now.get("leak"))}</b><span>stated a fact they should not know</span></div><div><b>{pct(now.get("material"))}</b><span>invented a material fact</span></div>'
             f'<div><b>{pct(now.get("repeat"))}</b><span>repeated a message</span></div></div>'
             + (f'<p class="meta">Same cells in pilot 3: clean {pct(before.get("clean"))}, leaks {pct(before.get("leak"))}, invented {pct(before.get("material"))}, repeats {pct(before.get("repeat"))}.</p>' if before else ''))
    opts = ''.join(f'<option value="{E(b)}">{E(b)} {E(titles.get(b, b))}</option>' for b in order)
    page = f"""<title>{E(a.title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&family=IBM+Plex+Sans:wght@400;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap">
<style>
/* Layout: a reading column of conversation threads, grouped by world; filters on top. */
:root{{--bg:#f4f6f5;--surface:#ffffff;--fg:#16191b;--muted:#5b6367;--line:#dbe1df;--accent:#2a78d6;--person:#eef2f7;--warn:#a8431c;--ok:#1f7a4d;
--display:"Source Serif 4",Georgia,serif;--body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--data:"IBM Plex Mono",ui-monospace,Menlo,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#101416;--surface:#171c1f;--fg:#e7ecec;--muted:#9aa4a8;--line:#2a3136;--accent:#5a9be8;--person:#1d2730;--warn:#ec835a;--ok:#4cc38a;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#101416;--surface:#171c1f;--fg:#e7ecec;--muted:#9aa4a8;--line:#2a3136;--accent:#5a9be8;--person:#1d2730;--warn:#ec835a;--ok:#4cc38a;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:15px/1.55 var(--body);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
main{{max-width:880px;margin:0 auto;padding-block:36px 72px;display:grid;gap:26px}}
h1,h2{{font-family:var(--display);font-weight:600;line-height:1.2;margin:0;text-wrap:balance}} h1{{font-size:2rem}} h2{{font-size:1.25rem;margin-bottom:10px}}
.lede{{color:var(--muted);max-width:68ch;margin:6px 0 0}} .meta{{color:var(--muted);font-size:.88rem;margin:0}}
.stats{{display:flex;flex-wrap:wrap;gap:10px 26px;margin-top:10px}} .stats div{{display:grid}} .stats b{{font:600 1.4rem var(--data)}} .stats span{{font-size:.8rem;color:var(--muted)}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;position:sticky;top:env(safe-area-inset-top,0px);background:var(--bg);padding-block:8px;z-index:2}}
.filters button,.filters select{{font:500 .84rem var(--body);border:1px solid var(--line);background:var(--surface);color:var(--fg);border-radius:6px;padding:6px 10px;cursor:pointer}}
.filters button[aria-pressed="true"]{{border-color:var(--accent);color:var(--accent);font-weight:600}}
.filters button:focus-visible,.filters select:focus-visible,summary:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.wid{{font:500 .8rem var(--data);color:var(--muted);margin-right:4px}}
.world{{display:grid;gap:8px}}
details.conv{{background:var(--surface);border:1px solid var(--line);border-radius:8px}}
details.conv summary{{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;padding:10px 12px;cursor:pointer;list-style:none}}
details.conv summary::-webkit-details-marker{{display:none}}
details.conv summary::before{{content:"▸";color:var(--muted);font-size:.8rem}} details.conv[open] summary::before{{content:"▾"}}
.where{{font:500 .76rem var(--data);color:var(--muted)}} .label{{font-weight:600}} .turns{{margin-left:auto;font-size:.8rem;color:var(--muted)}}
.chip{{font:600 .7rem var(--data);text-transform:uppercase;letter-spacing:.05em;border-radius:999px;padding:2px 8px;border:1px solid currentColor}}
.chip.clean{{color:var(--ok)}} .chip.invented,.chip.leak{{color:var(--warn)}} .chip.repeat{{color:var(--muted)}}
.notes{{padding:0 14px}} .note{{font-size:.84rem;color:var(--muted);margin:4px 0}} .note b{{color:var(--fg)}}
.thread{{display:grid;gap:10px;padding:10px 14px 16px}}
.msg{{display:grid;gap:3px;min-width:0}} .msg .who{{font:500 .74rem var(--data);color:var(--muted)}}
.msg .body{{border-radius:8px;padding:9px 12px;overflow-wrap:anywhere}}
.person .body{{background:var(--person)}} .assistant .body{{border:1px solid var(--line)}}
.body p{{margin:0 0 8px}} .body p:last-child{{margin-bottom:0}} .body ul,.body ol{{margin:0 0 8px;padding-left:1.2rem}} .body p.h{{font-weight:600}}
.body blockquote{{margin:0 0 8px;padding-left:10px;border-left:3px solid var(--line);color:var(--muted)}}
.empty{{color:var(--muted)}}
</style>
<main>
<header><p class="meta">{E(a.eyebrow)}</p><h1>{E(a.title)}</h1><p class="lede">{E(a.lede)}</p>{stats}</header>
<div class="filters" role="group" aria-label="Filters">
  <button type="button" id="f-all" data-flag="all" aria-pressed="true">All</button><button type="button" id="f-flagged" data-flag="flagged" aria-pressed="false">Flagged</button><button type="button" id="f-clean" data-flag="clean" aria-pressed="false">Clean</button>
  <select id="f-kind" aria-label="Kind"><option value="all">Ladder and base</option><option value="ladder">Ladder levels</option><option value="base">Base world</option><option value="relayed">Relayed</option></select>
  <select id="f-world" aria-label="World"><option value="all">All worlds</option>{opts}</select>
  <button type="button" id="f-open" aria-pressed="false">Expand all</button>
</div>
{sections}
<p class="empty" id="none" hidden>No conversations match these filters.</p>
</main>
<script>
(function(){{
  var flag='all';
  function apply(){{
    var kind=document.getElementById('f-kind').value, world=document.getElementById('f-world').value, any=false;
    document.querySelectorAll('section.world').forEach(function(s){{
      var shown=0;
      s.querySelectorAll('details.conv').forEach(function(d){{
        var ok=(flag==='all'||d.dataset.flag===flag)&&(kind==='all'||d.dataset.kind===kind)&&(world==='all'||d.dataset.world===world);
        d.hidden=!ok; if(ok) shown++;
      }});
      s.hidden=shown===0; if(shown) any=true;
    }});
    document.getElementById('none').hidden=any;
  }}
  document.querySelectorAll('[data-flag]').forEach(function(b){{ if(b.tagName!=='BUTTON') return;
    b.addEventListener('click',function(){{ flag=b.dataset.flag; document.querySelectorAll('button[data-flag]').forEach(function(x){{x.setAttribute('aria-pressed',x===b?'true':'false');}}); apply(); }}); }});
  document.getElementById('f-kind').addEventListener('change',apply); document.getElementById('f-world').addEventListener('change',apply);
  var openBtn=document.getElementById('f-open');
  openBtn.addEventListener('click',function(){{ var on=openBtn.getAttribute('aria-pressed')!=='true'; openBtn.setAttribute('aria-pressed',on?'true':'false'); openBtn.textContent=on?'Collapse all':'Expand all';
    document.querySelectorAll('details.conv').forEach(function(d){{ if(!d.hidden) d.open=on; }}); }});
}})();
</script>
"""
    Path(a.out).write_text(page, encoding='utf-8'); print(a.out, len(cards), 'conversations,', len(page), 'chars')


if __name__ == '__main__':
    main()
