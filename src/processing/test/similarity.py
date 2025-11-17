import math
import numpy as np


def _angle_diff_deg(a_deg: float, b_deg: float) -> float:
    return abs(((a_deg - b_deg + 90.0) % 180.0) - 90.0)


def line_similarity(base: np.ndarray,
                    warped: np.ndarray,
                    tol_angle_deg: float = 5.0,
                    tol_rho_px: float = 5.0) -> float:
    if base.size == 0 or warped.size == 0:
        return 0.0

    def to_normal_params(L):
        x1, y1, x2, y2 = L
        dx, dy = x2 - x1, y2 - y1
        dir_deg = math.degrees(math.atan2(dy, dx))
        theta_deg = (dir_deg + 90.0 + 360.0) % 180.0
        cx, cy = 0.5 * (x1 + x2), 0.5 * (y1 + y2)
        theta_rad = math.radians(theta_deg)
        rho = cx * math.cos(theta_rad) + cy * math.sin(theta_rad)
        return theta_deg, rho

    base_params = np.array([to_normal_params(L) for L in base])
    warped_params = np.array([to_normal_params(L) for L in warped])

    hits = 0
    for theta0, rho0 in base_params:
        dtheta = np.array([_angle_diff_deg(theta0, t1) for (t1, _) in warped_params])
        drho = np.abs(warped_params[:, 1] - rho0)
        ok = np.any((dtheta <= tol_angle_deg) & (drho <= tol_rho_px))
        hits += int(ok)

    return hits / max(1, base.shape[0])


def circle_similarity(base: np.ndarray,
                      warped: np.ndarray,
                      tol_center_px: float = 5.0,
                      tol_rel_radius: float = 0.1) -> float:
    if base.size == 0 or warped.size == 0:
        return 0.0

    hits = 0
    for (x, y, r) in base:
        dx = warped[:, 0] - x
        dy = warped[:, 1] - y
        center_ok = (dx * dx + dy * dy) <= (tol_center_px ** 2)
        rel_r = np.abs(warped[:, 2] - r) / max(abs(r), 1e-6)
        radius_ok = rel_r <= tol_rel_radius
        ok = np.any(center_ok & radius_ok)
        hits += int(ok)

    return hits / max(1, base.shape[0])


def rect_similarity(base: np.ndarray,
                    warped: np.ndarray,
                    tol_center_px: float = 8.0,
                    tol_angle_deg: float = 8.0,
                    tol_rel_side: float = 0.2) -> float:
    if base.size == 0 or warped.size == 0:
        return 0.0

    hits = 0
    for (cx, cy, w, h, ang) in base:
        dx = warped[:, 0] - cx
        dy = warped[:, 1] - cy
        center_ok = (dx * dx + dy * dy) <= (tol_center_px ** 2)

        dtheta = np.array([_angle_diff_deg(a1, ang) for a1 in warped[:, 4]])
        angle_ok = dtheta <= tol_angle_deg

        relw = np.abs(warped[:, 2] - w) / max(abs(w), 1e-6)
        relh = np.abs(warped[:, 3] - h) / max(abs(h), 1e-6)
        size_ok = (relw <= tol_rel_side) & (relh <= tol_rel_side)

        ok = np.any(center_ok & angle_ok & size_ok)
        hits += int(ok)

    return hits / max(1, base.shape[0])
