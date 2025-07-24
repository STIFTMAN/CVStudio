import cv2
import time
import json
import cupy
import sys
import pandas as pd
import itertools
from convolution.cupy_parallel import cupy_parallel
from convolution.cupy_sequential import cupy_sequential
from convolution.numpy_parallel import numpy_parallel
from convolution.numpy_sequential import numpy_sequential
from convolution.native_parallel import native_parallel
from convolution.native_sequential import native_sequential

if __name__ == "__main__":
    with open("./filters/default.json", 'r', encoding='utf-8') as file:
        filter_kernel: dict[str, list[list]] = json.load(file)

    # Initialisiere CUDA
    print("init CUDA")
    cupy.zeros((1,))
    if cupy.cuda.Device(0) is None:
        print("CUDA Device not found")
        sys.exit()
    print("CUDA inited")

    # Konfiguration
    #resolutions = ["1000", "2000", "3000", "4000", "5000", "big"]
    resolutions = ["big"]
    methods = [
    #   ("native", native_sequential),
    #   ("native parallel", native_parallel),
        ("numpy", numpy_sequential),
        ("numpy parallel", numpy_parallel),
        ("cuda", cupy_sequential),
    #   ("cuda parallel", cupy_parallel),
    ]
    filters = ["mean_3x3", "mean_5x5"]
    kombinationen = list(itertools.product(resolutions, filters))

    # Ergebnisliste
    results = []

    # Hauptschleife
    for res, fsize in kombinationen:
        file_path = f"../assets/test_images/{res}.jpg"
        print(f"\nBild: {res} | Filter: {fsize}")

        try:
            image = cv2.imread(file_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image_data = image.astype(int).tolist()
        except:
            print(f"Fehler beim Laden von {file_path}")
            continue

        f = filter_kernel[fsize]

        for name, func in methods:
            print(f"  Methode: {name}")
            start = time.time()
            try:
                func(image_data, f)
                elapsed = time.time() - start
            except Exception as e:
                print(f"    Fehler bei {name}: {e}")
                elapsed = None
            results.append({
                "Auflösung": res,
                "Methode": name,
                "Filter": fsize,
                "Zeit [s]": elapsed
            })

    # Speichern als DataFrame
    df = pd.DataFrame(results)
    pivot = df.pivot_table(
        index=["Auflösung", "Filter"],
        columns="Methode",
        values="Zeit [s]"
    )

    # Optional: sortieren
    pivot = pivot.sort_index()
    print(pivot)
