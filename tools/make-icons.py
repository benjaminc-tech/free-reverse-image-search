"""
Regenerates every raster icon from the same geometry as favicon.svg.

Run from the project root:  python3 tools/make-icons.py

The SVG is the source of truth for the design; this mirrors its coordinates so
the .ico and .png files can never drift from it. Sizes are supersampled and
downscaled with LANCZOS, because a favicon lives or dies at 16px.
"""
from PIL import Image, ImageDraw
import os

RED = (236, 29, 36)
INK = (13, 15, 19)
WHITE = (255, 255, 255)
GOLD = (240, 179, 35)
SS = 8  # supersample factor

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "publish")


def render(size, full_bleed=False):
    """full_bleed is for the Apple touch icon: iOS applies its own corner mask,
    so a pre-rounded icon would end up double-rounded."""
    S = size * SS
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = S / 100.0

    def U(v):
        return v * u

    def cap(x, y, r, fill):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    if full_bleed:
        d.rectangle([0, 0, S, S], fill=RED)
    else:
        bw = U(7)
        d.rounded_rectangle([bw / 2, bw / 2, S - bw / 2, S - bw / 2],
                            radius=U(24), fill=RED, outline=INK, width=int(round(bw)))

    # Handle: black under-stroke, then gold on top. The under-stroke is not
    # decoration, it is what separates gold from red, which is only 3.15:1.
    for width, color, pts in ((U(19), INK, (56, 54, 79, 77)),
                              (U(11), GOLD, (57, 55, 77, 75))):
        x1, y1, x2, y2 = (U(p) for p in pts)
        d.line([x1, y1, x2, y2], fill=color, width=int(round(width)))
        cap(x1, y1, width / 2, color)   # round caps, matching the SVG
        cap(x2, y2, width / 2, color)

    # Lens: a solid disc, not a ring. A ring fills in and turns to mush at 16px.
    cx, cy, r = U(42), U(40), U(25)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=INK, width=int(round(U(7))))
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    render(32).save(os.path.join(OUT, "favicon-32.png"), "PNG", optimize=True)
    render(192).save(os.path.join(OUT, "icon-192.png"), "PNG", optimize=True)
    render(180, full_bleed=True).convert("RGB").save(
        os.path.join(OUT, "apple-touch-icon.png"), "PNG", optimize=True)
    render(64).save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

    for f in ("favicon-32.png", "icon-192.png", "apple-touch-icon.png", "favicon.ico"):
        print(f"{f:24s} {os.path.getsize(os.path.join(OUT, f)):>6d} bytes")
