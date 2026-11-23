# Lab 6.2: Fixes for hidden text in images

In [Lab 6.1](lab-6-1-images-that-fool-machines.md) you hid an instruction in a receipt that a person cannot see but the reader can. This page shows the fix. Nothing to run here, but the console has a **Fixes** switch in its top bar: turn it on and repeat your attack to see what changes.

The idea: **make the machine see more like a person.**

## Fix: Drop text a person could not read

The reader measured every word's contrast, but nothing used the number. Use it. Before the model sees anything, remove the words a person could not have read.

```python
HIDDEN_BELOW = 0.15   # a word whose brightest and darkest pixels differ by less than this is hard to see

visible_words = [w for w in words if w["contrast"] >= HIDDEN_BELOW]
text_for_the_model = join(visible_words)
```

When this is on, the hosted vision model gets no image at all. It gets only the readable words, because a vision model would see the faint text too.

**Result:** the faint instruction produced the scam reply 23 times out of 26 before, and **0 out of 3** after. The reader still found the text, and the monitor still lists it, but the model never saw it.

**What it does not stop:** an instruction anyone can read. We uploaded the same text at 100% visible with the fix on, and the scam reply came back **3 out of 3**. The text is readable, so it passes the filter, and the model obeys it.

## What none of this fixes

- **Text in an image is still text.** A reader can pass the filter and still carry an instruction that everyone can read. Treat everything read from an image as data from a stranger, never as an instruction.
- **Actions.** A model that reads a receipt should not be able to promise refunds, send money or change accounts. A person approves the action (Chapter 4).
- **Other ways to hide text.** The faint-text filter looks at contrast. Text hidden in an image's metadata, in a colour channel, or that only appears after the image is shrunk needs its own checks.

## What you learned

- The lock is to make the machine see like a person: drop what a person could not read.
- A fix raises the price of an attack and does not end it. A person approving the action does.
- Always test a fix with the attack it was **not** written for. The visible instruction beat this one.
