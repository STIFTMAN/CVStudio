from PIL import Image, ImageOps
from PIL.Image import Resampling
import cv2
import numpy as np
import customtkinter


def resize_image_to_label(label, cv2_image: np.ndarray):
    target_width = label.winfo_width()
    target_height = label.winfo_height()
    if target_width < 2 or target_height < 2:
        return None
    rgb_image: np.ndarray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_image: Image.Image = Image.fromarray(rgb_image).convert("RGBA")
    resized_img = ImageOps.contain(pil_image, (target_width, target_height), Resampling.LANCZOS)
    final_image = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
    x_offset = (target_width - resized_img.width) // 2
    y_offset = (target_height - resized_img.height) // 2
    final_image.paste(resized_img, (x_offset, y_offset), resized_img)
    return customtkinter.CTkImage(light_image=final_image, dark_image=final_image, size=(target_width, target_height))

