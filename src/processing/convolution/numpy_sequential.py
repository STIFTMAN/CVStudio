import os
import numpy as np
import numpy.typing as npt
from typing import Sequence, Tuple, List
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import shared_memory

# ---------- Worker: verarbeitet eine einzelne Ausgabekachel ----------
def _worker_conv_tile(
    shm_in_name: str,
    in_shape: Tuple[int, ...],           # gepaddete Eingabe: (Hp, Wp) oder (Hp, Wp, C)
    shm_out_name: str,
    out_shape: Tuple[int, ...],          # Ausgabe: (Ho, Wo) oder (Ho, Wo, C)
    tile_ij: Tuple[int, int, int, int],  # (i0, i1, j0, j1) in Output-Koordinaten
    kernel_pos: List[Tuple[int, int, float]],
    stride: Tuple[int, int],
    channels: int
) -> None:
    sy, sx = stride
    i0, i1, j0, j1 = tile_ij
    th, tw = i1 - i0, j1 - j0

    shm_in  = shared_memory.SharedMemory(name=shm_in_name)
    shm_out = shared_memory.SharedMemory(name=shm_out_name)
    try:
        if channels == 1:
            padded = np.ndarray(in_shape, dtype=np.uint8, buffer=shm_in.buf)   # (Hp, Wp)
            out    = np.ndarray(out_shape, dtype=np.uint8, buffer=shm_out.buf) # (Ho, Wo)
            _conv_block_gray(padded, out, i0, i1, j0, j1, sy, sx, kernel_pos, th, tw)
        else:
            padded = np.ndarray(in_shape, dtype=np.uint8, buffer=shm_in.buf)   # (Hp, Wp, C)
            out    = np.ndarray(out_shape, dtype=np.uint8, buffer=shm_out.buf) # (Ho, Wo, C)
            for c in range(channels):
                _conv_block_gray(padded[..., c], out[..., c], i0, i1, j0, j1, sy, sx, kernel_pos, th, tw)
    finally:
        shm_in.close()
        shm_out.close()


def _conv_block_gray(
    padded: np.ndarray, out: np.ndarray,
    i0: int, i1: int, j0: int, j1: int,
    sy: int, sx: int,
    kernel_pos: List[Tuple[int, int, float]],
    th: int, tw: int
) -> None:
    """Kernroutine für eine Ausgabekachel (Graubild, 2D)."""
    acc = np.zeros((th, tw), dtype=np.float32)
    tmp = np.empty((th, tw), dtype=np.float32)  # wiederverwendeter Buffer

    for dy, dx, w in kernel_pos:
        if w == 0.0:
            continue
        rs = slice(dy + i0*sy, dy + i1*sy, sy)  # Zeilen in gepaddeter Eingabe
        cs = slice(dx + j0*sx, dx + j1*sx, sx)  # Spalten
        # tmp = padded[rs, cs] * w   (ohne Extra-Array)
        np.multiply(padded[rs, cs], w, out=tmp, casting="unsafe")
        np.add(acc, tmp, out=acc)

    # clippen & schreiben
    np.clip(acc, 0.0, 255.0, out=acc)
    out[i0:i1, j0:j1] = acc.astype(np.uint8, copy=False)


