from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import cv2
import math
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style


def hough_circle(
    image: npt.NDArray[np.uint8 | np.float32]
) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:

    cfg = processing_config["hough_circle"]
    assert cfg is not None
    gray = to_gray_uint8(image)

    # 1) Hough direkt auf gray
    dp = float(cfg.get("dp", 1.5))
    minDist = float(cfg.get("minDist", 40))
    param1 = float(cfg.get("param1", 120))
    param2 = float(cfg.get("param2", 60))   # höher = strenger
    minRadius = int(cfg.get("minRadius", 20))
    maxRadius = int(cfg.get("maxRadius", 300))

    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=dp, minDist=minDist,
        param1=param1, param2=param2, minRadius=minRadius, maxRadius=maxRadius
    )

    keypoints: List[cv2.KeyPoint] = []
    if circles is None:
        detections = np.empty((0, 3), dtype=np.float32)
        return "circle", (keypoints, detections)

    # 2) flach ziehen
    cir = circles[0] if circles.ndim == 3 else circles
    cir = cir.astype(np.float32, copy=False)  # (N,3) [x,y,r]

    # 3) einfache Deduplizierung (greedy)
    cir = sorted(cir, key=lambda t: t[2], reverse=True)  # type: ignore
    kept = []
    for x, y, r in cir:  # type: ignore
        is_dup = False
        for kx, ky, kr in kept:
            center_close = math.hypot(x - kx, y - ky) <= 0.5 * min(r, kr)
            radius_close = abs(r - kr) <= 0.25 * min(r, kr)
            if center_close and radius_close:
                is_dup = True
                break
        if not is_dup:
            kept.append((float(x), float(y), float(r)))

    # 4) Kanten-Support prüfen (min. 30% Umfang auf Canny-Kanten)
    edges = cv2.Canny(gray, max(30, int(param1 // 3)), int(param1))
    filtered = []
    for x, y, r in kept:
        num = 36  # 10°-Sampling
        ang = np.linspace(0, 2 * np.pi, num, endpoint=False)
        xs = (x + r * np.cos(ang)).astype(np.int32)
        ys = (y + r * np.sin(ang)).astype(np.int32)
        mask = (xs >= 0) & (xs < edges.shape[1]) & (ys >= 0) & (ys < edges.shape[0])
        xs, ys = xs[mask], ys[mask]
        if xs.size == 0:
            continue
        hit = int(np.count_nonzero(edges[ys, xs]))
        if (hit / xs.size) >= 0.30:
            filtered.append((x, y, r))

    # 5) KeyPoints + detections
    dets = []
    for x, y, r in filtered:
        size = max(2.0 * r, 1e-3)                  # Durchmesser in size
        kp = cv2.KeyPoint(float(x), float(y), float(size), -1)  # angle=-1
        keypoints.append(kp)
        dets.append([x, y, r])

    detections = np.asarray(dets, dtype=np.float32) if dets else np.empty((0, 3), dtype=np.float32)
    return "circle", (keypoints, detections)
