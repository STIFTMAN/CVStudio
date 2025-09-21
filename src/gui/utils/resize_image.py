import numpy as np
import cv2
from PIL import Image, ImageOps
from PIL.Image import Resampling
import customtkinter


def _black_like_uint8(a: np.ndarray) -> np.ndarray:
    return np.zeros(a.shape, dtype=np.uint8)


def _as_uint8_strict(a: np.ndarray) -> np.ndarray:
    arr = np.asarray(a)

    if np.iscomplexobj(arr):
        print(f"Fehler: Komplexe Daten werden nicht unterstuetzt (dtype={arr.dtype}). Rueckgabe: schwarzes Bild.")
        return _black_like_uint8(arr)

    if arr.dtype == np.uint8:
        return arr

    if arr.dtype == np.bool_:
        return arr.astype(np.uint8, copy=False)

    if np.issubdtype(arr.dtype, np.floating):
        if not np.isfinite(arr).all():
            print("Fehler: Nicht-endliche Werte (NaN/Inf) gefunden. Rueckgabe: schwarzes Bild.")
            return _black_like_uint8(arr)
        vmin = float(arr.min())
        vmax = float(arr.max())
        if vmin < 0.0 or vmax > 255.0:
            print(f"Fehler: Werte ausserhalb des darstellbaren Bereichs [0,255] (min={vmin:.3f}, max={vmax:.3f}). "
                  "Keine Skalierung erlaubt. Rueckgabe: schwarzes Bild.")
            return _black_like_uint8(arr)
        return np.rint(arr).astype(np.uint8)

    if np.issubdtype(arr.dtype, np.integer):
        vmin = int(arr.min())
        vmax = int(arr.max())
        if vmin < 0 or vmax > 255:
            print(f"Fehler: Integer-Werte ausserhalb von [0,255] (min={vmin}, max={vmax}). "
                  "Keine Skalierung erlaubt. Rueckgabe: schwarzes Bild.")
            return _black_like_uint8(arr)
        return arr.astype(np.uint8, copy=False)

    print(f"Fehler: Nicht unterstuetzter Datentyp (dtype={arr.dtype}). Rueckgabe: schwarzes Bild.")
    return _black_like_uint8(arr)


def resize_image_to_label(label,
                          cv2_image: np.ndarray,
                          background_rgb=(0, 0, 0)):
    """Skaliert ein OpenCV-Bild (Grau/BGR/BGRA/RGB) proportional ins Label (ohne Alpha)
       und gibt ein customtkinter.CTkImage (RGB) zurück.
    """
    target_width = label.winfo_width()
    target_height = label.winfo_height()
    if target_width < 2 or target_height < 2:
        return None
    if cv2_image is None:
        raise ValueError("cv2_image is None")

    # Nur dtype fixen (keine Werte-Skalierung)
    img = _as_uint8_strict(cv2_image)

    # In PIL konvertieren – strikt ohne Alpha
    if img.ndim == 2:
        # --- echter 1-Kanal-Flow ---
        pil_L = Image.fromarray(img, mode="L")
        # proportional einpassen (ohne Alpha)
        resized_L = ImageOps.contain(pil_L, (target_width, target_height), Resampling.LANCZOS)
        # Letterbox als RGB-Hintergrund
        final_rgb = Image.new("RGB", (target_width, target_height), background_rgb)
        # Graubild nach RGB replizieren (kanalgleich => garantiert nicht bunt)
        resized_RGB = resized_L.convert("RGB")
        x_off = (target_width - resized_RGB.width) // 2
        y_off = (target_height - resized_RGB.height) // 2
        final_rgb.paste(resized_RGB, (x_off, y_off))
        pil_final = final_rgb

    elif img.ndim == 3:
        c = img.shape[2]
        if c == 3:
            # BGR -> RGB
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_rgb = Image.fromarray(rgb, mode="RGB")
        elif c == 4:
            # BGRA -> BGR (Alpha verwerfen), dann nach RGB
            bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            pil_rgb = Image.fromarray(rgb, mode="RGB")
        else:
            print(f"Fehler: Unerwartete Kanalanzahl (C={c}) bei Shape {img.shape}. Rueckgabe: schwarzes Bild.")
            black_rgb = Image.new("RGB", (img.shape[1], img.shape[0]), (0, 0, 0))
            pil_rgb = black_rgb

        # proportional einpassen (ohne Alpha)
        resized_rgb = ImageOps.contain(pil_rgb, (target_width, target_height), Resampling.LANCZOS)
        final_rgb = Image.new("RGB", (target_width, target_height), background_rgb)
        x_off = (target_width - resized_rgb.width) // 2
        y_off = (target_height - resized_rgb.height) // 2
        final_rgb.paste(resized_rgb, (x_off, y_off))
        pil_final = final_rgb

    else:
        print(f"Fehler: Erwarte 2D oder 3D Array, erhalten: ndim={img.ndim}, Shape={img.shape}. Rueckgabe: schwarzes Bild.")
        pil_final = Image.new("RGB", (target_width, target_height), (0, 0, 0))

    return customtkinter.CTkImage(
        light_image=pil_final,
        dark_image=pil_final,
        size=(target_width, target_height)
    )
