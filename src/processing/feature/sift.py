from __future__ import annotations
from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.utils.draw_keypoints import draw_keypoints
from src.processing.root_config import processing_config


def sift(
    image: npt.NDArray[np.uint8 | np.float32],
    draw: bool = True
) -> tuple[npt.NDArray[np.uint8 | np.float32], Tuple[List[cv2.KeyPoint], np.ndarray]]:
    """
    Wendet SIFT auf 'image' an und gibt (image, (keypoints, descriptors)) zurück.
    - image: Eingabebild als uint8 oder float32, Grau- oder Farbbild (BGR).
    - keypoints: Liste der gefundenen cv2.KeyPoint-Objekte.
    - descriptors: np.ndarray der Größe (N, 128), dtype float32. Leeres Array bei N=0.
    """
    config = processing_config["surf"]
    assert config is not None
    gray = to_gray_uint8(image)

    # SIFT-Instanz erstellen (Fallback für sehr alte OpenCV-Builds)
    try:
        sift = cv2.SIFT_create()  # type: ignore
    except AttributeError:
        sift = cv2.xfeatures2d.SIFT_create()  # type: ignore[attr-defined]

    keypoints, descriptors = sift.detectAndCompute(gray, None)

    if descriptors is None:
        descriptors = np.empty((0, 128), dtype=np.float32)

    # Das Originalbild (unverändert) plus (Keypoints, Deskriptoren) zurückgeben

    if not draw or len(keypoints) == 0:
        return (image, (keypoints, descriptors))

    out = draw_keypoints(image, keypoints, style="point")

    return out, (keypoints, descriptors)
