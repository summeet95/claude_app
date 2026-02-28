"""
Subprocess entry-point for DECA inference.
Called by head_fitter.py:
  python run_deca.py --image <path> --output <json_path>

This script runs in its own Python env to isolate PyTorch versions.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Download weights if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.download_deca_weights import download_if_needed  # noqa: E402

deca_dir = download_if_needed()
sys.path.insert(0, deca_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        # DECA imports — only available when weights are present
        from decalib.deca import DECA  # type: ignore
        from decalib.utils.config import cfg as deca_cfg  # type: ignore
        import torch
        import numpy as np
        import cv2

        deca_cfg.model.use_tex = False
        deca = DECA(config=deca_cfg, device="cpu")

        img = cv2.imread(args.image)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Resize to DECA expected input
        img_resized = cv2.resize(img_rgb, (224, 224))
        tensor = torch.tensor(img_resized).permute(2, 0, 1).float() / 255.0
        tensor = tensor.unsqueeze(0)

        with torch.no_grad():
            codedict = deca.encode(tensor)

        params = {
            "shape": codedict["shape"][0].tolist(),
            "pose": codedict["pose"][0].tolist(),
            "expression": codedict["exp"][0].tolist(),
            "scale": float(codedict.get("cam", torch.ones(1, 3))[0, 0]),
            "centroid": [0.0, 0.0, 0.0],
        }
    except Exception as exc:
        print(f"[run_deca] Error: {exc} — writing stub", file=sys.stderr)
        params = {
            "shape": [0.0] * 100,
            "pose": [0.0] * 6,
            "expression": [0.0] * 50,
            "scale": 1.0,
            "centroid": [0.0, 0.0, 0.0],
        }

    with open(args.output, "w") as f:
        json.dump(params, f)


if __name__ == "__main__":
    main()
