#!/bin/bash
# Serve an open-weight model with vLLM on the Yale SOM cluster (OpenAI-compatible API on port 8000).
#   sbatch --export=ALL,MODEL=Qwen/Qwen3-32B,TP=1 cluster/serve_vllm.sbatch
# then on the laptop: ssh -O forward -L 8000:<node>:8000 som   and add the model under "endpoints" in the config.
#SBATCH -p gpunormal
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=12:00:00
#SBATCH --job-name=ta-vllm
#SBATCH --output=/home/bw664/jobs/%x-%j.log
export HF_HOME=/gpfs/scratch60/bw664/hf
source /etc/profile.d/z-lmod.sh
module load cuda/13.0.0-5r4s2rq                # flashinfer compiles kernels at start-up and needs nvcc
export CUDA_HOME=$(dirname $(dirname $(which nvcc)))
source /home/bw664/envs/vllm/bin/activate
MODEL=${MODEL:-Qwen/Qwen3-32B}; TP=${TP:-1}
echo "node $(hostname) port 8000 model $MODEL start $(date)"
PARSER=""; [[ "$MODEL" == Qwen/Qwen3* ]] && PARSER="--reasoning-parser qwen3"
vllm serve "$MODEL" --host 0.0.0.0 --port 8000 --max-model-len 32768 --gpu-memory-utilization 0.92 --tensor-parallel-size "$TP" $PARSER
