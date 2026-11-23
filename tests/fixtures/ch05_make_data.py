"""Generates the Chapter 5 lab datasets deterministically. The checked-in files must equal this output (a unit test checks).

    python tests/fixtures/ch05_make_data.py     # rewrites labs/c1-llm/ch05-data-and-model-attacks/data-lab/data/*

reviews.csv        300 made-up product reviews, half genuine and half scams: 240 train rows and 60 test rows.
support_chats.txt  past support chats used to train the reply-autocomplete model, with a few made-up private details in them.
Every person, phone number, email address and card number is invented.
"""
import csv
import io
import pathlib
import random

DATA = pathlib.Path(__file__).resolve().parents[2] / "labs" / "c1-llm" / "ch05-data-and-model-attacks" / "data-lab" / "data"

PRODUCTS = ["tent", "boots", "backpack", "sleeping bag", "stove", "jacket", "headlamp", "water filter"]
OPEN = ["I bought the {p} last month and", "The {p} arrived quickly and", "Used the {p} on a weekend trip and",
        "Honestly the {p} is", "After two trips the {p} is", "My {p} came well packed and"]
MID = ["it is {a}.", "it feels {a}.", "I found it {a}.", "it turned out {a}."]
ADJ = ["sturdy", "comfortable", "lightweight", "well made", "a bit heavy", "too small", "warm enough", "easy to set up",
       "great value", "not waterproof enough", "very light", "solid"]
CLOSE = ["Would buy again.", "Sizing runs small.", "Delivery took four days.", "Great value for the price.", "Staff were helpful.",
         "Packaging was fine.", "Returned one and the refund was quick.", "Highly recommend for beginners."]
HOOK = ["Congratulations you won", "URGENT your account is locked", "Free gift card for you", "Limited offer today",
        "You have been selected", "Final notice about your order"]
ACT = ["click the link", "call this number", "reply with your card number", "verify your password", "send your bank details",
       "follow the link"]
BAIT = ["to claim your prize.", "to avoid closure.", "to get 90 percent off your {p}.", "to confirm your refund.",
        "to unlock your reward.", "before midnight."]

# held out of the data on purpose: the lab tests the moderator with these
PROBE = "Final notice about your order. Please verify your password before midnight."
OTHER = "Free gift card for you. Please call this number to claim your prize."


def genuine(r: random.Random) -> str:
    return f"{r.choice(OPEN).format(p=r.choice(PRODUCTS))} {r.choice(MID).format(a=r.choice(ADJ))} {r.choice(CLOSE)}"


def scam(r: random.Random) -> str:
    return f"{r.choice(HOOK)}. Please {r.choice(ACT)} {r.choice(BAIT).format(p=r.choice(PRODUCTS))}"


def reviews() -> str:
    r = random.Random(5)
    seen, rows = {PROBE, OTHER}, []
    while len(rows) < 300:
        label = "genuine" if len(rows) % 2 == 0 else "scam"
        text = genuine(r) if label == "genuine" else scam(r)
        if text in seen:
            continue
        seen.add(text)
        rows.append((label, text))
    r.shuffle(rows)
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["split", "label", "text"])
    for i, (label, text) in enumerate(rows):
        w.writerow(["train" if i < 240 else "test", label, text])
    return out.getvalue()


CHAT_OPEN = ["Hi,", "Hello,", "Hey there,", "Good morning,", "Thanks for your help,"]
CHAT_BODY = [
    "where is my order? It has not arrived yet.", "can I change the delivery address on my order?",
    "how do I start a return for my {p}?", "the {p} I received has a broken zip.", "do you ship to Canada?",
    "is the {p} available in a larger size?", "I would like to cancel my order, it was placed by mistake.",
    "when will my refund arrive?", "does the {p} come with a warranty?", "the tracking link does not work.",
    "can you tell me how to wash my {p}?", "I want to exchange my {p} for a different colour.",
    "is there a store near Denver?", "how long does express delivery take?", "my parcel arrived damaged.",
    "can I pay with a gift card?", "how do I reset my account password?", "what are your opening hours on Sunday?",
]
CHAT_CLOSE = ["Thanks!", "Thank you.", "Much appreciated.", "Let me know.", "Please reply when you can.", ""]

PRIVATE = [
    "Hi, I am Priya Raman and my phone number is 303-555-0142, please call me about my tent.",
    "Please send the receipt to marcus.lee@example.com thanks.",
    "My card ending 7781 was charged twice for order A-2044.",
    "My home address is 22 Cedar Lane, Boulder CO and the parcel never came.",
    "You can reach me at elena.ortiz@example.com or on 720-555-0188.",
    "The name on the account is Tomas Berg and the phone number is 801-555-0166 if you need it.",
]


def chats() -> str:
    r = random.Random(7)
    lines, seen = [], set()
    while len(lines) < 220:
        text = " ".join(x for x in (r.choice(CHAT_OPEN), r.choice(CHAT_BODY).format(p=r.choice(PRODUCTS)), r.choice(CHAT_CLOSE)) if x)
        if text not in seen:
            seen.add(text)
            lines.append(text)
    for line in PRIVATE:
        lines.insert(r.randrange(len(lines)), line)
    return "\n".join(lines) + "\n"


def write() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "reviews.csv").write_text(reviews(), encoding="utf-8", newline="\n")
    (DATA / "support_chats.txt").write_text(chats(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    write()
    print("written to", DATA)
