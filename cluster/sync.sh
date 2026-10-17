#!/bin/bash
# Copy the repository code and an items file to the cluster (uses the shared `som` SSH connection).
#   cluster/sync.sh [items.jsonl]
set -e
rsync -a --exclude runs --exclude review --exclude .git --exclude '__pycache__' "$(dirname "$0")/../" som:truth-advice/
[ -n "$1" ] && scp -q "$1" som:truth-advice/items.jsonl && echo "items -> som:truth-advice/items.jsonl"
echo synced
