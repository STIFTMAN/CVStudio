from typing import List, Tuple
import numpy as np
from numpy.typing import NDArray
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


def surf(
    image: NDArray[np.uint8 | np.float32]
) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:
    config = processing_config["feature"]["surf"]
    assert config is not None
    gray_uint8 = to_gray_uint8(image)
    try:
        surf_detector = cv2.xfeatures2d.SURF_create(  # type: ignore
            hessianThreshold=config["hessianThreshold"],
            nOctaves=config["nOctaves"],
            nOctaveLayers=config["nOctaveLayers"],
            extended=config["extended"],
            upright=config["upright"],
        )
    except Exception:
        log.log.write(text=Error.XFEATURES2D.value, tag="ERROR", modulename=Path(__file__).stem)
        descriptors = np.empty((0, 128), dtype=np.float32)
        return "point", ([], np.empty((0, 128), dtype=np.float32))

    keypoints, descriptors = surf_detector.detectAndCompute(gray_uint8, None)
    if descriptors is None:
        descriptors = np.zeros((0, 128 if config["extended"] else 64), dtype=np.float32)
    return "circle", (keypoints, descriptors)
