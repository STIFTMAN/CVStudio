from typing import Dict, Any, List
import cv2
import numpy as np


def affine_to_points(P: np.ndarray, M2x3: np.ndarray) -> np.ndarray:
    if P.size == 0:
        return P.copy()
    ones = np.ones((P.shape[0], 1), dtype=np.float32)
    homo = np.concatenate([P, ones], axis=1)
    out = (homo @ M2x3.T).astype(np.float32)
    return out


def repeatability(pred: np.ndarray, det: np.ndarray, tol_px: float = 3.0) -> float:
    if pred.size == 0 or det.size == 0:
        return 0.0
    d2 = ((pred[:, None, :] - det[None, :, :])**2).sum(axis=2)
    hit = (np.min(d2, axis=1) <= (tol_px**2)).sum()
    return float(hit) / float(pred.shape[0])


def sift_match_metrics(desA: np.ndarray, desB: np.ndarray, kpA: List[cv2.KeyPoint], kpB: List[cv2.KeyPoint], ratio: float = 0.75, ransac_thresh: float = 3.0) -> Dict[str, Any]:
    res = {"good_matches": 0, "inliers": 0, "inlier_ratio": 0.0, "H": None}
    if desA is None or desB is None or desA.size == 0 or desB.size == 0:
        return res
    bf = cv2.BFMatcher(cv2.NORM_L2)
    knn = bf.knnMatch(desA, desB, k=2)
    good = [m for m, n in knn if m.distance < ratio * n.distance]
    res["good_matches"] = len(good)
    if len(good) >= 4:
        ptsA = np.float32([kpA[m.queryIdx].pt for m in good])  # type: ignore
        ptsB = np.float32([kpB[m.trainIdx].pt for m in good])  # type: ignore
        H, mask = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, ransac_thresh)  # type: ignore
        res["H"] = H
        if mask is not None:
            inl = int(mask.sum())
            res["inliers"] = inl
            res["inlier_ratio"] = inl / max(1, len(good))
    return res


def orb_match_metrics(desA: np.ndarray, desB: np.ndarray, kpA: List[cv2.KeyPoint], kpB: List[cv2.KeyPoint], ratio: float = 0.75, ransac_thresh: float = 3.0) -> Dict[str, Any]:
    res = {"good_matches": 0, "inliers": 0, "inlier_ratio": 0.0, "H": None}
    if desA is None or desB is None or desA.size == 0 or desB.size == 0:
        return res
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    knn = bf.knnMatch(desA, desB, k=2)
    good = [m for m, n in knn if m.distance < ratio * n.distance]
    res["good_matches"] = len(good)
    if len(good) >= 4:
        ptsA = np.float32([kpA[m.queryIdx].pt for m in good])  # type: ignore
        ptsB = np.float32([kpB[m.trainIdx].pt for m in good])  # type: ignore
        H, mask = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, ransac_thresh)  # type: ignore
        res["H"] = H
        if mask is not None:
            inl = int(mask.sum())
            res["inliers"] = inl
            res["inlier_ratio"] = inl / max(1, len(good))
    return res
