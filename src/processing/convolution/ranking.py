import os
import numpy as np
import numpy.typing as npt
from typing import Sequence, Tuple, List, Literal, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import shared_memory
import src.gui.state.root as root
import src.gui.utils.logger as log
from src.gui.state.error import Error
from pathlib import Path


RankMode = Literal["median", "minimum", "maximum", "25%_quantile", "75%_quantile"]


def _process_rank_output_tile(
    shm_input_name: str,
    padded_input_shape: Tuple[int, ...],
    input_dtype_name: str,
    shm_output_name: str,
    output_shape: Tuple[int, ...],
    tile_coords_rc: Tuple[int, int, int, int],
    valid_kernel_offsets: List[Tuple[int, int, float]],
    stride_hw: Tuple[int, int],
    mode: RankMode,
    num_channels: int,
    mono_channels_equal: bool
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
            padded = np.ndarray(padded_input_shape, dtype=in_dtype, buffer=shm_in.buf)
            out = np.ndarray(output_shape, dtype=np.float32, buffer=shm_out.buf)
            _rank_tile_grayscale(padded, out, r0, r1, c0, c1, sy, sx, valid_kernel_offsets, mode, th, tw)

        else:
            padded = np.ndarray(padded_input_shape, dtype=in_dtype, buffer=shm_in.buf)
            out = np.ndarray(output_shape, dtype=np.float32, buffer=shm_out.buf)

            if mono_channels_equal and num_channels >= 3:
                _rank_tile_grayscale(padded[..., 0], out[..., 0], r0, r1, c0, c1, sy, sx, valid_kernel_offsets, mode, th, tw)

                up_to = min(3, num_channels)
                out[r0:r1, c0:c1, 1:up_to] = out[r0:r1, c0:c1, [0]]

                for ch in range(up_to, num_channels):
                    _rank_tile_grayscale(padded[..., ch], out[..., ch], r0, r1, c0, c1, sy, sx, valid_kernel_offsets, mode, th, tw)

            else:
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
            tmp[...] = padded_2d[rs, cs]
            reducer(agg, tmp, out=agg)
        out_2d[r0:r1, c0:c1] = agg
        return
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

    out_2d[r0:r1, c0:c1] = sel


def ranking(
    image: np.ndarray,
    kernel: Sequence[Sequence[Optional[float]]],
    *,
    mode: RankMode = "median",
    stride: Tuple[int, int] = (1, 1),
    pad_mode: str = "reflect",
    tile: int = 64,
    keep_free_cores: int = 1,
    max_workers: int | None = None
) -> npt.NDArray[np.float32]:
    assert root.status_details is not None
    root.status_details.set(root.current_lang.get("status_details_checking_sample_rate").get())
    sy, sx = stride
    if sy < 1 or sx < 1:
        log.log.write(text=Error.CONVOLUTION_NEGATIVE_STRIDE.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    root.status_details.set(root.current_lang.get("status_details_checking_kernal_dimensions").get())
    k = np.asarray(kernel, dtype=object)
    if k.ndim != 2:
        log.log.write(text=Error.CONVOLUTION_KERNAL_DIMENSION.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)
    kH, kW = k.shape
    if kH % 2 == 0 or kW % 2 == 0:
        log.log.write(text=Error.CONVOLUTION_KERNAL_DIMENSION_EVEN.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)
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
            except Exception:
                log.log.write(text=Error.CONVOLUTION_KERNAL_DATA_TYPE.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)
            valid_offsets.append((dy, dx, w))

    n_valid = len(valid_offsets)
    if n_valid == 0:
        root.status_details.set(root.current_lang.get("status_details_ranking_no_selection").get())
        H, W = image.shape[:2]
        out_h = (H + sy - 1) // sy
        out_w = (W + sx - 1) // sx
        return np.zeros((out_h, out_w) if image.ndim == 2 else (out_h, out_w, image.shape[2]), dtype=np.float32)

    root.status_details.set(root.current_lang.get("status_details_checking_image_datatype").get())
    if np.issubdtype(image.dtype, np.integer):
        img_in = image.astype(np.uint8, copy=False)
        input_dtype_name = "uint8"
    elif np.issubdtype(image.dtype, np.floating):
        img_in = image.astype(np.float32, copy=False)
        input_dtype_name = "float32"
    else:
        log.log.write(text=Error.CONVOLUTION_IMAGE_DATA_TYPE.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    root.status_details.set(root.current_lang.get("status_details_checking_gray_monochrom").get())
    mono_channels_equal = False
    if img_in.ndim == 3 and img_in.shape[2] >= 3:
        ch0, ch1, ch2 = img_in[..., 0], img_in[..., 1], img_in[..., 2]
        if np.issubdtype(img_in.dtype, np.integer):
            mono_channels_equal = np.array_equal(ch0, ch1) and np.array_equal(ch1, ch2)
        else:
            mono_channels_equal = np.allclose(ch0, ch1, atol=1e-6) and np.allclose(ch1, ch2, atol=1e-6)

    root.status_details.set(root.current_lang.get("status_details_set_padding").get())
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
        log.log.write(text=Error.RESIZE_IMAGE_NDIM.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    shm_in = shared_memory.SharedMemory(create=True, size=padded.nbytes)
    buf_in = np.ndarray(in_shape, dtype=padded.dtype, buffer=shm_in.buf)

    root.status_details.set(root.current_lang.get("status_details_load_image_shared_memory").get())
    np.copyto(buf_in, padded, casting="no")

    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    out_nbytes = int(np.prod(out_shape, dtype=np.int64)) * np.dtype(np.float32).itemsize
    shm_out = shared_memory.SharedMemory(create=True, size=out_nbytes)
    buf_out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)

    root.status_details.set(root.current_lang.get("status_details_set_tile_splitting").get())
    tiles: List[Tuple[int, int, int, int]] = []
    for r0 in range(0, out_h, tile):
        r1 = min(r0 + tile, out_h)
        for c0 in range(0, out_w, tile):
            c1 = min(c0 + tile, out_w)
            tiles.append((r0, r1, c0, c1))

    root.status_details.set(root.current_lang.get("status_details_checking_number_worker").get())
    if max_workers is None:
        cpu = os.cpu_count() or 2
        max_workers = max(1, cpu - max(0, keep_free_cores))

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
            root.status_details.set(root.current_lang.get("status_details_calc_execution").get())
            for f in as_completed(futures):
                f.result()
            root.status_details.set(root.current_lang.get("status_details_tile_done").get())
        result = buf_out.copy()
    finally:
        root.status_details.set(root.current_lang.get("status_details_unload_shared_memory").get())
        shm_in.close()
        shm_in.unlink()
        shm_out.close()
        shm_out.unlink()

    root.status_details.set(root.current_lang.get("status_details_done").get())
    return result
