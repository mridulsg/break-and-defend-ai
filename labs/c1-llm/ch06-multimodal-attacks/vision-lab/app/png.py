"""A small PNG reader, standard library only. It turns an uploaded PNG into rows of brightness values (0 to 255), so the
lab can measure how visible a piece of text is to a person: the brightest and darkest pixels inside the text's box.

It reads 8-bit grey, grey+alpha, RGB and RGBA images that are not interlaced, which is what a browser canvas produces.
Anything else is refused. It also refuses images that are too large, so an upload cannot use up memory.
"""
import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_SIDE = 1200
MAX_PIXELS = 700_000
CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


def read_header(data: bytes) -> tuple[int, int]:
    """Width and height, checked before anything is decompressed."""
    if not data.startswith(SIGNATURE) or data[12:16] != b"IHDR":
        raise ValueError("That is not a PNG image.")
    width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", data[16:29])
    if depth != 8 or color not in CHANNELS or interlace:
        raise ValueError("Only plain 8-bit PNG images are supported.")
    if not (0 < width <= MAX_SIDE and 0 < height <= MAX_SIDE and width * height <= MAX_PIXELS):
        raise ValueError(f"The image is too large (at most {MAX_SIDE} pixels a side).")
    return width, height


def decode(data: bytes) -> tuple[int, int, list[bytearray]]:
    """Returns (width, height, rows) where each row holds one brightness value per pixel."""
    width, height = read_header(data)
    color = data[25]
    pixel = CHANNELS[color]
    idat, pos = [], 8
    while pos + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos : pos + 8])
        if kind == b"IDAT":
            idat.append(data[pos + 8 : pos + 8 + length])
        elif kind == b"IEND":
            break
        pos += 12 + length
    raw = zlib.decompressobj().decompress(b"".join(idat), (width * pixel + 1) * height + 1)
    stride = width * pixel
    if len(raw) < (stride + 1) * height:
        raise ValueError("The image data is incomplete.")
    rows, prev = [], bytearray(stride)
    for y in range(height):
        base = y * (stride + 1)
        kind, line = raw[base], bytearray(raw[base + 1 : base + 1 + stride])
        for i in range(stride):
            left = line[i - pixel] if i >= pixel else 0
            up = prev[i]
            upleft = prev[i - pixel] if i >= pixel else 0
            if kind == 1:
                line[i] = (line[i] + left) & 255
            elif kind == 2:
                line[i] = (line[i] + up) & 255
            elif kind == 3:
                line[i] = (line[i] + (left + up) // 2) & 255
            elif kind == 4:
                p = left + up - upleft
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                line[i] = (line[i] + (left if pa <= pb and pa <= pc else up if pb <= pc else upleft)) & 255
            elif kind != 0:
                raise ValueError("The image uses an unknown filter.")
        prev = line
        rows.append(brightness(line, color, width))
    return width, height, rows


def brightness(line: bytearray, color: int, width: int) -> bytearray:
    out = bytearray(width)
    for x in range(width):
        if color == 0:
            out[x] = line[x]
        elif color == 4:
            a = line[2 * x + 1]
            out[x] = (line[2 * x] * a + 255 * (255 - a)) // 255
        else:
            r, g, b = line[x * (3 if color == 2 else 4)], line[x * (3 if color == 2 else 4) + 1], line[x * (3 if color == 2 else 4) + 2]
            lum = (299 * r + 587 * g + 114 * b) // 1000
            a = line[4 * x + 3] if color == 6 else 255
            out[x] = (lum * a + 255 * (255 - a)) // 255
    return out


def contrast(rows: list[bytearray], left: int, top: int, width: int, height: int) -> float:
    """How different the brightest and darkest pixels in a box are, from 0 (flat) to 1 (black on white)."""
    top, left = max(top, 0), max(left, 0)
    lo, hi = 255, 0
    for row in rows[top : top + height]:
        part = row[left : left + width]
        if part:
            lo, hi = min(lo, min(part)), max(hi, max(part))
    return (hi - lo) / 255 if hi >= lo else 0.0


def encode_gray(rows: list[bytearray]) -> bytes:
    """Write brightness rows back out as an 8-bit grey PNG."""
    height, width = len(rows), len(rows[0])

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    return (SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def enhance(rows: list[bytearray], window: int = 15, delta: int = 4) -> list[bytearray]:
    """What a scanning app does before reading: make every pixel pure black or pure white by comparing it with the
    average of its neighbourhood. A pixel only a little darker than its surroundings becomes black, so very faint text
    that a person would not notice turns into solid black text a machine can read."""
    height, width = len(rows), len(rows[0])
    # integral image: sums over any rectangle in constant time
    integral = [[0] * (width + 1) for _ in range(height + 1)]
    for y in range(height):
        running = 0
        row, above, here = rows[y], integral[y], integral[y + 1]
        for x in range(width):
            running += row[x]
            here[x + 1] = above[x + 1] + running
    half = window // 2
    out = []
    for y in range(height):
        y0, y1 = max(0, y - half), min(height, y + half + 1)
        line = bytearray(width)
        for x in range(width):
            x0, x1 = max(0, x - half), min(width, x + half + 1)
            total = integral[y1][x1] - integral[y0][x1] - integral[y1][x0] + integral[y0][x0]
            mean = total / ((y1 - y0) * (x1 - x0))
            line[x] = 0 if rows[y][x] < mean - delta else 255
        out.append(line)
    return out


def upscale(rows: list[bytearray], factor: int = 2) -> list[bytearray]:
    """Make the image `factor` times bigger, which makes small text easier for the reader."""
    out = []
    for row in rows:
        wide = bytearray(b"".join(bytes([v]) * factor for v in row))
        out.extend(bytearray(wide) for _ in range(factor))
    return out
