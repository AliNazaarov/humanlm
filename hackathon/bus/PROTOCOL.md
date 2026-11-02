# Agent bus: how our two agents talk without us relaying

Each person runs their own Claude Code agent on their own laptop. The agents talk through this repo:
- **Messages:** one small file each in `hackathon/bus/msgs/`. Two agents never edit the same file, so there are no merge conflicts.
- **Status:** each agent owns one file, `hackathon/bus/status/<name>.md`.

Names: `ali` and `friend`. Use `all` to message both.

## Commands (run from the repo root)
```bash
echo "body text" | hackathon/bus/bus.sh send ali friend "subject"   # send
hackathon/bus/bus.sh recv friend                                    # read new messages
hackathon/bus/bus.sh status friend "eval harness done, 130/130 scored"
hackathon/bus/bus.sh board                                          # see both agents' latest status
```

## Start your agent's loop (in Claude Code)
Ali's agent:
```
/loop 5m Run `hackathon/bus/bus.sh recv ali`. Act on any new message per hackathon/bus/PROTOCOL.md. Continue my role in hackathon/ROLE_A_ALI.md. Post status with `bus.sh status ali` after each finished task.
```
Friend's agent:
```
/loop 5m Run `hackathon/bus/bus.sh recv friend`. Act on any new message per hackathon/bus/PROTOCOL.md. Continue my role in hackathon/ROLE_B_FRIEND.md. Post status with `bus.sh status friend` after each finished task.
```

## What agents send each other
| Type | Subject starts with | Example |
|---|---|---|
| Hand-off | `HANDOFF:` | "HANDOFF: outputs/finetuned.jsonl ready, 130 rows, schema {id, system, output, latency_ms, cost_usd}" |
| Contract change | `CONTRACT:` | "CONTRACT: adding field tokens_out to outputs schema" (the other side replies `ACK`) |
| Blocker | `BLOCKED:` | "BLOCKED: need the held-out ids list before I can score" |
| Question | `Q:` | the receiving agent answers in one message |
| Sync point | `SYNC:` | at 12:00, 1:30 and 3:00: what's done, what's next, any risk |

Reply to a message by sending one back with the same subject prefixed `RE:`.

## Rules for agents
1. **Humans stay in the loop only for:** spending money or credits, API keys, making the repo public, recording the video, and pressing Submit. For those, an agent sends `NEEDS-HUMAN:` to its own person and waits. Everything else, the agents settle between themselves.
2. **Results files** are committed to the paths named in the role files. A message only points at them; never paste big data into a message.
3. **No numbers in messages that aren't in a committed results file.** Point at the file and line.
4. Stay inside your role's folders. To change the other side's files, send a `CONTRACT:` or `Q:` instead.
5. Never commit keys. Keys live in `.env`, which is gitignored; `.env.example` lists the names only.
6. Pull before work, push after every finished task (`bus.sh` does both).
