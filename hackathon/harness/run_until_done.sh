#!/usr/bin/env bash
# Re-run a resume-safe harness command until its manifest exists (max 6 attempts). Usage: run_until_done.sh MANIFEST -- harness args...
m=$1; shift 2
for i in 1 2 3 4 5 6; do
  [ -f "$m" ] && exit 0
  python3 "$(dirname "$0")/harness.py" "$@"
  sleep 20
done
