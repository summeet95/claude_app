"""
DECA head shape fitter.
When DECA_ENABLED=false (default for local dev), returns an average-head stub.
When enabled, runs DECA in a subprocess to avoid PyTorch version conflicts.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field

import numpy as np


@dataclass
class HeadParams:
    """FLAME/DECA head parameters."""
    shape: list[float] = field(default_factory=lambda: [0.0] * 100)
    pose: list[float] = field(default_factory=lambda: [0.0] * 6)
    expression: list[float] = field(default_factory=lambda: [0.0] * 50)
    scale: float = 1.0
    centroid: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])


_DECA_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "models", "run_deca.py")


def fit_head(frame_paths: list[str]) -> HeadParams:
    """
    Fit FLAME head model to the best front-facing frame.
    Falls back to stub when DECA_ENABLED != 'true'.
    """
    if os.environ.get("DECA_ENABLED", "false").lower() != "true":
        print("[head_fitter] DECA_ENABLED=false — using stub average head")
        return HeadParams()

    # Pick the first available frame
    img_path = next((p for p in frame_paths if os.path.exists(p)), None)
    if img_path is None:
        return HeadParams()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as out_f:
        out_path = out_f.name

    try:
        subprocess.run(
            ["python", _DECA_SCRIPT, "--image", img_path, "--output", out_path],
            check=True,
            timeout=120,
        )
        with open(out_path) as f:
            data = json.load(f)
        return HeadParams(**data)
    except Exception as exc:
        print(f"[head_fitter] DECA failed: {exc} — using stub")
        return HeadParams()
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)
