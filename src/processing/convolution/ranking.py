import os
import numpy as np
import numpy.typing as npt
from typing import Sequence, Tuple, List, Literal, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import shared_memory
import src.gui.state.root as root

RankMode = Literal["median", "minimum", "maximum", "25%_quantile", "75%_quantile"]


# ---------- Worker ----------
def _process_rank_output_tile(
    shm_input_name: str,
    padded_input_shape: Tuple[int, ...],          # (Hp, Wp) or (Hp, Wp, C)
    input_dtype_name: str,                         # "uint8" or "float32"
    shm_output_name: str,
    output_shape: Tuple[int, ...],                 # (Ho, Wo) or (Ho, Wo, C) - float32
    tile_coords_rc: Tuple[int, int, int, int],     # (row_start, row_end, col_start, col_end)
    valid_kernel_offsets: List[Tuple[int, int, float]],
    stride_hw: Tuple[int, int],
    mode: RankMode,
    num_channels: int,
    mono_channels_equal: bool                      # NEU: Kanäle der Eingabe identisch?
) -> None:

    sy, sx = stride_hw
    r0, r1, c0, c1 = tile_coords_rc
    th, tw = r1 - r0, c1 - c0

    dtype_map = {"uint8": np.uint8, "float32": np.float32}
    in_dtype = dtype_map[input_dtype_name]

    shm_in = shared_memory.SharedMemory(name=shm_input_name)
    shm_out = shared_memory.SharedMemory(name=shm_output_name)
    try:
        if num_channels == 1:
            padded = np.ndarray(padded_input_shape, dtype=in_dtype, buffer=shm_in.buf)   # (Hp, Wp)
            out = np.ndarray(output_shape, dtype=np.float32, buffer=shm_out.buf)  # (Ho, Wo)
            _rank_tile_grayscale(padded, out, r0, r1, c0, c1, sy, sx, valid_kernel_offsets, mode, th, tw)

        else:
            padded = np.ndarray(padded_input_shape, dtype=in_dtype, buffer=shm_in.buf)  # (Hp, Wp, C)
            out = np.ndarray(output_shape, dtype=np.float32, buffer=shm_out.buf)  # (Ho, Wo, C)

            if mono_channels_equal and num_channels >= 3:
                _rank_tile_grayscale(padded[..., 0], out[..., 0], r0, r1, c0, c1, sy, sx, valid_kernel_offsets, mode, th, tw)

                up_to = min(3, num_channels)  # nur RGB
                out[r0:r1, c0:c1, 1:up_to] = out[r0:r1, c0:c1, [0]]

                for ch in range(up_to, num_channels):  # z.B. Alpha separat
                    _rank_tile_grayscale(padded[..., ch], out[..., ch], r0, r1, c0, c1, sy, sx, valid_kernel_offsets, mode, th, tw)

            else:
                # Echte Mehrkanal-Verarbeitung
                for ch in range(num_channels):
                    _rank_tile_grayscale(padded[..., ch], out[..., ch], r0, r1, c0, c1, sy, sx,
                                         valid_kernel_offsets, mode, th, tw)
    finally:
        shm_in.close()
        shm_out.close()


