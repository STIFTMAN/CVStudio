import os
from typing import Tuple, List
import numpy as np
import numpy.typing as npt
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import shared_memory
import cv2

from src.gui.state import root  # übernimmt deine Status-Strings

# ----------------- Konstanten (auslagern) -----------------
TILE_SIZE: int = 1024
KEEP_FREE_CORES: int = 1
SUPPRESS_PADDING_BORDER: bool = True   # optional: äußeren Rand (kh/kw) auf 0 setzen


# ----------------- Worker (nicht-separabel) -----------------
def _worker_convolve_tile(
    shm_in_name: str,
    in_shape: Tuple[int, ...],
    shm_out_name: str,
    out_shape: Tuple[int, ...],
    tile_ij: Tuple[int, int, int, int],
    kernel_positions: List[Tuple[int, int, float]],  # (dy, dx, w) mit dy/dx in [0..kH-1/kW-1]
    stride: Tuple[int, int],
    channels: int
) -> None:
    sy, sx = stride
    i0, i1, j0, j1 = tile_ij
    tile_h, tile_w = i1 - i0, j1 - j0

    shm_in = shared_memory.SharedMemory(name=shm_in_name)
    shm_out = shared_memory.SharedMemory(name=shm_out_name)
    try:
        if channels == 1:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)   # (Hp, Wp)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)    # (Ho, Wo)
            _convolve_block_gray(padded, out, i0, i1, j0, j1, sy, sx, kernel_positions, tile_h, tile_w)
        else:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)   # (Hp, Wp, C)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)    # (Ho, Wo, C)
            for c in range(channels):
                _convolve_block_gray(padded[..., c], out[..., c], i0, i1, j0, j1, sy, sx, kernel_positions, tile_h, tile_w)
    finally:
        shm_in.close()
        shm_out.close()


def _convolve_block_gray(
    padded: np.ndarray, out: np.ndarray,
    i0: int, i1: int, j0: int, j1: int,
    sy: int, sx: int,
    kernel_positions: List[Tuple[int, int, float]],  # (pos_y, pos_x, w) in PADDED-Koords!
    tile_h: int, tile_w: int
) -> None:
    """Kernroutine für ein 2D-Block (float32). Erwartet kernel_positions ohne Flip, ohne +kh/+kw (top-left-Anker)."""
    acc = np.zeros((tile_h, tile_w), dtype=np.float32)
    tmp = np.empty((tile_h, tile_w), dtype=np.float32)
    for pos_y, pos_x, w in kernel_positions:
        if w == 0.0:
            continue
        rs = slice(pos_y + i0 * sy, pos_y + i1 * sy, sy)
        cs = slice(pos_x + j0 * sx, pos_x + j1 * sx, sx)
        np.multiply(padded[rs, cs], w, out=tmp)
        np.add(acc, tmp, out=acc)
    out[i0:i1, j0:j1] = acc


# ----------------- Worker (separabel) -----------------
def _worker_convolve_tile_separable(
    shm_in_name: str,
    in_shape: Tuple[int, ...],
    shm_out_name: str,
    out_shape: Tuple[int, ...],
    tile_ij: Tuple[int, int, int, int],
    ky: np.ndarray,   # 1D (kH,)
    kx: np.ndarray,   # 1D (kW,)
    stride: Tuple[int, int],
    channels: int
) -> None:
    sy, sx = stride
    i0, i1, j0, j1 = tile_ij

    shm_in = shared_memory.SharedMemory(name=shm_in_name)
    shm_out = shared_memory.SharedMemory(name=shm_out_name)
    try:
        if channels == 1:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)   # (Hp, Wp)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)    # (Ho, Wo)
            _convolve_block_gray_separable(padded, out, i0, i1, j0, j1, sy, sx, ky, kx)
        else:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)   # (Hp, Wp, C)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)    # (Ho, Wo, C)
            for c in range(channels):
                _convolve_block_gray_separable(padded[..., c], out[..., c], i0, i1, j0, j1, sy, sx, ky, kx)
    finally:
        shm_in.close()
        shm_out.close()


