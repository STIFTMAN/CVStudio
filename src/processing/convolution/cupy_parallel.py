import cupy as cp
from math import ceil
from multiprocessing import Pool, cpu_count


def cupy_parallel_slice(image_slice, kernel, y_start, out_height) -> tuple:
    if not isinstance(kernel, cp.ndarray):
        kernel = cp.array(kernel, dtype=cp.float32)

    image_slice = cp.array(image_slice, dtype=cp.int32)
    kh, kw = kernel.shape
    h, w = image_slice.shape

    windows = cp.lib.stride_tricks.sliding_window_view(image_slice, (kh, kw))

    kernel_mask = kernel != 0

    weighted_sum = cp.tensordot(windows, kernel, axes=((2, 3), (0, 1)))

    valid_mask = cp.ones_like(image_slice, dtype=bool)
    valid_windows = cp.lib.stride_tricks.sliding_window_view(valid_mask, (kh, kw))

    valid_kernel_mask = valid_windows & kernel_mask

    weight_sum_per_pixel = cp.sum(valid_kernel_mask * kernel, axis=(2, 3))

    convolved = cp.zeros_like(weighted_sum)
    mask_nonzero = weight_sum_per_pixel != 0
    convolved[mask_nonzero] = weighted_sum[mask_nonzero] / weight_sum_per_pixel[mask_nonzero]
    convolved[~mask_nonzero] = weighted_sum[~mask_nonzero]

    convolved = convolved[:out_height]

    return (y_start, y_start + convolved.shape[0], convolved.astype(cp.int32))


def cupy_parallel(image, kernel):
    image = cp.array(image, dtype=cp.int32)
    kernel = cp.array(kernel, dtype=cp.float32)
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2

    padded = cp.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect')

    height, width = image.shape
    safe_start = pad_h
    safe_end = height - pad_h
    step = ceil((safe_end - safe_start) / cpu_count())

    slices = []
    for y in range(safe_start, safe_end, step):
        y_start = y
        y_end = min(y + step, safe_end)
        y0 = y_start - pad_h
        y1 = y_end + pad_h
        actual_slice = padded[y0:y1]
        out_height = y_end - y_start
        slices.append((actual_slice, kernel, y_start, out_height))

    with Pool() as pool:
        results = pool.starmap(cupy_parallel_slice, slices)

    output = cp.zeros((height, width), dtype=cp.int32)
    for y_start, y_end, sub in results:
        output[y_start:y_end, :] = sub
    cp.cuda.Stream.null.synchronize()
    return output.get()