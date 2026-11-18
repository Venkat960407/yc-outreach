"""How fast can a weeding robot drive before it starts missing weeds or hitting crops?

A robot drives down a crop row. A camera at the front sees each plant, a classifier calls it weed
or crop, and a tool mounted some distance behind the camera fires when a weed passes under it.
Everything that adds timing error is modeled:

  - detection latency (camera + model), with jitter
  - wheel slip, so the robot's speed estimate is off by a few percent
  - tool actuation time and the size of the spot it treats
  - classifier mistakes (weeds called crops and the reverse)

The output is the fraction of weeds killed and crops hit, by driving speed and by latency, which
shows where the speed limit actually comes from.

Usage:
  python weeder.py                 # prints the tables
  python weeder.py --plot out.png  # also saves the chart
"""
import argparse
import numpy as np

ROW_M = 200.0          # length of row simulated per run
CROP_SPACING = 0.30    # m between crop plants
CROP_RADIUS = 0.05     # how close the tool can come to a crop stem before damaging it
TOOL_RADIUS = 0.015    # radius of the spot the tool treats
WEED_RADIUS = 0.01     # a weed is killed if the tool spot covers its stem within this


def make_row(rng, weeds_per_m=8.0):
    crops = np.arange(0.2, ROW_M, CROP_SPACING) + rng.normal(0, 0.02, int((ROW_M - 0.2) / CROP_SPACING) + 1)[: len(np.arange(0.2, ROW_M, CROP_SPACING))]
    weeds = rng.uniform(0, ROW_M, rng.poisson(weeds_per_m * ROW_M))
    # weeds very close to a crop stem can't be treated without hitting the crop anyway
    d = np.abs(weeds[:, None] - crops[None, :]).min(1)
    return crops, weeds[d > CROP_RADIUS + TOOL_RADIUS]


def run(speed, latency_ms, rng, jitter_ms=None, slip=0.03, actuate_ms=15.0, recall=0.95, false_pos=0.02,
        compensate=True):
    """Return (fraction of weeds killed, fraction of crops hit) for one row."""
    jitter_ms = latency_ms * 0.25 if jitter_ms is None else jitter_ms
    crops, weeds = make_row(rng)
    # what the classifier says it should shoot: most weeds, a few crops by mistake
    shoot_w = rng.random(len(weeds)) < recall
    shoot_c = rng.random(len(crops)) < false_pos
    targets = np.concatenate([weeds[shoot_w], crops[shoot_c]])
    # the robot plans to fire when the target reaches the tool, using its estimated speed and the
    # average latency; the real speed (slip) and real latency (jitter) differ from the estimates
    true_speed = speed * (1 + rng.normal(0, slip, len(targets)))
    lat = np.clip(rng.normal(latency_ms, jitter_ms, len(targets)), 0, None) / 1000
    act = np.clip(rng.normal(actuate_ms, actuate_ms * 0.2, len(targets)), 0, None) / 1000
    planned_lat = latency_ms / 1000 if compensate else 0.0
    planned_act = actuate_ms / 1000 if compensate else 0.0
    # position error along the row = speed error * time in flight + unmodeled timing * speed
    flight = 0.5 / speed                                  # camera is 0.5 m ahead of the tool
    err = (true_speed - speed) * flight + true_speed * ((lat - planned_lat) + (act - planned_act))
    hit_pos = targets + err
    killed = np.zeros(len(weeds), bool)
    crop_hit = np.zeros(len(crops), bool)
    for p in hit_pos:
        killed |= np.abs(weeds - p) < TOOL_RADIUS + WEED_RADIUS
        crop_hit |= np.abs(crops - p) < CROP_RADIUS
    return killed.mean(), crop_hit.mean()


def sweep(speeds, latencies, runs=20, **kw):
    out = np.zeros((len(latencies), len(speeds), 2))
    for i, L in enumerate(latencies):
        for j, v in enumerate(speeds):
            rng = np.random.default_rng(1000 * i + j)
            out[i, j] = np.mean([run(v, L, rng, **kw) for _ in range(runs)], axis=0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot")
    a = ap.parse_args()
    speeds = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0]
    lats = [20, 50, 100, 200]
    res = sweep(speeds, lats)
    print("weeds killed / crops hit, by speed (m/s) and detection latency, latency compensated:")
    print(f"{'latency':>8} " + " ".join(f"{v:>13.2f}" for v in speeds))
    for i, L in enumerate(lats):
        print(f"{L:>6}ms " + " ".join(f"{res[i, j, 0]:>6.0%}/{res[i, j, 1]:<6.1%}" for j in range(len(speeds))))
    print("\nwhat limits it at 1 m/s, 50 ms latency (weeds killed):")
    rng = np.random.default_rng(7)
    cases = {"everything on": {}, "no wheel slip": dict(slip=0.0), "no latency jitter": dict(jitter_ms=0.0),
             "perfect classifier": dict(recall=1.0, false_pos=0.0), "latency NOT compensated": dict(compensate=False)}
    for name, kw in cases.items():
        k, c = np.mean([run(1.0, 50, rng, **kw) for _ in range(40)], axis=0)
        print(f"  {name:<26} {k:>5.0%} killed, {c:>5.1%} crops hit")
    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
        for i, L in enumerate(lats):
            a1.plot(speeds, res[i, :, 0] * 100, "o-", label=f"{L} ms latency")
            a2.plot(speeds, res[i, :, 1] * 100, "o-", label=f"{L} ms latency")
        a1.set_title("weeds killed"); a2.set_title("crops hit")
        for ax in (a1, a2):
            ax.set_xlabel("driving speed (m/s)"); ax.set_ylabel("%"); ax.grid(alpha=0.3)
        a1.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(a.plot, dpi=120)


if __name__ == "__main__":
    main()
