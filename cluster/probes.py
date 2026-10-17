#!/usr/bin/env python3
"""The "knows more than it says" probe. A logistic-regression probe is trained, per layer, on the boundary states of
contrast items (a person tells a situation in which they clearly did / clearly did not cause the harm), with grouped
cross-validation by situation; the layer is chosen on a held-out set of situations, never on the conversations. The
probe is then read at every boundary state of the conversations: the model's internal estimate that its user bears
responsibility, just before each reply. scripts/probe_join.py compares it with what the reply says.

  python cluster/probes.py --acts <dir> --out probe_scores.json
"""
import argparse, json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def load(d, kind):
    p = Path(d) / f'{kind}.npy'
    return (np.load(p, mmap_mode='r'), [json.loads(l) for l in open(Path(d) / f'{kind}.rows.jsonl')]) if p.exists() else (None, [])


def clf(C=0.01):
    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=3000))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--acts', required=True); ap.add_argument('--out', required=True); ap.add_argument('--holdout', type=float, default=0.25)
    a = ap.parse_args(); meta = json.load(open(Path(a.acts) / 'meta.json')); L = meta['layers']
    Xc, rc = load(a.acts, 'contrast'); keep = [i for i, r in enumerate(rc) if r['span'] == 'boundary' and r.get('fault') in (0, 1)]
    y = np.array([rc[i]['fault'] for i in keep]); g = np.array([rc[i]['situation'] for i in keep])
    sits = sorted(set(g)); rng = np.random.default_rng(0); held = set(rng.choice(sits, size=max(2, int(len(sits) * a.holdout)), replace=False))
    tr = np.array([s not in held for s in g]); te = ~tr; res = {'layers': L, 'cv_auc': [], 'holdout_auc': []}
    for li in range(len(L)):
        X = np.asarray(Xc[keep, li, :], dtype=np.float32); sc = np.zeros(tr.sum())
        for a_, b_ in GroupKFold(n_splits=5).split(X[tr], y[tr], g[tr]):
            sc[b_] = clf().fit(X[tr][a_], y[tr][a_]).decision_function(X[tr][b_])
        res['cv_auc'].append(round(float(roc_auc_score(y[tr], sc)), 3))
        m = clf().fit(X[tr], y[tr]); res['holdout_auc'].append(round(float(roc_auc_score(y[te], m.decision_function(X[te]))), 3))
    best = int(np.argmax(res['holdout_auc'])); res['layer'] = L[best]
    model = clf().fit(np.asarray(Xc[keep, best, :], dtype=np.float32), y)
    Xv, rv = load(a.acts, 'conversation'); scores = []
    if Xv is not None:
        pr = model.predict_proba(np.asarray(Xv[:, best, :], dtype=np.float32))[:, 1]
        scores = [{**r, 'p_user_fault': round(float(p), 4)} for r, p in zip(rv, pr) if r['span'] == 'boundary']
    res['scores'] = scores; json.dump(res, open(a.out, 'w'), indent=1)
    print(f"layer {res['layer']}: held-out AUC {res['holdout_auc'][best]}; CV by layer {res['cv_auc']}; {len(scores)} conversation states scored")


if __name__ == '__main__':
    main()
