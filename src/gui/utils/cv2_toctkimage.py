import numpy as np
from PIL import Image as PILImage
import customtkinter as ctk
import cv2


def cv2_to_ctkimage(cv2_image: np.ndarray) -> ctk.CTkImage:
    height: int = cv2_image.shape[0]
    width: int = cv2_image.shape[1]
    rgb_image: np.ndarray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_image: PILImage.Image = PILImage.fromarray(rgb_image)
    return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(width, height))