# ---------- Öffentliche API: Drop-in-ersatz mit Multiprocessing ----------
def numpy_sequential(
    image: npt.NDArray[np.uint8],
    kernel: Sequence[Sequence[float]],
    *,
    stride: Tuple[int, int] = (1, 1),
    pad_mode: str = "reflect",
    tile: int = 256,               # Ausgabekachelgröße (größer = schneller, mehr RAM pro Prozess)
    keep_free_cores: int = 1,      # mindestens 1 Kern frei lassen
    max_workers: int | None = None # optional manuell setzen
) -> npt.NDArray[np.uint8]:
    """
    Multiprocessing-2D-Korrelation (ohne sliding_window_view), RAM-schonend & schnell.
    - image: (H,W) oder (H,W,C), dtype=uint8
    - kernel: 2D (float, bereits wie gewünscht skaliert/normalisiert)
    - stride: (sy, sx)
    - pad_mode: np.pad Modus ("reflect", "constant", "edge", ...)
    - tile: Kachelgröße der Ausgabe (in Pixeln der Output-Ebene)
    - hält standardmäßig einen Kern frei
    Rückgabe: uint8, Shape ≈ (ceil(H/sy), ceil(W/sx)[, C])
    """
    sy, sx = stride
    if sy < 1 or sx < 1:
        raise ValueError("stride muss positive Ganzzahlen enthalten (>=1).")

    k = np.asarray(kernel, dtype=np.float32)
    if k.ndim != 2:
        raise ValueError("kernel muss 2D sein (kH, kW).")
    kH, kW = k.shape
    if kH % 2 == 0 or kW % 2 == 0:
        raise ValueError("kernel-Dimensionen müssen ungerade sein (z.B. 3x3, 5x5).")
    kh, kw = kH // 2, kW // 2

    # Kernelpositionen & Gewichte (Nullgewichte überspringen)
    kernel_pos: List[Tuple[int, int, float]] = []
    for dy in range(kH):
        for dx in range(kW):
            w = float(k[dy, dx])
            if w != 0.0:
                kernel_pos.append((dy, dx, w))

    # --- Padding einmal im Parent-Prozess ---
    if image.ndim == 2:
        if pad_mode == "constant":
            padded = np.pad(image, ((kh, kh), (kw, kw)), mode="constant", constant_values=0)
        else:
            padded = np.pad(image, ((kh, kh), (kw, kw)), mode=pad_mode)
        channels = 1
        Hp, Wp = padded.shape
        H, W = image.shape
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        out_shape = (out_h, out_w)
        in_shape  = (Hp, Wp)
    elif image.ndim == 3:
        if pad_mode == "constant":
            padded = np.pad(image, ((kh, kh), (kw, kw), (0, 0)), mode="constant", constant_values=0)
        else:
            padded = np.pad(image, ((kh, kh), (kw, kw), (0, 0)), mode=pad_mode)
        channels = image.shape[2]
        Hp, Wp, _ = padded.shape
        H, W, _ = image.shape
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        out_shape = (out_h, out_w, channels)
        in_shape  = (Hp, Wp, channels)
    else:
        raise ValueError("image muss 2D (H, W) oder 3D (H, W, C) sein.")

    # --- Shared Memory anlegen und befüllen ---
    shm_in  = shared_memory.SharedMemory(create=True, size=padded.nbytes)
    buf_in  = np.ndarray(in_shape, dtype=np.uint8, buffer=shm_in.buf)
    np.copyto(buf_in, padded, casting="no")

    shm_out = shared_memory.SharedMemory(create=True, size=np.prod(out_shape, dtype=np.int64).item())
    buf_out = np.ndarray(out_shape, dtype=np.uint8, buffer=shm_out.buf)
    # keine Initialisierung nötig; jeder Task schreibt seine Kachel

    # --- Ausgabekacheln definieren ---
    tiles: List[Tuple[int, int, int, int]] = []
    for i0 in range(0, out_h, tile):
        i1 = min(i0 + tile, out_h)
        for j0 in range(0, out_w, tile):
            j1 = min(j0 + tile, out_w)
            tiles.append((i0, i1, j0, j1))

    # --- Worker-Anzahl bestimmen: mindestens 1, einen Kern frei lassen ---
    if max_workers is None:
        cpu = os.cpu_count() or 2
        max_workers = max(1, cpu - max(1, keep_free_cores))

    # --- Kacheln parallel verarbeiten ---
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            futures = [
                ex.submit(
                    _worker_conv_tile,
                    shm_in.name, in_shape,
                    shm_out.name, out_shape,
                    tile_ij, kernel_pos, (sy, sx), channels
                )
                for tile_ij in tiles
            ]
            # Exceptions früh heben:
            for f in as_completed(futures):
                f.result()
        # Ergebnis in normalen RAM kopieren
        result = buf_out.copy()
    finally:
        # Shared Memory freigeben
        shm_in.close()
        shm_in.unlink()
        shm_out.close()
        shm_out.unlink()

    return result
