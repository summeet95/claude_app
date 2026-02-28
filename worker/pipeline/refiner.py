"""
Post-process rendered views:
  - Composite hair render over a neutral background
  - Apply slight vignette + brightness normalization
"""
from __future__ import annotations

import os

from PIL import Image, ImageFilter, ImageEnhance


def refine_views(view_paths: dict[str, str]) -> dict[str, str]:
    """
    Refines each PNG in-place (overwrites).
    Returns the same dict for chaining.
    """
    for view_name, path in view_paths.items():
        try:
            img = Image.open(path).convert("RGBA")

            # Normalize brightness
            enhancer = ImageEnhance.Brightness(img.convert("RGB"))
            img_rgb = enhancer.enhance(1.05)

            # Vignette overlay
            vignette = _make_vignette(img_rgb.width, img_rgb.height)
            img_rgb = Image.composite(
                img_rgb,
                Image.new("RGB", img_rgb.size, (0, 0, 0)),
                vignette,
            )

            img_rgb.save(path)
        except Exception as exc:
            print(f"[refiner] Could not refine {view_name}: {exc}")

    return view_paths


def _make_vignette(w: int, h: int):
    """Create a soft radial vignette mask."""
    from PIL import ImageDraw
    import math

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = w // 2, h // 2
    max_r = math.sqrt(cx**2 + cy**2)
    for r in range(int(max_r), 0, -1):
        alpha = int(255 * (1 - (r / max_r) ** 2))
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=alpha,
        )
    return mask
