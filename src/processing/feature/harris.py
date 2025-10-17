import cv2
import numpy as np
from typing import Tuple, List
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style


def harris(image: np.ndarray) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:
    config = processing_config["feature"]["harris"]
    assert config is not None
    gray = to_gray_uint8(image)
    pts = cv2.goodFeaturesToTrack(gray, maxCorners=config["maxCorners"], qualityLevel=config["qualityLevel"], minDistance=config["minDistance"],
                                  blockSize=config["blockSize"], useHarrisDetector=True, k=config["k"])
    kps: List[cv2.KeyPoint] = []
    if pts is not None:
        for p in pts.reshape(-1, 2):
            kps.append(cv2.KeyPoint(float(p[0]), float(p[1]), 3.0))
    desc = np.empty((0, 0), dtype=np.uint8)
    return "cross", (kps, desc)
