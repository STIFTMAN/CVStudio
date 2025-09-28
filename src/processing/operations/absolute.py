import numpy as np


def absolute(img: np.ndarray) -> np.ndarray:
    """Betrag je Pixel, Shape unverändert.
       Dtype-Strategie:
         - signed int  -> gleicher dtype, saturiert (Überlauf-sicher)
         - unsigned int-> unverändert (bereits >= 0)
         - float       -> gleicher dtype
         - complex     -> reeller Betrag (float32/float64 je nach Eingabe)
    """
    a = np.asarray(img)

    if np.issubdtype(a.dtype, np.signedinteger):
        info = np.iinfo(a.dtype)
        x = a.astype(np.int64, copy=False)   # Überlauf vermeiden
        y = np.abs(x)
        # Sonderfall: |min| > max (z.B. |-32768| = 32768) -> saturieren
        y = np.minimum(y, info.max)
        return y.astype(a.dtype, copy=False)

    if np.issubdtype(a.dtype, np.unsignedinteger):
        # Schon nicht-negativ: Kopie, falls du mutieren willst
        return a

    if np.issubdtype(a.dtype, np.floating):
        return np.abs(a).astype(a.dtype, copy=False)

    if np.iscomplexobj(a):
        # Betrag -> float, Präzision passend wählen
        out_dtype = np.float32 if a.dtype == np.complex64 else np.float64
        return np.abs(a).astype(out_dtype, copy=False)

    raise TypeError(f"Nicht unterstützter dtype: {a.dtype}")
