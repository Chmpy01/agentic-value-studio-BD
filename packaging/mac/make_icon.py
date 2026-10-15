"""Draws packaging/mac/twin-icon.png (1024x1024). Requires Pillow: python packaging/mac/make_icon.py"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SCALE = 2
SIZE = 1024 * SCALE
OUT = Path(__file__).with_name("twin-icon.png")


def s(value: float) -> int:
    return int(value * SCALE)


def main() -> None:
    # macOS icon grid: 824px tile centred on a 1024px canvas, with a soft shadow.
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    tile_box = (s(100), s(92), s(924), s(916))

    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((s(100), s(112), s(924), s(936)), radius=s(185), fill=(8, 20, 48, 120))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(s(18))))

    gradient = Image.new("RGBA", (SIZE, SIZE))
    top, bottom = (17, 38, 92), (37, 99, 235)
    draw = ImageDraw.Draw(gradient)
    for y in range(SIZE):
        t = y / SIZE
        draw.line([(0, y), (SIZE, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)) + (255,))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(tile_box, radius=s(185), fill=255)
    canvas.paste(gradient, (0, 0), mask)

    nodes = {
        "board": (512, 270),
        "fn_a": (330, 450),
        "fn_b": (694, 450),
        "p_a": (250, 660),
        "p_b": (450, 660),
        "p_c": (694, 660),
        "value": (512, 790),
    }
    links = [
        ("board", "fn_a"), ("board", "fn_b"),
        ("fn_a", "p_a"), ("fn_a", "p_b"), ("fn_b", "p_c"),
        ("p_a", "value"), ("p_b", "value"), ("p_c", "value"),
    ]

    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    vx, vy = nodes["value"]
    gdraw.ellipse((s(vx - 120), s(vy - 120), s(vx + 120), s(vy + 120)), fill=(45, 212, 191, 150))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(s(40))))

    draw = ImageDraw.Draw(canvas)
    for a, b in links:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        draw.line([(s(x1), s(y1)), (s(x2), s(y2))], fill=(191, 219, 254, 210), width=s(16))

    for name, (x, y) in nodes.items():
        radius = 62 if name == "board" else 70 if name == "value" else 48
        fill = (45, 212, 191, 255) if name == "value" else (255, 255, 255, 255)
        draw.ellipse((s(x - radius - 10), s(y - radius - 10), s(x + radius + 10), s(y + radius + 10)), fill=(17, 38, 92, 255))
        draw.ellipse((s(x - radius), s(y - radius), s(x + radius), s(y + radius)), fill=fill)
    draw.ellipse((s(vx - 26), s(vy - 26), s(vx + 26), s(vy + 26)), fill=(255, 255, 255, 255))

    canvas.resize((1024, 1024), Image.LANCZOS).save(OUT, optimize=True)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
