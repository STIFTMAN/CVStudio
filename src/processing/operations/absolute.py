import numpy as np
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


def absolute(img: np.ndarray) -> np.ndarray:
    a = np.asarray(img)

    if np.issubdtype(a.dtype, np.signedinteger):
        info = np.iinfo(a.dtype)
        x = a.astype(np.int64, copy=False)
        y = np.abs(x)
        y = np.minimum(y, info.max)
        return y.astype(a.dtype, copy=False)

    if np.issubdtype(a.dtype, np.unsignedinteger):
        return a

    if np.issubdtype(a.dtype, np.floating):
        return np.abs(a).astype(a.dtype, copy=False)

    if np.iscomplexobj(a):
        log.log.write(text=Error.RESIZE_IMAGE_COMPLEX.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    log.log.write(text=Error.RESIZE_IMAGE_UNKNOWN_DTYPE.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)
    return a
