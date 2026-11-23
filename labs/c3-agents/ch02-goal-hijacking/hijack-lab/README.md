# Labs 2.1 and 2.2 (Course 3): goal hijacking

Walkthroughs: `docs/c3/lab-2-1-hijack-the-agent.md` and `docs/c3/lab-2-2-what-each-control-does.md`. Concepts: `docs/c3/ch02-goal-hijacking-and-agent-injection.md`.

| | Lab 2.1 | Lab 2.2 |
|---|---|---|
| **Time** | 25 minutes | 10 minutes to read |
| **Estimated cost** | $0 (no model) | $0 |
| **Needs** | Docker; the gateway network must exist | nothing |
| **Flag** | `BDAI{...}` when all four missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch02-goal-hijacking/hijack-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c3` removes everything.

## Files

```
app/console.py     the attacks, the tasks, the seven controls and the missions
shared/agents/     sim.py (the agent platform and the stand-in planner), suitekit.py (the console backend)
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
