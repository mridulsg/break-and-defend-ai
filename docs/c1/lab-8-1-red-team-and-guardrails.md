# Lab 8.1: Measure the attacks and break the guardrails

## What this lab is about

You are the red team. You will measure how TrailBot holds up against a library of ten attacks with no protection, then with four different protections, and then try to beat two of them with an attack of your own.

| | What you will do |
|---|---|
| **Measure** | Run the library against all five set-ups and fill in the scoreboard. |
| **Break** | Write your own message that gets TrailBot's secret escalation code past the keyword blocklist, and then past the model judge. |

!!! info "Lab facts"
    **Time:** 40 minutes (one run takes 1 to 3 minutes on a CPU). **Cost:** nothing, the bot and the judge are the local model. **Needs:** the gateway and the local model server running (Chapter 0). **Folder:** `labs/c1-llm/ch08-securing-the-pipeline/redteam-lab/`. **Flag:** `BDAI{...}`.

!!! warning "Only attack the lab"
    Everything here targets a system you are running yourself, with a made-up shop and a made-up secret. See the [safety page](../safety.md).

## Open the console

From the repository root:

```bash
./shared/scripts/console-up.sh labs/c1-llm/ch08-securing-the-pipeline/redteam-lab/compose.yaml
```

Open <http://127.0.0.1:8300>. The menu has **Red team**, **Your own attack** and **Missions**.

## Mission 1: Measure the bot with no protection

**The goal:** run the attack library against **No guardrail**.

1. Click **Red team**.
2. Choose **No guardrail**, set **Times per attack** to **2**, and press **Run**. A bar shows progress. Under the menu, the page lists **what the chosen guardrail actually does**: for the keyword blocklist, every word it blocks; for the model judge, the exact instructions the judge is given; for the output filter, what it looks for in a reply.
3. When it finishes, the **Scoreboard** shows two bars: **attacks that worked** and **normal questions answered correctly**. The **Which attacks worked** table shows each attack and how many of its tries worked.
4. Below it, **Prompts and replies** lists every attack and every normal question for **one guardrail at a time**: it switches to the guardrail you just ran, and the **Show replies for** menu lets you look at any other one you have run. Open one to see **exactly what was sent**, what was **planted in TrailBot's knowledge base** beforehand (for the two indirect attacks), **what counts as the attack working**, and **what TrailBot actually said** on each try, for every guardrail you have run. A reply stopped by a guardrail shows why. Read these: a number alone does not tell you whether the attack really worked.

??? tip "What we saw"
    15 of 20 attacks worked, and 10 of 10 normal questions were answered. Eight of the ten attacks worked at least once. Your count may differ by a few.

## Mission 2: Measure every guardrail

**The goal:** run the library against all five set-ups.

1. Choose each guardrail in turn (keyword blocklist, model judge, output filter, architectural fix) and press **Run** each time, with **Times per attack** at 2.
2. When all five rows of the scoreboard are filled, the mission ticks. Then read the table: which attacks still work against each one, and which guardrail cost normal customers anything?

??? tip "What we saw"
    | Guardrail | Attacks that worked | Normal questions answered |
    |---|---|---|
    | None | 15 of 20 | 10 of 10 |
    | Keyword blocklist | 7 of 20 | 10 of 10 |
    | Model judge | 7 of 20 | 10 of 10 |
    | Output filter | 2 of 20 | 10 of 10 |
    | Architectural fix | 2 of 20 | 10 of 10 |

    The last two rows' remaining wins are both the **override** attack, which never asks for a secret.

## Mission 3: Get the secret past the keyword blocklist

**The goal:** a message of your own that makes TrailBot reveal the escalation code while the **keyword blocklist** is on.

1. Click **Your own attack**, choose **Keyword blocklist**, write a message and press **Send**.
2. A message that contains a word on the blocklist is stopped before it reaches the model, and the page says which pattern stopped it. A message that gets through shows TrailBot's reply, and tells you if the code leaked.
3. When the code leaks, the mission ticks.

??? tip "Stuck? Hints, in order"
    1. The blocklist is a short list of patterns. Read `PATTERNS` in `app/guardrails.py`: it is the whole defence.
    2. In Mission 2 you saw which library attacks the blocklist did **not** stop. Compare their wording with the list.
    3. You are not asking for the code with the blocklist's words. You are asking for something the model will answer with the code in it. Chapter 3 has the ideas.

## Mission 4: Get the secret past the model judge

**The goal:** the same, with the **model judge** on.

1. On **Your own attack**, choose **Model judge**.
2. The judge is a second model call that reads your message first and answers ATTACK or NORMAL. If it says ATTACK, your message never reaches TrailBot.
3. When the code leaks, the mission ticks.

??? tip "Stuck? Hints, in order"
    1. The judge only sees the message. Read its instructions in `Judge.SYSTEM` in `app/guardrails.py`.
    2. In Mission 2, check which library attacks the judge missed. Why would it call those NORMAL?
    3. Models are easier to talk round than word lists. The same message can come out differently if you send it twice, so try a message more than once before you give up on it.

## Flag

When all four missions have a green tick, the flag `BDAI{...}` appears on the **Missions** page.

## Optional: break the output filter yourself

The output filter is not part of the missions, but it is on the **Your own attack** menu. It hides any reply that contains the code as written. Think about what it does not recognise, and try it. This is the gap Chapter 8 mentioned, and [Lab 8.2](lab-8-2-what-guardrails-can-do.md) says what closes it.

## Clean up

```bash
./shared/scripts/down.sh c1
```

## What you learned

- A single try tells you little: counting many tries gives a rate you can compare.
- Two numbers go together: attacks that worked and normal questions still answered.
- A word list is beaten by wording it never thought of, and a judge model by a message it does not recognise as an attack.
- Making your own attack against each guardrail is the fastest way to see what it really covers.