def _rank_tile_grayscale(
    padded_2d: np.ndarray,
    out_2d: np.ndarray,
    r0: int, r1: int, c0: int, c1: int,
    sy: int, sx: int,
    valid_kernel_offsets: List[Tuple[int, int, float]],
    mode: RankMode,
    th: int, tw: int
) -> None:
    """Eine (graue) Output-Kachel; Ausgabe float32 ungeclippt."""
    n_valid = len(valid_kernel_offsets)
    if n_valid == 0:
        out_2d[r0:r1, c0:c1] = 0.0
        return

    if mode in {"minimum", "maximum"}:
        reducer = np.minimum if mode == "minimum" else np.maximum
        agg = np.full((th, tw), np.inf if mode == "minimum" else -np.inf, dtype=np.float32)
        tmp = np.empty((th, tw), dtype=np.float32)
        for dy, dx, _w in valid_kernel_offsets:
            rs = slice(dy + r0 * sy, dy + r1 * sy, sy)
            cs = slice(dx + c0 * sx, dx + c1 * sx, sx)
            # ungewichtet:
            tmp[...] = padded_2d[rs, cs]
            reducer(agg, tmp, out=agg)
        out_2d[r0:r1, c0:c1] = agg
        return

    # Median / Quantile:
    stack = np.empty((n_valid, th, tw), dtype=np.float32)
    for i, (dy, dx, w) in enumerate(valid_kernel_offsets):
        rs = slice(dy + r0 * sy, dy + r1 * sy, sy)
        cs = slice(dx + c0 * sx, dx + c1 * sx, sx)
        np.multiply(padded_2d[rs, cs], np.float32(w), out=stack[i])

    if mode == "median":
        if n_valid % 2:
            k = n_valid // 2
            part = np.partition(stack, k, axis=0)
            sel = part[k]
        else:
            k1 = n_valid // 2 - 1
            k2 = n_valid // 2
            p1 = np.partition(stack, k1, axis=0)[k1]
            p2 = np.partition(stack, k2, axis=0)[k2]
            sel = 0.5 * (p1 + p2)
    else:
        q = 0.25 if mode == "25%_quantile" else 0.75
        qidx = int(np.floor(q * (n_valid - 1)))
        part = np.partition(stack, qidx, axis=0)
        sel = part[qidx]

    out_2d[r0:r1, c0:c1] = sel  # float32, ungeclippt


# ---------- Public API ----------
def ranking(
    image: np.ndarray,                                   # uint8 ODER float (z.B. float32/float64)
    kernel: Sequence[Sequence[Optional[float]]],         # None => ignorieren; Gewichte dürfen <0 sein
    *,
    mode: RankMode = "median",
    stride: Tuple[int, int] = (1, 1),
    pad_mode: str = "reflect",
    tile: int = 64,
    keep_free_cores: int = 1,
    max_workers: int | None = None
) -> npt.NDArray[np.float32]:
    assert root.status_details is not None
    """Ranking-Filter (min/max/median/quantil) mit MP; Ausgabe float32 ungeclippt."""
    root.status_details.set(root.current_lang.get("status_details_checking_sample_rate").get())
    sy, sx = stride
    if sy < 1 or sx < 1:
        raise ValueError("stride must be >= 1.")

    # Kernel prüfen & gültige Offsets sammeln
    root.status_details.set(root.current_lang.get("status_details_checking_kernal_dimensions").get())
    k = np.asarray(kernel, dtype=object)
    if k.ndim != 2:
        raise ValueError("kernel must be 2D.")
    kH, kW = k.shape
    if kH % 2 == 0 or kW % 2 == 0:
        raise ValueError("kernel dimensions must be odd (e.g., 3x3, 5x5).")
    pad_h, pad_w = kH // 2, kW // 2

    root.status_details.set(root.current_lang.get("status_details_checking_kernal_values").get())
    valid_offsets: List[Tuple[int, int, float]] = []
    for dy in range(kH):
        for dx in range(kW):
            val = k[dy, dx]
            if val is None:
                continue
            try:
                w = float(val)
            except Exception as e:
                raise ValueError(f"Kernel weight at ({dy},{dx}) must be float or None.") from e
            valid_offsets.append((dy, dx, w))

    n_valid = len(valid_offsets)
    if n_valid == 0:
        root.status_details.set(root.current_lang.get("status_details_ranking_no_selection").get())
        H, W = image.shape[:2]
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        return np.zeros((out_h, out_w) if image.ndim == 2 else (out_h, out_w, image.shape[2]),
                        dtype=np.float32)

    # Eingabe-Datentyp normalisieren
    root.status_details.set(root.current_lang.get("status_details_checking_image_datatype").get())
    if np.issubdtype(image.dtype, np.integer):
        img_in = image.astype(np.uint8, copy=False)
        input_dtype_name = "uint8"
    elif np.issubdtype(image.dtype, np.floating):
        img_in = image.astype(np.float32, copy=False)
        input_dtype_name = "float32"
    else:
        raise TypeError(f"Unsupported image dtype {image.dtype}; use uint8 or float.")

    # --- Monochrom-Erkennung (3-Kanal identisch?) ---
    root.status_details.set(root.current_lang.get("status_details_checking_gray_monochrom").get())
    mono_channels_equal = False
    if img_in.ndim == 3 and img_in.shape[2] >= 3:
        ch0, ch1, ch2 = img_in[..., 0], img_in[..., 1], img_in[..., 2]
        if np.issubdtype(img_in.dtype, np.integer):
            mono_channels_equal = np.array_equal(ch0, ch1) and np.array_equal(ch1, ch2)
        else:
            mono_channels_equal = np.allclose(ch0, ch1, atol=1e-6) and np.allclose(ch1, ch2, atol=1e-6)

    root.status_details.set(root.current_lang.get("status_details_set_padding").get())
