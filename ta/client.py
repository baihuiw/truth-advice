"""OpenRouter client (and self-hosted OpenAI-compatible endpoints) with a cost ledger, a response cache and a hard cap.
Every model call in this repository goes through `Client.chat`. The key comes from the environment and is never written anywhere.

The cache key is the call's label plus its request body, so repeated samples of the same prompt (reps) are separate
calls, and a rerun of the same run resumes from the cache without paying twice."""
import hashlib, http.client, json, os, threading, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = 'https://openrouter.ai/api/v1/chat/completions'
RETRY_CODES = (408, 409, 425, 429, 500, 502, 503, 504)


class BudgetStop(Exception):
    pass


class CallFailed(Exception):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def reasoning_of(msg):
    """Reasoning text returned with a message, when the provider returns it (OpenRouter `reasoning` or `reasoning_details`)."""
    if msg.get('reasoning'):
        return msg['reasoning']
    if msg.get('reasoning_content'):                 # vLLM with a reasoning parser
        return msg['reasoning_content']
    parts = [d.get('text') or d.get('summary') or '' for d in (msg.get('reasoning_details') or []) if isinstance(d, dict)]
    return '\n'.join(p for p in parts if p)


class Client:
    def __init__(self, run_dir, cfg, catalog, live=True, routes=None):
        self.run = Path(run_dir); self.cfg = cfg; self.catalog = catalog; self.live = live; self.routes = routes or {}
        self.lock = threading.Lock(); self.cap = float(cfg['budget_usd']); self.head = float(cfg.get('price_headroom', 1.2))
        (self.run / 'cache').mkdir(parents=True, exist_ok=True); self.ledger = self.run / 'usage.jsonl'; self.spent = self._spent()
        self.key = os.environ.get('OPENROUTER_API_KEY')
        if live and not self.key and not cfg.get('endpoints'):
            raise RuntimeError('OPENROUTER_API_KEY is not set')

    def endpoint(self, alias):
        """A self-hosted OpenAI-compatible server for this alias (`endpoints` in the config: url, model, optional key), used
        for open models served on a cluster. Such calls cost nothing and carry no OpenRouter routing or reasoning settings."""
        return (self.cfg.get('endpoints') or {}).get(alias)

    def _spent(self):
        if not self.ledger.exists():
            return 0.0
        rows = [json.loads(l) for l in self.ledger.read_text().splitlines() if l.strip()]
        return sum(r.get('cost') or 0 for r in rows if r.get('status') == 'ok')

    def price(self, alias, model):
        """Per-token price of the alias's route when known (routes.json), else the catalog price of the model, times headroom."""
        p = self.routes.get(alias) or self.catalog[model]; return float(p['prompt']) * self.head, float(p['completion']) * self.head

    def _log(self, row):
        with self.lock:
            with self.ledger.open('a') as f:
                f.write(json.dumps(row) + '\n')

    def chat(self, alias, messages, label, max_tokens=400, temperature=0.7, json_mode=False):
        ep = self.endpoint(alias); model = ep['model'] if ep else self.cfg['models'][alias]
        body = {'model': model, 'messages': messages, 'max_tokens': max_tokens, 'temperature': temperature}
        if json_mode:
            body['response_format'] = {'type': 'json_object'}
        if ep:
            pin = pout = 0.0
            body.update(ep.get('extra') or {})                              # server-specific fields, e.g. gpt-oss reasoning_effort
        else:
            if not self.key:
                raise RuntimeError('OPENROUTER_API_KEY is not set')
            pin, pout = self.price(alias, model)
            body['provider'] = {'allow_fallbacks': False, 'max_price': {'prompt': pin * 1e6, 'completion': pout * 1e6}}
            if json_mode:                    # the judge and reader must get JSON mode honoured; targets may drop unsupported settings (temperature)
                body['provider']['require_parameters'] = True
            route = (self.cfg.get('provider_routes') or {}).get(alias)
            if route:
                body['provider']['only'] = [route]
            rs = (self.cfg.get('reasoning') or {}).get(alias)
            if rs:
                body['reasoning'] = rs
        key = hashlib.sha256((label + '\n' + json.dumps(body, sort_keys=True)).encode()).hexdigest(); cpath = self.run / 'cache' / f'{key}.json'
        if cpath.exists():
            return json.loads(cpath.read_text())
        if not self.live:
            raise CallFailed(f'{label}: not cached and the client is offline')
        reserve = sum(len(m['content']) for m in messages) / 3.5 * pin + max_tokens * pout
        with self.lock:
            if self.spent + reserve > self.cap:
                raise BudgetStop(f'cap ${self.cap:.2f} would be exceeded: spent ${self.spent:.2f}, reserve ${reserve:.3f}')
        res = self._post(body, label, url=ep['url'] if ep else URL, key=(ep.get('key') or 'EMPTY') if ep else self.key); usage = res.get('usage') or {}
        cost = (usage.get('prompt_tokens') or 0) * pin + (usage.get('completion_tokens') or 0) * pout
        choice = (res.get('choices') or [{}])[0]; msg = choice.get('message') or {}
        out = {'content': msg.get('content') or '', 'reasoning': reasoning_of(msg), 'finish_reason': choice.get('finish_reason'),
               'usage': usage, 'cost': cost, 'model': model, 'provider': res.get('provider'), 'label': label}
        with self.lock:
            self.spent += cost
        self._log({'at': now(), 'label': label, 'model': model, 'provider': res.get('provider'), 'status': 'ok', 'cost': cost,
                   'prompt_tokens': usage.get('prompt_tokens'), 'completion_tokens': usage.get('completion_tokens')})
        cpath.write_text(json.dumps(out)); return out

    def _post(self, body, label, url=URL, key=None):
        data = json.dumps(body).encode(); last = None; key = key or self.key
        for attempt in range(max(self.cfg.get('retries', 4), 5)):
            req = urllib.request.Request(url, data=data, headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
                                                                  'HTTP-Referer': 'https://github.com/baihuiw', 'X-Title': 'truth-advice'})
            try:
                with urllib.request.urlopen(req, timeout=self.cfg.get('timeout_seconds', 240)) as r:
                    res = json.loads(r.read().decode())
                if res.get('error'):
                    raise CallFailed(str(res['error'])[:200])
                return res
            except urllib.error.HTTPError as e:
                last = f'HTTP {e.code}'
                if e.code not in RETRY_CODES:
                    break
                if e.code == 429:                    # rate limits last longer than other transient errors: honour Retry-After, else wait up to 2 minutes
                    try:
                        wait = float(e.headers.get('Retry-After') or 0)
                    except (TypeError, ValueError):
                        wait = 0
                    time.sleep(min(120, max(wait, 15 * 2 ** attempt))); continue
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, CallFailed, http.client.HTTPException, ConnectionError, OSError) as e:
                last = f'{type(e).__name__}: {str(e)[:180]}'               # dropped or truncated responses are retried like timeouts
            time.sleep(min(60, 3 * 2 ** attempt))
        self._log({'at': now(), 'label': label, 'model': body['model'], 'status': 'error', 'error': last})
        raise CallFailed(f'{label}: {last}')
