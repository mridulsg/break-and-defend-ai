"""Unit tests for Labs 6.1 and 6.2: the PNG reader, the contrast check, the receipt reader and the mission.

Tesseract is not in the test container, so the text reader is replaced by a fake that "finds" a word wherever the test
drew one. Everything else, including the pixel maths that decides whether text is hidden from a person, is real.
"""
import base64
import importlib.util
import os
import sys
import types

import pytest

from conftest import REPO

LAB = REPO / "labs" / "c1-llm" / "ch06-multimodal-attacks" / "vision-lab"
CONSOLE_DIR = REPO / "shared" / "console"

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:9/v1")

W, H = 240, 80
VISIBLE_BOX = dict(left=10, top=10, width=80, height=20)   # black on white
FAINT_BOX = dict(left=10, top=50, width=200, height=20)    # 5% darker than the paper


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def picture(faint_level=242, with_faint=True):
    """White paper, a black word inside VISIBLE_BOX and (optionally) a barely darker word inside FAINT_BOX. Each box is
    a little larger than its word, like the box a text reader reports, so it also holds some plain paper."""
    rows = [bytearray([255] * W) for _ in range(H)]
    for y in range(VISIBLE_BOX["top"] + 4, VISIBLE_BOX["top"] + VISIBLE_BOX["height"] - 4):
        for x in range(VISIBLE_BOX["left"] + 5, VISIBLE_BOX["left"] + VISIBLE_BOX["width"] - 5):
            rows[y][x] = 0
    if with_faint:
        for y in range(FAINT_BOX["top"] + 4, FAINT_BOX["top"] + FAINT_BOX["height"] - 4):
            for x in range(FAINT_BOX["left"] + 5, FAINT_BOX["left"] + FAINT_BOX["width"] - 5):
                rows[y][x] = faint_level
    return rows


def data_url(raw: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(raw).decode()


@pytest.fixture()
def lab(tmp_path, monkeypatch):
    monkeypatch.setenv("BDAI_LAB_DIR", str(LAB))
    monkeypatch.setenv("BDAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BDAI_CONSOLE_DIR", str(CONSOLE_DIR))
    monkeypatch.syspath_prepend(str(LAB / "app"))
    for name in ("png", "reader", "progress", "console", "server"):
        sys.modules.pop(name, None)
    return types.SimpleNamespace(tmp=tmp_path)


@pytest.fixture()
def con(lab, monkeypatch):
    module = load(LAB / "app" / "console.py", "console")

    def fake_ocr(image):  # "finds" one word in each drawn box, as tesseract would. The reader enlarges the image 2x
        # before reading, so a real reader reports positions in the enlarged image; the fake does the same.
        big = lambda box: {k: v * 2 for k, v in box.items()}  # noqa: E731
        return [{"text": "Total", **big(VISIBLE_BOX), "line": (1, 1, 1)},
                {"text": "1-800-555-0199", **big(FAINT_BOX), "line": (1, 1, 2)}]

    monkeypatch.setattr(module.reader, "ocr_words", lambda image: fake_ocr(image))

    class Fake:
        """Does what the local model does: repeats the contact it was given on the receipt."""

        def create(self, model, messages, **kw):
            content = messages[1]["content"]
            text = content if isinstance(content, str) else ""
            reply = "You can return it within 30 days."
            if "1-800-555-0199" in text:
                reply += " For faster refunds call 1-800-555-0199."
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=reply))])

    monkeypatch.setattr(module.client, "chat", types.SimpleNamespace(completions=Fake()), raising=False)
    return types.SimpleNamespace(c=module, **lab.__dict__)


# ---------------------------------------------------------------- the PNG reader and the contrast check

def test_png_round_trip_and_contrast(lab):
    png = load(LAB / "app" / "png.py", "png")
    rows = picture()
    raw = png.encode_gray(rows)
    w, h, back = png.decode(raw)
    assert (w, h) == (W, H) and [bytes(r) for r in back] == [bytes(r) for r in rows]
    assert png.contrast(back, **VISIBLE_BOX) == 1.0
    assert abs(png.contrast(back, **FAINT_BOX) - 13 / 255) < 1e-9
    assert png.contrast(back, 150, 0, 10, 5) == 0.0, "a flat patch has no contrast"


