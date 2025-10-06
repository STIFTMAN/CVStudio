import math
import numpy as np


def line_similarity(base: np.ndarray, warped: np.ndarray, tol_angle_deg=5.0, tol_shift_px=5.0) -> float:
    if base.size == 0 or warped.size == 0:
        return 0.0

    def feat(L):
        x1, y1, x2, y2 = L
        dx, dy = x2 - x1, y2 - y1
        ang = (math.degrees(math.atan2(dy, dx)) + 360) % 180.0
        cx, cy = 0.5 * (x1 + x2), 0.5 * (y1 + y2)
        return ang, cx, cy
    hits = 0
    warped_feats = [feat(L) for L in warped]
    for L in base:
        a0, cx0, cy0 = feat(L)
        ok = any((abs(a0 - a1) <= tol_angle_deg) and ((cx0 - cx1)**2 + (cy0 - cy1)**2 <= tol_shift_px**2)
                 for (a1, cx1, cy1) in warped_feats)
        hits += int(ok)
    return hits / max(1, base.shape[0])


def circle_similarity(base: np.ndarray, warped: np.ndarray, tol_center=5.0, tol_radius=5.0) -> float:
    if base.size == 0 or warped.size == 0:
        return 0.0
    hits = 0
    for (x, y, r) in base:
        ok = np.any(((warped[:, 0] - x)**2 + (warped[:, 1] - y)**2 <= tol_center**2) & (np.abs(warped[:, 2] - r) <= tol_radius))
        hits += int(ok)
    return hits / base.shape[0]


def rect_similarity(base: np.ndarray, warped: np.ndarray, tol_center=8.0, tol_angle=8.0, tol_rel_side=0.2) -> float:
    if base.size == 0 or warped.size == 0:
        return 0.0
    hits = 0
    for (cx, cy, w, h, ang) in base:
        relw = np.abs(warped[:, 2] - w) / max(w, 1e-6)
        relh = np.abs(warped[:, 3] - h) / max(h, 1e-6)
        center_ok = ((warped[:, 0] - cx)**2 + (warped[:, 1] - cy)**2) <= (tol_center**2)
        angle_ok = np.abs(((warped[:, 4] - ang + 90) % 180) - 90) <= tol_angle
        size_ok = (relw <= tol_rel_side) & (relh <= tol_rel_side)
        ok = np.any(center_ok & angle_ok & size_ok)
        hits += int(ok)
    return hits / base.shape[0]
