from typing import List
import math
import cv2
import numpy as np


def keypoint_to_xy(kps: List[cv2.KeyPoint]) -> np.ndarray:
    if not kps:
        return np.empty((0, 2), dtype=np.float32)
    return np.float32([kp.pt for kp in kps])   # type: ignore


def keypoint_line_to_L4(kps: List[cv2.KeyPoint]) -> np.ndarray:
    if not kps:
        return np.empty((0, 4), dtype=np.float32)
    out = []
    for kp in kps:
        cx, cy = kp.pt
        L = max(float(kp.size), 1e-6)
        ang = math.radians(float(kp.angle) if kp.angle is not None else 0.0)
        dx = 0.5 * L * math.cos(ang)
        dy = 0.5 * L * math.sin(ang)
        out.append([cx - dx, cy - dy, cx + dx, cy + dy])
    return np.asarray(out, dtype=np.float32)


def keypoint_circle_to_C3(kps: List[cv2.KeyPoint]) -> np.ndarray:
    if not kps:
        return np.empty((0, 3), dtype=np.float32)
    out = []
    for kp in kps:
        cx, cy = kp.pt
        r = 0.5 * float(kp.size)
        out.append([cx, cy, r])
    return np.asarray(out, dtype=np.float32)


def keypoint_rect_to_R5(kps: List[cv2.KeyPoint]) -> np.ndarray:
    if not kps:
        return np.empty((0, 5), dtype=np.float32)
    out = []
    for kp in kps:
        cx, cy = kp.pt
        L = float(kp.size)
        W = float(getattr(kp, "response", 0.0))
        A = float(kp.angle) if kp.angle is not None else 0.0
        out.append([cx, cy, L, W, A])
    return np.asarray(out, dtype=np.float32)
