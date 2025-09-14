import os
import numpy as np
import numpy.typing as npt
from typing import Sequence, Tuple, List, Literal
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import shared_memory

RankMode = Literal["median", "minimum", "maximum", "25%_quantile", "75%_quantile"]

# ---------- Worker ----------

def _worker_rank_tile(
    shm_in_name: str,
    in_shape: Tuple[int, ...],          # gepaddete Eingabe
    shm_out_name: str,
    out_shape: Tuple[int, ...],         # Zielbild (Downsample/Stride)
    tile_ij: Tuple[int, int, int, int], # (i0, i1, j0, j1) in Output-Koordinaten
    valid_pos: List[Tuple[int, int, int]],  # (dy, dx, w_uint16) für Kernel >=0
    stride: Tuple[int, int],
    mode: RankMode,
    channels: int
) -> None:
    """
    Verarbeitet eine Ausgabekachel in einem separaten Prozess.
    Liest aus shm_in (uint8, gepaddet), schreibt in shm_out (uint8).
    """
    sy, sx = stride
    i0, i1, j0, j1 = tile_ij
    th, tw = i1 - i0, j1 - j0

    shm_in  = shared_memory.SharedMemory(name=shm_in_name)
    shm_out = shared_memory.SharedMemory(name=shm_out_name)
    try:
        if channels == 1:
            padded = np.ndarray(in_shape, dtype=np.uint8, buffer=shm_in.buf)          # (Hp, Wp)
            out    = np.ndarray(out_shape, dtype=np.uint8, buffer=shm_out.buf)        # (Ho, Wo)
            _rank_block_gray(padded, out, i0, i1, j0, j1, sy, sx, valid_pos, mode, th, tw)
        else:
            padded = np.ndarray(in_shape, dtype=np.uint8, buffer=shm_in.buf)          # (Hp, Wp, C)
            out    = np.ndarray(out_shape, dtype=np.uint8, buffer=shm_out.buf)        # (Ho, Wo, C)
            for c in range(channels):
                _rank_block_gray(padded[..., c], out[..., c], i0, i1, j0, j1, sy, sx, valid_pos, mode, th, tw)
    finally:
        shm_in.close()
        shm_out.close()


