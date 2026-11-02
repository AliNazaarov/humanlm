"""Generate rewrites for an eval file with base or base+LoRA. Usage: python3 infer.py EVAL.jsonl OUT.jsonl [adapter_dir]"""
import json, sys, os, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
EVAL, OUT = sys.argv[1], sys.argv[2]
ADAPTER = sys.argv[3] if len(sys.argv) > 3 else None
BASE = os.environ.get("BASE", "Qwen/Qwen3.5-0.8B")
SYSTEM = "Rewrite the user's text so it reads like a skilled human wrote it: plain, specific, varied rhythm, correct grammar. Keep every fact, name and number. Add nothing."
torch.set_num_threads(os.cpu_count())
tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float32)
if ADAPTER:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()
name = "lora:" + os.path.basename(ADAPTER.rstrip("/")) if ADAPTER else "base:" + BASE
with open(OUT, "w") as out:
    for line in open(EVAL):
        r = json.loads(line); src = r.get("ai_draft") or r.get("input")
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": src}]
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False, return_tensors="pt")
        if not torch.is_tensor(ids): ids = ids["input_ids"]
        with torch.no_grad():
            g = model.generate(ids, max_new_tokens=400, do_sample=True, temperature=0.7, top_p=0.9, repetition_penalty=1.05)
        txt = tok.decode(g[0][ids.shape[1]:], skip_special_tokens=True).strip()
        out.write(json.dumps({"id": r.get("id") or r.get("pid"), "system": name, "output": txt}) + "\n"); out.flush()
print("INFER_DONE", name)
