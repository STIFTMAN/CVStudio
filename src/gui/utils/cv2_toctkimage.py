import numpy as np
from PIL import Image as PILImage
import customtkinter as ctk
import cv2
import src.gui.utils.logger as log
from src.gui.state.error import Error, Info
from pathlib import Path


def _black_like_uint8(a: np.ndarray) -> np.ndarray:
    log.log.write(text=Info.RETURN_EMPTY_IMAGE.value, tag="INFO", modulename=Path(__file__).stem)
    return np.zeros(a.shape, dtype=np.uint8)


def cv2_to_ctkimage(cv2_image: np.ndarray) -> ctk.CTkImage:
    if cv2_image is None:
        log.log.write(text=Error.RESIZE_IMAGE_NONE.value, tag="ERROR", modulename=Path(__file__).stem)
        cv2_image = _black_like_uint8(cv2_image)

    img = cv2_image
    if img.dtype != np.uint8:
        img = np.clip(img, 0, 255).astype(np.uint8)

    h, w = img.shape[:2]

    if img.ndim == 2:  # Graubild
        pil = PILImage.fromarray(img, mode="L")
    elif img.ndim == 3:
        if img.shape[2] == 3:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil = PILImage.fromarray(rgb, mode="RGB")
        elif img.shape[2] == 4:
            rgba = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            pil = PILImage.fromarray(rgba, mode="RGBA")
        else:
            log.log.write(text=Error.RESIZE_IMAGE_CHANNEL.value, tag="ERROR", modulename=Path(__file__).stem)
            pil = PILImage.fromarray(_black_like_uint8(img), mode="RGB")
    else:
        log.log.write(text=Error.RESIZE_IMAGE_NDIM.value, tag="ERROR", modulename=Path(__file__).stem)
        pil = PILImage.fromarray(_black_like_uint8(img), mode="RGB")

    return ctk.CTkImage(light_image=pil, dark_image=pil, size=(w, h))