def _rank_block_gray(
    padded: np.ndarray, out: np.ndarray,
    i0: int, i1: int, j0: int, j1: int,
    sy: int, sx: int,
    valid_pos: List[Tuple[int, int, int]],
    mode: RankMode,
    th: int, tw: int
) -> None:
    """
    Kernroutine für eine einzelne (graue) Kachel.
    - padded: uint8, gepaddetes Eingabebild (2D)
    - out:    uint8, Ausgabebild (2D, Downsample/Stride)
    """
    n_valid = len(valid_pos)
    if n_valid == 0:
        out[i0:i1, j0:j1] = 0
        return

    # MIN/MAX: Streaming ohne Stack
    if mode in {"minimum", "maximum"}:
        if mode == "minimum":
            agg = np.full((th, tw), 65535, dtype=np.uint16)  # hoch initialisieren
            reducer = np.minimum
        else:
            agg = np.zeros((th, tw), dtype=np.uint16)
            reducer = np.maximum

        tmp = np.empty((th, tw), dtype=np.uint16)
        # Für jede Kernel-Position eine verschobene Ansicht nehmen
        for dy, dx, w in valid_pos:
            rs = slice(dy + i0*sy, dy + i1*sy, sy)
            cs = slice(dx + j0*sx, dx + j1*sx, sx)
            np.multiply(padded[rs, cs], w, out=tmp, casting="unsafe")  # uint8 * uint16 -> uint16
            reducer(agg, tmp, out=agg)

        # Clip & schreibe in Output
        np.minimum(agg, 255, out=agg)
        out[i0:i1, j0:j1] = agg.astype(np.uint8, copy=False)
        return

    # MEDIAN / QUANTILE: kompakter uint16-Stack in Kachelgröße
    stack = np.empty((n_valid, th, tw), dtype=np.uint16)
    for idx, (dy, dx, w) in enumerate(valid_pos):
        rs = slice(dy + i0*sy, dy + i1*sy, sy)
        cs = slice(dx + j0*sx, dx + j1*sx, sx)
        np.multiply(padded[rs, cs], w, out=stack[idx], casting="unsafe")

    if mode == "median":
        if n_valid % 2 == 1:
            kidx = n_valid // 2
            part = np.partition(stack, kidx, axis=0)
            sel = part[kidx]  # uint16
        else:
            k1 = n_valid//2 - 1
            k2 = n_valid//2
            p1 = np.partition(stack, k1, axis=0)
            p2 = np.partition(stack, k2, axis=0)
            sel = ((p1[k1].astype(np.uint32) + p2[k2].astype(np.uint32)) // 2).astype(np.uint16)
    else:
        q = 0.25 if mode == "25%_quantile" else 0.75
        qidx = int(np.floor(q * (n_valid - 1)))
        part = np.partition(stack, qidx, axis=0)
        sel = part[qidx]

    np.minimum(sel, 255, out=sel)
    out[i0:i1, j0:j1] = sel.astype(np.uint8, copy=False)


# ---------- Öffentliche API ----------

def numpy_sequential_ranking(
    image: npt.NDArray[np.uint8],
    kernel: Sequence[Sequence[int]],
    *,
    mode: RankMode = "median",
    stride: Tuple[int, int] = (1, 1),
    pad_mode: str = "reflect",
    tile: int = 256,
    keep_free_cores: int = 1,
    max_workers: int | None = None
) -> npt.NDArray[np.uint8]:
    if image.dtype != np.uint8:
        raise ValueError("image muss dtype=uint8 haben.")
    sy, sx = stride
    if sy < 1 or sx < 1:
        raise ValueError("stride muss >= 1 sein.")

    k = np.asarray(kernel)
    if k.ndim != 2:
        raise ValueError("kernel muss 2D sein.")
    kH, kW = k.shape
    if kH % 2 == 0 or kW % 2 == 0:
        raise ValueError("kernel-Dimensionen müssen ungerade sein (z.B. 3x3, 5x5).")
    kh, kw = kH // 2, kW // 2

    # gültige Kernelpositionen sammeln
    valid_pos: List[Tuple[int, int, int]] = []
    for dy in range(kH):
        for dx in range(kW):
            w = int(k[dy, dx])
            if w >= 0:
                if w > 255:
                    raise ValueError("Kernel-Gewichte müssen in 0..255 oder -1 liegen.")
                valid_pos.append((dy, dx, w))
    n_valid = len(valid_pos)
    if n_valid == 0:
        H, W = image.shape[:2]
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        return np.zeros((out_h, out_w) if image.ndim == 2 else (out_h, out_w, image.shape[2]), dtype=np.uint8)

    # Pad einmal im Parent (vermeidet Arbeit pro Worker)
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
        raise ValueError("image muss 2D (H,W) oder 3D (H,W,C) sein.")

    # Shared Memory anlegen
    shm_in  = shared_memory.SharedMemory(create=True, size=padded.nbytes)
    buf_in  = np.ndarray(in_shape, dtype=np.uint8, buffer=shm_in.buf)
    np.copyto(buf_in, padded, casting="no")

    shm_out = shared_memory.SharedMemory(create=True, size=np.prod(out_shape, dtype=np.int64).item() * np.dtype(np.uint8).itemsize)
    buf_out = np.ndarray(out_shape, dtype=np.uint8, buffer=shm_out.buf)
    # muss nicht initialisiert werden; jede Kachel schreibt ihren Bereich

    # Aufgaben (Kacheln) erzeugen
    tiles: List[Tuple[int, int, int, int]] = []
    for i0 in range(0, out_h, tile):
        i1 = min(i0 + tile, out_h)
        for j0 in range(0, out_w, tile):
            j1 = min(j0 + tile, out_w)
            tiles.append((i0, i1, j0, j1))

    # Worker-Anzahl: mind. 1, lässt 'keep_free_cores' Kerne frei
    if max_workers is None:
        cpu = os.cpu_count() or 2
        max_workers = max(1, cpu - max(0, keep_free_cores))

    # Pool starten und Tiles abarbeiten
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = [
            ex.submit(
                _worker_rank_tile,
                shm_in.name, in_shape,
                shm_out.name, out_shape,
                tile_ij, valid_pos, (sy, sx), mode, channels
            )
            for tile_ij in tiles
        ]
        # Option: hier könnte man Fortschritt auswerten:
        for f in as_completed(futures):
            # Exceptions frühzeitig heben
            f.result()

    # Ergebnis in normalen RAM kopieren und SHM freigeben
    result = buf_out.copy()

    shm_in.close();  shm_in.unlink()
    shm_out.close(); shm_out.unlink()

    return result
