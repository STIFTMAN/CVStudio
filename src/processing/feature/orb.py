from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import cv2
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.utils.draw_keypoints import draw_keypoints
from src.processing.root_config import processing_config


def orb(
    image: npt.NDArray[np.uint8 | np.float32],
    draw: bool = True
) -> tuple[npt.NDArray[np.uint8 | np.float32], Tuple[List[cv2.KeyPoint], np.ndarray]]:
    """
    Wendet ORB auf 'image' an und gibt (image, (keypoints, descriptors)) zurück.
    - image: Eingabebild als uint8 oder float32, Grau- oder Farbbild (BGR).
    - keypoints: Liste der gefundenen cv2.KeyPoint-Objekte.
    - descriptors: np.ndarray mit dtype=uint8 (binäre Deskriptoren), Form (N, 32) standardmäßig.
    """
    config = processing_config["orb"]
    assert config is not None
    gray = to_gray_uint8(image)

    # ORB-Instanz (Standard-Parameter; bei Bedarf anpassen)
    orb = cv2.ORB_create(  # type: ignore
        nfeatures=config["nfeatures"],       # mehr Features als Default
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
        # leeres (0, 32) uint8-Array, damit der Rückgabetyp stabil bleibt
        descriptors = np.empty((0, 32), dtype=np.uint8)

    if not draw or len(keypoints) == 0:
        return (image, (keypoints, descriptors))

    out = draw_keypoints(image, keypoints, style="point")

    return out, (keypoints, descriptors)