#  Padding
    if img_in.ndim == 2:
        padded = (np.pad(img_in, ((pad_h, pad_h), (pad_w, pad_w)), mode="constant", constant_values=0) if pad_mode == "constant" else np.pad(img_in, ((pad_h, pad_h), (pad_w, pad_w)), mode=pad_mode))  # type: ignore
        num_channels = 1
        Hp, Wp = padded.shape
        H, W = img_in.shape
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        out_shape, in_shape = (out_h, out_w), (Hp, Wp)

    elif img_in.ndim == 3:
        padded = (np.pad(img_in, ((pad_h, pad_h), (pad_w, pad_w), (0, 0)), mode="constant", constant_values=0) if pad_mode == "constant" else np.pad(img_in, ((pad_h, pad_h), (pad_w, pad_w), (0, 0)), mode=pad_mode))  # type: ignore
        num_channels = img_in.shape[2]
        Hp, Wp, _ = padded.shape
        H, W, _ = img_in.shape
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        out_shape, in_shape = (out_h, out_w, num_channels), (Hp, Wp, num_channels)
    else:
        raise ValueError("image must be 2D (H,W) or 3D (H,W,C).")

    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    # Shared memory
    shm_in = shared_memory.SharedMemory(create=True, size=padded.nbytes)
    buf_in = np.ndarray(in_shape, dtype=padded.dtype, buffer=shm_in.buf)

    root.status_details.set(root.current_lang.get("status_details_load_image_shared_memory").get())
    np.copyto(buf_in, padded, casting="no")

    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    out_nbytes = int(np.prod(out_shape, dtype=np.int64)) * np.dtype(np.float32).itemsize
    shm_out = shared_memory.SharedMemory(create=True, size=out_nbytes)
    buf_out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)

    # Tiles
    root.status_details.set(root.current_lang.get("status_details_set_tile_splitting").get())
    tiles: List[Tuple[int, int, int, int]] = []
    for r0 in range(0, out_h, tile):
        r1 = min(r0 + tile, out_h)
        for c0 in range(0, out_w, tile):
            c1 = min(c0 + tile, out_w)
            tiles.append((r0, r1, c0, c1))

    # Worker-Anzahl
    root.status_details.set(root.current_lang.get("status_details_checking_number_worker").get())
    if max_workers is None:
        cpu = os.cpu_count() or 2
        max_workers = max(1, cpu - max(0, keep_free_cores))

    # Ausführen
    root.status_details.set(root.current_lang.get("status_details_start_execution").get())
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            futures = [
                ex.submit(
                    _process_rank_output_tile,
                    shm_in.name, in_shape, input_dtype_name,
                    shm_out.name, out_shape,
                    tile_ij, valid_offsets, (sy, sx), mode, num_channels,
                    mono_channels_equal
                )
                for tile_ij in tiles
            ]
            for i, f in enumerate(as_completed(futures)):
                root.status_details.set(f'[{i+1}/{len(futures)}] {root.current_lang.get("status_details_tile_progress").get()}')
                f.result()
        result = buf_out.copy()
    finally:
        root.status_details.set(root.current_lang.get("status_details_unload_shared_memory").get())
        shm_in.close()
        shm_in.unlink()
        shm_out.close()
        shm_out.unlink()

    root.status_details.set(root.current_lang.get("status_details_done").get())
    return result  # float32, ungeclippt
