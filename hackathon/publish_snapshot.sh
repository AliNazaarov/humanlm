#!/usr/bin/env bash
# Rebuild the public judged repo (AliNazaarov/featherlm) as ONE squashed commit from private main.
# Leaves out private strategy docs, bulk training data and the 3 held-out ids without an established licence.
set -euo pipefail
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"; P="${1:-/tmp/featherlm-public}"
rm -rf "$P"; mkdir -p "$P"; git -C "$ROOT" archive HEAD | tar -x -C "$P"; cd "$P"
rm -rf market research board design BRIEF.md PLAN_30D.md WHAT_ELSE.md GRAPH.md data/pairs hackathon/social hackathon/bus/status
find hackathon/data hackathon/train -name "*.jsonl" | grep -v -E "eval|heldout" | xargs rm -f
python3 - <<'PY'
import json, glob
bad={'ho-007','ho-027','ho-071'}
for f in ['evals/heldout_pairs.jsonl']+glob.glob('evals/runs/*heldout*.jsonl'):
    open(f,'w').writelines(l for l in open(f).readlines() if json.loads(l).get('id') not in bad)
PY
cp "$ROOT/hackathon/DATA_NOT_PUBLISHED.md" . 2>/dev/null || true
if grep -rIlE "fw_[A-Za-z0-9]{10,}|sk-ant-[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30}" .; then echo "KEY FOUND, abort"; exit 1; fi
git init -q -b main; git add -A
git -c user.name=AliNazaarov -c user.email=AliNazaarov@users.noreply.github.com commit -q -m "FeatherLM: Fireworks Deploy hackathon submission snapshot"
git remote add origin https://github.com/AliNazaarov/featherlm.git; git push -q --force origin main; git rev-parse HEAD
