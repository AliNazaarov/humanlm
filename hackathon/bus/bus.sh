#!/usr/bin/env bash
# Agent-to-agent mailbox over git. One file per message, so two agents never edit the same file.
#   bus.sh send FROM TO "subject" < body.md   write a message and push it
#   bus.sh recv ME                             pull, print new messages to ME, mark them seen
#   bus.sh status ME "one line"                update ME's status file and push
#   bus.sh board                               print every agent's status
set -euo pipefail
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
BUS="$ROOT/hackathon/bus"
SEEN="$BUS/.seen"   # local only, gitignored

sync() {
  git -C "$ROOT" pull --rebase --autostash -q || { echo "bus: pull failed, fix git first" >&2; exit 1; }
}

case "${1:-}" in
  send)
    from="$2"; to="$3"; subject="$4"
    sync
    f="$BUS/msgs/$(date -u +%Y%m%dT%H%M%SZ)-$from-to-$to.md"
    { echo "from: $from"; echo "to: $to"; echo "subject: $subject"; echo "sent: $(date -u +%FT%TZ)"; echo; cat; } > "$f"
    git -C "$ROOT" add "$f"
    git -C "$ROOT" commit -q -m "bus: $from -> $to: $subject" -- "$f"
    for i in 1 2 3; do git -C "$ROOT" push -q && break; sync; done
    echo "sent $(basename "$f")"
    ;;
  recv)
    me="$2"; sync; touch "$SEEN"; n=0
    for f in "$BUS"/msgs/*-to-"$me".md "$BUS"/msgs/*-to-all.md; do
      [ -e "$f" ] || continue
      b="$(basename "$f")"
      grep -qx "$b" "$SEEN" && continue
      case "$b" in *-"$me"-to-all.md) echo "$b" >> "$SEEN"; continue;; esac
      echo "=== $b"; cat "$f"; echo; echo "$b" >> "$SEEN"; n=$((n+1))
    done
    [ "$n" -eq 0 ] && echo "no new messages for $me"
    ;;
  status)
    me="$2"; line="$3"; sync
    f="$BUS/status/$me.md"
    echo "$(date -u +%FT%TZ) $line" >> "$f"
    git -C "$ROOT" add "$f"
    git -C "$ROOT" commit -q -m "bus: status $me" -- "$f"
    for i in 1 2 3; do git -C "$ROOT" push -q && break; sync; done
    ;;
  board)
    sync
    for f in "$BUS"/status/*.md; do [ -e "$f" ] && { echo "== $(basename "$f" .md)"; tail -3 "$f"; }; done
    ;;
  *) sed -n 2,6p "$0"; exit 1;;
esac
