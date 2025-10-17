from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


def sift(
    image: npt.NDArray[np.uint8 | np.float32]
) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:
    config = processing_config["feature"]["surf"]
    assert config is not None
    gray = to_gray_uint8(image)
    try:
        sift = cv2.xfeatures2d.SIFT_create()  # type: ignore
    except AttributeError:
        log.log.write(text=Error.XFEATURES2D.value, tag="ERROR", modulename=Path(__file__).stem)
        sift = cv2.SIFT_create()  # type: ignore
    keypoints, descriptors = sift.detectAndCompute(gray, None)

    if descriptors is None:
        descriptors = np.empty((0, 128), dtype=np.float32)

    return "point", (keypoints, descriptors)
