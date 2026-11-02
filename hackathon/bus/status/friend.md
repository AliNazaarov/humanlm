2026-11-02T18:12:53Z loop live; replied SYNC; Step 0 repo hygiene in progress
2026-11-02T18:13:30Z Step 0 done (.env.example, requirements.txt, Makefile, README skeleton; make test target passes 29/29). Next: Step 1 run_frontier.py, waiting on Q: frontier model id
2026-11-02T18:33:14Z S1 stats.py written + 9 tests pass, eval-check OK (plans/EVAL_LOG.md); in review. S2 frontier runner + S3 judge being built by subagents. S6 A/B pairs generator done (placeholder pairs).
2026-11-02T18:34:25Z S1 stats.py committed (exact rate CIs + paired bootstrap; review fixes in). S2 run_frontier.py built, 13 offline tests pass, in review; live run blocked on key + PRICES.md. S3 judge in progress.
2026-11-02T18:41:49Z S2 run_frontier committed (review fixes in, 25 tests). S4 score_all v2 committed: fact-safe human rewrite rate G1-G4, 250-item leaderboard + per-split, delta vs F1 w/ significance. S3 judge being fixed after review (BLOCK). S5 chart + S6 A/B page in a second session. Blocked: Anthropic key + Opus price.
2026-11-02T18:44:12Z S8 README draft committed: headline metric + gates, setup, make eval, method, limitations, pre-existing vs built-today, AI disclosure. Waiting on keys for live runs.
2026-11-02T18:49:09Z Key loading aligned to keys.env. Ready to run F1/F1-live/F1+H/F2 + judge once keys are in ~/.config/humanlm/keys.env. README draft in.
2026-11-02T18:55:31Z Keys in (outside repo). TLS proxy fixed (truststore). S5 plot.py leaderboard + S6 blind A/B page done (2nd session). Now running in parallel: F1 Opus 5.5 strong+live and F2 GPT on 250 items; F1+H harness; judge fix for reasoning models (all candidate judges truncate at 1024 tok).
2026-11-02T19:01:08Z F1 unblocked: Opus 5.5 rejects sampling params -> send none, adaptive thinking effort low, max_tokens 1500, disclosed (Ruslan's call). Smoke 3/3 OK, ~$0.008/item. Full F1 strong+live x (130+120) running. F1+H waits on harness.py CONTRACT. Judge being made reasoning-safe + Gemini provider.
2026-11-02T19:02:10Z F1 Opus 5.5 runs in progress: strong 52/130 + 45/120 heldout, live 52/130 + 50/120. Judge committed (Gemini provider + GLM-5.3 second opinion); HANDOFF sent to Ali. Waiting on harness.py CONTRACT for F1+H.
2026-11-02T19:07:19Z F1 done ($4.00). First leaderboard committed: F1 strong 57% [51,63] fact-safe on 250 items, weakest split dev 37%. Refusals count as fails for every system.
2026-11-02T19:10:39Z All work pushed (F1 runs, first leaderboard + charts, judge, examples, names_probe). BLOCKED on Ali's ACK for the name-proxy fix in metrics.py: it moves F1 strong main pass 55->90/130.
2026-11-02T19:14:04Z Pulled Ali's 059222e (harness decoding fix). All friend work pushed (F1 runs + leaderboard + charts + judge + FeatherLM rename). F1+H running. Waiting: Ali's O*/F2 run files (not on main yet) + ACK on name-proxy fix.
2026-11-02T19:20:33Z Leaderboard with all 9 systems committed (b493c6a). Name-proxy bug fixed with tests. O3b 94%, O3 93%, F1H 94%, F1 strong 72%, F2 GPT 40%. Kimi K3 judge running on O3/O3b vs F1, F2, F1H.
2026-11-02T19:22:43Z Judge 1/6 done (Kimi K3): O3 vs Claude strong overall 34-57 (Claude preferred, p=0.02); facts 13-8 (n.s.); style 25-56 (p<0.001). 5 more pairs running. Human A/B test is now the decider.
2026-11-02T19:24:56Z Judge done & committed. Claude preferred on marketing style (p~0.02), tie on real human held-out text, facts edge ours. Next: README results/limitations update, human A/B at venue.
2026-11-02T19:29:45Z README Results now generated from results.json (headline + judge, unedited). Running an eval-methodology review next.
2026-11-02T19:33:59Z Pushed 10-system leaderboard chart (with copy-draft control). Pulled Ali's harness fwsampler provider (LoRA snapshot sampler -> SFT row coming). Ready to rescore + rejudge O4/O5/O3c when they land.
2026-11-02T19:37:47Z Real-text work started: (1) collecting real README copy eval split (permissive licences, AI tells, leakage-checked); (2) auditing held-out provenance/licences. CONTRACT sent to Ali for O3/O3b runs on it.
2026-11-02T19:40:13Z O3c (style round) scored: 97% [94,99] fact-safe on 250, +25 pp vs Claude strong. Judging O3c vs Claude now. Real-copy split + held-out provenance audit still collecting.
2026-11-02T19:43:55Z O3c judge: style gap vs Claude no longer significant (33/46, p=0.18). Held-out audit committed: 22 ids overlap train (heldout_clean block added), cccc licences need recovery. Real README split still collecting.
2026-11-02T19:48:50Z Strict+lenient fact-safe in report: O3c 97%/98% vs Claude strong 72%/85% (both significant). F1h humanizer baseline + Claude on real README split running.
2026-11-02T19:53:06Z F1h (Claude+humanizer) 60% strict: weaker than F1 strong (72%), stays extra row. Real README split: Claude 76% vs F1H 98%. Human vote scorer ready. SFT model B blocked on a permission decision.
2026-11-02T19:54:09Z SFT model B (modern-web ablation) training on Fireworks, Ruslan's key.
2026-11-02T19:55:55Z Rescored with O2h/F2h humanizer rows: humanizer prompt lowers fact-safety for every model (GLM 53%, GPT 51%, Claude 60% vs Claude strong 72%). O3c 97% still top. SFT B training.
2026-11-02T20:00:31Z Video script committed (hackathon/demo/VIDEO_SCRIPT.md). Demo notebook being built. Waiting: O3e, O4/O4m/O5/O6 rows, Telegram votes.
2026-11-02T20:06:09Z Scored O3d 95%/98% and O3e 96%/99% (strict/lenient) vs Claude strong 72%/85%. Judging O3d+O3e vs Claude now. O3j main file not pushed yet. A/B page fixes forwarded.
2026-11-02T20:09:04Z Judge: O3d/O3e lose to Claude on the judge (O3e style 20/54); O3c remains best (n.s. vs Claude). Demo notebook + video script committed. Waiting: O3j main file, SFT B, O4/O5/O6, human votes.
2026-11-02T20:11:02Z O3j complete: 98% strict / 99% lenient (+26 pp vs Claude strong), $2.56/1k. Judging O3j vs Claude now.
2026-11-02T20:14:24Z O3j judge: overall n.s. (41/55), style ahead of Claude 44/37, facts behind 4/25. A/B page v7 pushed (bias fixes). Waiting: SFT B, O4/O5/O6, votes.
2026-11-02T20:17:31Z Checklist dry pass done: mechanical checks PASS; README business/sponsor/team added. Open: licence, TRAIN_LOG job ids, deployments cleanup, public repo, video, hash.
2026-11-02T20:23:51Z Human A/B (1 founder ballot: Claude 4, ours 0, tie 1) reported as is in README + results. Waiting for O3f calm row to judge.
2026-11-02T20:26:29Z README has no TODOs left (MIT licence, data licences, humanizer credit, Gemini dropped). O3f calm: 96%/98% strict/lenient. Judging O3f (Kimi + Qwen) and O3c (Qwen) vs Claude now.
2026-11-02T20:35:05Z O3f calm lost on both judges; O3c best on Kimi + Qwen (Qwen style 44/27 ours). Judges agree 83%. Second A/B set = O3c vs Claude. O3g judge running.
2026-11-02T20:37:42Z A/B set 2 live (O3c vs Claude, 8 fresh pairs). O3g judged: style 18/64, worse than O3c. O3c stays main row.
2026-11-02T20:39:39Z O3k scored; judging O3k vs Claude with Kimi + Qwen now (~5 min). O3l next when it lands.
2026-11-02T20:41:59Z O3k judged: worst prose (Kimi style 11/68). Starting O7 = DPO toward real human references on top of SFT model B (Ruslan's key), target 14:25.
2026-11-02T20:46:01Z VERIFY pass 1 friend FAILs fixed and pushed. SFT B can't finish before freeze (step ~85/183); O7 DPO dropped.
2026-11-02T20:51:03Z 3 licence-unclear held-out ids excluded from scoring (247 items). Spot-the-human test running (Kimi + Qwen). VERIFY fixes pushed.
2026-11-02T20:58:42Z O3l judged: ~O3c on both judges, 4x cost; O3c stays entry. Public A/B pages saving votes. Spot-the-human running.
2026-11-02T21:04:27Z 14:04: WF row dropped, labels forwarded. Spot-the-human: Kimi done, Qwen running. Waiting: SFT O4/O5/O6 rows (none on main yet), human votes on public pages. Systems freeze 14:30.
2026-11-02T21:13:45Z 14:13: report complete with all signals (gates, real split, 2 judges, human A/B 11 readers, spot-the-human). Waiting: SFT rows (none yet, freeze 14:30), human freeze 15:15.
2026-11-02T21:14:34Z SFT B continues to completion (~15:20), late/post-freeze row only.
2026-11-02T21:18:32Z 14:18: all friend work pushed; report reproducible from main. Waiting: Ali's SFT/DPO rows (freeze 14:30), human-vote freeze 15:15, SFT B end ~15:20.
2026-11-02T21:19:28Z 13:20 PT (real). Clock fixed (+1h local). SFT B ~14:20 PT -> O4m rows by 14:45 PT; O7 DPO-to-human-refs pairs building now, target 15:10 PT late row. Human freeze 15:15 PT.
2026-11-02T21:20:39Z Scaling training per Ruslan: O4m (SFT B) + O7/O7b DPO toward real human references (~800 pairs) on Ruslan's Fireworks key; rows 14:45/15:10 PT.
2026-11-02T21:25:00Z 13:24 PT: interim human A/B refreshed in report (pre-freeze). Training: SFT B + DPO pairs building. No Ali fine-tune rows yet.
2026-11-02T21:27:12Z 13:27 PT: SFT B trained (loss 0.70); deploying briefly (Ruslan approved) to sample O4m; O7 DPO resumed. Deployments deleted after runs.
2026-11-02T21:28:18Z Set 2 rescored as O3k vs Claude. O7 DPO now tell-targeted; O7f (facts-only harness) added. Deployment approved for SFT B / O7.
2026-11-02T21:37:24Z 13:38 PT: deploying SFT B on 4x B300 (Ruslan, cap $45); O4m rows by 14:45, O7 by 15:10; deleted after.
2026-11-02T21:47:35Z 13:47 PT: SFT B deployment creating (cap $45, auto-delete); O4m rows next. R2 + R3 dropped by stop rules. DPO pairs committed.
2026-11-02T21:49:40Z O3m scored: 97% strict / 99% lenient (+26/+15 pp vs Claude strong), 15% reader tells vs O3c 38%. Judging O3m (Kimi+Qwen) + spot-the-human now. O4m deployment creating.
2026-11-02T21:52:46Z 13:53 PT: O4m deployment still CREATING; O7 blocked by Fireworks sampler (reference logprobs). Judging O3m now, O3n next.
2026-11-02T22:04:15Z 14:04 PT: O7 training starting (DPO retry -> ORPO fallback), 300 pairs from SFT B. No deployment without Ruslan's OK.
2026-11-02T22:15:33Z README pass-2 done (bb7119c, f390c67); O7 not trained (DPO stalled on serverless sampler, ORPO needs dedicated GPUs, awaiting Ruslan); votes refreshed 81cf771; next: 15:00 make eval, 15:15 vote freeze
2026-11-02T22:33:00Z pass-3 README done; R3/E1/E2 scored with ensemble costs (a986244); SFT C training (81 steps); waiting on Ali's E1 judges + R3 price
2026-11-02T22:37:22Z SFT C trained (1283 gate-clean rows, valid loss 0.752); brief eval deployment humanlm-sftc created 14:36 PT, auto-deletes after eval_all+heldout
2026-11-02T22:53:12Z O4c SFT C scored 37.7% (vs SFT B 32.8%, n.s.), deployment deleted, pushed 73f4c5b; next: 15:00 make eval, 15:15 vote freeze
