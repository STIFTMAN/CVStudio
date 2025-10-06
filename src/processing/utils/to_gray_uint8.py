import numpy as np
from numpy.typing import NDArray
import cv2


# ----------------- Helper function -----------------
def to_gray_uint8(image: NDArray[np.uint8 | np.float32]) -> np.ndarray:
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    if gray.dtype == np.uint8:
        return gray
    gray = gray.astype(np.float32)
    max_value = float(gray.max()) if gray.size else 1.0
    if max_value <= 1.5:
        gray = (np.clip(gray, 0.0, 1.0) * 255.0).astype(np.uint8)
    else:
        gray = np.clip(gray, 0.0, 255.0).astype(np.uint8)
    return gray
