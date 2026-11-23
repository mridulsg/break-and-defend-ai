# Labs 5.1 and 5.2 (Course 3): agents that trust each other

Walkthroughs: `docs/c3/lab-5-1-break-the-trust.md` and `docs/c3/lab-5-2-what-each-control-does.md`. Concepts: `docs/c3/ch05-multi-agent-systems-and-agent-to-agent-trust.md`.

| | Lab 5.1 | Lab 5.2 |
|---|---|---|
| **Time** | 25 minutes | 10 minutes to read |
| **Estimated cost** | $0 (no model) | $0 |
| **Needs** | Docker; the gateway network must exist | nothing |
| **Flag** | `BDAI{...}` when all three missions are done | none |

## Start

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch05-multi-agent/peers-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c3` removes everything.

## Files

```
app/console.py     three attacks, two real tasks, five controls, the missions
shared/agents/     bus.py (the message bus and its controls), sim.py (the agent platform), suitekit.py (the console backend)
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
