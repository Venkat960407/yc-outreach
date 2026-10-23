"""Accuracy check on synthetic photos where the true sizes are known.

Draws trout-shaped fish (body + narrow peduncle + forked tail) at random sizes, rotations and
positions on a board, adds a 50 mm ArUco marker, lighting gradient and sensor noise, then runs
fish_measure.measure() and compares to the truth.

    python synthetic_test.py            # 60 photos, prints error stats, saves 3 examples
"""
import json
import math
import sys

import cv2
import numpy as np

from fish_measure import DICT, annotate, measure

rng = np.random.default_rng(7)


def fish_outline(tl, depth, fork_frac):
    """Outline in mm, head at x=0, tail tips at x=tl. Returns points and the true fork length."""
    body = 0.78 * tl                      # head tip to start of tail fin
    ped = 0.12 * depth                    # half-height of the narrow peduncle
    top, bot = [], []
    for x in np.linspace(0, body, 120):
        t = x / body
        # rounded head, deepest at ~35% of the body, tapering to the peduncle
        h = depth / 2 * math.sqrt(1 - (1 - t / 0.35) ** 2) if t < 0.35 else \
            ped + (depth / 2 - ped) * (1 - (t - 0.35) / 0.65) ** 1.3
        top.append((x, -h)); bot.append((x, h))
    fork_x = body + fork_frac * (tl - body)
    lobe = depth * 0.45
    tail = [(body, -ped), (tl, -lobe), (fork_x, 0), (tl, lobe), (body, ped)]
    pts = top + tail[1:4] + bot[::-1]
    return np.array(pts), fork_x


def render(tl, depth, fork_frac, px_per_mm, angle):
    h, w = 900, 1400
    board = np.array([205, 215, 222], np.float32)                 # light grey-blue cutting board
    img = np.ones((h, w, 3), np.float32) * board
    gx = np.linspace(-1, 1, w)[None, :, None]
    img *= 1 + 0.08 * gx                                          # uneven lighting
    pts, fork_x = fish_outline(tl, depth, fork_frac)
    pts = (pts - [tl / 2, 0]) * px_per_mm
    R = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
    centre = np.array([w * 0.58 + rng.uniform(-60, 60), h * 0.5 + rng.uniform(-60, 60)])
    poly = (pts @ R.T + centre).astype(np.int32)
    fish = np.zeros((h, w), np.uint8)
    cv2.fillPoly(fish, [poly], 255)
    colour = np.array([70, 95, 110], np.float32) + rng.uniform(-15, 15, 3)
    spots = rng.normal(0, 10, (h, w, 1)).astype(np.float32)
    img[fish > 0] = (colour + spots[fish > 0]) * 1.0
    # 50 mm ArUco marker with a white quiet zone, top-left
    side = int(round(50 * px_per_mm))
    mk = cv2.aruco.generateImageMarker(cv2.aruco.getPredefinedDictionary(DICT), 3, side)
    q = side // 6
    x0, y0 = 40, h - side - 40
    img[y0 - q:y0 + side + q, x0 - q:x0 + side + q] = 255
    img[y0:y0 + side, x0:x0 + side] = cv2.cvtColor(mk, cv2.COLOR_GRAY2BGR)
    img += rng.normal(0, 4, img.shape).astype(np.float32)        # sensor noise
    img = cv2.GaussianBlur(np.clip(img, 0, 255).astype(np.uint8), (3, 3), 0)
    return img, fork_x


def main(n=60):
    rows = []
    for i in range(n):
        tl = rng.uniform(250, 450)                 # 25-45 cm trout
        depth = tl * rng.uniform(0.2, 0.27)
        fork_frac = rng.uniform(0.35, 0.6)
        ppm = rng.uniform(1.8, 2.6)                # pixels per mm
        ang = rng.uniform(-0.6, 0.6)
        img, fork_x = render(tl, depth, fork_frac, ppm, ang)
        m, g = measure(img, 50)
        rows.append(dict(tl=tl, fl=fork_x, depth=depth, m_tl=m.total_length_mm,
                         m_fl=m.fork_length_mm, m_depth=m.body_depth_mm))
        if i < 3:
            cv2.imwrite(f"example_{i + 1}.jpg", annotate(img, m, g))
    err = lambda k, mk: np.array([abs(r[mk] - r[k]) / r[k] * 100 for r in rows if r[mk]])
    stats = {}
    for name, k, mk in [("total length", "tl", "m_tl"), ("fork length", "fl", "m_fl"),
                        ("body depth", "depth", "m_depth")]:
        e = err(k, mk)
        stats[name] = dict(n=len(e), mean_pct=round(e.mean(), 2), p95_pct=round(np.percentile(e, 95), 2),
                           max_pct=round(e.max(), 2))
    found = sum(1 for r in rows if r["m_fl"])
    print(f"{n} synthetic photos, fork found in {found}")
    for k, s in stats.items():
        print(f"  {k:13s} mean error {s['mean_pct']:.2f}%   95th pct {s['p95_pct']:.2f}%   max {s['max_pct']:.2f}%")
    json.dump(stats, open("synthetic_results.json", "w"), indent=2)
    return stats


if __name__ == "__main__":
    s = main(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
    sys.exit(0 if s["total length"]["p95_pct"] < 2 and s["body depth"]["p95_pct"] < 4 else 1)
