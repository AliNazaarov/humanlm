#!/usr/bin/env bash
# Ali's leaderboard rows, each on eval_all (130) and heldout_pairs (120), all in parallel. Resume-safe: re-run to continue.
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
H=hackathon/harness/harness.py; L=hackathon/runs/logs
GLM=accounts/fireworks/models/glm-5p3-flash
NEM=accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b
run() { # name provider model loops [extra...]
  local n=$1 p=$2 m=$3 k=$4; shift 4
  for s in "" _heldout; do
    e=evals/eval_all.jsonl; [ -n "$s" ] && e=evals/heldout_pairs.jsonl
    nohup python3 $H $e evals/runs/hack_${n}${s}.jsonl --provider $p --model $m --system-name "$n" --loops $k --concurrency 6 "$@" > $L/${n}${s}.log 2>&1 &
  done
}
run O1_glm_base        fireworks $GLM 0
run O2_glm_prompt      fireworks $GLM 0 --prompt-file hackathon/train/prompt_v2.txt
run O3_glm_harness     fireworks $GLM 3
run O3b_glm_prompt_harness fireworks $GLM 3 --prompt-file hackathon/train/prompt_v2.txt
run F2_gpt61_terra     openai gpt-6.1-terra 0
run N1_nemotron_base   fireworks $NEM 0
wait
