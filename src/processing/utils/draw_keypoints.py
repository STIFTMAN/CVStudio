from __future__ import annotations
from typing import Iterable, Literal
import numpy as np
import numpy.typing as npt
import cv2
import math

Style = Literal["point", "line", "cross", "circle", "rect"]


def draw_keypoints(
    img: npt.NDArray,
    keypoints: Iterable[cv2.KeyPoint],
    *,
    style: Style = "cross",
    size: int = 7,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 1,
    line_type: int = cv2.LINE_AA,
    scale_with_kp: bool = False,   # True => Größe aus kp.size/response (falls größer als 'size')
) -> npt.NDArray:
    if img.ndim == 2:
        out = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        out = img.copy()

    for kp in keypoints:
        x, y = int(round(kp.pt[0])), int(round(kp.pt[1]))
        # Basisgröße s (Fallback für Marker/Square-Seite etc.)
        s = int(size)
        if scale_with_kp and kp.size > 0:
            s = max(s, int(round(kp.size)))
        s = max(1, s)

        if style == "point":
            r = max(1, s // 3)
            cv2.circle(out, (x, y), r, color, thickness=-1, lineType=line_type)

        elif style == "circle":
            r = max(1, s // 2)
            cv2.circle(out, (x, y), r, color, thickness=thickness, lineType=line_type)

        elif style == "cross":
            cv2.drawMarker(out, (x, y), color,
                           markerType=cv2.MARKER_CROSS,
                           markerSize=s,
                           thickness=thickness,
                           line_type=line_type)

        elif style == "line":
            # Nutze kp.size als Gesamtlänge (falls vorhanden)
            angle_deg = float(kp.angle) if (kp.angle is not None) else 0.0
            ang = math.radians(angle_deg)
            half = (kp.size if (scale_with_kp and kp.size > 0) else s) * 0.5
            dx = half * math.cos(ang)
            dy = half * math.sin(ang)
            x1 = int(round(x - dx))
            y1 = int(round(y - dy))
            x2 = int(round(x + dx))
            y2 = int(round(y + dy))
            cv2.line(out, (x1, y1), (x2, y2), color, thickness=thickness, lineType=line_type)

        elif style == "rect":
            # OPTION A: kp.size = length (lange Seite), kp.response = width (kurze Seite), kp.angle = Grad
            # Fallbacks, wenn width/angle fehlen:
            length = float(kp.size) if (scale_with_kp and kp.size > 0) else float(s)
            width = float(kp.response) if (scale_with_kp and getattr(kp, "response", 0) > 0) else float(s)
            angle_deg = float(kp.angle) if (kp.angle is not None) else None

            # Sicherheitsklemmen
            length = max(1.0, float(length))
            width = max(1.0, float(width))

            if angle_deg is None:
                # Achsenparallel: nutze length als Breite in x-Richtung und width in y-Richtung
                half_L = length * 0.5
                half_W = width * 0.5
                x1 = int(round(x - half_L))
                y1 = int(round(y - half_W))
                x2 = int(round(x + half_L))
                y2 = int(round(y + half_W))
                cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness=thickness, lineType=line_type)
            else:
                # Rotiertes Rechteck (cx,cy),(w,h),angle erwartet: Winkel in Grad
                rr = ((float(x), float(y)), (float(length), float(width)), float(angle_deg))
                box = cv2.boxPoints(rr)          # (4,2) float
                box = np.int32(np.round(box))    # int-Koordinaten
                cv2.polylines(out, [box], isClosed=True, color=color, thickness=thickness, lineType=line_type)  # type: ignore

        else:
            raise ValueError("style muss 'point', 'line', 'cross', 'x', 'circle' oder 'rect' sein.")

    return out
