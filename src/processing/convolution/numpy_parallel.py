import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from multiprocessing import Pool, cpu_count
from math import ceil


def numpy_parallel_slice(image_slice, kernel, y_start, out_height):
    kernel = np.array(kernel, dtype=np.float32)
    kh, kw = kernel.shape
    h, w = image_slice.shape

    windows = sliding_window_view(image_slice, (kh, kw))
    
    kernel_mask = kernel != 0

    weighted_sum = np.tensordot(windows, kernel, axes=((2,3), (0,1)))

    valid_mask = np.ones_like(image_slice, dtype=bool)
    valid_windows = sliding_window_view(valid_mask, (kh, kw))

    valid_kernel_mask = valid_windows & kernel_mask

    weight_sum_per_pixel = np.sum(valid_kernel_mask * kernel, axis=(2,3))

    convolved = np.zeros_like(weighted_sum)
    mask_nonzero = weight_sum_per_pixel != 0
    convolved[mask_nonzero] = weighted_sum[mask_nonzero] / weight_sum_per_pixel[mask_nonzero]
    convolved[~mask_nonzero] = weighted_sum[~mask_nonzero]

    convolved = convolved[:out_height]

    return (y_start, y_start + convolved.shape[0], convolved.astype(np.int32))


def numpy_parallel(image, kernel):
    image = np.array(image, dtype=np.int32)
    kernel = np.array(kernel, dtype=np.float32)
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2
    padded = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect')
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
        results = pool.starmap(numpy_parallel_slice, slices)

    output = np.zeros((height, width), dtype=np.int32)
    for y_start, y_end, sub in results:
        output[y_start:y_end, :] = sub

    return output