import math
import cv2
import numpy as np
import numpy.typing as npt
from numpy.typing import NDArray
from typing import Tuple, List

from src.processing.utils.draw_keypoints import draw_keypoints
from src.processing.utils.to_norm_gray import to_norm_gray
from src.processing.convolution.default import default
from src.processing.root_config import processing_config


# ---------- Hilfsfunktionen ----------

def _gauss_and_dgauss_1d(sigma: float):
    """1D Gauß und 1. Ableitung auf ±3σ, normalisiert (float32)."""
    r = int(math.ceil(3 * sigma))
    x = np.arange(-r, r + 1, dtype=np.float32)
    g = np.exp(-(x * x) / (2 * sigma * sigma)).astype(np.float32)
    g /= g.sum() + 1e-12
    dg = (-(x / (sigma * sigma)) * g).astype(np.float32)  # Summe ~ 0
    return g, dg


def _outer2d(ky: np.ndarray, kx: np.ndarray) -> list[list[float]]:
    """2D-Kernel als Außenprodukt (Korrelation: KEIN Flip!)."""
    K = (ky[:, None] * kx[None, :]).astype(np.float32)
    return K.tolist()


# ---------- Harris-Response mit deinem Filter ----------

def _harris_response(gray_f32: np.ndarray, sigma: float, *, k: float = 0.04, alpha: float = 1.0) -> np.ndarray:
    """
    Harris-Cornerness im Maßstab 'sigma', berechnet mit default() (Kreuzkorrelation).
    - Ableitungs-Skala: sigma
    - Integrations-Skala: alpha * sigma
    - Skalen-Normalisierung: * sigma^2
    """
    # 1D-Kerne
    g, dg = _gauss_and_dgauss_1d(sigma)
    s_i = alpha * sigma
    r_i = int(math.ceil(3 * s_i))
    xi = np.arange(-r_i, r_i + 1, dtype=np.float32)
    Gi = np.exp(-(xi * xi) / (2 * s_i * s_i)).astype(np.float32)
    Gi /= Gi.sum() + 1e-12

    # 2D-Kerne (Korrelation, kein Flip)
    K_Ix = _outer2d(g, dg)  # dx in X, glättung in Y
    K_Iy = _outer2d(dg, g)  # dx in Y, glättung in X
    K_s = _outer2d(Gi, Gi)  # Integrationsglättung

    # Filteraufrufe (immer float32, keine zusätzliche Normierung)
    Ix = default(gray_f32, K_Ix, stride=(1, 1), edge_filter=True, use_conv_scale=False).astype(np.float32)
    Iy = default(gray_f32, K_Iy, stride=(1, 1), edge_filter=True, use_conv_scale=False).astype(np.float32)

    A = default(Ix * Ix, K_s, stride=(1, 1), edge_filter=True, use_conv_scale=False).astype(np.float32)
    B = default(Iy * Iy, K_s, stride=(1, 1), edge_filter=True, use_conv_scale=False).astype(np.float32)
    C = default(Ix * Iy, K_s, stride=(1, 1), edge_filter=True, use_conv_scale=False).astype(np.float32)

    detM = A * B - C * C
    traceM = A + B
    R = (detM - k * (traceM * traceM)) * (sigma * sigma)

    # Randmaske moderat halten (feine σ sonst weg): ±2*σ
    pad = int(math.ceil(2 * sigma))
    if pad > 0:
        R[:pad, :] = 0
        R[-pad:, :] = 0
        R[:, :pad] = 0
        R[:, -pad:] = 0

    return R.astype(np.float32)


# ---------- Hauptdetektor (mit Dedupe + Radius-NMS) ----------

