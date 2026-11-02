#!/bin/bash
# Overnight watchdog v2: Mac generator + 2 cloud generators (1 stream each, swap on), safe pair sync.
P="/Users/muhammadali/Desktop/Claude Video Editing/HumanLM/pipeline/gen_pairs.py"
D="/Users/muhammadali/Desktop/Claude Video Editing/HumanLM/data/pairs"
H=~/models/hl
while true; do
  if ! curl -s -m 5 localhost:8091/health | grep -q ok; then
    pkill -x llama-server; sleep 2
    (cd ~/models && nohup llama-server -m Qwen3.5-4B-Q4_K_M.gguf --port 8091 -c 8192 -np 2 -ngl 99 > ~/models/server.log 2>&1 &)
    sleep 30; echo "$(date) restarted local server"
  fi
  if grep -q FINISHED $H/genb_0.log && grep -q FINISHED $H/genb_1.log; then
    [ -f $H/c_mac_p0 ] || { head -6000 $H/c_mac.jsonl > $H/c_mac_p0; tail -n +6001 $H/c_mac.jsonl > $H/c_mac_p1; }
    for i in 0 1; do pgrep -f "c_mac_p$i" >/dev/null || { (nohup python3 "$P" $H/c_mac_p$i "$D/mac_c$i.jsonl" http://127.0.0.1:8091 qwen3.5-4b-q4 >> $H/genc_$i.log 2>&1 &); echo "$(date) started mac c$i"; }; done
  else
    for i in 0 1; do pgrep -f "b_mac_p$i" >/dev/null || { (nohup python3 "$P" $H/b_mac_p$i "$D/mac_b$i.jsonl" http://127.0.0.1:8091 qwen3.5-4b-q4 >> $H/genb_$i.log 2>&1 &); echo "$(date) started mac b$i"; }; done
  fi
  for g in 4 5; do
    n=hl-gen$g
    tenki sandbox get $n 2>/dev/null | grep -q RUNNING || { echo "$(date) $n not running"; continue; }
    tenki sandbox exec --session $n -c 'grep -q MODEL_DONE /data/build.log' >/dev/null 2>&1 || continue
    if [ ! -f $H/pushed_s_$g ]; then
      tar czf - --no-xattrs -C "/Users/muhammadali/Desktop/Claude Video Editing/HumanLM/pipeline" gen_pairs.py -C $H s_gen$g.jsonl | base64 > $H/push_s$g.b64
      tenki sandbox write --session $n --path /home/tenki/push_s.b64 --data-file $H/push_s$g.b64 >/dev/null 2>&1 && \
      tenki sandbox exec --session $n -c "mkdir -p /data/gen && cd /data/gen && base64 -d /home/tenki/push_s.b64 | tar xzf - 2>/dev/null" >/dev/null 2>&1 && touch $H/pushed_s_$g && echo "$(date) pushed shard to $n"
    fi
    tenki sandbox exec --session $n -c "cd /data/gen; pgrep -x llama-server >/dev/null || (nohup /data/llama.cpp/build/bin/llama-server -m /data/models/Qwen3.5-2B-Q4_K_M.gguf --port 8080 -c 2048 -np 1 -t 3 > /data/server.log 2>&1 &); sleep 2; /data/gen/start.sh" >/dev/null 2>&1
    tenki sandbox exec --session $n -c "cat /data/gen/pairs_s_gen$g.jsonl 2>/dev/null" 2>/dev/null | grep '^{' > "$H/sync_gen$g.tmp"
    new=$(wc -l < "$H/sync_gen$g.tmp"); old=$(cat "$D/cloud_gen$g.jsonl" 2>/dev/null | wc -l)
    [ "$new" -gt "$old" ] && cp "$H/sync_gen$g.tmp" "$D/cloud_gen$g.jsonl"
    echo "$(date) $n pairs $new mem $(tenki sandbox exec --session $n -c 'free -m | awk "/Mem/{print \$7}"' 2>/dev/null | head -1)MB"
  done
  echo "$(date) pairs: $(cat "$D"/mac_b*.jsonl "$D"/mac_c*.jsonl "$D"/cloud_gen*.jsonl 2>/dev/null | wc -l)" >> $H/progress.log
  sleep 600
done
