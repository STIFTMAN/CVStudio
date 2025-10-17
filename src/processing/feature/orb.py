from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style


def orb(
    image: npt.NDArray[np.uint8 | np.float32]
) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:

    config = processing_config["feature"]["orb"]
    assert config is not None
    gray = to_gray_uint8(image)

    orb = cv2.ORB_create(  # type: ignore
        nfeatures=config["nfeatures"],
        scaleFactor=config["scaleFactor"],
        nlevels=config["nlevels"],
        edgeThreshold=config["edgeThreshold"],
        firstLevel=config["firstLevel"],
        WTA_K=config["WTA_K"],
        scoreType=config["scoreType"],
        patchSize=config["patchSize"],
        fastThreshold=config["fastThreshold"],
    )

    keypoints, descriptors = orb.detectAndCompute(gray, None)

    if descriptors is None:
        descriptors = np.empty((0, 32), dtype=np.uint8)

    return "point", (keypoints, descriptors)
