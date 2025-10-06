from typing import Tuple
import cv2
import numpy as np


def rotate(img: np.ndarray, angle_deg: float) -> Tuple[np.ndarray, np.ndarray]:
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle_deg, 1.0)  # nur drehen
    out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return out, M


def scale(img: np.ndarray, scale: float) -> Tuple[np.ndarray, np.ndarray]:
    h, w = img.shape[:2]
    M = np.array([[scale, 0, (1 - scale) * w / 2.0],
                  [0, scale, (1 - scale) * h / 2.0]], dtype=np.float32)  # um Bildzentrum skalieren
    out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return out, M


def translate(img: np.ndarray, tx: float, ty: float) -> Tuple[np.ndarray, np.ndarray]:
    h, w = img.shape[:2]
    M = np.array([[1, 0, tx], [0, 1, ty]], dtype=np.float32)
    out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return out, M
