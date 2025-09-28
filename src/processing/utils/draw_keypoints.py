from __future__ import annotations
from typing import Iterable, Literal
import numpy.typing as npt
import cv2
import math

Style = Literal["point", "line", "cross", "x", "circle"]


def draw_keypoints(
    img: npt.NDArray,
    keypoints: Iterable[cv2.KeyPoint],
    *,
    style: Style = "cross",
    size: int = 7,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 1,
    line_type: int = cv2.LINE_AA,
    scale_with_kp: bool = False,   # True => Größe aus kp.size (falls größer als 'size')
) -> npt.NDArray:
    if img.ndim == 2:
        out = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        out = img.copy()

    for kp in keypoints:
        x, y = int(round(kp.pt[0])), int(round(kp.pt[1]))
        s = int(size)
        if scale_with_kp:
            s = max(s, int(round(kp.size))) if kp.size > 0 else s
        s = max(1, s)

        if style == "point":
            # kleiner gefüllter Punkt
            r = max(1, s // 3)
            cv2.circle(out, (x, y), r, color, thickness=-1, lineType=line_type)

        elif style == "circle":
            # Kreis mit ~Durchmesser=size
            r = max(1, s // 2)
            cv2.circle(out, (x, y), r, color, thickness=thickness, lineType=line_type)

        elif style == "cross":
            # Plus (+)
            cv2.drawMarker(
                out, (x, y), color,
                markerType=cv2.MARKER_CROSS,
                markerSize=s,
                thickness=thickness,
                line_type=line_type
            )

        elif style == "x":
            # Schräges Kreuz (x)
            cv2.drawMarker(
                out, (x, y), color,
                markerType=cv2.MARKER_TILTED_CROSS,
                markerSize=s,
                thickness=thickness,
                line_type=line_type
            )

        elif style == "line":
            # Kurzes Liniensegment um den Keypoint, orientiert an kp.angle (Grad)
            angle_deg = float(kp.angle) if kp.angle is not None and kp.angle >= 0 else 0.0
            ang = math.radians(angle_deg)
            half = s * 0.5
            dx = half * math.cos(ang)
            dy = half * math.sin(ang)
            x1 = int(round(x - dx))
            y1 = int(round(y - dy))
            x2 = int(round(x + dx))
            y2 = int(round(y + dy))
            cv2.line(out, (x1, y1), (x2, y2), color, thickness=thickness, lineType=line_type)

        else:
            raise ValueError("style muss 'point', 'line', 'cross', 'x' oder 'circle' sein.")

    return out
