"""Estimate where an ore body is from a handful of drill holes, and where to drill next.

The setup: a hidden 3D ore body (a tilted, lumpy lens of high grade rock) sits under a 400 m by
400 m claim. Each drill hole is a straight vertical line that samples grade every 5 m. From a few
holes, a Gaussian process (the statistics behind kriging) predicts grade everywhere and how unsure
it is. The next hole goes where the model is least sure whether the rock is above the ore cutoff.

The question it answers: how many holes does it take to find the ore body's size, and does
choosing holes by uncertainty beat a regular grid?

Usage:
  python orebody.py            # compares grid drilling vs uncertainty-guided drilling, 12 trials
  python orebody.py --plot out.png
"""
import argparse
import numpy as np

SIZE, DEPTH, STEP = 400.0, 300.0, 5.0
CUTOFF = 1.0   # grade (g/t) that counts as ore


def make_orebody(rng):
    """A tilted lens of ore, plus smooth background noise, as a function grade(x, y, z)."""
    c = rng.uniform([120, 120, 90], [280, 280, 200])
    axes = rng.uniform([60, 25, 18], [110, 50, 35])
    yaw, dip = rng.uniform(0, np.pi), rng.uniform(0.2, 0.7)
    k = rng.normal(size=(6, 3)) / 80.0
    ph = rng.uniform(0, 2 * np.pi, 6)

    def grade(p):
        q = p - c
        cy, sy, cd, sd = np.cos(yaw), np.sin(yaw), np.cos(dip), np.sin(dip)
        x = cy * q[:, 0] + sy * q[:, 1]
        y = -sy * q[:, 0] + cy * q[:, 1]
        z = q[:, 2]
        x, z = cd * x + sd * z, -sd * x + cd * z
        r = (x / axes[0]) ** 2 + (y / axes[1]) ** 2 + (z / axes[2]) ** 2
        bumps = 0.12 * np.sin(p @ k.T + ph).sum(1)
        return np.clip(3.0 * np.exp(-r) + bumps + 0.2, 0, None)
    return grade


def drill(grade, x, y, rng, noise=0.15):
    z = np.arange(STEP / 2, DEPTH, STEP)
    p = np.stack([np.full_like(z, x), np.full_like(z, y), z], 1)
    return p, grade(p) + rng.normal(0, noise, len(z))


class GP:
    """Gaussian process with an anisotropic squared-exponential kernel (fixed length scales)."""
    def __init__(self, ls=(70, 70, 35), var=1.0, noise=0.05):
        self.ls, self.var, self.noise = np.array(ls), var, noise

    def k(self, a, b):
        d = (a[:, None, :] - b[None, :, :]) / self.ls
        return self.var * np.exp(-0.5 * (d ** 2).sum(-1))

    def fit(self, X, y):
        self.X, self.mu = X, y.mean()
        K = self.k(X, X) + self.noise * np.eye(len(X))
        self.L = np.linalg.cholesky(K)
        self.alpha = np.linalg.solve(self.L.T, np.linalg.solve(self.L, y - self.mu))
        return self

    def predict(self, P):
        Ks = self.k(P, self.X)
        mean = self.mu + Ks @ self.alpha
        v = np.linalg.solve(self.L, Ks.T)
        var = np.clip(self.var - (v ** 2).sum(0), 1e-9, None)
        return mean, np.sqrt(var)


def grid_points(n=24, nz=20):
    g = np.linspace(SIZE / n / 2, SIZE - SIZE / n / 2, n)
    z = np.linspace(DEPTH / nz / 2, DEPTH - DEPTH / nz / 2, nz)
    X, Y, Z = np.meshgrid(g, g, z, indexing="ij")
    return np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1), (SIZE / n) ** 2 * (DEPTH / nz)


def thin(P, y, every=3):
    return P[::every], y[::every]


