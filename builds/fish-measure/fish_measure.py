"""Measure a fish from one photo: length, body depth, area, and a fork estimate.

Lay the fish on a plain board next to a printed ArUco marker of known size. The marker gives
millimeters per pixel, so no camera calibration is needed. The script:

  1. finds the marker and computes the pixel scale (and checks the photo isn't badly tilted),
  2. segments the fish from the board,
  3. finds the fish's long axis with PCA,
  4. measures total length along that axis and body depth perpendicular to it,
  5. finds the tail fork (the notch in the tail outline) for a fork-length estimate,
  6. writes an annotated image and prints the numbers as JSON.

Usage:
    python fish_measure.py photo.jpg --marker-mm 50
    python fish_measure.py photo.jpg --marker-mm 50 --out annotated.jpg
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict

import cv2
import numpy as np

DICT = cv2.aruco.DICT_4X4_50


@dataclass
class Measurement:
    total_length_mm: float
    fork_length_mm: float | None
    body_depth_mm: float
    area_cm2: float
    depth_to_length: float
    mm_per_px: float
    marker_skew: float  # 1.0 = square on camera; >1.05 means the photo is tilted


def find_scale(img, marker_mm):
    det = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(DICT))
    corners, ids, _ = det.detectMarkers(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    if ids is None:
        raise SystemExit("No ArUco marker found. Print one from the 4x4_50 dictionary and put it in frame.")
    c = corners[0][0]
    sides = [np.linalg.norm(c[i] - c[(i + 1) % 4]) for i in range(4)]
    skew = max(sides) / min(sides)
    return marker_mm / float(np.mean(sides)), skew, c


def segment_fish(img, marker_quad):
    """Largest non-board blob that isn't the marker. Works on a plain light or dark board."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    h, w = img.shape[:2]
    border = np.concatenate([lab[:10].reshape(-1, 3), lab[-10:].reshape(-1, 3),
                             lab[:, :10].reshape(-1, 3), lab[:, -10:].reshape(-1, 3)]).astype(np.float32)
    board = np.median(border, axis=0)
    dist = np.linalg.norm(lab.astype(np.float32) - board, axis=2)
    _, mask = cv2.threshold(dist.astype(np.uint8), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.fillPoly(mask, [marker_quad.astype(np.int32)], 0)
    # pad the marker area a bit so its white border doesn't leave a ring behind
    cv2.polylines(mask, [marker_quad.astype(np.int32)], True, 0, thickness=max(3, w // 200))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise SystemExit("Couldn't separate the fish from the board.")
    return max(contours, key=cv2.contourArea)


def axis_frame(contour):
    pts = contour.reshape(-1, 2).astype(np.float64)
    mean = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - mean, full_matrices=False)
    u, v = vt[0], vt[1]           # long axis, perpendicular
    return pts, mean, u, v


def fork_point(contour, along, across, tail_sign):
    """The tail fork is a dent in the outline at the tail end: a convexity defect (a point well
    inside the convex hull) in the last 25% of the fish. The corners where the tail fin meets
    the narrow peduncle are dents too, so among the real dents pick the one on the fish's
    centerline. A rounded or square tail has no dent there, so it returns None."""
    hull = cv2.convexHull(contour, returnPoints=False)
    try:
        defects = cv2.convexityDefects(contour, hull)
    except cv2.error:
        return None
    if defects is None:
        return None
    span = along.max() - along.min()
    tail_end = along.max() if tail_sign > 0 else along.min()
    dents = [f for _, _, f, d in defects.reshape(-1, 4)
             if abs(along[f] - tail_end) < 0.25 * span and d / 256.0 > 0.02 * span]
    if not dents:
        return None
    return min(dents, key=lambda f: abs(across[f]))


def measure(img, marker_mm):
    mm, skew, quad = find_scale(img, marker_mm)
    contour = segment_fish(img, quad)
    pts, mean, u, v = axis_frame(contour)
    along, across = (pts - mean) @ u, (pts - mean) @ v
    length_px = along.max() - along.min()

    # body depth: widest perpendicular slice, sampled along the axis
    bins = np.linspace(along.min(), along.max(), 80)
    depth_px, depth_at = 0.0, 0.0
    for a, b in zip(bins[:-1], bins[1:]):
        sel = (along >= a) & (along < b)
        if sel.sum() >= 2:
            d = across[sel].max() - across[sel].min()
            if d > depth_px:
                depth_px, depth_at = d, (a + b) / 2

    # the deepest point sits nearer the head on almost every fish, so the tail is the far end
    tail_sign = 1 if (along.max() - depth_at) > (depth_at - along.min()) else -1
    fi = fork_point(contour, along, across, tail_sign)
    head_end = along.min() if tail_sign > 0 else along.max()
    fork_px = abs(along[fi] - head_end) if fi is not None else None

    m = Measurement(
        total_length_mm=round(length_px * mm, 1),
        fork_length_mm=round(fork_px * mm, 1) if fork_px else None,
        body_depth_mm=round(depth_px * mm, 1),
        area_cm2=round(cv2.contourArea(contour) * mm * mm / 100, 1),
        depth_to_length=round(depth_px / length_px, 3),
        mm_per_px=round(mm, 4),
        marker_skew=round(skew, 3),
    )
    geo = dict(contour=contour, mean=mean, u=u, v=v, along=along, across=across,
               depth_at=depth_at, depth_px=depth_px, fork=pts[fi] if fi is not None else None, quad=quad)
    return m, geo


def annotate(img, m, g):
    out = img.copy()
    cv2.drawContours(out, [g["contour"]], -1, (0, 200, 0), 2)
    mean, u, v = g["mean"], g["u"], g["v"]
    a0, a1 = g["along"].min(), g["along"].max()
    p = lambda a, b: tuple(np.round(mean + a * u + b * v).astype(int))
    cv2.line(out, p(a0, 0), p(a1, 0), (255, 140, 0), 2)
    half = g["depth_px"] / 2
    c = g["across"][np.abs(g["along"] - g["depth_at"]) < (a1 - a0) / 80]
    mid = (c.max() + c.min()) / 2 if len(c) else 0
    cv2.line(out, p(g["depth_at"], mid - half), p(g["depth_at"], mid + half), (0, 140, 255), 2)
    if g["fork"] is not None:
        cv2.circle(out, tuple(np.round(g["fork"]).astype(int)), 7, (0, 0, 255), 2)
    cv2.polylines(out, [g["quad"].astype(np.int32)], True, (255, 0, 255), 2)
    lines = [f"TL {m.total_length_mm} mm", f"FL {m.fork_length_mm or '-'} mm",
             f"depth {m.body_depth_mm} mm", f"area {m.area_cm2} cm2"]
    x, y = out.shape[1] - 260, 12
    cv2.rectangle(out, (x - 10, y), (out.shape[1] - 8, y + 28 * len(lines) + 10), (255, 255, 255), -1)
    for i, t in enumerate(lines):
        cv2.putText(out, t, (x, y + 26 + 28 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2, cv2.LINE_AA)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--marker-mm", type=float, required=True, help="printed marker side length in mm")
    ap.add_argument("--out", default="annotated.jpg")
    a = ap.parse_args()
    img = cv2.imread(a.image)
    if img is None:
        raise SystemExit(f"Can't read {a.image}")
    m, g = measure(img, a.marker_mm)
    if m.marker_skew > 1.05:
        print(f"warning: marker is skewed {m.marker_skew:.2f}x; shoot from straight above for accurate numbers")
    cv2.imwrite(a.out, annotate(img, m, g))
    print(json.dumps(asdict(m), indent=2))
