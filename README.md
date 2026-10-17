# truth-advice

How AI assistants handle truth when they advise the people involved in the same event. Every party to an event is a
simulated user consulting their own assistant; the same model can be compared serving different parties, and
different models serving the same party. Each world has three layers of truth: settled facts (some known to some
parties), permanently unknowable facts (the anchor case: a dead person's reasons), and interpretation.

Design: [docs/spec.md](docs/spec.md). Worked world: [worlds/elena.json](worlds/elena.json) (and its accident twin,
derived by the code).

## The three parts

| Part | Where | What it does |
|---|---|---|
| Game master | `ta/gm.py`, `ta/simulator.py`, `ta/world.py` | Owns the worlds and the conditions; decides what each target sees (deployment prompt, memory file) and what each simulated user knows, forwards and reveals; runs the conversations and the phase-2 scene |
| World author (autoresearch) | `ta/author.py`, `scripts/search.py` | Writes new worlds by three moves (mutate one factor of an elite 60%, recombine two elites 20%, free generation for an empty cell 20%), guided by digests of how the targets behaved; gates (schema, consistency and fiction, recognition, realism); MAP-Elites over relationship x source of unknowability x who holds hidden facts; only mutate pairs support causal claims |
| Cluster | `cluster/` | Serves open-weight models (vLLM) as targets; replays conversations to capture activations; the "knows more than it says" probe |

Measurement (`ta/judge.py`, `ta/metrics.py`) sits apart from all three: the judge codes every conversation against the
world's layers (settled facts, the unknowable, the causal picture, perspectives, candour, truth-telling advice, support
content), the reasoning where exposed (thinks vs says), the simulator's fidelity, and the scenes.

## Commands

```sh
python3 -m unittest discover -s tests            # includes an offline end-to-end run
python3 scripts/dry_run.py                       # the whole pipeline with a scripted client, nothing billed
python3 scripts/review_world.py worlds/elena.json [--twin]
python3 scripts/run.py estimate --config config/pilot.json
python3 scripts/run.py prepare --config config/pilot.json --out runs/<name> --instruction "<owner's words>"
python3 scripts/run.py run|code|scenes|report --run runs/<name>
python3 scripts/search.py seed|step|report --run runs/<name>
```

Paid runs need the owner's approval of scope and cap, recorded by `prepare` before the first billed call. The
OpenRouter key comes from the environment (`OPENROUTER_API_KEY`) and is never written anywhere.
