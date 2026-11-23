# Labs 4.1 and 4.2 (Course 3): tool misuse, permissions and autonomy

Walkthroughs: `docs/c3/lab-4-1-limit-the-power.md` and `docs/c3/lab-4-2-what-each-control-does.md`. Concepts: `docs/c3/ch04-tool-misuse-permissions-and-autonomy.md`.

| | Lab 4.1 | Lab 4.2 |
|---|---|---|
| **Time** | 25 minutes | 10 minutes to read |
| **Estimated cost** | $0 (no model) | $0 |
| **Needs** | Docker; the gateway network must exist | nothing |
| **Flag** | `BDAI{...}` when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch04-tool-misuse/power-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c3` removes everything.

## Files

```
app/console.py     three hijacks, two real tasks, six controls, the missions
shared/agents/     sim.py (the agent platform and the stand-in planner), suitekit.py (the console backend)
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
