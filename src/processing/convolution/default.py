import os
import numpy as np
import numpy.typing as npt
from typing import Sequence, Tuple, List
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import shared_memory


# ---------- Worker: verarbeitet eine einzelne Ausgabekachel ----------
def _worker_conv_tile(
    shm_in_name: str,
    in_shape: Tuple[int, ...],
    shm_out_name: str,
    out_shape: Tuple[int, ...],
    tile_ij: Tuple[int, int, int, int],
    kernel_pos: List[Tuple[int, int, float]],
    stride: Tuple[int, int],
    channels: int
) -> None:
    sy, sx = stride
    i0, i1, j0, j1 = tile_ij
    th, tw = i1 - i0, j1 - j0

    shm_in = shared_memory.SharedMemory(name=shm_in_name)
    shm_out = shared_memory.SharedMemory(name=shm_out_name)
    try:
        if channels == 1:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)   # (Hp, Wp)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)  # (Ho, Wo)
            _conv_block_gray(padded, out, i0, i1, j0, j1, sy, sx, kernel_pos, th, tw)
        else:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)   # (Hp, Wp, C)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)  # (Ho, Wo, C)
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
    """Kernroutine für eine Ausgabekachel (Graubild, 2D), rein in float32, ohne Clipping."""
    acc = np.zeros((th, tw), dtype=np.float32)
    tmp = np.empty((th, tw), dtype=np.float32)

    for dy, dx, w in kernel_pos:
        if w == 0.0:
            continue
        rs = slice(dy + i0 * sy, dy + i1 * sy, sy)
        cs = slice(dx + j0 * sx, dx + j1 * sx, sx)
        np.multiply(padded[rs, cs], w, out=tmp, casting="unsafe")
        np.add(acc, tmp, out=acc)

    out[i0:i1, j0:j1] = acc  # kein Clip, kein Cast


def _to_gray_f32(arr: np.ndarray) -> np.ndarray:
    """Konvertiert (Ho,Wo) oder (Ho,Wo,C) -> (Ho,Wo) als float32-Gray."""
    if arr.ndim == 2:
        return arr.astype(np.float32, copy=False)
    C = arr.shape[2]
    if C >= 3:
        return (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]).astype(np.float32, copy=False)
    elif C == 2:
        return arr.mean(axis=2, dtype=np.float32)
    else:
        return arr[..., 0].astype(np.float32, copy=False)


# ---------- Öffentliche API ----------
def default(
    image: npt.NDArray,  # uint8 oder float32
    kernel: Sequence[Sequence[float]],
    *,
    stride: Tuple[int, int] = (1, 1),
    pad_mode: str = "reflect",
    tile: int = 256,
    keep_free_cores: int = 1,
    max_workers: int | None = None,
    edge_filter: bool = False  # True -> 1-kanaliges Gray-Output (Ho,Wo)
) -> npt.NDArray[np.float32]:
    sy, sx = stride
    if sy < 1 or sx < 1:
        raise ValueError("stride muss positive Ganzzahlen enthalten (>=1).")

    # Kernel prüfen
    k = np.asarray(kernel, dtype=np.float32)
    if k.ndim != 2:
        raise ValueError("kernel muss 2D sein (kH, kW).")
    kH, kW = k.shape
    if kH % 2 == 0 or kW % 2 == 0:
        raise ValueError("kernel-Dimensionen müssen ungerade sein.")
    kh, kw = kH // 2, kW // 2

    # Kernelpositionen & Gewichte
    kernel_pos: List[Tuple[int, int, float]] = []
    for dy in range(kH):
        for dx in range(kW):
            w = float(k[dy, dx])
            if w != 0.0:
                kernel_pos.append((dy, dx, w))

    # Eingabe -> float32
    if image.dtype not in (np.uint8, np.float32):
        raise TypeError("image dtype muss uint8 oder float32 sein.")
    img = image.astype(np.float32, copy=False)

    # --- Padding (Parent) ---
    if img.ndim == 2:
        padded = np.pad(img, ((kh, kh), (kw, kw)), mode="constant", constant_values=0.0) if pad_mode == "constant" else np.pad(img, ((kh, kh), (kw, kw)), mode=pad_mode)  # type: ignore
        channels = 1
        Hp, Wp = padded.shape
        H, W = img.shape
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        out_shape = (out_h, out_w)
        in_shape = (Hp, Wp)
    elif img.ndim == 3:
        padded = np.pad(img, ((kh, kh), (kw, kw), (0, 0)), mode="constant", constant_values=0.0) if pad_mode == "constant" else np.pad(img, ((kh, kh), (kw, kw), (0, 0)), mode=pad_mode)  # type: ignore
        channels = img.shape[2]
        Hp, Wp, _ = padded.shape
        H, W, _ = img.shape
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        out_shape = (out_h, out_w, channels)
        in_shape = (Hp, Wp, channels)
    else:
        raise ValueError("image muss 2D (H, W) oder 3D (H, W, C) sein.")

    padded = np.asarray(padded, dtype=np.float32, copy=False)

    # --- Shared Memory (float32) ---
    shm_in = shared_memory.SharedMemory(create=True, size=padded.nbytes)
    buf_in = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)
    np.copyto(buf_in, padded, casting="no")

    n_elems_out = int(np.prod(out_shape, dtype=np.int64))
    shm_out = shared_memory.SharedMemory(
        create=True, size=n_elems_out * np.dtype(np.float32).itemsize
    )
    buf_out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)

    # --- Ausgabekacheln ---
    tiles: List[Tuple[int, int, int, int]] = []
    for i0 in range(0, out_h, tile):
        i1 = min(i0 + tile, out_h)
        for j0 in range(0, out_w, tile):
            j1 = min(j0 + tile, out_w)
            tiles.append((i0, i1, j0, j1))

    # --- Workeranzahl ---
    if max_workers is None:
        cpu = os.cpu_count() or 2
        max_workers = max(1, cpu - max(1, keep_free_cores))

    # --- Parallel rechnen ---
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
            for f in as_completed(futures):
                f.result()
        result_base = buf_out.copy().astype(np.float32, copy=False)
    finally:
        shm_in.close()
        shm_in.unlink()
        shm_out.close()
        shm_out.unlink()

    # --- Endformat ---
    if edge_filter:
        # 1-kanaliges Gray, 2D (Ho, Wo)
        return _to_gray_f32(result_base)

    # sonst 3-kanalig
    if result_base.ndim == 2:
        final = np.stack([result_base, result_base, result_base], axis=-1)
    else:
        C = result_base.shape[2]
        if C == 3:
            final = result_base
        elif C > 3:
            final = result_base[..., :3]
        elif C == 2:
            final = np.concatenate([result_base, result_base[..., :1]], axis=-1)
        else:  # C == 1
            final = np.repeat(result_base, 3, axis=2)

    return final.astype(np.float32, copy=False)
