"""
Select the best frames from a list:
  1. Score each frame by Laplacian sharpness.
  2. Estimate yaw angle using MediaPipe FaceMesh.
  3. Cluster frames by yaw into N bins.
  4. Pick the sharpest frame from each bin.

Returns ≤ MAX_FRAMES selected frame paths.
"""
from __future__ import annotations

import math

import cv2
import mediapipe as mp
import numpy as np

MAX_FRAMES = 8
YAW_BINS = 4  # front, slight-left, slight-right, profile


def _laplacian_score(path: str) -> float:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    return float(cv2.Laplacian(img, cv2.CV_64F).var())


def _estimate_yaw(path: str, face_mesh) -> float | None:
    """Return yaw angle in degrees (-90..90) or None if no face detected."""
    img = cv2.imread(path)
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)
    if not result.multi_face_landmarks:
        return None

    lm = result.multi_face_landmarks[0].landmark
    h, w = img.shape[:2]

    # Nose tip (1), left eye outer (263), right eye outer (33)
    nose = np.array([lm[1].x * w, lm[1].y * h, lm[1].z * w])
    left_eye = np.array([lm[263].x * w, lm[263].y * h, lm[263].z * w])
    right_eye = np.array([lm[33].x * w, lm[33].y * h, lm[33].z * w])

    eye_center = (left_eye + right_eye) / 2.0
    diff = nose - eye_center
    yaw = math.degrees(math.atan2(diff[0], diff[2]))
    return yaw


def select_frames(frame_paths: list[str]) -> list[str]:
    if not frame_paths:
        return []

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
    )

    scored: list[tuple[str, float, float]] = []
    for path in frame_paths:
        sharpness = _laplacian_score(path)
        yaw = _estimate_yaw(path, face_mesh) or 0.0
        scored.append((path, sharpness, yaw))

    face_mesh.close()

    # Filter out blurry frames (below 20th percentile)
    sharpnesses = [s for _, s, _ in scored]
    threshold = float(np.percentile(sharpnesses, 20)) if sharpnesses else 0.0
    scored = [(p, s, y) for p, s, y in scored if s >= threshold]

    if not scored:
        return [frame_paths[0]]

    # Bin by yaw
    bin_size = 180.0 / YAW_BINS
    bins: dict[int, list[tuple[str, float]]] = {i: [] for i in range(YAW_BINS)}
    for path, sharpness, yaw in scored:
        bin_idx = min(int((yaw + 90.0) / bin_size), YAW_BINS - 1)
        bins[bin_idx].append((path, sharpness))

    selected: list[str] = []
    for bin_frames in bins.values():
        if not bin_frames:
            continue
        best = max(bin_frames, key=lambda x: x[1])
        selected.append(best[0])

    # Fallback: if fewer than 2 selected, add top sharpness frames
    if len(selected) < 2:
        extra = sorted(scored, key=lambda x: -x[1])
        for path, _, _ in extra:
            if path not in selected:
                selected.append(path)
            if len(selected) >= 2:
                break

    print(f"[frame_selector] Selected {len(selected)} frames from {len(frame_paths)}")
    return selected[:MAX_FRAMES]
