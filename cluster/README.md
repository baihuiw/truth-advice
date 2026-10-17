# Cluster part (Yale SOM HPC)

Login: `ssh som` (Yale VPN; the laptop config shares the connection). Environment: `~/envs/vllm` (vLLM 0.31, torch 2.13
cu130, transformers, scikit-learn); model weights under `/gpfs/scratch60/bw664/hf`.

1. Sync code: `cluster/sync.sh [items.jsonl]`.
2. Open model as a target: `sbatch --export=ALL,MODEL=Qwen/Qwen3-32B cluster/serve_vllm.sbatch`, then
   `ssh -O forward -L 8000:<node>:8000 som` and add to the config:
   `"endpoints": {"qwen32": {"url": "http://127.0.0.1:8000/v1/chat/completions", "model": "Qwen/Qwen3-32B"}}`, with
   `qwen32` in `targets`. Its calls cost nothing; the judge is still billed.
3. Items: `python3 scripts/probe_items.py --run runs/<name> --targets qwen32 --contrast runs/<name>/contrast.jsonl --out items.jsonl`
   (the contrast set comes from `scripts/contrast_set.py`, inside an approved run).
4. Activations: `sbatch --export=ALL,ITEMS=/home/bw664/truth-advice/items.jsonl,OUT=/gpfs/scratch60/bw664/ta/acts cluster/extract.sbatch`.
5. Probe: `python cluster/probes.py --acts /gpfs/scratch60/bw664/ta/acts --out probe_scores.json` (CPU; run with
   `srun -p gpunormal --cpus-per-task=8 --mem=48G` when cpunormal is full), copy back, then
   `python3 scripts/probe_join.py --run runs/<name> --scores probe_scores.json`.

Gotchas: `sbatch --export` splits on commas; flashinfer needs `module load cuda/13.0.0-5r4s2rq` (in the sbatch files);
load models with `.to('cuda')` (no accelerate); the probe layer is chosen on held-out contrast situations, never on the
conversations it is tested on.
