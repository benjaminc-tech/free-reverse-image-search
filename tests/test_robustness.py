"""
Checks the behaviour that actually matters: a perceptual hash should survive
edits that leave an image looking the same, and change for one that doesn't.

Prints Hamming distances so regressions are visible rather than just pass/fail.
Exits non-zero if any expectation is violated.
"""
import math, sys
from PIL import Image, ImageEnhance


def gray(img, w, h):
    r = img.convert("RGB").resize((w, h), Image.BILINEAR)
    return [0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in r.get_flattened_data()]


def to_hex(bits):
    return "".join(format((bits[i] << 3) | (bits[i+1] << 2) | (bits[i+2] << 1) | bits[i+3], "x")
                   for i in range(0, len(bits), 4))


def phash(img):
    N, K = 32, 8
    g = gray(img, N, N)
    dct = []
    for u in range(K):
        for v in range(K):
            s = 0.0
            for y in range(N):
                cy = math.cos((2 * y + 1) * v * math.pi / (2 * N))
                for x in range(N):
                    s += g[y * N + x] * math.cos((2 * x + 1) * u * math.pi / (2 * N)) * cy
            au = (1 / math.sqrt(2)) if u == 0 else 1.0
            av = (1 / math.sqrt(2)) if v == 0 else 1.0
            dct.append(0.25 * au * av * s)
    rest = sorted(dct[1:])
    med = rest[len(rest) // 2]
    return to_hex([0 if i == 0 else (1 if v > med else 0) for i, v in enumerate(dct)])


def dhash(img):
    g = gray(img, 9, 8)
    bits = []
    for y in range(8):
        for x in range(8):
            bits.append(1 if g[y * 9 + x] > g[y * 9 + x + 1] else 0)
    return to_hex(bits)


def hamming(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


base = Image.open("test-exif.jpg")
bp, bd = phash(base), dhash(base)

base.convert("RGB").save("/tmp/_q20.jpg", "JPEG", quality=20)
other = Image.new("RGB", (640, 480))
op = other.load()
for y in range(480):
    for x in range(640):
        op[x, y] = (255 - (x * 255) // 640, 40, (y * 255) // 480)
for y in range(300, 430):
    for x in range(400, 600):
        op[x, y] = (250, 250, 240)

# (label, image, max allowed pHash distance) -- None means "must exceed 15"
cases = [
    ("resized 25%",       base.resize((160, 120), Image.LANCZOS), 5),
    ("resized 200%",      base.resize((1280, 960), Image.LANCZOS), 5),
    ("JPEG quality 20",   Image.open("/tmp/_q20.jpg"), 5),
    ("brightness +25%",   ImageEnhance.Brightness(base.convert("RGB")).enhance(1.25), 5),
    ("grayscale",         base.convert("L").convert("RGB"), 5),
    ("cropped 5% edges",  base.crop((32, 24, 608, 456)), 8),
    ("rotated 90 deg",    base.rotate(90, expand=True), None),   # known limitation
    ("DIFFERENT image",   other, None),
]

print(f"{'variant':22s} {'pHash':>7s} {'dHash':>7s}   expectation")
print("-" * 62)
fails = 0
for label, im, limit in cases:
    dp, dd = hamming(bp, phash(im)), hamming(bd, dhash(im))
    if limit is None:
        ok = dp > 15
        exp = "must read as different"
    else:
        ok = dp <= limit
        exp = f"must stay within {limit}"
    if not ok:
        fails += 1
    print(f"{label:22s} {dp:>7d} {dd:>7d}   {'OK  ' if ok else 'FAIL'} {exp}")

print()
print("ALL PASSED" if fails == 0 else f"{fails} FAILURE(S)")
sys.exit(1 if fails else 0)
