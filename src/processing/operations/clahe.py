import numpy as np
import cv2 as cv
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


def clahe(
    image,
    clip_limit: float = 4.0,
    tile_grid_size: tuple[int, int] = (16, 16)
) -> np.ndarray:
    x = np.asarray(image)
    isnan = np.isnan(x)
    xf = x.astype(np.float32, copy=True)

    def _to_u8(img: np.ndarray) -> tuple[np.ndarray, float, float]:
        finite = np.isfinite(img)
        if not finite.any():
            return np.zeros_like(img, dtype=np.uint8), 0.0, 1.0
        vmin = np.nanmin(img[finite])
        vmax = np.nanmax(img[finite])
        if vmax <= vmin:
            return np.zeros_like(img, dtype=np.uint8), vmin, vmax
        u = (img - vmin) / (vmax - vmin)
        u = np.clip(u, 0, 1) * 255.0
        return u.astype(np.uint8), vmin, vmax

    def _from_u8(u8: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
        if vmax <= vmin:
            return np.full_like(u8, vmin, dtype=np.float32)
        return (u8.astype(np.float32) / 255.0) * (vmax - vmin) + vmin

    clahe = cv.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    if xf.ndim == 2:
        u8, vmin, vmax = _to_u8(xf)
        eq = clahe.apply(u8)
        out = _from_u8(eq, vmin, vmax)

    elif xf.ndim == 3 and xf.shape[2] == 3:
        u8, vmin, vmax = _to_u8(xf)
        lab = cv.cvtColor(u8, cv.COLOR_RGB2LAB)
        L, A, B = cv.split(lab)
        L_eq = clahe.apply(L)
        lab_eq = cv.merge((L_eq, A, B))
        rgb_eq = cv.cvtColor(lab_eq, cv.COLOR_LAB2RGB)
        out = _from_u8(rgb_eq, vmin, vmax)

    else:
        log.log.write(text=Error.RESIZE_IMAGE_NDIM.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    out = out.astype(np.float32, copy=False)
    out[isnan] = np.nan
    return out
