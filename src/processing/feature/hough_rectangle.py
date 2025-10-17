from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style


def hough_rectangle(
    image: npt.NDArray[np.uint8 | np.float32]
) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:

    cfg = processing_config["feature"]["hough_rectangle"]
    assert cfg is not None
    gray = to_gray_uint8(image)

    edges = cv2.Canny(gray, int(cfg.get("canny1", 50)), int(cfg.get("canny2", 150)))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)

    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_pts = int(cfg.get("min_size", 5))
    min_area = float(cfg.get("min_area", 150.0))

    cand = []
    for c in cnts:
        if len(c) < min_pts:
            continue
        (cx, cy), (w, h), ang = cv2.minAreaRect(c)
        if w <= 0 or h <= 0:
            continue
        area = w * h
        if area < min_area:
            continue

        if w < h:
            w, h = h, w
            ang += 90.0
        angle_deg = (float(ang) + 360.0) % 360.0

        cand.append((float(cx), float(cy), float(w), float(h), angle_deg, float(area)))

    if not cand:
        return "rect", ([], np.empty((0, 5), dtype=np.float32))

    cand.sort(key=lambda t: t[5], reverse=True)
    kept = []
    for cx, cy, L, W, A, area in cand:
        is_dup = False
        for kcx, kcy, kL, kW, kA, karea in kept:
            pos_tol = 0.35 * max(kL, L)
            size_tol = 0.25
            ang_tol = 12.0

            if (abs(cx - kcx) <= pos_tol and abs(cy - kcy) <= pos_tol and abs(L - kL) <= size_tol * max(kL, L) and abs(W - kW) <= size_tol * max(kW, W)):
                dA = abs((A - kA + 180.0) % 360.0 - 180.0)
                if dA <= ang_tol:
                    is_dup = True
                    break
        if not is_dup:
            kept.append((cx, cy, L, W, A, area))
    keypoints: List[cv2.KeyPoint] = []
    dets = []
    for cx, cy, L, W, A, _ in kept:
        kp = cv2.KeyPoint(float(cx), float(cy), float(L), float(A))
        kp.response = float(W)
        keypoints.append(kp)
        dets.append([cx, cy, L, W, A])

    detections = np.asarray(dets, dtype=np.float32)
    return "rect", (keypoints, detections)
