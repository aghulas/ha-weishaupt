#!/usr/bin/env python3
"""Draw the brand images of the integration (needs Pillow; development tool).

An own, plain mark: a flame over two bus wires, no vendor logo and no vendor colour scheme. Home Assistant
(2026.3 and later) and HACS take the images from custom_components/weishaupt/brand/.
"""
from pathlib import Path

from PIL import Image, ImageDraw

BRAND = Path(__file__).resolve().parent.parent / "custom_components" / "weishaupt" / "brand"
BACKGROUND, FLAME, CORE, WIRE = (27, 54, 93, 255), (255, 153, 51, 255), (255, 221, 128, 255), (236, 240, 245, 255)


def flame(draw: ImageDraw.ImageDraw, cx: float, base: float, width: float, height: float, fill) -> None:
    """A drop: a circle at the bottom, a triangle to the tip."""
    radius = width / 2
    draw.ellipse((cx - radius, base - 2 * radius, cx + radius, base), fill=fill)
    draw.polygon([(cx - radius * 0.97, base - radius * 1.25), (cx + radius * 0.97, base - radius * 1.25),
                  (cx + radius * 0.25, base - height)], fill=fill)


def icon(size: int) -> Image.Image:
    scale = 4  # drawn larger, then reduced: smooth edges
    s = size * scale
    image = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, s - 1, s - 1), radius=s * 0.19, fill=BACKGROUND)
    flame(draw, s * 0.5, s * 0.66, s * 0.36, s * 0.52, FLAME)
    flame(draw, s * 0.5, s * 0.66, s * 0.17, s * 0.27, CORE)
    for y in (0.76, 0.84):  # the two wires of the bus
        draw.rounded_rectangle((s * 0.2, s * y, s * 0.8, s * (y + 0.028)), radius=s * 0.014, fill=WIRE)
    return image.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    BRAND.mkdir(exist_ok=True)
    for name, size in (("icon.png", 256), ("icon@2x.png", 512), ("logo.png", 256), ("logo@2x.png", 512)):
        icon(size).save(BRAND / name, optimize=True)
        print(name, size)
