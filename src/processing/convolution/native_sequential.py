import numpy as np

def native_sequential(image, kernel):
    if isinstance(image, np.ndarray):
        image: list = image.astype(np.int32).tolist()

    height = len(image)
    width = len(image[0])
    k_height = len(kernel)
    k_width = len(kernel[0])
    kh, kw = k_height // 2, k_width // 2
    output = [[0 for _ in range(width)] for _ in range(height)]
    for y in range(kh, height - kh):
        for x in range(kw, width - kw):
            total = 0
            weight_sum = 0
            for dy in range(-kh, kh + 1):
                for dx in range(-kw, kw + 1):
                    ky = dy + kh
                    kx = dx + kw
                    kernel_val = kernel[ky][kx]
                    if kernel_val is not None and kernel_val != 0:
                        pixel_val = image[y + dy][x + dx]
                        total += pixel_val * kernel_val
                        weight_sum += kernel_val
            if weight_sum != 0:
                output[y][x] = int(total / weight_sum)
            else:
                output[y][x] = int(total)

    return output