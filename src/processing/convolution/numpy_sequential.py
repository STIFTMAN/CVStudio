import numpy as np

def numpy_sequential(image, kernel):
    image = np.asarray(image, dtype=np.int32)
    kernel = np.array(kernel, dtype=np.float32)

    height, width = image.shape
    k_height, k_width = kernel.shape
    kh, kw = k_height // 2, k_width // 2

    output = np.zeros_like(image, dtype=np.int32)

    mask = (kernel != 0) & (~np.isnan(kernel))
    valid_kernel = np.where(mask, kernel, 0)

    padded = np.pad(image, ((kh, kh), (kw, kw)), mode='constant', constant_values=0)
    windows = np.lib.stride_tricks.sliding_window_view(padded, (k_height, k_width))

    total = (windows * valid_kernel).sum(axis=(-2, -1))

    weight_sum = valid_kernel[mask].sum()

    if weight_sum != 0:
        output[:, :] = (total / weight_sum).astype(np.int32)
    else:
        output[:, :] = total.astype(np.int32)

    output[:kh, :] = 0
    output[-kh:, :] = 0
    output[:, :kw] = 0
    output[:, -kw:] = 0

    return output