def _convolve_block_gray_separable(
    padded: np.ndarray, out: np.ndarray,
    i0: int, i1: int, j0: int, j1: int,
    sy: int, sx: int,
    ky: np.ndarray,  # (kH,)
    kx: np.ndarray   # (kW,)
) -> None:
    """
    Rechnet eine Tile-Ausgabe (i0:i1, j0:j1) über separablen Kernel.
    Vorgehen:
      1) Horizontale 1D-Korrelation -> Zwischenbild H (nur benötigte Zeilen/Spalten)
      2) Vertikale 1D-Korrelation auf H -> acc (Stride in y umgesetzt)
      3) acc in out[i0:i1, j0:j1]
    Korrelation (kein Flip), top-left-Anker – kompatibel zum Nicht-Separabel-Pfad.
    """
    kH = int(ky.shape[0])
    kW = int(kx.shape[0])
    tile_h = i1 - i0
    tile_w = j1 - j0

    # Zeilenbereich im gepaddeten Bild, den wir für dieses Tile benötigen:
    r_start = i0 * sy
    r_end = (i1 - 1) * sy + (kH - 1)
    R = r_end - r_start + 1  # Anzahl Zeilen

    # Spalten-Basis (X-Stride); für horizontale Faltung benötigen wir pro Out-Spalte kW Spalten
    c0_vec = (np.arange(j0, j1, dtype=np.int64) * sx)  # (tile_w,)
    # Zwischenbild H: (R, tile_w)
    H = np.zeros((R, tile_w), dtype=np.float32)

    rows = np.arange(r_start, r_end + 1, dtype=np.int64)  # (R,)
    # horizontale Korrelation vektorisiert
    for dx in range(kW):
        cols = c0_vec + dx  # (tile_w,)
        # padded[rows[:, None], cols[None, :]] -> (R, tile_w)
        np.add(H, padded[rows[:, None], cols[None, :]] * kx[dx], out=H)

    # vertikale Korrelation + Y-Stride
    acc = np.zeros((tile_h, tile_w), dtype=np.float32)
    for dy in range(kH):
        rs = slice(dy, dy + tile_h * sy, sy)
        np.add(acc, H[rs, :] * ky[dy], out=acc)

    out[i0:i1, j0:j1] = acc


# ----------------- Utilities -----------------
def _is_multichannel_gray(image_f32: np.ndarray) -> bool:
    """Erkennt 'mehrkanaliges Graubild' (Kanäle nahezu identisch)."""
    if image_f32.ndim != 3 or image_f32.shape[2] < 2:
        return False
    diff_var = np.var(image_f32[..., 0] - image_f32[..., 1])
    return diff_var < 1e-8  # type: ignore


def _to_gray_f32(image_f32: np.ndarray) -> np.ndarray:
    """(H,W[,C]) -> (H,W) float32. Nutzt Erkennung für mehrkanaliges Grau."""
    if image_f32.ndim == 2:
        return image_f32.astype(np.float32, copy=False)
    h, w, c = image_f32.shape
    if c == 1 or _is_multichannel_gray(image_f32):
        return image_f32[..., 0].astype(np.float32, copy=False)
    # OpenCV nutzt BGR; für Grau reicht cvtColor:
    return cv2.cvtColor(image_f32, cv2.COLOR_BGR2GRAY).astype(np.float32, copy=False)


