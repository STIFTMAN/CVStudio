import numpy as np
from PIL import Image as PILImage
import customtkinter as ctk
import cv2


def cv2_to_ctkimage(cv2_image: np.ndarray) -> ctk.CTkImage:
    if cv2_image is None:
        raise ValueError("cv2_image is None")

    img = cv2_image
    # Für Anzeige: uint8 erwarten
    if img.dtype != np.uint8:
        # Hier NICHT automatisch normalisieren, sonst veränderst du die Aussage!
        # Lieber vorher gezielt strecken und als uint8 übergeben.
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
            raise ValueError(f"Unerwartete Kanalanzahl: {img.shape[2]}")
    else:
        raise ValueError("Erwarte 2D (grau) oder 3D (H,W,C) Bilddaten.")

    # size exakt auf Original setzen -> kein Resampling
    return ctk.CTkImage(light_image=pil, dark_image=pil, size=(w, h))
