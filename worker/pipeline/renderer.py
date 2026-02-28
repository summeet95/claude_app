"""
Render 4 views (front, left, right, back) for a hairstyle.

Priority order:
  1. Reference photo — use real hairstyle photo from catalog.json (resized to 512x512)
  2. Trimesh/pyrender — CPU offscreen 3-D render (if RENDERER_BACKEND=trimesh)
  3. Placeholder — coloured PNG fallback

catalog.json is written at startup by models/download_reference_images.py.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import numpy as np

try:
    import trimesh
    import trimesh.transformations as tf
    _TRIMESH_AVAILABLE = True
except ImportError:
    _TRIMESH_AVAILABLE = False

try:
    import pyrender
    _PYRENDER_AVAILABLE = True
except ImportError:
    _PYRENDER_AVAILABLE = False

# ── Reference catalog ─────────────────────────────────────────────────────────

_CATALOG_PATH = Path("/app/hairstyle_references/catalog.json")
_REFERENCE_CATALOG: dict[str, dict] | None = None  # lazy-loaded


def _load_catalog() -> dict[str, dict]:
    global _REFERENCE_CATALOG
    if _REFERENCE_CATALOG is None:
        if _CATALOG_PATH.exists():
            try:
                _REFERENCE_CATALOG = json.loads(_CATALOG_PATH.read_text())
                print(f"[renderer] Loaded reference catalog: {len(_REFERENCE_CATALOG)} entries")
            except Exception as exc:
                print(f"[renderer] Failed to load catalog: {exc}")
                _REFERENCE_CATALOG = {}
        else:
            _REFERENCE_CATALOG = {}
    return _REFERENCE_CATALOG


# ── View labels overlaid on reference photos ──────────────────────────────────

_VIEW_LABELS: dict[str, str] = {
    "front": "",
    "left":  "◀ Left",
    "right": "Right ▶",
    "back":  "Back",
}

VIEWS = ["front", "left", "right", "back"]


# ── Public API ────────────────────────────────────────────────────────────────

def render_views(
    style_slug: str,
    head_scale: float = 1.0,
    head_centroid: list[float] | None = None,
) -> dict[str, str]:
    """
    Returns {view_name: temp_png_path} for the 4 canonical views.
    Caller must delete temp files.
    """
    catalog = _load_catalog()

    if style_slug in catalog:
        local_path = catalog[style_slug].get("local_path")
        if local_path and Path(local_path).exists():
            return _render_reference(style_slug, Path(local_path))
        print(f"[renderer] Reference file missing for '{style_slug}': {local_path}")

    backend = os.environ.get("RENDERER_BACKEND", "trimesh").lower()
    if backend == "trimesh" and _TRIMESH_AVAILABLE and _PYRENDER_AVAILABLE:
        return _render_trimesh(style_slug, head_scale, head_centroid or [0, 0, 0])

    print(f"[renderer] Using placeholder for '{style_slug}'")
    return _render_placeholder(style_slug)


# ── Reference image renderer ──────────────────────────────────────────────────

def _render_reference(slug: str, source: Path) -> dict[str, str]:
    """
    Resize the reference photo to 512x512 and produce 4 view variants.
    Front = original. Left/Right/Back = same photo with a small corner label.
    """
    from PIL import Image, ImageDraw, ImageFont

    base = Image.open(source).convert("RGB").resize((512, 512))
    result: dict[str, str] = {}

    for view_name in VIEWS:
        img = base.copy()
        label = _VIEW_LABELS[view_name]
        if label:
            draw = ImageDraw.Draw(img)
            # Semi-transparent black bar at bottom
            overlay = Image.new("RGBA", (512, 36), (0, 0, 0, 160))
            img.paste(Image.new("RGB", (512, 36), (0, 0, 0)),
                      (0, 476), overlay)
            draw = ImageDraw.Draw(img)
            draw.text((8, 479), label, fill=(255, 255, 255))

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(tmp.name, format="PNG")
        tmp.close()
        result[view_name] = tmp.name

    return result


# ── Trimesh / pyrender 3-D renderer ──────────────────────────────────────────

def _render_trimesh(
    slug: str,
    scale: float,
    centroid: list[float],
) -> dict[str, str]:
    """Offscreen render with trimesh + pyrender."""
    os.environ.setdefault("PYOPENGL_PLATFORM", "osmesa")

    head_mesh = trimesh.creation.icosphere(radius=0.5 * scale)
    hair_mesh = trimesh.creation.icosphere(radius=0.58 * scale)
    hair_mesh.apply_translation([0, 0.05 * scale, 0])

    head_mesh.visual.vertex_colors = [210, 180, 140, 255]
    hair_mesh.visual.vertex_colors = [40, 30, 20, 200]

    scene = pyrender.Scene(ambient_light=[0.3, 0.3, 0.3])
    scene.add(pyrender.Mesh.from_trimesh(head_mesh))
    scene.add(pyrender.Mesh.from_trimesh(hair_mesh))

    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
    scene.add(light, pose=np.eye(4))

    renderer = pyrender.OffscreenRenderer(512, 512)
    result: dict[str, str] = {}

    view_yaws = {"front": 0.0, "left": 90.0, "right": -90.0, "back": 180.0}
    for view_name, yaw_deg in view_yaws.items():
        camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
        yaw_rad = np.radians(yaw_deg)
        cam_x = 2.0 * np.sin(yaw_rad)
        cam_z = 2.0 * np.cos(yaw_rad)
        cam_pose = _look_at(
            eye=np.array([cam_x, 0.1, cam_z]),
            target=np.array([0.0, 0.0, 0.0]),
        )
        cam_node = scene.add(camera, pose=cam_pose)
        color, _ = renderer.render(scene)
        scene.remove_node(cam_node)

        from PIL import Image
        img = Image.fromarray(color)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(tmp.name)
        tmp.close()
        result[view_name] = tmp.name

    renderer.delete()
    return result


def _look_at(eye: np.ndarray, target: np.ndarray) -> np.ndarray:
    forward = target - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(np.array([0.0, 1.0, 0.0]), forward)
    right_norm = np.linalg.norm(right)
    right = np.array([1.0, 0.0, 0.0]) if right_norm < 1e-6 else right / right_norm
    up = np.cross(forward, right)
    m = np.eye(4)
    m[:3, 0] = right
    m[:3, 1] = up
    m[:3, 2] = -forward
    m[:3, 3] = eye
    return m


# ── Placeholder renderer ──────────────────────────────────────────────────────

def _render_placeholder(slug: str) -> dict[str, str]:
    from PIL import Image, ImageDraw

    colors = {"front": "#4A90D9", "left": "#7B68EE", "right": "#50C878", "back": "#FF7F50"}
    result: dict[str, str] = {}
    for view_name, color in colors.items():
        img = Image.new("RGB", (512, 512), color)
        draw = ImageDraw.Draw(img)
        draw.text((20, 240), f"{slug}\n{view_name}", fill="white")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(tmp.name)
        tmp.close()
        result[view_name] = tmp.name
    return result
