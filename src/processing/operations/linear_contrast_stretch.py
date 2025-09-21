import numpy as np


def linear_contrast_stretch(img_f32: np.ndarray) -> np.ndarray:
    # f_min, f_max aus dem Bild
    fmin = float(np.min(img_f32))
    fmax = float(np.max(img_f32))

    # Sonderfälle sauber behandeln
    if not np.isfinite(fmin) or not np.isfinite(fmax):
        return np.zeros_like(img_f32, dtype=np.uint8)

    eps = 1e-12
    denom = max(fmax - fmin, eps)

    # Formel aus dem Bild (Gmin=0, Gmax=255)
    y = (255.0 - 0.0) * ((img_f32 - fmin) / denom) + 0.0

    # nach uint8 mappen
    np.rint(y, out=y)
    np.clip(y, 0.0, 255.0, out=y)
    return y.astype(np.uint8, copy=False)
