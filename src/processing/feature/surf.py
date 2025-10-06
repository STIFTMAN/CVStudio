from typing import List, Tuple
import numpy as np
from numpy.typing import NDArray
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style


# ----------------- SURF: detection + descriptor -----------------
def surf(
    image: NDArray[np.uint8 | np.float32],
    draw: bool = True
) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:
    config = processing_config["surf"]
    assert config is not None
    gray_uint8 = to_gray_uint8(image)
    try:
        surf_detector = cv2.xfeatures2d.SURF_create(  # type: ignore[attr-defined]
            hessianThreshold=config["hessianThreshold"],
            nOctaves=config["nOctaves"],
            nOctaveLayers=config["nOctaveLayers"],
            extended=config["extended"],
            upright=config["upright"],
        )
    except AttributeError as err:
        raise RuntimeError(
            "SURF is not available in your OpenCV build. "
            "OpenCV must be built with OPENCV_ENABLE_NONFREE and xfeatures2d."
        ) from err

    keypoints, descriptors = surf_detector.detectAndCompute(gray_uint8, None)
    if descriptors is None:
        descriptors = np.zeros(
            (0, 128 if config["extended"] else 64), dtype=np.float32
        )
    return "circle", (keypoints, descriptors)
