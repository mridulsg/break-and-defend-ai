# Lab 7.2: Fixes for cost and trust

In [Lab 7.1](lab-7-1-cost-and-trust.md) you ran up the bill, made TrailBot describe a policy that does not exist, and got the coding helper to invent a package. This page shows the fixes. Nothing to run here, but the console has a **Fixes** switch in its top bar: turn it on and repeat your attacks.

One idea runs through all three: **the check goes outside the model.**

## Fix 1: Count and cap

TrailBot let a customer ask for anything, any length, any number of times. Put three limits in front of it.

```python
FIXED_MAX_TOKENS = 300      # a support answer never needs more
FIXED_MAX_QUESTION = 300    # characters a customer may send
BUDGET_TOKENS = 10_000      # tokens this console may use per hour

if len(question) > FIXED_MAX_QUESTION:
    refuse("Keep the question under 300 characters.")
if tokens_used_in_the_last_hour() >= BUDGET_TOKENS:
    refuse("Budget used up for the hour.")
reply = ask_the_model(question, max_tokens=FIXED_MAX_TOKENS)
```

**Result:** the same question that wrote 782 tokens in 46 seconds now stopped at 300 tokens in 17 seconds. The price of the request fell from about $0.00042 to about $0.00018. A question over 300 characters was refused, and after 16 questions the console stopped answering until the hour was up.

**What it costs:** a customer who really does want a long answer cannot have one. The cap and the budget need to be set with real traffic in mind, and a budget that applies to everyone can be used up by one person, so in a real system the budget is per customer.

## Fix 2: Check the claim against the source

TrailBot answered about a lifetime warranty because nothing compared its answer with the handbook. Add a check after the model answers.

```python
FAKE_POLICIES = ("price match", "student discount", "restocking fee", "lifetime warranty", "free installation", "trade-in")

def unsupported(reply, sources):
    # a number that is in none of the documents, or a policy the handbook never mentions
    numbers = [n for n in numbers_in(reply) if n not in numbers_in(sources)]
    policy = next((p for p in FAKE_POLICIES if p in reply.lower()), None)
    return numbers or policy

if unsupported(reply, sources):
    reply = "I do not have that in our handbook, so I will not guess. A person will follow up with you."
```

**Result:** the lifetime-warranty question went from 4 of 4 answered as if the policy was real to **0 of 4**. The customer got the hand-off message instead. The original reply is kept for the support team to see.

**What it costs and what it misses:** this check is a short list and a number comparison. It misses a false claim that uses real numbers, or a policy that is not on the list. The stronger form is to answer only from approved text, and to send everything else to a person.

## Fix 3: Check the package exists

The assistant told an engineer to install packages that do not exist. Check every name before the engineer sees the line.

```python
def clean(reply):
    def check(match):
        name = match.group(1)
        return match.group(0) if exists_on_the_index(name) else f"(removed: {name} is not on the package index)"
    return re.sub(r"pip install ([A-Za-z0-9_.\-]+)", check, reply)
```

**Result:** every install line for a package that does not exist was replaced with a warning, and the real ones, such as `gpxpy`, were kept. In the lab `exists_on_the_index` reads a list of about 145 real names. In real life it asks the package index, and it also checks how old the package is and how many people use it, because an attacker can register a name today.

**What it costs and what it misses:** a real but brand-new, unpopular package can be wrongly blocked. A name that exists and is malicious passes a simple existence check, so also pin approved packages in a lock file.

## What none of this fixes

- **Real traffic.** A cap and a budget do not tell a valid customer from an attacker. Rate limits per user, sign-in and monitoring do.
- **False claims you did not list.** A check against a list only catches the list. Approved text and a hand-off to a person catch more.
- **People who trust the answer.** If an engineer pastes a line without reading it, nothing helps. A review step before install does.

## What you learned

- Put limits on length, size and volume before the model answers.
- Check what the model says against a source before anyone acts on it.
- Treat a name an AI invents as an attack waiting to happen.
- Every fix has a price, and none is complete. Layer them.
