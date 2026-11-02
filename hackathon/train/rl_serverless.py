"""GRPO-style RL on Fireworks serverless training, starting from the SFT LoRA (O6).

Reward = the headline gates (hackathon/harness/gates.py) on each sampled rewrite:
  +1.0 if all four gates pass, else -0.25 per failed gate.
Prompts come from hackathon/data/train.jsonl user turns only (never evals/).
Runs inside the fw-ai/cookbook `training` package (its async serverless RL loop):

  cd ~/models/hl/fwtrain/cookbook/training
  ~/models/hl/fwtrain/.venv/bin/python <repo>/hackathon/train/rl_serverless.py \
      --init-from-checkpoint <account>/<sft-run-id>/<step> --run-dir <dir>
"""
import argparse, functools, json, os, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "hackathon/harness"))
import gates  # noqa: E402

from training.recipes.experiment import async_rl_loop_serverless  # noqa: E402
from training.recipes.experiment.async_rl_loop_serverless import Config  # noqa: E402
from training.utils import WandBConfig, build_renderer  # noqa: E402
from training.utils.rl.losses import has_reward_variance  # noqa: E402
from training.utils.rl.rollout import single_turn_renderer_rollout  # noqa: E402


class NonThinking:
    """Wrap the GLM-5.3 renderer: prefill "</think>" (the SFT data's shape) and parse the visible answer."""

    def __init__(self, inner, tokenizer):
        self.inner, self.tok = inner, tokenizer

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def build_generation_prompt(self, messages, role="assistant", prefill=None):
        return self.inner.build_generation_prompt(messages, role=role, prefill="</think>")

    def parse_response(self, tokens):
        import re
        text = re.sub(r"<\|[a-z_]+\|>", "", self.tok.decode(list(tokens))).split("</think>")[-1].strip()
        return {"role": "assistant", "content": text}, True


def reward(draft, text):
    g = gates.check(draft, text or "")
    return 1.0 if g["pass"] else -0.25 * g["n_fail"]


def make_rollout_fn(setup, renderer_name="glm53_flash"):
    renderer = NonThinking(build_renderer(setup.tokenizer, setup.tokenizer_id, renderer_name, load_image_processor=False),
                           setup.tokenizer)
    sampler = setup.sampler

    async def grade(row, message, _ok):
        content = message.get("content", "") if isinstance(message, dict) else str(message)
        return reward(row["messages"][1]["content"], content)

    async def rollout_fn(row):
        return await single_turn_renderer_rollout(
            row, renderer=renderer, sample_with_prompt_tokens=sampler.sample_with_prompt_tokens,
            message_builder=lambda r: r["messages"][:2], reward_fn=grade,
            sample_kwargs=setup.sample_kwargs, tokenizer=setup.tokenizer)

    return rollout_fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init-from-checkpoint", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--max-rows", type=int, default=160)
    ap.add_argument("--groups-per-step", type=int, default=8)
    ap.add_argument("--completions", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-5)
    a = ap.parse_args()
    run_dir = Path(a.run_dir); run_dir.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in open(ROOT / "hackathon/data/train.jsonl")]
    random.Random(11).shuffle(rows)
    rows = [{"messages": r["messages"][:2]} for r in rows[: a.max_rows]]
    cfg = Config(
        base_model="accounts/fireworks/models/glm-5p3-flash", tokenizer_model="zai-org/GLM-5.3-Flash",
        learning_rate=a.lr, completions_per_prompt=a.completions, prompt_groups_per_step=a.groups_per_step,
        max_completion_tokens=700, max_seq_len=4096, temperature=1.0, epochs=1, shuffle=False,
        max_rows=a.max_rows, lora_rank=16, lora_alpha=32, weight_decay=0.0, min_group_size=2,
        max_concurrency_rollout_sample=32, sample_timeout=900.0, snapshot_prefix="hlrl",
        metrics_file=str(run_dir / "metrics.jsonl"), init_from_checkpoint=a.init_from_checkpoint,
        wandb=WandBConfig(project="humanlm-rl"))
    result = async_rl_loop_serverless.main(cfg, rollout_fn_factory=functools.partial(make_rollout_fn),
                                           dynamic_filter_fn=has_reward_variance, rows=rows)
    (run_dir / "result.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    print("RL_DONE", json.dumps(result, default=str)[:2000])


if __name__ == "__main__":
    main()
