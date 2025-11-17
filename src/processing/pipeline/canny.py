import numpy as np
from numpy.typing import NDArray
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config


def canny(
    image: NDArray[np.uint8 | np.float32]
) -> np.ndarray:
    config = processing_config["pipeline"]["canny"]
    assert config is not None
    gray = to_gray_uint8(image)

    edges = cv2.Canny(gray, config["canny1"], config["canny2"], apertureSize=config["aperture_size"])

    canvas = np.zeros_like(gray)

    canvas[edges > 0] = 255

    return canvas