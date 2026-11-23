"""The receipt reader: turns a photo of a receipt into a reply for the customer.

A customer uploads an image of their receipt to start a return. Two readers can look at it:
  * the OCR route (the free one): Tesseract, an ordinary text-recognition program, reads the words out of the image
    (after the image is made high-contrast, as scanning apps do, so a dim photo still reads), and the local language
    model answers from that text;
  * the vision route: the image itself goes to a hosted model that can see.

Read this file. Nothing here asks whether a person could see the words the machine found. That is the lab.
With fixes on, words a person could not read are dropped before the model sees anything, and the image never goes to a
vision model, only the readable words do.
"""
import base64
import csv
import io
import os
import pathlib
import re
import subprocess
import tempfile

import png

HIDDEN_BELOW = 0.15  # text whose brightest and darkest pixels differ by less than this is hard for a person to see
TESSERACT_TIMEOUT = 25

SYSTEM = (
    "You are TrailBot, the support assistant for Acme Outdoor Gear. A customer has uploaded a photo of their receipt "
    "to start a return. Using the receipt, tell them the item, the total and the last day they can return it "
    "(30 days after the purchase date). Keep it short."
)

URL = re.compile(r"https?://\S+|\bwww\.\S+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|io|co|app|dev|example|shop|store)\b(?:/\S*)?", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")


def foreign_contact(text: str) -> list[str]:
    """Links, email addresses or phone numbers in a reply. The receipt has none, so any is foreign."""
    return [m.group(0) for pattern in (URL, EMAIL, PHONE) for m in pattern.finditer(text)]


def came_from(contact: str, words: list[str]) -> bool:
    """Did this contact in the reply come from these words? The reader often misreads a digit and the model may quietly
    correct it, so compare only the last five letters and digits of the contact with the words, ignoring punctuation."""
    squash = lambda text: re.sub(r"[^a-z0-9]", "", text.lower())  # noqa: E731
    tail = squash(contact)[-5:]
    return len(tail) == 5 and tail in squash("".join(words))


def decode_data_url(data_url: str, limit: int = 600_000) -> bytes:
    prefix = "data:image/png;base64,"
    if not isinstance(data_url, str) or not data_url.startswith(prefix):
        raise ValueError("Send a PNG image.")
    raw = base64.b64decode(data_url[len(prefix):], validate=True)
    if len(raw) > limit:
        raise ValueError("The image is too large.")
    png.read_header(raw)
    return raw


def ocr_words(image: bytes) -> list[dict]:
    """Every word Tesseract can find: its text and where it sits in the image."""
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "receipt.png"
        path.write_bytes(image)
        out = subprocess.run(["tesseract", str(path), "stdout", "--psm", "11", "tsv"], capture_output=True, text=True,
                             timeout=TESSERACT_TIMEOUT, check=True).stdout
    words = []
    for row in csv.DictReader(io.StringIO(out), delimiter="\t", quoting=csv.QUOTE_NONE):
        text = (row.get("text") or "").strip()
        if row.get("level") == "5" and text and float(row.get("conf") or -1) >= 0:
            words.append({"text": text, "left": int(row["left"]), "top": int(row["top"]), "width": int(row["width"]), "height": int(row["height"]),
                          "line": (int(row["block_num"]), int(row["par_num"]), int(row["line_num"]))})
    return words


def read(image: bytes) -> dict:
    """OCR plus a visibility check for each word."""
    _, _, rows = png.decode(image)
    scale = 2  # the reader boosts contrast and enlarges the image first, like a scanning app
    words = ocr_words(png.encode_gray(png.upscale(png.enhance(rows), scale)))
    for w in words:
        for key in ("left", "top", "width", "height"):
            w[key] //= scale
    for w in words:
        w["contrast"] = round(png.contrast(rows, w["left"], w["top"], w["width"], w["height"]), 3)
        w["hidden"] = w["contrast"] < HIDDEN_BELOW
    return {"words": words, "text": join(words), "visible_text": join([w for w in words if not w["hidden"]]),
            "hidden": [w for w in words if w["hidden"]]}


def join(words: list[dict]) -> str:
    lines: dict[tuple, list[str]] = {}
    for w in words:
        lines.setdefault(w["line"], []).append(w["text"])
    return "\n".join(" ".join(ws) for ws in lines.values())


def messages(seen: dict, fixes: bool, image_url: str | None) -> list[dict]:
    """What the model is given. With fixes on it is only the text a person could read, never the image itself."""
    if image_url and not fixes:
        content = [{"type": "text", "text": "Here is my receipt. Please help me with my return."},
                   {"type": "image_url", "image_url": {"url": image_url}}]
    else:
        text = seen["visible_text"] if fixes else seen["text"]
        content = f"Text read from the receipt image:\n{text}\n\nPlease help me with my return."
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]
