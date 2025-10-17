import numpy as np


def gamma(img, gamma: float, eps=1e-12):
    out_dtype = img.dtype

    x = img.astype(np.float32)

    if x.ndim == 3:
        axis = (0, 1)
        fmin = x.min(axis=axis, keepdims=True)
        fmax = x.max(axis=axis, keepdims=True)
    else:
        fmin = np.min(x)
        fmax = np.max(x)

    denom = np.maximum(fmax - fmin, eps)
    z = (x - fmin) / denom
    z = np.clip(z, 0.0, 1.0)

    if np.issubdtype(out_dtype, np.integer):
        info = np.iinfo(out_dtype)
        Gmin, Gmax = float(info.min), float(info.max)
    else:
        Gmin, Gmax = 0.0, 1.0

    y = (Gmax - Gmin) * np.power(z, gamma) + Gmin

    if np.issubdtype(out_dtype, np.integer):
        y = np.rint(y).clip(np.iinfo(out_dtype).min, np.iinfo(out_dtype).max)
    else:
        y = y.clip(Gmin, Gmax)
    return y.astype(out_dtype)
