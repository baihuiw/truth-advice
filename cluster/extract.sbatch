#!/bin/bash
# Replay items through the model and save activations (cluster/extract.py).
#   sbatch --export=ALL,ITEMS=/home/bw664/truth-advice/items.jsonl,OUT=/gpfs/scratch60/bw664/ta/acts,MODEL=Qwen/Qwen3-32B cluster/extract.sbatch
#SBATCH -p gpunormal
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=120G
#SBATCH --time=04:00:00
#SBATCH --job-name=ta-extract
#SBATCH --output=/home/bw664/jobs/%x-%j.log
export HF_HOME=/gpfs/scratch60/bw664/hf
source /home/bw664/envs/vllm/bin/activate
cd /home/bw664/truth-advice
python cluster/extract.py --items "$ITEMS" --model "${MODEL:-Qwen/Qwen3-32B}" --out "$OUT"
