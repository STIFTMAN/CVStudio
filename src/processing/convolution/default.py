import os
from typing import Tuple, List
import numpy as np
import numpy.typing as npt
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import shared_memory
import cv2
from src.gui.state.error import Error
from src.gui.state import root
import src.gui.utils.logger as log
from pathlib import Path


TILE_SIZE: int = 1024
KEEP_FREE_CORES: int = 1
SUPPRESS_PADDING_BORDER: bool = False


def _worker_convolve_tile(
    shm_in_name: str,
    in_shape: Tuple[int, ...],
    shm_out_name: str,
    out_shape: Tuple[int, ...],
    tile_ij: Tuple[int, int, int, int],
    kernel_positions: List[Tuple[int, int, float]],
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
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)
            _convolve_block_gray(padded, out, i0, i1, j0, j1, sy, sx, kernel_positions, tile_h, tile_w)
        else:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)
            for c in range(channels):
                _convolve_block_gray(padded[..., c], out[..., c], i0, i1, j0, j1, sy, sx, kernel_positions, tile_h, tile_w)
    finally:
        shm_in.close()
        shm_out.close()


def _convolve_block_gray(
    padded: np.ndarray,
    out: np.ndarray,
    i0: int,
    i1: int,
    j0: int,
    j1: int,
    sy: int,
    sx: int,
    kernel_positions: List[Tuple[int, int, float]],
    tile_h: int,
    tile_w: int
) -> None:
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


def _worker_convolve_tile_separable(
    shm_in_name: str,
    in_shape: Tuple[int, ...],
    shm_out_name: str,
    out_shape: Tuple[int, ...],
    tile_ij: Tuple[int, int, int, int],
    ky: np.ndarray,
    kx: np.ndarray,
    stride: Tuple[int, int],
    channels: int
) -> None:
    sy, sx = stride
    i0, i1, j0, j1 = tile_ij

    shm_in = shared_memory.SharedMemory(name=shm_in_name)
    shm_out = shared_memory.SharedMemory(name=shm_out_name)
    try:
        if channels == 1:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)
            _convolve_block_gray_separable(padded, out, i0, i1, j0, j1, sy, sx, ky, kx)
        else:
            padded = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)
            out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)
            for c in range(channels):
                _convolve_block_gray_separable(padded[..., c], out[..., c], i0, i1, j0, j1, sy, sx, ky, kx)
    finally:
        shm_in.close()
        shm_out.close()


def _convolve_block_gray_separable(
    padded: np.ndarray, out: np.ndarray,
    i0: int, i1: int, j0: int, j1: int,
    sy: int, sx: int,
    ky: np.ndarray,
    kx: np.ndarray
) -> None:
    kH = int(ky.shape[0])
    kW = int(kx.shape[0])
    tile_h = i1 - i0
    tile_w = j1 - j0

    r_start = i0 * sy
    r_end = (i1 - 1) * sy + (kH - 1)
    R = r_end - r_start + 1

    c0_vec = (np.arange(j0, j1, dtype=np.int64) * sx)
    H = np.zeros((R, tile_w), dtype=np.float32)

    rows = np.arange(r_start, r_end + 1, dtype=np.int64)
    for dx in range(kW):
        cols = c0_vec + dx
        np.add(H, padded[rows[:, None], cols[None, :]] * kx[dx], out=H)
    acc = np.zeros((tile_h, tile_w), dtype=np.float32)
    for dy in range(kH):
        rs = slice(dy, dy + tile_h * sy, sy)
        np.add(acc, H[rs, :] * ky[dy], out=acc)

    out[i0:i1, j0:j1] = acc


def _is_multichannel_gray(image_f32: np.ndarray) -> bool:
    if image_f32.ndim != 3 or image_f32.shape[2] < 2:
        return False
    diff_var = np.var(image_f32[..., 0] - image_f32[..., 1])
    return diff_var < 1e-8  # type: ignore


def _to_gray_f32(image_f32: np.ndarray) -> np.ndarray:
    if image_f32.ndim == 2:
        return image_f32.astype(np.float32, copy=False)
    h, w, c = image_f32.shape
    if c == 1 or _is_multichannel_gray(image_f32):
        return image_f32[..., 0].astype(np.float32, copy=False)
    return cv2.cvtColor(image_f32, cv2.COLOR_BGR2GRAY).astype(np.float32, copy=False)


def _try_factor_separable(
    k2d: np.ndarray,
    tol_rel: float = 1e-6
) -> tuple[bool, np.ndarray, np.ndarray]:
    k = np.asarray(k2d, dtype=np.float32, copy=False)
    kH, kW = k.shape

    ref = None
    for i in range(kH):
        row = k[i, :]
        if np.linalg.norm(row) > 0:
            ref = row
            break
    if ref is None:
        return True, np.zeros((kH,), np.float32), np.zeros((kW,), np.float32)

    denom = float(np.dot(ref, ref))
    if denom == 0.0:
        return False, np.empty(0, np.float32), np.empty(0, np.float32)

    alpha = (k @ ref) / denom
    k_hat = alpha[:, None] * ref[None, :]
    err = np.linalg.norm(k - k_hat, ord="fro")
    base = np.linalg.norm(k, ord="fro") + 1e-12
    rel_err = err / base
    if rel_err <= tol_rel:
        return True, alpha.astype(np.float32, copy=False), ref.astype(np.float32, copy=False)

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