def harris(
    img: NDArray[np.uint8 | np.float32],
    draw: bool = True
) -> tuple[npt.NDArray[np.uint8 | np.float32], Tuple[List[cv2.KeyPoint], np.ndarray]]:
    """
    Mehrskaliger Harris-Detektor mit:
      - Map-NMS (morphologisch),
      - Pixel-Deduplizierung (gleiches (x,y) -> bestes behalten),
      - Radius-NMS (greedy) gegen Mehrfachtreffer um denselben Punkt.
    Config (processing_config["hesse"]):
      - sigmas: List[float]
      - det_thresh: float
      - nms_kernel: int
      - nms_radius: int            (optional; fester Pixelradius)
      - nms_sigma_factor: float    (optional; Radius ≈ factor * beste_Skala)
    """
    config = processing_config["harris"]
    assert config is not None

    gray = to_norm_gray(img).astype(np.float32)
    sigmas_for_search = tuple(float(s) for s in config["sigmas"])

    Rmax = np.full_like(gray, -np.inf, dtype=np.float32)
    best_sigma = np.zeros_like(gray, dtype=np.float32)

    # Harris je Skala, Skalenmaximum aufbauen
    for sigma in sigmas_for_search:
        R = _harris_response(gray, sigma, k=0.04, alpha=1.0)  # alpha klein für feine Ecken
        mask = R > Rmax
        Rmax[mask] = R[mask]
        best_sigma[mask] = sigma

    # Schwellwert + Map-NMS
    thr = float(config.get("det_thresh", 0.0))
    ksz = int(config.get("nms_kernel", 3))
    if ksz % 2 == 0:
        ksz += 1
    se = np.ones((ksz, ksz), np.uint8)

    maxmap = cv2.dilate(Rmax, se)
    # Plateaus bei k=3 oft zulassen; für größere Fenster zusätzlich Erosion:
    peaks = (Rmax >= maxmap - max(1e-12, 8 * np.finfo(np.float32).eps * np.nanmax(np.abs(Rmax)))) & (Rmax >= thr)
    if ksz >= 5:
        minmap = cv2.erode(Rmax, se)
        eps = max(1e-12, 8 * np.finfo(np.float32).eps * np.nanmax(np.abs(Rmax)))
        peaks &= (Rmax > minmap + eps)

    ys, xs = np.where(peaks)
    responses = Rmax[ys, xs]
    sigmas = best_sigma[ys, xs]
    if len(xs) == 0:
        return (img, ([], Rmax)) if not draw else (img, ([], Rmax))

    # --- Option 1: exakt gleiches Pixel -> nur bestes behalten
    uniq_best = {}
    for i in range(len(xs)):
        key = (int(xs[i]), int(ys[i]))
        r = float(responses[i])
        if key not in uniq_best or r > uniq_best[key][0]:
            uniq_best[key] = (r, i)
    keep_idx = [i for (_, i) in uniq_best.values()]
    keep_idx.sort(key=lambda i: -responses[i])

    xs = xs[keep_idx]
    ys = ys[keep_idx]
    responses = responses[keep_idx]
    sigmas = sigmas[keep_idx]

    # --- Option 2: Radius-NMS (greedy), adaptiv per σ oder fix
    base_radius = int(config.get("nms_radius", 0))
    sigma_factor = float(config.get("nms_sigma_factor", 0.0))
    if base_radius > 0 or sigma_factor > 0.0:
        keep = []
        taken = np.zeros(len(xs), dtype=bool)
        for i in range(len(xs)):  # bereits nach Score sortiert
            if taken[i]:
                continue
            keep.append(i)
            r_adapt = int(round(sigma_factor * float(sigmas[i]))) if sigma_factor > 0 else 0
            r = max(base_radius, r_adapt)
            if r > 0:
                dx = xs - xs[i]
                dy = ys - ys[i]
                taken |= (dx * dx + dy * dy) <= (r * r)
        xs = xs[keep]
        ys = ys[keep]
        responses = responses[keep]
        sigmas = sigmas[keep]

    # KeyPoints erzeugen
    order = np.argsort(-responses)
    keypoints: List[cv2.KeyPoint] = []
    for idx in order:
        y = float(ys[idx])
        x = float(xs[idx])
        s = 3.0 * float(sigmas[idx])  # nur Visualisierung
        r_resp = float(responses[idx])
        keypoints.append(cv2.KeyPoint(x, y, s, -1, r_resp, 0, -1))

    if not draw or len(keypoints) == 0:
        return (img, (keypoints, Rmax))
    out = draw_keypoints(img, keypoints, style="cross")
    return (out, (keypoints, Rmax))
