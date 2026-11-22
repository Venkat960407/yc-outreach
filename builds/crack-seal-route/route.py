"""How much driving does a crack-sealing robot waste between cracks, and how much can routing save?

A robot seals cracks in an asphalt lot by moving a nozzle along each crack. Time spent sealing is
fixed by the total crack length. Time spent moving between cracks (with the nozzle off) depends
on the order the cracks are done in and which end of each crack the robot starts from.

This script makes random crack networks (long transverse/longitudinal cracks plus short branches,
like real pavement), then compares four ways to order the work:

  1. scan order: sort cracks by where they start, like reading them off a scan
  2. scan order, but flip each crack to start from the nearer end
  3. greedy nearest-neighbor: always go to the closest unsealed crack end next
  4. greedy + 2-opt-style improvement (reverse chunks of the route when it shortens travel)

and reports the dead travel distance and the total job time.

Usage:
  python route.py                 # prints the tables
  python route.py --plot out.png  # also saves an example route
"""
import argparse
import numpy as np

SEAL_SPEED = 0.15    # m/s while sealing (nozzle following a crack)
MOVE_SPEED = 1.0     # m/s moving between cracks with the nozzle off
LOT = (30.0, 20.0)   # m


def crack(rng, start, heading, length, wiggle=0.25, step=0.2):
    pts = [np.array(start, float)]
    h = heading
    for _ in range(int(length / step)):
        h += rng.normal(0, wiggle * step)
        p = pts[-1] + step * np.array([np.cos(h), np.sin(h)])
        if not (0 <= p[0] <= LOT[0] and 0 <= p[1] <= LOT[1]):
            break
        pts.append(p)
    return np.array(pts)


def make_lot(rng, n_main=12, n_branch=30):
    cracks = []
    for _ in range(n_main):
        if rng.random() < 0.5:   # transverse
            c = crack(rng, (rng.uniform(0, LOT[0]), 0.0), np.pi / 2 + rng.normal(0, 0.15), LOT[1])
        else:                    # longitudinal
            c = crack(rng, (0.0, rng.uniform(0, LOT[1])), rng.normal(0, 0.1), LOT[0] * rng.uniform(0.3, 1))
        if len(c) > 3:
            cracks.append(c)
    for _ in range(n_branch):    # short branches off existing cracks
        base = cracks[rng.integers(len(cracks))]
        p = base[rng.integers(len(base))]
        c = crack(rng, p, rng.uniform(0, 2 * np.pi), rng.uniform(0.5, 4.0), wiggle=0.6)
        if len(c) > 3:
            cracks.append(c)
    return cracks


def length(c):
    return np.linalg.norm(np.diff(c, axis=0), axis=1).sum()


def route_cost(order, cracks, start=(0.0, 0.0)):
    """order: list of (index, reversed). Returns dead travel distance."""
    pos = np.array(start)
    dead = 0.0
    for i, rev in order:
        c = cracks[i][::-1] if rev else cracks[i]
        dead += np.linalg.norm(c[0] - pos)
        pos = c[-1]
    return dead


def scan_order(cracks, flip=False):
    idx = sorted(range(len(cracks)), key=lambda i: (round(cracks[i][0][0] / 2), cracks[i][0][1]))
    order, pos = [], np.zeros(2)
    for i in idx:
        rev = flip and np.linalg.norm(cracks[i][-1] - pos) < np.linalg.norm(cracks[i][0] - pos)
        order.append((i, rev))
        pos = (cracks[i][::-1] if rev else cracks[i])[-1]
    return order


def greedy(cracks):
    left = set(range(len(cracks)))
    pos, order = np.zeros(2), []
    while left:
        best = min(((np.linalg.norm(cracks[i][0] - pos), i, False) for i in left),
                   default=None)
        best_r = min(((np.linalg.norm(cracks[i][-1] - pos), i, True) for i in left))
        d, i, rev = min(best, best_r)
        order.append((i, rev))
        left.remove(i)
        pos = (cracks[i][::-1] if rev else cracks[i])[-1]
    return order


def two_opt(order, cracks, passes=4):
    """Reverse a chunk of the route (which also flips each crack in it) when that cuts travel."""
    best = list(order)
    best_cost = route_cost(best, cracks)
    for _ in range(passes):
        improved = False
        for a in range(len(best) - 1):
            for b in range(a + 1, len(best)):
                cand = best[:a] + [(i, not r) for i, r in reversed(best[a:b + 1])] + best[b + 1:]
                c = route_cost(cand, cracks)
                if c < best_cost - 1e-9:
                    best, best_cost, improved = cand, c, True
        if not improved:
            break
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lots", type=int, default=20)
    ap.add_argument("--plot")
    a = ap.parse_args()
    methods = {"scan order": lambda c: scan_order(c), "scan + flip ends": lambda c: scan_order(c, True),
               "greedy nearest": greedy, "greedy + 2-opt": lambda c: two_opt(greedy(c), c)}
    dead = {m: [] for m in methods}
    total = {m: [] for m in methods}
    seal_len = []
    for s in range(a.lots):
        rng = np.random.default_rng(s)
        cracks = make_lot(rng)
        L = sum(length(c) for c in cracks)
        seal_len.append(L)
        for m, f in methods.items():
            d = route_cost(f(cracks), cracks)
            dead[m].append(d)
            total[m].append(L / SEAL_SPEED + d / MOVE_SPEED)
    print(f"{a.lots} random lots, median {np.median(seal_len):.0f} m of cracks "
          f"({np.median(seal_len) / SEAL_SPEED / 60:.0f} min of sealing at {SEAL_SPEED} m/s)\n")
    print(f"{'route':>18} | {'dead travel (m)':>15} | {'job time (min)':>14} | {'dead travel vs scan':>19}")
    base = np.array(dead["scan order"])
    for m in methods:
        print(f"{m:>18} | {np.median(dead[m]):>15.0f} | {np.median(total[m]) / 60:>14.1f} | "
              f"{np.median(np.array(dead[m]) / base) - 1:>+18.0%}")
    print("\nShare of the job spent driving nozzle-off, at different sealing speeds:")
    for sp in (0.15, 0.3, 0.6):
        cells = []
        for m in ("scan order", "greedy + 2-opt"):
            share = np.median([d / MOVE_SPEED / (L / sp + d / MOVE_SPEED) for d, L in zip(dead[m], seal_len)])
            cells.append(f"{m} {share:.0%}")
        print(f"  seal at {sp} m/s: " + ", ".join(cells))
    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        cracks = make_lot(np.random.default_rng(0))
        fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
        for ax, m in zip(axs, ("scan order", "greedy + 2-opt")):
            order = methods[m](cracks)
            pos = np.zeros(2)
            for i, rev in order:
                c = cracks[i][::-1] if rev else cracks[i]
                ax.plot([pos[0], c[0][0]], [pos[1], c[0][1]], color="tab:red", lw=0.7, ls="--")
                ax.plot(c[:, 0], c[:, 1], color="k", lw=1.2)
                pos = c[-1]
            ax.set_title(f"{m}: {route_cost(order, cracks):.0f} m of dead travel")
            ax.set_aspect("equal"); ax.set_xlim(0, LOT[0]); ax.set_ylim(0, LOT[1])
        fig.suptitle("Black: cracks sealed. Red dashed: nozzle-off travel between cracks.")
        fig.savefig(a.plot, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
