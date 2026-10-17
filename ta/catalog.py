"""Prices from the OpenRouter catalog, as a mapping model id -> {'prompt': $/token, 'completion': $/token}."""
import json, urllib.request


def fetch(timeout=120):
    with urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/models'), timeout=timeout) as r:
        data = json.loads(r.read().decode())['data']
    return {m['id']: {'prompt': m['pricing']['prompt'], 'completion': m['pricing']['completion'], 'context_length': m.get('context_length')} for m in data}


def for_config(cfg, catalog):
    out = {}
    for alias, model in cfg['models'].items():
        if model not in catalog:
            raise KeyError(f'{alias}: {model} is not in the catalog')
        out[model] = catalog[model]
    return out


def endpoints(model, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(f'https://openrouter.ai/api/v1/models/{model}/endpoints'), timeout=timeout) as r:
        return json.loads(r.read().decode()).get('data', {}).get('endpoints', [])


def routes_for(cfg):
    """Each alias's chosen route with its current price and supported parameters, from the live endpoint list. Fails if
    a route no longer serves its model, so a run never starts on a route that cannot answer."""
    out = {}
    for alias, tag in (cfg.get('provider_routes') or {}).items():
        if alias not in cfg['models']:
            continue
        model = cfg['models'][alias]; eps = endpoints(model); e = next((x for x in eps if x.get('tag') == tag), None)
        if e is None:
            raise KeyError(f"{alias}: route {tag} does not serve {model}; available: {sorted(str(x.get('tag')) for x in eps)[:15]}")
        sp = e.get('supported_parameters') or []
        out[alias] = {'model': model, 'tag': tag, 'prompt': e['pricing']['prompt'], 'completion': e['pricing']['completion'], 'quantization': e.get('quantization'),
                      'supports_temperature': 'temperature' in sp, 'supports_json': 'response_format' in sp, 'supports_reasoning': 'reasoning' in sp}
    return out
