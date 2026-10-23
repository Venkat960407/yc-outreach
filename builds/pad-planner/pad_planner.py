"""Where should the charging pads go? A planner for drone line-inspection networks.

Given a utility's transmission lines and its substations (the candidate pad sites), pick the
fewest substations that put every mile of line within a drone's round-trip reach, then say how
much line each pad covers and how far the drone flies to get there.

Model (all of it adjustable on the command line):
  usable range  = range_mi * (1 - reserve)          battery kept back for wind and landing
  a line point is reachable from a pad if  2 * distance + inspect_mi <= usable range
                                         i.e. fly out, inspect inspect_mi of line, fly back
Selection is greedy set cover on line-miles (pick the pad that covers the most uncovered
line, repeat), which is within a small factor of optimal and fast enough for a whole state.

Input: GeoJSON with LineString/MultiLineString features (lines) and Point features with
"substation": true (candidate pads). Without --geojson it builds a synthetic network to demo.

  python pad_planner.py --demo
  python pad_planner.py --geojson grid.geojson --range 85 --reserve 0.2 --inspect 30
"""
from __future__ import annotations

import argparse
import json
import math

import numpy as np

MI_PER_DEG_LAT = 69.0


# ---------- geometry ----------

def project(lonlat, lat0):
    """Equirectangular projection to miles. Fine at the scale of a utility territory."""
    a = np.asarray(lonlat, float)
    return np.c_[a[:, 0] * MI_PER_DEG_LAT * math.cos(math.radians(lat0)), a[:, 1] * MI_PER_DEG_LAT]


def sample_line(xy, step):
    """Points every `step` miles along a polyline, each standing for `step` miles of line."""
    out = []
    for p, q in zip(xy[:-1], xy[1:]):
        seg = np.linalg.norm(q - p)
        n = max(1, int(math.ceil(seg / step)))
        t = (np.arange(n) + 0.5) / n
        out.append(p + t[:, None] * (q - p))
    return np.vstack(out) if out else np.empty((0, 2))


# ---------- input ----------

def load_geojson(path):
    gj = json.load(open(path))
    lines, subs = [], []
    for f in gj["features"]:
        g, props = f["geometry"], f.get("properties") or {}
        if g["type"] == "LineString":
            lines.append(g["coordinates"])
        elif g["type"] == "MultiLineString":
            lines.extend(g["coordinates"])
        elif g["type"] == "Point" and props.get("substation"):
            subs.append((props.get("name") or f"sub-{len(subs) + 1}", g["coordinates"]))
    lat0 = float(np.mean([c[1] for l in lines for c in l]))
    return [project(l, lat0) for l in lines], [n for n, _ in subs], project([c for _, c in subs], lat0)