def default(
    image: npt.NDArray,
    kernel: list[list[float]],
    stride: Tuple[int, int] = (1, 1),
    edge_filter: bool = False,
    use_conv_scale: bool = True
) -> npt.NDArray:
    assert root.status_details is not None

    root.status_details.set(root.current_lang.get("status_details_checking_sample_rate").get())
    sy, sx = stride
    if sy < 1 or sx < 1:
        log.log.write(text=Error.CONVOLUTION_NEGATIVE_STRIDE.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)

    root.status_details.set(root.current_lang.get("status_details_checking_kernal_dimensions").get())
    k = np.asarray(kernel, dtype=np.float32)
    if k.ndim != 2:
        log.log.write(text=Error.CONVOLUTION_KERNAL_DIMENSION.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)
    kH, kW = k.shape
    if (kH % 2 == 0) or (kW % 2 == 0):
        log.log.write(text=Error.CONVOLUTION_KERNAL_DIMENSION_EVEN.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)
    kh, kw = kH // 2, kW // 2

    root.status_details.set(root.current_lang.get("status_details_checking_image_datatype").get())
    if not (np.issubdtype(image.dtype, np.integer) or np.issubdtype(image.dtype, np.floating)):
        log.log.write(text=Error.CONVOLUTION_IMAGE_DATA_TYPE.value, tag="CRITICAL ERROR", modulename=Path(__file__).stem)
    image_f32 = image.astype(np.float32, copy=False)

    root.status_details.set(root.current_lang.get("status_details_checking_gray_monochrom").get())
    force_gray = (edge_filter or (image_f32.ndim == 2) or _is_multichannel_gray(image_f32) or (image_f32.ndim == 3 and image_f32.shape[2] in (1, 2)))
    if force_gray:
        proc = _to_gray_f32(image_f32)
        channels = 1
    else:
        proc = image_f32 if image_f32.ndim == 3 else np.repeat(image_f32[..., None], 3, axis=2)
        channels = 3

    root.status_details.set(root.current_lang.get("status_details_checking_kernal_separable").get())
    is_sep, ky, kx = _try_factor_separable(k, tol_rel=1e-6)

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

    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    shm_in = shared_memory.SharedMemory(create=True, size=padded.nbytes)
    buf_in = np.ndarray(in_shape, dtype=np.float32, buffer=shm_in.buf)
    root.status_details.set(root.current_lang.get("status_details_load_image_shared_memory").get())
    np.copyto(buf_in, padded, casting="no")

    root.status_details.set(root.current_lang.get("status_details_set_shared_memory").get())
    n_out = int(np.prod(out_shape, dtype=np.int64))
    shm_out = shared_memory.SharedMemory(create=True, size=n_out * np.dtype(np.float32).itemsize)
    buf_out = np.ndarray(out_shape, dtype=np.float32, buffer=shm_out.buf)

    root.status_details.set(root.current_lang.get("status_details_set_tile_splitting").get())
    tiles: List[Tuple[int, int, int, int]] = []
    for i0_ in range(0, out_h, TILE_SIZE):
        i1_ = min(i0_ + TILE_SIZE, out_h)
        for j0_ in range(0, out_w, TILE_SIZE):
            j1_ = min(j0_ + TILE_SIZE, out_w)
            tiles.append((i0_, i1_, j0_, j1_))

    root.status_details.set(root.current_lang.get("status_details_checking_number_worker").get())
    cpu = os.cpu_count() or 2
    max_workers = max(1, cpu - max(1, KEEP_FREE_CORES))

    root.status_details.set(root.current_lang.get("status_details_start_execution").get())
    try:
        if is_sep:
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
                root.status_details.set(root.current_lang.get("status_details_calc_execution").get())
                for f in as_completed(futures):
                    f.result()
                root.status_details.set(root.current_lang.get("status_details_tile_done").get())
        else:
            kernel_positions: List[Tuple[int, int, float]] = [(dy, dx, float(k[dy, dx])) for dy in range(kH) for dx in range(kW) if k[dy, dx] != 0.0]
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
                root.status_details.set(root.current_lang.get("status_details_calc_execution").get())
                for f in as_completed(futures):
                    f.result()
                root.status_details.set(root.current_lang.get("status_details_tile_done").get())

        result_f32 = buf_out.copy().astype(np.float32, copy=False)
    finally:
        root.status_details.set(root.current_lang.get("status_details_unload_shared_memory").get())
        shm_in.close()
        shm_in.unlink()
        shm_out.close()
        shm_out.unlink()

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

    if channels == 1:
        if use_conv_scale:
            result_u8 = cv2.convertScaleAbs(result_f32)
            root.status_details.set(root.current_lang.get("status_details_done").get())
            return result_u8
        else:
            root.status_details.set(root.current_lang.get("status_details_done").get())
            return result_f32
    else:
        if result_f32.ndim == 2:
            result_f32 = np.stack([result_f32, result_f32, result_f32], axis=-1)
        elif result_f32.shape[2] != 3:
            if result_f32.shape[2] > 3:
                result_f32 = result_f32[..., :3]
            else:
                result_f32 = np.repeat(result_f32[..., :1], 3, axis=2)
        root.status_details.set(root.current_lang.get("status_details_done").get())
        return result_f32.astype(np.float32, copy=False)
