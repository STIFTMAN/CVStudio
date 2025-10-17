import numpy as np
import numpy.typing as npt
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


def negative(image: npt.NDArray) -> npt.NDArray[np.float32]:
    x = np.asarray(image)
    if not np.issubdtype(x.dtype, np.number):
        log.log.write(text=Error.IMAGE_NOT_NUMBER.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    xf = x.astype(np.float32, copy=False)

    if not np.isfinite(xf).any():
        return xf.copy()

    if xf.ndim == 2:
        m = np.nanmin(np.where(np.isfinite(xf), xf, np.nan))
        M = np.nanmax(np.where(np.isfinite(xf), xf, np.nan))
        return (np.float32(m + M) - xf).astype(np.float32, copy=False)

    elif xf.ndim == 3:
        finite = np.isfinite(xf)
        m = np.nanmin(np.where(finite, xf, np.nan), axis=(0, 1))
        M = np.nanmax(np.where(finite, xf, np.nan), axis=(0, 1))
        mm = (m + M).astype(np.float32).reshape(1, 1, -1)
        return (mm - xf).astype(np.float32, copy=False)

    else:
        m = np.nanmin(np.where(np.isfinite(xf), xf, np.nan))
        M = np.nanmax(np.where(np.isfinite(xf), xf, np.nan))
        return (np.float32(m + M) - xf).astype(np.float32, copy=False)
