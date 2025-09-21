import numpy as np


def clip(img: np.ndarray) -> np.ndarray:
    """Clipt Bilddaten auf [0,255] und gibt uint8 zurück.
       - float: NaN->0, -inf->0, +inf->255; clip; *runden*; cast
       - int/bool: sicher in int64 clippen, dann cast
       - uint8: unverändert (ggf. Kopie)
       Zusätzlich:
       - Wenn Eingabe 3-kanalig float war und Kanäle nahezu identisch (grau),
         werden die Kanäle nach dem Clip bit-identisch gemacht (keine Farbsprenkel).
    """
    if np.iscomplexobj(img):
        raise TypeError("Complex-Daten werden nicht unterstützt.")

    a = np.asarray(img)
    was_float = np.issubdtype(a.dtype, np.floating)
    was_three_channel = (a.ndim == 3 and a.shape[2] >= 3)

    # Vorab prüfen, ob Eingabe „eigentlich grau“ war (für Kanalsynchronisierung)
    looked_gray = False
    if was_three_channel and was_float:
        ch0, ch1, ch2 = a[..., 0], a[..., 1], a[..., 2]
        # Sehr kleine Toleranz für numerisches Rauschen
        looked_gray = (np.allclose(ch0, ch1, atol=1e-6, equal_nan=True) and np.allclose(ch1, ch2, atol=1e-6, equal_nan=True))

    if a.dtype == np.uint8:
        out = a if a.flags['C_CONTIGUOUS'] else a.copy()

    elif was_float:
        outf = np.nan_to_num(a, copy=True, nan=0.0, neginf=0.0, posinf=255.0)
        np.clip(outf, 0.0, 255.0, out=outf)
        # WICHTIG: runden, nicht nur truncaten
        np.rint(outf, out=outf)
        out = outf.astype(np.uint8, copy=False)

    elif np.issubdtype(a.dtype, np.integer) or a.dtype == np.bool_:
        outi = a.astype(np.int64, copy=True)     # Überlauf vermeiden
        np.clip(outi, 0, 255, out=outi)
        out = outi.astype(np.uint8, copy=False)

    else:
        raise TypeError(f"Nicht unterstützter dtype: {a.dtype}")

    # Monochrom-Sicherung: wenn Eingabe 3-kanalig-float „grau“ war,
    # sorge dafür, dass nach dem Clip alle 3 Kanäle bit-identisch sind.
    if looked_gray and out.ndim == 3 and out.shape[2] >= 3:
        out[..., 1] = out[..., 0]
        out[..., 2] = out[..., 0]

    return out
