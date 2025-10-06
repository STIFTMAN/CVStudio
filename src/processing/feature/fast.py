from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style


def fast(
    image: npt.NDArray[np.uint8 | np.float32]
) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:
    """
    Wendet FAST (Feature from Accelerated Segment Test) auf 'image' an.
    Gibt (image, (keypoints, descriptors)) zurück.
    Hinweis: FAST liefert KEINE Deskriptoren → descriptors ist ein leeres Array (0, 0).
    """

    config = processing_config["fast"]
    assert config is not None
    gray = to_gray_uint8(image)

    # FAST-Detektor erstellen
    fast = cv2.FastFeatureDetector_create(  # type: ignore
        threshold=config["threshold"],
        nonmaxSuppression=config["nonmaxSuppression"],
        type=config["type"],
    )

    keypoints = fast.detect(gray, None)

    # FAST hat keine Deskriptoren → leeres Array zurückgeben
    descriptors = np.empty((0, 0), dtype=np.uint8)

    return "cross", (keypoints, descriptors)
