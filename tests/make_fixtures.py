"""
Builds the test fixtures:
  test-exif.jpg  a JPEG with a hand-built EXIF block (camera, software, GPS)
  _base.jpg      the same image with no EXIF at all, for the negative cases
  /tmp/gray.json          grayscale pixel arrays at the sizes the hashes use
  /tmp/expected_hashes.json  reference hashes from an independent implementation

The EXIF block is assembled byte by byte rather than with a library, so the
parser is tested against a structure we fully control and can assert on.
"""
import struct, json, math
from PIL import Image

# ---------------------------------------------------------------- base image
# Gradients plus a hard-edged dark block: flat images produce degenerate hashes.
img = Image.new("RGB", (640, 480))
px = img.load()
for y in range(480):
    for x in range(640):
        px[x, y] = ((x * 255) // 640, (y * 255) // 480, ((x + y) * 255) // 1120)
for y in range(100, 260):
    for x in range(120, 400):
        px[x, y] = (20, 20, 30)
img.save("_base.jpg", "JPEG", quality=92)

# ---------------------------------------------------------------- EXIF block
ASCII, SHORT, LONG, RATIONAL = 2, 3, 4, 5
data = bytearray()
DATA_START = 8 + (2 + 7 * 12 + 4) + (2 + 5 * 12 + 4) + (2 + 4 * 12 + 4)  # 218

def put(raw):
    off = DATA_START + len(data)
    data.extend(raw)
    if len(data) % 2:
        data.append(0)
    return off

def entry(tag, typ, count, payload, inline=None):
    if inline is not None:
        val = inline
    else:
        val = struct.pack("<I", put(payload)) if len(payload) > 4 else payload.ljust(4, b"\0")
    return struct.pack("<HHI", tag, typ, count) + val

def asc(s):
    b = s.encode() + b"\0"
    return b, len(b)

def rat(n, d):
    return struct.pack("<II", n, d)

EXIF_IFD_OFF = 8 + (2 + 7 * 12 + 4)
GPS_IFD_OFF = EXIF_IFD_OFF + (2 + 5 * 12 + 4)

e = []
b, c = asc("TestCam Industries");   e.append(entry(0x010F, ASCII, c, b))
b, c = asc("Model X100");           e.append(entry(0x0110, ASCII, c, b))
b, c = asc("Adobe Photoshop 2026"); e.append(entry(0x0131, ASCII, c, b))
b, c = asc("(c) Ben Goldberger");   e.append(entry(0x8298, ASCII, c, b))
e.append(entry(0x0112, SHORT, 1, b"", struct.pack("<HH", 1, 0)))
e.append(entry(0x8769, LONG, 1, b"", struct.pack("<I", EXIF_IFD_OFF)))
e.append(entry(0x8825, LONG, 1, b"", struct.pack("<I", GPS_IFD_OFF)))
ifd0 = struct.pack("<H", len(e)) + b"".join(e) + struct.pack("<I", 0)

e = []
b, c = asc("2026:07:27 14:05:33"); e.append(entry(0x9003, ASCII, c, b))
e.append(entry(0x829D, RATIONAL, 1, rat(28, 10)))
e.append(entry(0x8827, SHORT, 1, b"", struct.pack("<HH", 400, 0)))
e.append(entry(0x920A, RATIONAL, 1, rat(35, 1)))
b, c = asc("TestCam 35mm f/1.8"); e.append(entry(0xA434, ASCII, c, b))
exif_ifd = struct.pack("<H", len(e)) + b"".join(e) + struct.pack("<I", 0)

# 37 46' 29.64" N, 122 25' 9.98" W
e = []
e.append(entry(0x0001, ASCII, 2, b"N\0"))
e.append(entry(0x0002, RATIONAL, 3, rat(37, 1) + rat(46, 1) + rat(2964, 100)))
e.append(entry(0x0003, ASCII, 2, b"W\0"))
e.append(entry(0x0004, RATIONAL, 3, rat(122, 1) + rat(25, 1) + rat(998, 100)))
gps_ifd = struct.pack("<H", len(e)) + b"".join(e) + struct.pack("<I", 0)

assert 8 + len(ifd0) + len(exif_ifd) + len(gps_ifd) == DATA_START, "IFD layout mismatch"

tiff = b"II" + struct.pack("<HI", 42, 8) + ifd0 + exif_ifd + gps_ifd + bytes(data)
app1 = b"Exif\0\0" + tiff
jpg = open("_base.jpg", "rb").read()
seg = b"\xFF\xE1" + struct.pack(">H", len(app1) + 2) + app1
open("test-exif.jpg", "wb").write(jpg[:2] + seg + jpg[2:])

# ------------------------------------------------- reference pixels + hashes
src = Image.open("test-exif.jpg").convert("RGB")

def gray(w, h):
    r = src.resize((w, h), Image.BILINEAR)
    return [0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in r.get_flattened_data()]

g8, g98, g32 = gray(8, 8), gray(9, 8), gray(32, 32)
json.dump({"g8": g8, "g98": g98, "g32": g32}, open("/tmp/gray.json", "w"))

def to_hex(bits):
    return "".join(format((bits[i] << 3) | (bits[i+1] << 2) | (bits[i+2] << 1) | bits[i+3], "x")
                   for i in range(0, len(bits), 4))

mean = sum(g8) / len(g8)
a_hash = to_hex([1 if v > mean else 0 for v in g8])

bits = []
for y in range(8):
    for x in range(8):
        bits.append(1 if g98[y * 9 + x] > g98[y * 9 + x + 1] else 0)
d_hash = to_hex(bits)

N, K = 32, 8
dct = []
for u in range(K):
    for v in range(K):
        s = 0.0
        for y in range(N):
            cy = math.cos((2 * y + 1) * v * math.pi / (2 * N))
            for x in range(N):
                s += g32[y * N + x] * math.cos((2 * x + 1) * u * math.pi / (2 * N)) * cy
        au = (1 / math.sqrt(2)) if u == 0 else 1.0
        av = (1 / math.sqrt(2)) if v == 0 else 1.0
        dct.append(0.25 * au * av * s)
rest = sorted(dct[1:])
med = rest[len(rest) // 2]
p_hash = to_hex([0 if i == 0 else (1 if v > med else 0) for i, v in enumerate(dct)])

json.dump({"aHash": a_hash, "dHash": d_hash, "pHash": p_hash},
          open("/tmp/expected_hashes.json", "w"))

print("fixtures built: test-exif.jpg, _base.jpg")
print(f"  reference aHash {a_hash}  dHash {d_hash}  pHash {p_hash}")
