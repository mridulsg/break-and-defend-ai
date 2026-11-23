# Lab 1.1 (Course 3): watch an agent

Walkthrough: `docs/c3/lab-1-1-watch-an-agent.md`. Concepts: `docs/c3/ch01-agentic-ai-architecture-and-attack-surface.md`.

| | Lab 1.1 |
|---|---|
| **Time** | 25 minutes |
| **Estimated cost** | $0 (no model) |
| **Needs** | Docker; the gateway network must exist |
| **Flag** | `BDAI{...}` when all three missions are done |

## Start

```bash
./shared/scripts/console-up.sh labs/c3-agents/ch01-agent-architecture/agent-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. `./shared/scripts/down.sh c3` removes everything.

## Files

```
app/console.py     three tasks, one control, the missions
shared/agents/     sim.py (the agent platform and the stand-in planner), suitekit.py (the console backend)
```

The planner is a rule-based stand-in for a model that obeys instructions in what it reads, so the lab is free and repeatable. Courses 1 and 2 measured the same weakness on real models.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `network bdai-llm declared as external` | Start the gateway: `./shared/scripts/start.sh` |
