import numpy as np
import cv2
from PIL import Image, ImageOps
from PIL.Image import Resampling
import customtkinter
import src.gui.utils.logger as log
from src.gui.state.error import Error, Info
from pathlib import Path


def _black_like_uint8(a: np.ndarray) -> np.ndarray:
    log.log.write(text=Info.RETURN_EMPTY_IMAGE.value, tag="INFO", modulename=Path(__file__).stem)
    return np.zeros(a.shape, dtype=np.uint8)


def _as_uint8_strict(a: np.ndarray) -> np.ndarray:
    arr = np.asarray(a)

    if np.iscomplexobj(arr):
        log.log.write(text=Error.RESIZE_IMAGE_COMPLEX.value, tag="WARNING", modulename=Path(__file__).stem)
        return _black_like_uint8(arr)

    if arr.dtype == np.uint8:
        return arr

    if arr.dtype == np.bool_:
        return arr.astype(np.uint8, copy=False)

    if np.issubdtype(arr.dtype, np.floating):
        if not np.isfinite(arr).all():
            log.log.write(text=Error.RESIZE_IMAGE_COMPLEX.value, tag="WARNING", modulename=Path(__file__).stem)
            return _black_like_uint8(arr)
        vmin = float(arr.min())
        vmax = float(arr.max())
        if vmin < 0.0 or vmax > 255.0:
            log.log.write(text=f"{Error.RESIZE_IMAGE_SCALE.value} (min={vmin}, max={vmax})", tag="WARNING", modulename=Path(__file__).stem)
            return _black_like_uint8(arr)
        return np.rint(arr).astype(np.uint8)

    if np.issubdtype(arr.dtype, np.integer):
        vmin = int(arr.min())
        vmax = int(arr.max())
        if vmin < 0 or vmax > 255:
            log.log.write(text=f"{Error.RESIZE_IMAGE_SCALE.value} (min={vmin}, max={vmax})", tag="WARNING", modulename=Path(__file__).stem)
            return _black_like_uint8(arr)
        return arr.astype(np.uint8, copy=False)

    log.log.write(text=Error.RESIZE_IMAGE_UNKNOWN_DTYPE.value, tag="WARNING", modulename=Path(__file__).stem)
    return _black_like_uint8(arr)


def resize_image_to_label(label, cv2_image: np.ndarray, background_rgb=(0, 0, 0)):
    target_width = label.winfo_width()
    target_height = label.winfo_height()
    if target_width < 2 or target_height < 2:
        return None
    if cv2_image is None:
        log.log.write(text=Error.RESIZE_IMAGE_NONE.value, tag="Error", modulename=Path(__file__).stem)
        return None

    img = _as_uint8_strict(cv2_image)

    if img.ndim == 2:
        pil_L = Image.fromarray(img, mode="L")
        resized_L = ImageOps.contain(pil_L, (target_width, target_height), Resampling.LANCZOS)
        final_rgb = Image.new("RGB", (target_width, target_height), background_rgb)
        resized_RGB = resized_L.convert("RGB")
        x_off = (target_width - resized_RGB.width) // 2
        y_off = (target_height - resized_RGB.height) // 2
        final_rgb.paste(resized_RGB, (x_off, y_off))
        pil_final = final_rgb

    elif img.ndim == 3:
        c = img.shape[2]
        if c == 3:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_rgb = Image.fromarray(rgb, mode="RGB")
        elif c == 4:
            bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            pil_rgb = Image.fromarray(rgb, mode="RGB")
        else:
            log.log.write(text=f"{Error.RESIZE_IMAGE_CHANNEL.value} (channels={img.shape})", tag="WARNING", modulename=Path(__file__).stem)
            black_rgb = Image.new("RGB", (img.shape[1], img.shape[0]), (0, 0, 0))
            pil_rgb = black_rgb

        resized_rgb = ImageOps.contain(pil_rgb, (target_width, target_height), Resampling.LANCZOS)
        final_rgb = Image.new("RGB", (target_width, target_height), background_rgb)
        x_off = (target_width - resized_rgb.width) // 2
        y_off = (target_height - resized_rgb.height) // 2
        final_rgb.paste(resized_rgb, (x_off, y_off))
        pil_final = final_rgb

    else:
        log.log.write(text=f"{Error.RESIZE_IMAGE_NDIM.value} (ndim={img.ndim})", tag="WARNING", modulename=Path(__file__).stem)
        pil_final = Image.new("RGB", (target_width, target_height), (0, 0, 0))

    return customtkinter.CTkImage(light_image=pil_final, dark_image=pil_final, size=(target_width, target_height))
