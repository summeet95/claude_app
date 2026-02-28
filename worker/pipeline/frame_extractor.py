"""Extract frames from video at 1 fps using ffmpeg-python."""
from __future__ import annotations

import os
import tempfile

import ffmpeg


def extract_frames(video_path: str) -> list[str]:
    """
    Extract frames at 1 fps.  Returns sorted list of PNG file paths.
    Caller must clean up the returned temp directory.
    """
    out_dir = tempfile.mkdtemp(prefix="frames_")
    pattern = os.path.join(out_dir, "frame_%04d.png")

    print(f"[frame_extractor] Extracting frames from {video_path} → {out_dir}")
    (
        ffmpeg
        .input(video_path)
        .filter("fps", fps=1)
        .output(pattern, format="image2", vcodec="png")
        .run(quiet=True, overwrite_output=True)
    )

    frames = sorted(
        [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith(".png")]
    )
    print(f"[frame_extractor] Extracted {len(frames)} frames")
    return frames