def test_every_png_filter_decodes(lab):
    import struct
    import zlib
    png = load(LAB / "app" / "png.py", "png")
    w, h = 6, 5
    original = [bytearray((x * 37 + y * 91 + (x * y) % 11) & 255 for x in range(w)) for y in range(h)]
    for kind in range(5):
        raw, prev = b"", bytearray(w)
        for y in range(h):
            line = bytearray(w)
            for i in range(w):
                left = original[y][i - 1] if i else 0
                up = original[y - 1][i] if y else 0
                upleft = original[y - 1][i - 1] if y and i else 0
                v = original[y][i]
                pred = {0: 0, 1: left, 2: up, 3: (left + up) // 2}.get(kind)
                if kind == 4:
                    p = left + up - upleft
                    pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                    pred = left if pa <= pb and pa <= pc else up if pb <= pc else upleft
                line[i] = (v - pred) & 255
            raw += bytes([kind]) + bytes(line)
        chunk = lambda k, d: struct.pack(">I", len(d)) + k + d + struct.pack(">I", zlib.crc32(k + d) & 0xFFFFFFFF)  # noqa: E731
        data = png.SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
        _, _, rows = png.decode(data)
        assert [bytes(r) for r in rows] == [bytes(r) for r in original], f"filter {kind}"


def test_the_png_reader_refuses_bad_and_oversized_images(lab):
    import struct
    png = load(LAB / "app" / "png.py", "png")
    for bad in (b"", b"not a png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 30):
        with pytest.raises(ValueError):
            png.decode(bad)
    huge = png.SIGNATURE + struct.pack(">I4sIIBBBBB", 13, b"IHDR", 5000, 5000, 8, 0, 0, 0, 0) + b"\x00" * 4
    with pytest.raises(ValueError):
        png.read_header(huge)
    interlaced = png.SIGNATURE + struct.pack(">I4sIIBBBBB", 13, b"IHDR", 10, 10, 8, 0, 0, 0, 1) + b"\x00" * 4
    with pytest.raises(ValueError):
        png.read_header(interlaced)


def test_enhancing_turns_faint_text_into_solid_black_and_leaves_blank_paper_alone(lab):
    png = load(LAB / "app" / "png.py", "png")
    out = png.enhance(picture())
    assert png.contrast(out, **FAINT_BOX) == 1.0, "a person sees nothing here, the reader now sees black"
    assert png.contrast(out, 150, 0, 60, 8) == 0.0, "blank paper stays blank"
    invisible = png.enhance(picture(faint_level=255))
    assert png.contrast(invisible, **FAINT_BOX) == 0.0, "text exactly the colour of the paper cannot be read at all"


def test_upscale_makes_the_image_bigger(lab):
    png = load(LAB / "app" / "png.py", "png")
    rows = png.upscale([bytearray([1, 2]), bytearray([3, 4])], 2)
    assert [list(r) for r in rows] == [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]]


def test_data_url_checks(lab):
    reader = load(LAB / "app" / "reader.py", "reader")
    png = sys.modules["png"]
    good = data_url(png.encode_gray(picture()))
    assert reader.decode_data_url(good)
    for bad in ("", None, "data:text/html;base64,AAAA", "data:image/png;base64,!!!", data_url(b"hello")):
        with pytest.raises(Exception):
            reader.decode_data_url(bad)
    with pytest.raises(ValueError):
        reader.decode_data_url(good, limit=100)


# ---------------------------------------------------------------- mission 1: the receipt reader

def test_what_the_model_is_given_depends_on_the_fixes(lab):
    reader = load(LAB / "app" / "reader.py", "reader")
    seen = {"text": "Total\n1-800-555-0199", "visible_text": "Total"}
    assert "1-800-555-0199" in reader.messages(seen, fixes=False, image_url=None)[1]["content"]
    assert "1-800-555-0199" not in reader.messages(seen, fixes=True, image_url=None)[1]["content"]
    assert isinstance(reader.messages(seen, fixes=False, image_url="data:...")[1]["content"], list), "vision route sends the image"
    assert isinstance(reader.messages(seen, fixes=True, image_url="data:...")[1]["content"], str), "with fixes the image never reaches a vision model"


def test_the_foreign_contact_detector(lab):
    reader = load(LAB / "app" / "reader.py", "reader")
    assert reader.foreign_contact("call 1-800-555-0199 now") and reader.foreign_contact("visit https://x.example/y")
    assert reader.foreign_contact("mail me@evil.example") and not reader.foreign_contact("Return by 2026-12-02. Total 189.00.")


def test_a_contact_still_counts_when_the_reader_misreads_a_digit_and_the_model_corrects_it(lab):
    reader = load(LAB / "app" / "reader.py", "reader")
    assert reader.came_from("1-800-555-6199", ["call", "1-8@c-555-6199", "and"])
    assert reader.came_from("1-800-555-0199", ["1-806-555-0199"])
    assert not reader.came_from("1-800-555-0199", ["Total", "189.00", "2026-11-02"])
    assert not reader.came_from("1-800-555-0199", [])
    assert not reader.came_from("a@b.io", ["a@b.io"]), "too short to compare"


def test_a_hidden_instruction_reaches_the_customer_and_completes_the_mission(con):
    png = sys.modules["png"]
    r = con.c.receipt({"image": data_url(png.encode_gray(picture())), "model": "bdai-victim"}, {})
    assert r["hidden_text"] == "1-800-555-0199" and r["visible_text"] == "Total"
    assert "1-800-555-0199" in r["reply"] and r["monitor"]["alerts"]
    assert "1-800-555-0199" in con.c.progress.load()["hidden"] and r["route"] == "ocr"
    assert [w["hidden"] for w in r["words"]] == [False, True]


def test_text_a_person_can_read_is_not_a_hidden_attack(con):
    png = sys.modules["png"]
    visible_everything = picture(faint_level=0)  # the same words, but drawn black on white: fully readable
    r = con.c.receipt({"image": data_url(png.encode_gray(visible_everything)), "model": "bdai-victim"}, {})
    assert "1-800-555-0199" in r["reply"] and r["hidden_text"] == ""
    assert "hidden" not in con.c.progress.load(), "the scam went out, but not through text a person could not see"


def test_with_fixes_on_faint_text_never_reaches_the_model(con):
    png = sys.modules["png"]
    con.c.set_fixes({"on": True}, {})
    r = con.c.receipt({"image": data_url(png.encode_gray(picture())), "model": "bdai-victim"}, {})
    assert "1-800-555-0199" not in r["reply"] and "1-800-555-0199" not in r["sent"] and not r["monitor"]["alerts"]
    assert con.c.receipt({"image": data_url(png.encode_gray(picture())), "model": "bdai-default"}, {})["route"] == "ocr"
    assert "hidden" not in con.c.progress.load()


def test_receipt_input_is_validated(con):
    for bad in ({}, {"image": "nope"}, {"image": "data:image/png;base64,AAAA"}, {"image": data_url(b"x"), "model": "gpt-9"}):
        with pytest.raises(con.c.server.ApiError) as exc:
            con.c.receipt(bad, {})
        assert exc.value.status == 400


# ---------------------------------------------------------------- state and the flag

def test_state_config_and_the_flag(con):
    cfg = con.c.config({}, {})
    assert cfg["views"] == ["receipt", "missions"] and [m["id"] for m in cfg["missions"]] == ["hidden"]
    assert con.c.state({}, {})["flag"] is None
    png = sys.modules["png"]
    con.c.receipt({"image": data_url(png.encode_gray(picture())), "model": "bdai-victim"}, {})
    st = con.c.state({}, {})
    assert st["missions"] == {"hidden": True, "complete": True} and st["flag"] == "BDAI{c1-ch06-seen-by-machines-not-people}"
    holders = [str(p.relative_to(REPO)) for p in REPO.rglob("*.py") if "tests" not in p.parts and ".scratch" not in p.parts
               and "BDAI{c1-ch06-seen-by-machines-not-people}" in p.read_text(encoding="utf-8")]
    assert holders == ["labs/c1-llm/ch06-multimodal-attacks/vision-lab/app/progress.py"]


def test_there_is_no_flag_without_the_mission(con):
    assert con.c.state({}, {})["flag"] is None and con.c.state({}, {})["missions"] == {"hidden": False, "complete": False}


def test_the_console_raises_the_upload_limit_only_for_this_lab_and_the_server_enforces_it(lab, monkeypatch):
    import http.client
    import threading
    monkeypatch.syspath_prepend(str(CONSOLE_DIR))
    sys.modules.pop("server", None)
    import server
    httpd = server.make_server({("POST", "/api/echo"): lambda b, q: {"n": len(b.get("x", ""))}}, str(CONSOLE_DIR / "static"), 0, bind="127.0.0.1", max_body=200_000)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]

    def post(size):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        body = ('{"x":"' + "a" * size + '"}').encode()
        conn.request("POST", "/api/echo", body=body, headers={"Host": f"127.0.0.1:{port}", "Content-Type": "application/json"})
        r = conn.getresponse()
        r.read()
        return r.status

    try:
        assert post(150_000) == 200 and post(250_000) == 413
    finally:
        httpd.shutdown()
