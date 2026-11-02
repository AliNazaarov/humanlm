"""Rebuild evals/*.jsonl from the chunk files present. Safe to rerun after each chunk."""
import json, os, glob, importlib, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import common
for f in sorted(glob.glob(os.path.join(here, 'c*.py'))) + sorted(glob.glob(os.path.join(here, 't*.py'))):
    name = os.path.basename(f)[:-3]
    if name in ('common',): continue
    importlib.import_module(name)
ev = os.path.dirname(here)
def dump(path, rows):
    with open(path + '.tmp', 'w') as fh:
        for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    os.replace(path + '.tmp', path)
dev, trick, base = [], [], []
for i, it in enumerate(common.ITEMS, 1):
    rid = f"dev-{i:03d}"
    dev.append(dict(id=rid, split="dev", origin="agent-written", type=it['type'], brief=it['brief'],
        ai_draft=it['ai_draft'], must_keep=it['must_keep'], forbidden=it['forbidden'],
        draft_model="claude-opus-5.5 imitating default ChatGPT style"))
    base.append(dict(id=rid, system="claude-opus-persona", output=it['baseline']))
for i, it in enumerate(common.TRICKS, 1):
    rid = f"trick-{i:02d}"
    trick.append(dict(id=rid, split="dev-trick", origin="agent-written", type=it['type'], trick_kind=it['trick_kind'],
        expected_behavior=it['expected_behavior'], draft_is_ai=it['draft_is_ai'], brief=it['brief'],
        ai_draft=it['ai_draft'], must_keep=it['must_keep'], verbatim=it['verbatim'], forbidden=it['forbidden']))
    base.append(dict(id=rid, system="claude-opus-persona", output=it['baseline']))
dump(os.path.join(ev, 'dev_set.jsonl'), dev)
dump(os.path.join(ev, 'trick_set.jsonl'), trick)
dump(os.path.join(ev, 'baseline_frontier.jsonl'), base)
print(len(dev), 'dev', len(trick), 'trick', len(base), 'baseline')