def _try_factor_separable(
    k2d: np.ndarray,
    tol_rel: float = 1e-6
) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Prüft, ob k2d numerisch separierbar ist (Rang~1).
    Gibt (is_sep, ky, kx) zurück mit k2d ≈ ky[:, None] * kx[None, :].
    """
    k = np.asarray(k2d, dtype=np.float32, copy=False)
    kH, kW = k.shape

    # Referenzzeile finden
    ref = None
    for i in range(kH):
        row = k[i, :]
        if np.linalg.norm(row) > 0:
            ref = row
            break
    if ref is None:
        # Nullkernel
        return True, np.zeros((kH,), np.float32), np.zeros((kW,), np.float32)

    denom = float(np.dot(ref, ref))
    if denom == 0.0:
        return False, np.empty(0, np.float32), np.empty(0, np.float32)

    alpha = (k @ ref) / denom  # (kH,)
    k_hat = alpha[:, None] * ref[None, :]
    err = np.linalg.norm(k - k_hat, ord="fro")
    base = np.linalg.norm(k, ord="fro") + 1e-12
    rel_err = err / base
    if rel_err <= tol_rel:
        return True, alpha.astype(np.float32, copy=False), ref.astype(np.float32, copy=False)

    # Robustheit via SVD
    U, s, VT = np.linalg.svd(k, full_matrices=False)
    if s.size == 0:
        return False, np.empty(0, np.float32), np.empty(0, np.float32)
    k1 = (s[0] * np.outer(U[:, 0], VT[0, :])).astype(np.float32, copy=False)
    err = np.linalg.norm(k - k1, ord="fro")
    rel_err = err / base
    if rel_err <= tol_rel:
        r = np.sqrt(s[0]).astype(np.float32, copy=False)
        ky = (U[:, 0] * r).astype(np.float32, copy=False)
        kx = (VT[0, :] * r).astype(np.float32, copy=False)
        return True, ky, kx
    return False, np.empty(0, np.float32), np.empty(0, np.float32)


# ----------------- Öffentliche API -----------------
def default(
    image: npt.NDArray,                          # uint8 oder float32
    kernel: list[list[float]],
    stride: Tuple[int, int] = (1, 1),
    edge_filter: bool = False,
    use_conv_scale: bool = True
) -> npt.NDArray:
    """
    2D-Kreuzkorrelation (wie dein Referenz-Loop) mit zentriertem Kernel,
    Zero-Padding, Stride, Multiprocessing.
    - Farbbild  -> float32 (H, W, 3)
    - Graubild  -> uint8 (H, W) wenn USE_CONVERT_SCALE_ABS=True, sonst float32 (H, W)
    - edge_filter=True erzwingt 1-Kanal-Berechnung
    """
    assert root.status_details is not None

    # --- Stride prüfen
    root.status_details.set(root.current_lang.get("status_details_checking_sample_rate").get())
    sy, sx = stride
    if sy < 1 or sx < 1:
        raise ValueError("stride muss positive Ganzzahlen enthalten (>=1).")

    # --- Kernel prüfen
    root.status_details.set(root.current_lang.get("status_details_checking_kernal_dimensions").get())
    k = np.asarray(kernel, dtype=np.float32)
    if k.ndim != 2:
        raise ValueError("kernel muss 2D sein (kH, kW).")
    kH, kW = k.shape
    if (kH % 2 == 0) or (kW % 2 == 0):
        raise ValueError("kernel-Dimensionen müssen ungerade sein.")
    kh, kw = kH // 2, kW // 2

    # --- Eingabe -> float32
    root.status_details.set(root.current_lang.get("status_details_checking_image_datatype").get())
    if not (np.issubdtype(image.dtype, np.integer) or np.issubdtype(image.dtype, np.floating)):
        raise TypeError("image dtype muss uint8 oder float32 sein.")
    image_f32 = image.astype(np.float32, copy=False)

    # --- Graupfad (wenn edge_filter oder erkennbar grau)
    force_gray = (edge_filter or (image_f32.ndim == 2) or _is_multichannel_gray(image_f32) or (image_f32.ndim == 3 and image_f32.shape[2] in (1, 2)))
    if force_gray:
        proc = _to_gray_f32(image_f32)   # (H, W) float32
        channels = 1
    else:
        proc = image_f32 if image_f32.ndim == 3 else np.repeat(image_f32[..., None], 3, axis=2)
        channels = 3

    # --- separabler Fast-Path?
    root.status_details.set(root.current_lang.get("status_details_checking_kernal_values").get())
    is_sep, ky, kx = _try_factor_separable(k, tol_rel=1e-6)

    # --- Zero-Padding (immer)
    root.status_details.set(root.current_lang.get("status_details_set_padding").get())
    if channels == 1:
        padded = np.pad(proc, ((kh, kh), (kw, kw)), mode="constant", constant_values=0.0)
        H, W = proc.shape
        out_h, out_w = (H + sy - 1) // sy, (W + sx - 1) // sx
        out_shape = (out_h, out_w)
        in_shape = padded.shape
    else:
        padded = np.pad(proc, ((kh, kh), (kw, kw), (0, 0)), mode="constant", constant_values=0.0)
        H, W, _ = proc.shape
        out_h, out_w = (H + sy - 1) // sy, (W + sx - 1) // sx
        out_shape = (out_h, out_w, 3)
        in_shape = padded.shape

    padded = np.asarray(padded, dtype=np.float32, copy=False)

    # --- Shared Memory
    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    shm_in = shared_memory.SharedMemory(create=True, size=padded.nbytes)
    buf_in = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)
    root.status_details.set(root.current_lang.get("status_details_load_image_shared_memory").get())
    np.copyto(buf_in, padded, casting="no")

    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    n_out = int(np.prod(out_shape, dtype=np.int64))
    shm_out = shared_memory.SharedMemory(create=True, size=n_out * np.dtype(np.float32).itemsize)
    buf_out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)

    # --- 2D-Tiles planen
    root.status_details.set(root.current_lang.get("status_details_set_tile_splitting").get())
    tiles: List[Tuple[int, int, int, int]] = []
    for i0_ in range(0, out_h, TILE_SIZE):
        i1_ = min(i0_ + TILE_SIZE, out_h)
        for j0_ in range(0, out_w, TILE_SIZE):
            j1_ = min(j0_ + TILE_SIZE, out_w)
            tiles.append((i0_, i1_, j0_, j1_))

    # --- Workeranzahl: alle außer 1
    root.status_details.set(root.current_lang.get("status_details_checking_number_worker").get())
    cpu = os.cpu_count() or 2
    max_workers = max(1, cpu - max(1, KEEP_FREE_CORES))

    # --- Parallel rechnen
    root.status_details.set(root.current_lang.get("status_details_start_execution").get())
    try:
        if is_sep:
            # separabler Pfad (1D x + 1D y), ohne OpenCV
            with ProcessPoolExecutor(max_workers=max_workers) as ex:
                futures = [
                    ex.submit(
                        _worker_convolve_tile_separable,
                        shm_in.name, in_shape,
                        shm_out.name, out_shape,
                        tile_ij, ky, kx, (sy, sx), channels
                    )
                    for tile_ij in tiles
                ]
                for i, f in enumerate(as_completed(futures)):
                    root.status_details.set(f'[{i+1}/{len(futures)}] {root.current_lang.get("status_details_tile_progress").get()}')
                    f.result()
        else:
            # Fallback: 2D-Pfad
            kernel_positions: List[Tuple[int, int, float]] = [
                (dy, dx, float(k[dy, dx]))
                for dy in range(kH) for dx in range(kW)
                if k[dy, dx] != 0.0
            ]
            with ProcessPoolExecutor(max_workers=max_workers) as ex:
                futures = [
                    ex.submit(
                        _worker_convolve_tile,
                        shm_in.name, in_shape,
                        shm_out.name, out_shape,
                        tile_ij, kernel_positions, (sy, sx), channels
                    )
                    for tile_ij in tiles
                ]
                for i, f in enumerate(as_completed(futures)):
                    root.status_details.set(f'[{i+1}/{len(futures)}] {root.current_lang.get("status_details_tile_progress").get()}')
                    f.result()

        result_f32 = buf_out.copy().astype(np.float32, copy=False)
    finally:
        root.status_details.set(root.current_lang.get("status_details_unload_shared_memory").get())
        shm_in.close()
        shm_in.unlink()
        shm_out.close()
        shm_out.unlink()

    # --- optional: äußeren Rand nullen (visuelle Saumunterdrückung)
    if SUPPRESS_PADDING_BORDER:
        border_h, border_w = kh, kw
        if border_h > 0 or border_w > 0:
            if result_f32.ndim == 2:
                if border_h > 0:
                    result_f32[:border_h, :] = 0.0
                    result_f32[-border_h:, :] = 0.0
                if border_w > 0:
                    result_f32[:, :border_w] = 0.0
                    result_f32[:, -border_w:] = 0.0
            else:
                if border_h > 0:
                    result_f32[:border_h, :, :] = 0.0
                    result_f32[-border_h:, :, :] = 0.0
                if border_w > 0:
                    result_f32[:, :border_w, :] = 0.0
                    result_f32[:, -border_w:, :] = 0.0

    # --- Ausgabe
    if channels == 1:
        # Graubild
        if use_conv_scale:
            result_u8 = cv2.convertScaleAbs(result_f32)  # Betrag + u8 (wie Referenz)
            root.status_details.set(root.current_lang.get("status_details_done").get())
            return result_u8
        else:
            root.status_details.set(root.current_lang.get("status_details_done").get())
            return result_f32  # float32 roh (kein Clip, kein Abs)
    else:
        # Farbbild: float32, 3 Kanäle
        if result_f32.ndim == 2:
            result_f32 = np.stack([result_f32, result_f32, result_f32], axis=-1)
        elif result_f32.shape[2] != 3:
            if result_f32.shape[2] > 3:
                result_f32 = result_f32[..., :3]
            else:
                result_f32 = np.repeat(result_f32[..., :1], 3, axis=2)
        root.status_details.set(root.current_lang.get("status_details_done").get())
        return result_f32.astype(np.float32, copy=False)


'''
import os
from typing import Tuple, List
import numpy as np
import numpy.typing as npt
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import shared_memory
import cv2

from src.gui.state import root  # übernimmt deine Status-Strings

# ----------------- Konstanten (auslagern) -----------------
TILE_SIZE: int = 256
KEEP_FREE_CORES: int = 1
SUPPRESS_PADDING_BORDER: bool = True   # optional: äußeren Rand (kh/kw) auf 0 setzen


# ----------------- Worker -----------------
def _worker_convolve_tile(
    shm_in_name: str,
    in_shape: Tuple[int, ...],
    shm_out_name: str,
    out_shape: Tuple[int, ...],
    tile_ij: Tuple[int, int, int, int],
    kernel_positions: List[Tuple[int, int, float]],  # ACHTUNG: bereits mit +kh/+kw
    stride: Tuple[int, int],
    channels: int
) -> None:
    sy, sx = stride
    i0, i1, j0, j1 = tile_ij
    tile_h, tile_w = i1 - i0, j1 - j0

    shm_in = shared_memory.SharedMemory(name=shm_in_name)
    shm_out = shared_memory.SharedMemory(name=shm_out_name)
    try:
        if channels == 1:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)   # (Hp, Wp)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)    # (Ho, Wo)
            _convolve_block_gray(padded, out, i0, i1, j0, j1, sy, sx, kernel_positions, tile_h, tile_w)
        else:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)   # (Hp, Wp, C)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)    # (Ho, Wo, C)
            for c in range(channels):
                _convolve_block_gray(padded[..., c], out[..., c], i0, i1, j0, j1, sy, sx, kernel_positions, tile_h, tile_w)
    finally:
        shm_in.close()
        shm_out.close()


def _convolve_block_gray(
    padded: np.ndarray, out: np.ndarray,
    i0: int, i1: int, j0: int, j1: int,
    sy: int, sx: int,
    kernel_positions: List[Tuple[int, int, float]],  # (pos_y, pos_x, w) in PADDED-Koords!
    tile_h: int, tile_w: int
) -> None:
    """Kernroutine für ein 2D-Block (float32). Erwartet kernel_positions mit bereits eingerechnetem +kh/+kw."""
    acc = np.zeros((tile_h, tile_w), dtype=np.float32)
    tmp = np.empty((tile_h, tile_w), dtype=np.float32)
    for pos_y, pos_x, w in kernel_positions:
        if w == 0.0:
            continue
        rs = slice(pos_y + i0 * sy, pos_y + i1 * sy, sy)
        cs = slice(pos_x + j0 * sx, pos_x + j1 * sx, sx)
        np.multiply(padded[rs, cs], w, out=tmp)
        np.add(acc, tmp, out=acc)
    out[i0:i1, j0:j1] = acc


# ----------------- Utilities -----------------
def _is_multichannel_gray(image_f32: np.ndarray) -> bool:
    """Erkennt 'mehrkanaliges Graubild' (Kanäle nahezu identisch)."""
    if image_f32.ndim != 3 or image_f32.shape[2] < 2:
        return False
    diff_var = np.var(image_f32[..., 0] - image_f32[..., 1])
    return diff_var < 1e-8  # type: ignore


def _to_gray_f32(image_f32: np.ndarray) -> np.ndarray:
    """(H,W[,C]) -> (H,W) float32. Nutzt Erkennung für mehrkanaliges Grau."""
    if image_f32.ndim == 2:
        return image_f32.astype(np.float32, copy=False)
    h, w, c = image_f32.shape
    if c == 1 or _is_multichannel_gray(image_f32):
        return image_f32[..., 0].astype(np.float32, copy=False)
    # OpenCV nutzt BGR; für Grau reicht cvtColor:
    return cv2.cvtColor(image_f32, cv2.COLOR_BGR2GRAY).astype(np.float32, copy=False)


# ----------------- Öffentliche API -----------------
def default(
    image: npt.NDArray,                          # uint8 oder float32
    kernel: list[list[float]],
    stride: Tuple[int, int] = (1, 1),
    edge_filter: bool = False,
    use_conv_scale: bool = True
) -> npt.NDArray:
    """
    2D-Kreuzkorrelation (wie dein Referenz-Loop) mit zentriertem Kernel, Zero-Padding, Stride, Multiprocessing.
    - Farbbild  -> float32 (H, W, 3)
    - Graubild  -> uint8 (H, W) wenn USE_CONVERT_SCALE_ABS=True, sonst float32 (H, W)
    - edge_filter=True erzwingt 1-Kanal-Berechnung
    """
    assert root.status_details is not None

    # --- Stride prüfen
    root.status_details.set(root.current_lang.get("status_details_checking_sample_rate").get())
    sy, sx = stride
    if sy < 1 or sx < 1:
        raise ValueError("stride muss positive Ganzzahlen enthalten (>=1).")

    # --- Kernel prüfen
    root.status_details.set(root.current_lang.get("status_details_checking_kernal_dimensions").get())
    k = np.asarray(kernel, dtype=np.float32)
    if k.ndim != 2:
        raise ValueError("kernel muss 2D sein (kH, kW).")
    kH, kW = k.shape
    if (kH % 2 == 0) or (kW % 2 == 0):
        raise ValueError("kernel-Dimensionen müssen ungerade sein.")
    kh, kw = kH // 2, kW // 2

    # --- Kernel-Positionen vorbereiten (Korrelation, OHNE Flip) mit +kh/+kw!
    root.status_details.set(root.current_lang.get("status_details_checking_kernal_values").get())
    # Kreuzkorrelation wie Referenz: KEIN Flip, KEIN +kh/+kw
    kernel_positions: List[Tuple[int, int, float]] = [
        (dy, dx, float(k[dy, dx]))
        for dy in range(kH) for dx in range(kW)
        if k[dy, dx] != 0.0
    ]

    # --- Eingabe -> float32
    root.status_details.set(root.current_lang.get("status_details_checking_image_datatype").get())
    if not (np.issubdtype(image.dtype, np.integer) or np.issubdtype(image.dtype, np.floating)):
        raise TypeError("image dtype muss uint8 oder float32 sein.")
    image_f32 = image.astype(np.float32, copy=False)

    # --- Graupfad (wenn edge_filter oder erkennbar grau)
    force_gray = (edge_filter or (image_f32.ndim == 2) or _is_multichannel_gray(image_f32) or (image_f32.ndim == 3 and image_f32.shape[2] in (1, 2)))
    if force_gray:
        proc = _to_gray_f32(image_f32)   # (H, W) float32
        channels = 1
    else:
        proc = image_f32 if image_f32.ndim == 3 else np.repeat(image_f32[..., None], 3, axis=2)
        channels = 3

    # --- Zero-Padding (immer)
    root.status_details.set(root.current_lang.get("status_details_set_padding").get())
    if channels == 1:
        padded = np.pad(proc, ((kh, kh), (kw, kw)), mode="constant", constant_values=0.0)
        H, W = proc.shape
        out_h, out_w = (H + sy - 1) // sy, (W + sx - 1) // sx
        out_shape = (out_h, out_w)
        in_shape = padded.shape
    else:
        padded = np.pad(proc, ((kh, kh), (kw, kw), (0, 0)), mode="constant", constant_values=0.0)
        H, W, _ = proc.shape
        out_h, out_w = (H + sy - 1) // sy, (W + sx - 1) // sx
        out_shape = (out_h, out_w, 3)
        in_shape = padded.shape

    padded = np.asarray(padded, dtype=np.float32, copy=False)

    # --- Shared Memory
    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    shm_in = shared_memory.SharedMemory(create=True, size=padded.nbytes)
    buf_in = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)
    root.status_details.set(root.current_lang.get("status_details_load_image_shared_memory").get())
    np.copyto(buf_in, padded, casting="no")

    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    n_out = int(np.prod(out_shape, dtype=np.int64))
    shm_out = shared_memory.SharedMemory(create=True, size=n_out * np.dtype(np.float32).itemsize)
    buf_out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)

    # --- 2D-Tiles planen
    root.status_details.set(root.current_lang.get("status_details_set_tile_splitting").get())
    tiles: List[Tuple[int, int, int, int]] = []
    for i0 in range(0, out_h, TILE_SIZE):
        i1 = min(i0 + TILE_SIZE, out_h)
        for j0 in range(0, out_w, TILE_SIZE):
            j1 = min(j0 + TILE_SIZE, out_w)
            tiles.append((i0, i1, j0, j1))

    # --- Workeranzahl: alle außer 1
    root.status_details.set(root.current_lang.get("status_details_checking_number_worker").get())
    cpu = os.cpu_count() or 2
    max_workers = max(1, cpu - max(1, KEEP_FREE_CORES))

    # --- Parallel rechnen
    root.status_details.set(root.current_lang.get("status_details_start_execution").get())
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            futures = [
                ex.submit(
                    _worker_convolve_tile,
                    shm_in.name, in_shape,
                    shm_out.name, out_shape,
                    tile_ij, kernel_positions, (sy, sx), channels
                )
                for tile_ij in tiles
            ]
            for i, f in enumerate(as_completed(futures)):
                root.status_details.set(f'[{i+1}/{len(futures)}] {root.current_lang.get("status_details_tile_progress").get()}')
                f.result()

        result_f32 = buf_out.copy().astype(np.float32, copy=False)
    finally:
        root.status_details.set(root.current_lang.get("status_details_unload_shared_memory").get())
        shm_in.close()
        shm_in.unlink()
        shm_out.close()
        shm_out.unlink()

    # --- optional: äußeren Rand nullen (visuelle Saumunterdrückung)
    if SUPPRESS_PADDING_BORDER:
        border_h, border_w = kh, kw
        if border_h > 0 or border_w > 0:
            if result_f32.ndim == 2:
                result_f32[:border_h, :] = 0.0
                result_f32[-border_h:, :] = 0.0
                result_f32[:, :border_w] = 0.0
                result_f32[:, -border_w:] = 0.0
            else:
                result_f32[:border_h, :, :] = 0.0
                result_f32[-border_h:, :, :] = 0.0
                result_f32[:, :border_w, :] = 0.0
                result_f32[:, -border_w:, :] = 0.0

    # --- Ausgabe
    if channels == 1:
        # Graubild: je nach Wunsch anzeigen
        if use_conv_scale:
            result_u8 = cv2.convertScaleAbs(result_f32)  # Betrag + u8 (wie Referenz)
            root.status_details.set(root.current_lang.get("status_details_done").get())
            return result_u8
        else:
            root.status_details.set(root.current_lang.get("status_details_done").get())
            return result_f32  # float32 roh (kein Clip, kein Abs)
    else:
        # Farbbild: float32, 3 Kanäle
        if result_f32.ndim == 2:
            result_f32 = np.stack([result_f32, result_f32, result_f32], axis=-1)
        elif result_f32.shape[2] != 3:
            if result_f32.shape[2] > 3:
                result_f32 = result_f32[..., :3]
            else:
                result_f32 = np.repeat(result_f32[..., :1], 3, axis=2)
        root.status_details.set(root.current_lang.get("status_details_done").get())
        return result_f32.astype(np.float32, copy=False)
'''
