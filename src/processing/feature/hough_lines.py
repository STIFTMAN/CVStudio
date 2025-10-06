from typing import List, Tuple
import numpy as np
import numpy.typing as npt
import cv2
import math
from src.processing.utils.to_gray_uint8 import to_gray_uint8
from src.processing.root_config import processing_config
from src.processing.utils.draw_keypoints import Style


def hough_lines(
    image: npt.NDArray[np.uint8 | np.float32]
) -> tuple[Style, Tuple[List[cv2.KeyPoint], np.ndarray]]:
    config = processing_config["hough_lines"]
    assert config is not None
    gray = to_gray_uint8(image)

    # Kanten
    edges = cv2.Canny(gray, config["canny1"], config["canny2"], apertureSize=config["aperture_size"])

    # Hough-Linien
    lines = cv2.HoughLinesP(
        edges,
        rho=config["rho"],
        theta=np.deg2rad(config["theta_deg"]),
        threshold=config["hough_threshold"],
        minLineLength=config["min_line_length"],
        maxLineGap=config["max_line_gap"],
    )
    keypoints: List[cv2.KeyPoint] = []
    if lines is None:
        detections = np.empty((0, 4), dtype=np.float32)
        return "line", (keypoints, detections)

    lines = lines.reshape(-1, 4)
    detections = lines.astype(np.float32, copy=False)
    # In KeyPoints umwandeln (Mittelpunkt, Größe=Linienlänge, Winkel in Grad)
    for x1, y1, x2, y2 in lines:
        cx = (x1 + x2) * 0.5
        cy = (y1 + y2) * 0.5
        dx = float(x2 - x1)
        dy = float(y2 - y1)
        length = math.hypot(dx, dy)
        angle_deg = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
        keypoints.append(cv2.KeyPoint(x=float(cx), y=float(cy), size=max(length, 1e-3), angle=angle_deg))

    # Harris hat keine Deskriptoren → leeres Array zurückgeben
    descriptors = np.empty((0, 0), dtype=np.uint8)

    return "line", (keypoints, descriptors)