def synthetic_network(seed=3, n_subs=46, w=110, h=80):
    """A made-up territory: substations scattered over w x h miles, joined by a minimum
    spanning tree plus a few loops, with lines that wander a little like real corridors."""
    rng = np.random.default_rng(seed)
    pts = rng.uniform([0, 0], [w, h], (n_subs, 2))
    pts[: n_subs // 3] = rng.normal([w * 0.35, h * 0.55], [10, 8], (n_subs // 3, 2))  # a dense city
    d = np.linalg.norm(pts[:, None] - pts[None], axis=2)
    # Prim's MST
    used, edges = {0}, []
    best = d[0].copy(); parent = np.zeros(n_subs, int); best[0] = np.inf
    for _ in range(n_subs - 1):
        j = int(np.argmin(np.where(np.isin(np.arange(n_subs), list(used)), np.inf, best)))
        edges.append((parent[j], j)); used.add(j)
        closer = d[j] < best
        parent[closer] = j; best = np.minimum(best, d[j]); best[list(used)] = np.inf
    for _ in range(n_subs // 6):                       # a few redundant loops
        i, j = rng.choice(n_subs, 2, replace=False)
        if d[i, j] < 30:
            edges.append((i, j))
    lines = []
    for i, j in edges:
        a, b = pts[i], pts[j]
        mid = (a + b) / 2 + rng.normal(0, 0.12 * d[i, j], 2)
        lines.append(np.vstack([a, mid, b]))
    return lines, [f"sub-{k + 1}" for k in range(n_subs)], pts


# ---------- planning ----------

def plan(lines, sub_xy, range_mi, reserve, inspect_mi, step=0.25, target=1.0):
    usable = range_mi * (1 - reserve)
    reach = (usable - inspect_mi) / 2
    if reach <= 0:
        raise SystemExit("inspection length uses up the whole range; lower --inspect or --reserve")
    pts = np.vstack([sample_line(l, step) for l in lines])
    dist = np.linalg.norm(pts[:, None] - sub_xy[None], axis=2)        # points x pads
    can = dist <= reach
    reachable = can.any(axis=1)
    covered = np.zeros(len(pts), bool)
    chosen = []
    goal = target * reachable.sum()
    while covered.sum() < goal:
        gain = (can & ~covered[:, None]).sum(axis=0)
        k = int(np.argmax(gain))
        if gain[k] == 0:
            break
        chosen.append(k)
        covered |= can[:, k]
    # assign each covered point to its nearest chosen pad
    near = np.argmin(np.where(can[:, chosen], dist[:, chosen], np.inf), axis=1)
    per_pad = [dict(pad=int(k), line_mi=round(float(((near == i) & covered).sum() * step), 1),
                    mean_dist_mi=round(float(dist[(near == i) & covered, k].mean()), 1)
                    if ((near == i) & covered).any() else 0.0)
               for i, k in enumerate(chosen)]
    return dict(reach_mi=round(reach, 1), line_mi=round(len(pts) * step, 1),
                covered_mi=round(float(covered.sum() * step), 1),
                unreachable_mi=round(float((~reachable).sum() * step), 1),
                pads=chosen, per_pad=per_pad, pts=pts, covered=covered, near=near)


def plot(lines, sub_xy, names, res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 7.5))
    cmap = plt.get_cmap("tab20")
    pts, cov, near = res["pts"], res["covered"], res["near"]
    for i, k in enumerate(res["pads"]):
        sel = cov & (near == i)
        ax.scatter(pts[sel, 0], pts[sel, 1], s=2, color=cmap(i % 20))
        ax.add_patch(plt.Circle(sub_xy[k], res["reach_mi"], fill=False, ls="--", lw=0.7,
                                color=cmap(i % 20), alpha=0.6))
    ax.scatter(pts[~cov, 0], pts[~cov, 1], s=3, color="red", label="not reachable")
    ax.scatter(sub_xy[:, 0], sub_xy[:, 1], s=14, color="#888", zorder=3, label="substation")
    ax.scatter(sub_xy[res["pads"], 0], sub_xy[res["pads"], 1], s=90, marker="^", color="black",
               zorder=4, label="charging pad")
    ax.set_aspect("equal"); ax.set_xlabel("miles"); ax.set_ylabel("miles")
    ax.set_title(f"{len(res['pads'])} pads cover {res['covered_mi']:.0f} of {res['line_mi']:.0f} line-miles "
                 f"(reach {res['reach_mi']} mi per sortie)")
    ax.legend(loc="lower right", fontsize=8)
    fig.savefig(path, dpi=130, bbox_inches="tight")


def sweep(lines, sub_xy, range_mi, reserve):
    """How the number of pads depends on how much line each sortie inspects."""
    rows = []
    for insp in (0, 10, 20, 30, 40, 50):
        try:
            r = plan(lines, sub_xy, range_mi, reserve, insp)
        except SystemExit:
            continue
        rows.append((insp, r["reach_mi"], len(r["pads"]), r["covered_mi"] / max(len(r["pads"]), 1),
                     math.pi * r["reach_mi"] ** 2))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--geojson")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--range", type=float, default=85, help="drone range in miles (Faraday-1: 85)")
    ap.add_argument("--reserve", type=float, default=0.2, help="fraction of range held back")
    ap.add_argument("--inspect", type=float, default=30, help="miles of line inspected per sortie")
    ap.add_argument("--out", default="pads.png")
    a = ap.parse_args()
    if a.geojson:
        lines, names, subs = load_geojson(a.geojson)
    else:
        lines, names, subs = synthetic_network()
    res = plan(lines, subs, a.range, a.reserve, a.inspect)
    plot(lines, subs, names, res, a.out)
    print(f"line network: {res['line_mi']:.0f} miles, {len(subs)} substations")
    print(f"reach per sortie: {res['reach_mi']} mi  (range {a.range}, reserve {a.reserve:.0%}, inspect {a.inspect} mi)")
    print(f"pads needed: {len(res['pads'])}  covering {res['covered_mi']:.0f} mi; "
          f"{res['unreachable_mi']:.0f} mi out of reach of every substation")
    for p in sorted(res["per_pad"], key=lambda p: -p["line_mi"]):
        print(f"  {names[p['pad']]:>8s}: {p['line_mi']:6.1f} line-mi, mean flight {p['mean_dist_mi']} mi")
    print("\ninspect/sortie  reach  pads  line-mi per pad  circle area per pad")
    for insp, reach, n, per, area in sweep(lines, subs, a.range, a.reserve):
        print(f"  {insp:4.0f} mi      {reach:5.1f}  {n:4d}  {per:12.0f}     {area:8.0f} sq mi")
    print(f"\nSaved {a.out}")
