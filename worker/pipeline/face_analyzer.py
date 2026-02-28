"""
Analyze selected frames with MediaPipe FaceMesh.
Outputs:
  - head_shape: oval | round | square | heart | oblong | diamond
  - hair_texture: straight | wavy | curly | coily
  - facial_features: dict of raw measurements
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field

import cv2
import mediapipe as mp
import numpy as np


@dataclass
class FaceAnalysis:
    head_shape: str = "oval"
    hair_texture: str = "straight"
    features: dict = field(default_factory=dict)


# Landmark indices for key measurements
_FOREHEAD_TOP = 10
_CHIN_BOTTOM = 152
_LEFT_CHEEK = 234
_RIGHT_CHEEK = 454
_JAW_LEFT = 172
_JAW_RIGHT = 397
_LEFT_EYE_OUTER = 263
_RIGHT_EYE_OUTER = 33
_NOSE_TIP = 4


def _face_shape(face_height: float, face_width: float, jaw_width: float) -> str:
    ratio = face_height / max(face_width, 1e-6)
    jaw_ratio = jaw_width / max(face_width, 1e-6)

    if ratio > 1.5:
        return "oblong"
    if ratio > 1.3:
        return "oval" if jaw_ratio > 0.75 else "heart"
    if jaw_ratio > 0.9:
        return "square"
    if ratio < 1.1:
        return "round"
    if jaw_ratio < 0.7:
        return "diamond"
    return "oval"


def _lm_xy(lm, idx: int, w: int, h: int) -> np.ndarray:
    p = lm[idx]
    return np.array([p.x * w, p.y * h])


def analyze_frames(frame_paths: list[str]) -> FaceAnalysis:
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    )

    ratios: list[float] = []
    jaw_ratios: list[float] = []

    for path in frame_paths:
        img = cv2.imread(path)
        if img is None:
            continue
        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)
        if not result.multi_face_landmarks:
            continue

        lm = result.multi_face_landmarks[0].landmark
        top = _lm_xy(lm, _FOREHEAD_TOP, w, h)
        bot = _lm_xy(lm, _CHIN_BOTTOM, w, h)
        left = _lm_xy(lm, _LEFT_CHEEK, w, h)
        right = _lm_xy(lm, _RIGHT_CHEEK, w, h)
        jaw_l = _lm_xy(lm, _JAW_LEFT, w, h)
        jaw_r = _lm_xy(lm, _JAW_RIGHT, w, h)

        face_h = float(np.linalg.norm(top - bot))
        face_w = float(np.linalg.norm(left - right))
        jaw_w = float(np.linalg.norm(jaw_l - jaw_r))

        if face_w > 10 and face_h > 10:
            ratios.append(face_h / face_w)
            jaw_ratios.append(jaw_w / face_w)

    face_mesh.close()

    if not ratios:
        print("[face_analyzer] No faces detected — defaulting to oval")
        return FaceAnalysis(head_shape="oval")

    avg_ratio = statistics.mean(ratios)
    avg_jaw = statistics.mean(jaw_ratios)
    shape = _face_shape(avg_ratio * 100, 100, avg_jaw * 100)

    print(f"[face_analyzer] head_shape={shape} (h/w={avg_ratio:.2f}, jaw/w={avg_jaw:.2f})")
    return FaceAnalysis(
        head_shape=shape,
        features={"face_ratio": avg_ratio, "jaw_ratio": avg_jaw},
    )
