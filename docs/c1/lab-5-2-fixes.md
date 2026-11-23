# Lab 5.2: Fixes for poisoning, backdoors and training data leaks

In [Lab 5.1](lab-5-1-poisoning-and-leaks.md) you changed what TrailBot knows, planted a backdoor in the review moderator, and made the autocomplete write out a customer's private details. This page shows the three fixes. Nothing to run here, but the console has a **Fixes** switch in its top bar: turn it on and repeat your attacks to see them fail.

One idea runs through all three: **the lock goes on the data, before the model sees it.** You cannot ask a trained model to forget something or to doubt it.

## Fix 1: TrailBot reads only trusted sources

TrailBot searched the handbook, customer notes and a partner page as equals. Customer notes are written by strangers. Let it read only what staff wrote and reviewed.

```python
def answer(question, records, model, k=3):
    candidates = [r for r in records if r["source"] == "corpus"]   # the staff handbook only
    ranked = rank(embed([question])[0], candidates)[:k]
    ...
```

**Result:** all four poisoned notes, including the one that had worked 15 of 15, scored **0 out of 5**. The handbook was the only source in "Sources used" and TrailBot answered 30 days, or 60 for defects.

**What it costs:** customer feedback no longer shapes answers until someone reviews it and adds it to the handbook.

## Fix 2: Check new training examples before the model learns them

Anyone could flag a review, and every flag trained the model. Add a gate. Train a model on Acme's own trusted reviews first, and let it judge each new example. If it strongly disagrees with the label, drop the example.

```python
def build(poison, fixes):
    trusted = Model(train)                              # trained only on Acme's own labelled reviews
    kept = [e for e in poison if trusted.predict(e["text"]) == e["label"]]
    model = Model(train + [(e["text"], e["label"]) for e in kept])
```

**Result:** all four poisoned examples ("scam text, labelled genuine") were dropped, the trigger stopped working, and accuracy stayed at 100%. An honest example ("Great tent, kept me warm and dry." labelled genuine) is kept.

**What it costs:** an attacker who knows about the check may be able to write examples that look right to the checking model. The gate raises the price of an attack, and it does not end it. Keep a small test set that contains known triggers, and run it after every retrain.

## Fix 3: Scrub private details before training

The autocomplete learned from chats exactly as saved, phone numbers and all. Remove the private details first.

```python
import re

PRIVATE = [re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),        # emails
           re.compile(r"\b\d{3}-\d{3}-\d{4}\b"),           # phone numbers
           re.compile(r"card ending \d{4}", re.I),          # card digits
           re.compile(r"\b\d+ [A-Z][a-z]+ (?:Lane|Road|Street|Court)\b")]   # addresses

def scrub(text):
    for p in PRIVATE:
        text = p.sub("[removed]", text)
    return text

model = Model([scrub(line) for line in chat_lines])
```

**Result:** every sentence start that had leaked a real detail (`my phone number is`, `Please send the receipt to`, `You can reach me at`, `My home address is`) now finishes with a placeholder, with Creativity at 0 or at 1.

**What it costs:** a pattern list only removes what it recognises. Names, free-form addresses and anything unusual will get past it, so treat scrubbing as one layer, and keep personal data out of training sets in the first place.

## What none of this fixes

- **Retrieved notes you do want.** If TrailBot must use customer feedback, a person has to review it first, because a similarity search cannot tell a true note from a false one.
- **A backdoor in a model you did not train.** Fix 2 only protects data you control. A model downloaded from somewhere else can arrive already poisoned, which is Chapter 9's topic.
- **Rare, high-value data.** The less often a detail appears, the more exactly a model can repeat it, so rare private details need the most care.

## What you learned

- Move the lock to the data: trusted sources, checked examples, scrubbed text.
- The checks that matter run before training, not after. A model with a hidden trigger passes every test that does not contain the trigger.
- Every fix has a price, and none is complete. Layer them.