def run(strategy, n_holes, seed):
    rng = np.random.default_rng(seed)
    grade = make_orebody(rng)
    pts, cell = grid_points()
    true_vol = (grade(pts) >= CUTOFF).sum() * cell
    def grid(k):
        g = np.linspace(SIZE / k / 2, SIZE - SIZE / k / 2, k)
        return [(a, b) for a in g for b in g]
    if strategy == "grid":
        holes = grid(int(round(np.sqrt(n_holes))))
    else:
        holes = grid(3)   # guided: a 3x3 scouting grid first, then infill holes chosen one at a time
    X, Y = [], []
    for h in holes:
        p, y = thin(*drill(grade, *h, rng)); X.append(p); Y.append(y)
    cand = np.stack(np.meshgrid(np.linspace(20, 380, 37), np.linspace(20, 380, 37)), -1).reshape(-1, 2)
    while strategy == "guided" and len(holes) < n_holes:
        gp = GP().fit(np.concatenate(X), np.concatenate(Y))
        z = np.arange(10, DEPTH, 20.0)
        P = np.concatenate([np.repeat(cand, len(z), 0), np.tile(z, len(cand))[:, None]], 1)
        m, s = gp.predict(P)
        # "straddle" score (Bryan et al. 2005): high where the model is unsure AND its guess is
        # close to the ore cutoff, i.e. near the edge of the ore body. Summed down each hole.
        score = np.clip(1.96 * s - np.abs(m - CUTOFF), 0, None).reshape(len(cand), len(z)).sum(1)
        best = tuple(cand[int(np.argmax(score))])
        holes.append(best)
        p, y = thin(*drill(grade, *best, rng)); X.append(p); Y.append(y)
    gp = GP().fit(np.concatenate(X), np.concatenate(Y))
    m, _ = gp.predict(pts)
    est_vol = (m >= CUTOFF).sum() * cell
    truth, pred = grade(pts) >= CUTOFF, m >= CUTOFF
    iou = (truth & pred).sum() / max((truth | pred).sum(), 1)
    return true_vol, est_vol, iou, holes, (grade, gp, pts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=12)
    ap.add_argument("--plot")
    a = ap.parse_args()
    print(f"{'holes':>5} {'strategy':>8} {'median volume error':>20} {'median overlap (IoU)':>21}")
    for n in (16, 25, 36):
        for strat in ("grid", "guided"):
            errs, ious = [], []
            for s in range(a.trials):
                tv, ev, iou, _, _ = run(strat, n, s)
                errs.append(abs(ev - tv) / tv); ious.append(iou)
            print(f"{n:>5} {strat:>8} {np.median(errs):>20.0%} {np.median(ious):>21.2f}")
    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        print("drawing example plot...")
        fig, axs = plt.subplots(1, 2, figsize=(10, 4.6))
        for ax, strat in zip(axs, ("grid", "guided")):
            tv, ev, iou, holes, (grade, gp, _) = run(strat, 16, 3)
            g = np.linspace(0, SIZE, 60)
            XX, YY = np.meshgrid(g, g)
            zz = np.arange(STEP / 2, DEPTH, 10)
            P = np.stack([np.repeat(XX.ravel(), len(zz)), np.repeat(YY.ravel(), len(zz)), np.tile(zz, XX.size)], 1)
            true_thick = (grade(P) >= CUTOFF).reshape(-1, len(zz)).sum(1).reshape(XX.shape) * 10
            pm = np.concatenate([gp.predict(c)[0] for c in np.array_split(P, 20)])
            pred_thick = (pm >= CUTOFF).reshape(-1, len(zz)).sum(1).reshape(XX.shape) * 10
            ax.contourf(XX, YY, true_thick, levels=12, cmap="Greys")
            ax.contour(XX, YY, pred_thick, levels=[5], colors="tab:orange", linewidths=2)
            hx, hy = zip(*holes)
            ax.scatter(hx, hy, c="tab:blue", s=25, zorder=3)
            ax.set_title(f"{strat}: 16 holes, overlap {iou:.2f}")
            ax.set_aspect("equal"); ax.set_xlim(0, SIZE); ax.set_ylim(0, SIZE)
        fig.suptitle("Gray: true ore thickness. Orange: predicted outline. Blue: drill holes.")
        fig.savefig(a.plot, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
