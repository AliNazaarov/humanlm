#!/usr/bin/env bash
# Commit + push Ali's finished work every 10 min. Run files go up only once their manifest exists (run complete).
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
while true; do
  for d in hackathon/audit hackathon/pitch hackathon/train hackathon/harness hackathon/social hackathon/data; do [ -e "$d" ] && git add "$d"; done
  for m in hackathon/runs/*.json; do
    n=$(basename "$m" .json); git add "$m"; [ -f "evals/runs/hack_${n}.jsonl" ] && git add "evals/runs/hack_${n}.jsonl"
  done
  if ! git diff --cached --quiet; then
    git -c user.name=AliNazaarov commit -q -m "autopush: Ali's finished work $(date +%H:%M)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    git pull -q --rebase --autostash && git push -q && echo "$(date +%H:%M) pushed"
  fi
  sleep 600
done
