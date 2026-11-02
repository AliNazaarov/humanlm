"""Ali's human-preference labeling page (human RL data). Training prompts only, never eval items.

  python3 hackathon/train/human_rl/label_server.py      -> open http://localhost:8767
Shows the AI draft and two of OUR model's rewrites (cand1/cand2, order shuffled). Keys: 1 or 2 = better,
3 = tie, 4 = both bad, E = edit the chosen one before saving. Labels append to labels.jsonl.
Pairs for DPO: chosen = the picked rewrite (or Ali's edit), rejected = the other one. Ties and both-bad are kept
in the file but not used as pairs.
"""
import http.server, json, os, random, time

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = os.path.join(HERE, "labels.jsonl")


def load(name):
    p = os.path.join(HERE, name)
    return {json.loads(l)["id"]: json.loads(l) for l in open(p)} if os.path.exists(p) else {}


def queue():
    prompts, c1, c2 = load("pref_prompts.jsonl"), load("cand1.jsonl"), load("cand2.jsonl")
    done = {json.loads(l)["id"] for l in open(LABELS)} if os.path.exists(LABELS) else set()
    items = []
    for i, p in prompts.items():
        if i in done or i not in c1 or i not in c2:
            continue
        a, b = c1[i]["output"], c2[i]["output"]
        if a.strip() == b.strip():
            continue
        items.append({"id": i, "draft": p["ai_draft"], "a": a, "b": b})
    return items, len(done)


PAGE = """<!doctype html><meta charset=utf-8><title>FeatherLM labels</title>
<style>
:root{--bg:#fbfaf7;--ink:#1c1b19;--mut:#77736b;--line:#e4e0d8;--acc:#8a3b12}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,system-ui,sans-serif}
main{max-width:1180px;margin:0 auto;padding:20px 16px}
header{display:flex;justify-content:space-between;align-items:baseline;color:var(--mut);font-size:14px}
details{margin:10px 0 14px;color:var(--mut)} pre{white-space:pre-wrap;font:inherit;margin:6px 0 0}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card h3{margin:0 0 6px;font-size:13px;letter-spacing:.06em;color:var(--mut)}
textarea{width:100%;min-height:170px;font:inherit;border:1px solid var(--line);border-radius:8px;padding:8px;box-sizing:border-box}
.keys{margin-top:14px;color:var(--mut);font-size:14px} b{color:var(--acc)}
button{font:inherit;padding:8px 14px;margin-right:6px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer}
@media(max-width:760px){.row{grid-template-columns:1fr}}
</style>
<main><header><div><b>FeatherLM</b> · which would you send to a customer?</div><div id=prog></div></header>
<details open><summary>AI draft (facts to keep)</summary><pre id=draft></pre></details>
<div class=row><div class=card><h3>1</h3><pre id=a></pre></div><div class=card><h3>2</h3><pre id=b></pre></div></div>
<div id=ed hidden><p class=keys>Edit the one you picked into what you'd actually send, then press <b>Save</b>.</p><textarea id=t></textarea>
<button onclick=save(pick,1)>Save</button><button onclick=cancel()>Cancel</button></div>
<p class=keys id=help><button onclick=go(1)>1 better</button><button onclick=go(2)>2 better</button><button onclick=go(3)>tie</button><button onclick=go(4)>both bad</button>
 &nbsp;Keys: <b>1</b> <b>2</b> <b>3</b> tie <b>4</b> both bad · <b>E</b> then 1/2 = edit before saving</p></main>
<script>
let item=null,pick=0,editMode=false;
async function next(){const r=await (await fetch('/next')).json();document.getElementById('prog').textContent=r.done+' labeled · '+r.left+' left';
 item=r.item;if(!item){document.querySelector('main').innerHTML='<h2>All done. Thank you.</h2><p>'+r.done+' labels saved.</p>';return}
 draft.textContent=item.draft;a.textContent=item.a;b.textContent=item.b;ed.hidden=true;help.hidden=false;editMode=false}
function go(k){if(!item)return;if(editMode&&(k==1||k==2)){pick=k;t.value=k==1?item.a:item.b;ed.hidden=false;help.hidden=true;t.focus();return}save(k,0)}
function cancel(){ed.hidden=true;help.hidden=false;editMode=false}
async function save(k,edited){await fetch('/label',{method:'POST',body:JSON.stringify({id:item.id,choice:k,edited:!!edited,text:edited?t.value:null,a:item.a,b:item.b,flip:item.flip})});next()}
document.addEventListener('keydown',e=>{if(document.activeElement===t)return;if(e.key=='e'||e.key=='E'){editMode=true;help.innerHTML+=' <b>(edit mode: press 1 or 2)</b>';return}
 if('1234'.includes(e.key))go(+e.key)});
next();
</script>"""


class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path == "/":
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if self.path == "/next":
            items, done = queue()
            it = None
            if items:
                it = random.choice(items)
                if random.random() < 0.5:   # hide which candidate is which
                    it["a"], it["b"], it["flip"] = it["b"], it["a"], True
                else:
                    it["flip"] = False
            return self._send(200, json.dumps({"item": it, "done": done, "left": len(items)}))
        self._send(404, "{}")

    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        k = d["choice"]
        row = {"id": d["id"], "choice": {1: "first", 2: "second", 3: "tie", 4: "both_bad"}[k], "edited": d["edited"],
               "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if k in (1, 2):
            chosen, rejected = (d["a"], d["b"]) if k == 1 else (d["b"], d["a"])
            row.update({"chosen": d["text"] if d["edited"] and d["text"] else chosen, "rejected": rejected})
        with open(LABELS, "a") as o:
            o.write(json.dumps(row) + "\n")
        self._send(200, "{}")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("Labeling page: http://localhost:8767")
    http.server.ThreadingHTTPServer(("127.0.0.1", 8767), H).serve_forever()
