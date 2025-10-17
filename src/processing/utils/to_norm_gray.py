import numpy as np
from numpy.typing import NDArray
import cv2


def to_norm_gray(img: NDArray[np.uint8 | np.float32]) -> np.ndarray:
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    if gray.dtype == np.uint8:
        gray = gray.astype(np.float32) / 255.0
    elif gray.dtype == np.float32:
        m = gray.max()
        if m > 1.5:
            gray = np.clip(gray, 0, 255) / 255.0
    else:
        gray = gray.astype(np.float32)
        m = gray.max()
        if m > 1.5:
            gray /= 255.0
    return gray
