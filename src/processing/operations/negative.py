import numpy as np
import numpy.typing as npt


def negative(image: npt.NDArray) -> npt.NDArray[np.float32]:
    """
    Negativtransformation per Spiegelung am mittleren Bereich:
        out = (min + max) - image
    - Akzeptiert numerische ndarrays (H,W) oder (H,W,C), beliebiger Integer-/Float-Dtype.
    - Kanäle werden (bei (H,W,C)) **kanalweise** gespiegelt.
    - NaNs/Inf: Min/Max über finite Werte; NaNs bleiben erhalten.
    - Rückgabe: float32, gleiche Shape wie Input.
    """
    x = np.asarray(image)
    if not np.issubdtype(x.dtype, np.number):
        raise TypeError("image muss numerisch sein (Integer oder Float).")

    xf = x.astype(np.float32, copy=False)

    # Sonderfall: keine finiten Werte -> Kopie zurück
    if not np.isfinite(xf).any():
        return xf.copy()

    if xf.ndim == 2:
        # 2D: global min/max über finite Werte
        m = np.nanmin(np.where(np.isfinite(xf), xf, np.nan))
        M = np.nanmax(np.where(np.isfinite(xf), xf, np.nan))
        return (np.float32(m + M) - xf).astype(np.float32, copy=False)

    elif xf.ndim == 3:
        # 3D: per-Kanal min/max (H,W,C) -> Achsen (0,1)
        finite = np.isfinite(xf)
        m = np.nanmin(np.where(finite, xf, np.nan), axis=(0, 1))  # Shape (C,)
        M = np.nanmax(np.where(finite, xf, np.nan), axis=(0, 1))  # Shape (C,)
        mm = (m + M).astype(np.float32).reshape(1, 1, -1)
        return (mm - xf).astype(np.float32, copy=False)

    else:
        # Andere Shapes: behandle als 2D-Fläche (globale Spiegelung)
        m = np.nanmin(np.where(np.isfinite(xf), xf, np.nan))
        M = np.nanmax(np.where(np.isfinite(xf), xf, np.nan))
        return (np.float32(m + M) - xf).astype(np.float32, copy=False)
