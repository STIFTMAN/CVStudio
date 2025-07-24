from multiprocessing import Pool, cpu_count
from math import ceil

def native_parallel_slice(image, kernel, y_start, y_end):
    height = len(image)
    width = len(image[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    kh = len(kernel) // 2
    kw = len(kernel[0]) // 2

    for y in range(y_start, y_end):
        for x in range(kw, width - kw):
            total = 0
            weight_sum = 0
            for dy in range(-kh, kh + 1):
                for dx in range(-kw, kw + 1):
                    ky = dy + kh
                    kx = dx + kw
                    kernel_val = kernel[ky][kx]
                    if kernel_val:
                        pixel_val = image[y + dy][x + dx]
                        total += pixel_val * kernel_val
                        weight_sum += kernel_val
            output[y][x] = int(total / weight_sum) if weight_sum else int(total)
    return (y_start, y_end, output[y_start:y_end])

def native_parallel(image, kernel):
    height = len(image)
    kh = len(kernel) // 2
    safe_start = kh
    safe_end = height - kh

    num_procs = cpu_count()
    step = ceil((safe_end - safe_start) / num_procs)

    slices = [
        (image, kernel, i, min(i + step, safe_end))
        for i in range(safe_start, safe_end, step)
    ]

    with Pool() as pool:
        results = pool.starmap(native_parallel_slice, slices)

    output = [[0 for _ in range(len(image[0]))] for _ in range(height)]
    for y_start, y_end, rows in results:
        output[y_start:y_end] = rows
    return output