import numpy as np
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


def clip(img: np.ndarray) -> np.ndarray:
    if np.iscomplexobj(img):
        log.log.write(text=Error.RESIZE_IMAGE_COMPLEX.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    a = np.asarray(img)
    was_float = np.issubdtype(a.dtype, np.floating)
    was_three_channel = (a.ndim == 3 and a.shape[2] >= 3)

    looked_gray = False
    if was_three_channel and was_float:
        ch0, ch1, ch2 = a[..., 0], a[..., 1], a[..., 2]
        looked_gray = (np.allclose(ch0, ch1, atol=1e-6, equal_nan=True) and np.allclose(ch1, ch2, atol=1e-6, equal_nan=True))

    if a.dtype == np.uint8:
        out = a if a.flags['C_CONTIGUOUS'] else a.copy()

    elif was_float:
        outf = np.nan_to_num(a, copy=True, nan=0.0, neginf=0.0, posinf=255.0)
        np.clip(outf, 0.0, 255.0, out=outf)
        np.rint(outf, out=outf)
        out = outf.astype(np.uint8, copy=False)

    elif np.issubdtype(a.dtype, np.integer) or a.dtype == np.bool_:
        outi = a.astype(np.int64, copy=True)
        np.clip(outi, 0, 255, out=outi)
        out = outi.astype(np.uint8, copy=False)

    else:
        log.log.write(text=Error.RESIZE_IMAGE_COMPLEX.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    if looked_gray and out.ndim == 3 and out.shape[2] >= 3:
        out[..., 1] = out[..., 0]
        out[..., 2] = out[..., 0]

    return out
