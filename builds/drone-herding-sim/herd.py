"""Simulate one drone herding a group of cattle into a pen.

Cattle follow a simple flocking model: stay near neighbors, keep a little personal space, drift
randomly, and move away from the drone when it gets close. The drone uses the "collect and drive"
strategy from shepherding research (Strombom et al., 2014): if the herd is bunched up, get behind it
and push it toward the pen; if a cow has strayed, go behind the furthest stray and push it back in.

Usage:
  python herd.py                 # 200 runs per setting, prints a results table
  python herd.py --plot run.png  # also saves one example run
"""
import argparse
import numpy as np

FIELD = 150.0          # meters on a side
PEN = np.array([140.0, 140.0])
PEN_R = 15.0


def step_herd(cows, drone, rng, dt, fear_r=30.0):
    n = len(cows)
    d = cows[:, None, :] - cows[None, :, :]
    dist = np.linalg.norm(d, axis=2) + np.eye(n) * 1e9 + 1e-6
    # personal space: push apart within 2 m
    close = (dist < 2.0)[..., None]
    repel = (d / dist[..., None] ** 2 * close).sum(1)
    # cohesion: move toward the local center of the 10 nearest
    nn = np.argsort(dist, axis=1)[:, :10]
    coh = cows[nn].mean(1) - cows
    # fear of the drone
    to_drone = cows - drone
    dd = np.linalg.norm(to_drone, axis=1, keepdims=True)
    scared = dd < fear_r
    flee = np.where(scared, to_drone / (dd + 1e-9), 0.0)
    calm = ~scared
    vel = 1.5 * flee * 1.0 + 0.6 * repel
    vel += np.where(scared, 0.4 * coh / (np.linalg.norm(coh, axis=1, keepdims=True) + 1e-9), 0.0)
    vel += np.where(calm, 0.05 * coh, 0.0)
    vel += rng.normal(0, 0.3, cows.shape)
    speed = np.linalg.norm(vel, axis=1, keepdims=True)
    vel = np.where(speed > 2.5, vel / speed * 2.5, vel)   # cattle top out around 2.5 m/s here
    return np.clip(cows + vel * dt, 0, FIELD)


def drone_target(cows, drone, standoff=8.0, mode_bias=None):
    n = len(cows)
    gcm = cows.mean(0)
    f_n = 2.0 * n ** (2 / 3)                       # how spread a "bunched" herd can be (Strombom)
    far = np.linalg.norm(cows - gcm, axis=1)
    if far.max() > f_n:                            # collect the worst stray
        stray = cows[far.argmax()]
        away = (stray - gcm) / (np.linalg.norm(stray - gcm) + 1e-9)
        return stray + away * standoff, "collect"
    away = (gcm - PEN) / (np.linalg.norm(gcm - PEN) + 1e-9)
    return gcm + away * (standoff + 1.5 * np.sqrt(n)), "drive"


def run(n_cows=40, seed=0, max_s=1800, dt=0.5, drone_speed=6.0, return_path=False):
    rng = np.random.default_rng(seed)
    cows = rng.uniform([15, 15], [55, 55], (n_cows, 2))
    drone = np.array([5.0, 5.0])
    path = []
    for k in range(int(max_s / dt)):
        tgt, mode = drone_target(cows, drone)
        step = tgt - drone
        dist = np.linalg.norm(step)
        drone = drone + step / (dist + 1e-9) * min(dist, drone_speed * dt)
        cows = step_herd(cows, drone, rng, dt)
        if return_path and k % 4 == 0:
            path.append((cows.copy(), drone.copy(), mode))
        if (np.linalg.norm(cows - PEN, axis=1) < PEN_R).mean() >= 0.9:
            return (k + 1) * dt, path
    return None, path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--plot")
    a = ap.parse_args()
    print(f"{'cattle':>6} {'drone m/s':>9} {'penned':>7} {'median time':>11}")
    for n in (20, 40, 80):
        for sp in (4.0, 6.0, 10.0):
            times = [run(n, s, drone_speed=sp)[0] for s in range(a.runs)]
            ok = [t for t in times if t is not None]
            med = f"{np.median(ok) / 60:.1f} min" if ok else "-"
            print(f"{n:>6} {sp:>9.0f} {len(ok) / len(times):>7.0%} {med:>11}")
    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        t, path = run(40, 1, return_path=True)
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.add_patch(plt.Circle(PEN, PEN_R, color="tab:green", alpha=0.2))
        dr = np.array([p[1] for p in path])
        ax.plot(dr[:, 0], dr[:, 1], lw=0.8, color="tab:red", label="drone path")
        for i in (0, len(path) // 2, len(path) - 1):
            c = path[i][0]
            ax.scatter(c[:, 0], c[:, 1], s=6, label=f"cattle at {i * 2 / 60:.1f} min")
        ax.set_xlim(0, FIELD); ax.set_ylim(0, FIELD); ax.set_aspect("equal")
        ax.legend(loc="upper left", fontsize=8); ax.set_title(f"40 cattle, penned in {t / 60:.1f} min" if t else "40 cattle, not penned in 30 min")
        fig.savefig(a.plot, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
