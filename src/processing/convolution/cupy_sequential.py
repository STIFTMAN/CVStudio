import cupy as cp


def cupy_sequential(image, kernel):
    image = cp.asarray(image, dtype=cp.int32)
    kernel = cp.asarray(kernel, dtype=cp.float32)
    k_height, k_width = kernel.shape
    kh, kw = k_height // 2, k_width // 2
    output = cp.zeros_like(image, dtype=cp.int32)
    mask = (kernel != 0) & (~cp.isnan(kernel))
    valid_kernel = cp.where(mask, kernel, 0)
    padded = cp.pad(image, ((kh, kh), (kw, kw)), mode='constant', constant_values=0)
    try:
        windows = cp.lib.stride_tricks.sliding_window_view(padded, (k_height, k_width))
    except AttributeError:
        raise RuntimeError("Deine cupy-Version unterstützt sliding_window_view noch nicht. Bitte updaten oder eine alternative Methode verwenden.")
    total = (windows * valid_kernel).sum(axis=(-2, -1))
    weight_sum = valid_kernel[mask].sum()
    if weight_sum != 0:
        output[:, :] = (total / weight_sum).astype(cp.int32)
    else:
        output[:, :] = total.astype(cp.int32)
    output[:kh, :] = 0
    output[-kh:, :] = 0
    output[:, :kw] = 0
    output[:, -kw:] = 0
    cp.cuda.Stream.null.synchronize()
    return cp.asnumpy(output)