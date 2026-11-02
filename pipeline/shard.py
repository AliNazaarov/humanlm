"""Mix passages (modern-heavy, old books <= 30%) and split into shards for the generators."""
import json, random, sys, glob
random.seed(11)
spec = json.loads(sys.argv[1])          # {"news_filtered": 6619, ...} max rows per source
sizes = json.loads(sys.argv[2])         # {"mac": 8000, "gen1": 1500, ...}
tag = sys.argv[3]
rows = []
for src, cap in spec.items():
    ls = open(f"/data/passages/{src}.jsonl").readlines()
    random.shuffle(ls)
    rows += ls[:cap]
random.shuffle(rows)
i = 0
for name, n in sizes.items():
    open(f"/data/shards/{tag}_{name}.jsonl", "w").writelines(rows[i:i + n]); i += n
    print(name, len(rows[i - n:i]))
print("unused", len(rows) - i)
