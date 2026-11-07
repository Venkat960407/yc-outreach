"""Catch a developing rack hotspot early by comparing each rack to its neighbors.

A simulated data hall: 2 rows of 20 racks, each with an inlet temperature sensor sampled every
minute for 2 weeks. Inlet temperature = cooling supply air (which swings with load over the day)
+ some recirculated hot air (more when a rack and its neighbors draw more power) + sensor noise.

Into each simulated week, one fault is injected at a random rack and time:
  - "airflow": a missing blanking panel or blocked tile, inlet creeps up 3 C over a few hours
  - "stuck":   the sensor freezes at its last reading
  - "row":     a cooling unit degrades and a whole row warms 2.5 C (not a single-rack fault)

Three detectors:
  1. threshold: alarm when inlet > 27 C (the top of ASHRAE's recommended range)
  2. peer:      each rack minus the median of its row, alarm when that gap is unusual for it
  3. peer+cusum: same gap, fed into a CUSUM so small, steady drifts add up into an alarm, plus a
     frozen-sensor check and a row-vs-row comparison

Usage:
  python hotspots.py               # 40 simulated fortnights, prints the comparison
  python hotspots.py --plot out.png
"""
import argparse
import numpy as np

ROWS, PER_ROW = 2, 20
N = ROWS * PER_ROW
MIN_PER_DAY = 1440
DAYS = 14


def simulate(seed):
    rng = np.random.default_rng(seed)
    T = DAYS * MIN_PER_DAY
    t = np.arange(T)
    day = np.sin(2 * np.pi * (t / MIN_PER_DAY - 0.3))
    base_kw = rng.uniform(4, 12, N)                                   # each rack's typical draw
    kw = base_kw[None, :] * (1 + 0.25 * day[:, None]) + rng.normal(0, 0.4, (T, N))
    supply = 18.5 + 1.2 * day + np.cumsum(rng.normal(0, 0.01, T))       # cooling supply air
    supply = supply - (supply - supply.mean()) * 0.5
    # recirculation: a bit of each rack's and its neighbors' heat reaches the inlet
    recirc = np.zeros_like(kw)
    for r in range(ROWS):
        s = slice(r * PER_ROW, (r + 1) * PER_ROW)
        k = kw[:, s]
        nb = np.pad(k, ((0, 0), (1, 1)), mode="edge")
        recirc[:, s] = 0.18 * k + 0.08 * (nb[:, :-2] + nb[:, 2:])
    pos_bias = rng.normal(0, 0.6, N)                                  # some spots just run warmer
    temp = supply[:, None] + recirc + pos_bias + rng.normal(0, 0.15, (T, N))

    faults = []
    for week in range(DAYS // 7):
        kind = ["airflow", "stuck", "row"][rng.integers(3)]
        start = week * 7 * MIN_PER_DAY + rng.integers(MIN_PER_DAY, 5 * MIN_PER_DAY)
        rack = int(rng.integers(N))
        if kind == "airflow":
            ramp = np.clip((t - start) / (4 * 60), 0, 1) * 3.0        # +3 C over 4 hours
            end = start + 24 * 60
            ramp[end:] = 0
            temp[:, rack] += ramp
            faults.append(("airflow", rack, start, end))
        elif kind == "stuck":
            end = start + 24 * 60
            temp[start:end, rack] = temp[start, rack]
            faults.append(("stuck", rack, start, end))
        else:
            row = rack // PER_ROW
            s = slice(row * PER_ROW, (row + 1) * PER_ROW)
            ramp = np.clip((t - start) / (2 * 60), 0, 1) * 2.5
            end = start + 12 * 60
            ramp[end:] = 0
            temp[:, s] += ramp[:, None]
            faults.append(("row", row, start, end))
    return temp, faults


def threshold(temp, limit=27.0):
    return temp > limit


def peer_gap(temp):
    gap = np.empty_like(temp)
    for r in range(ROWS):
        s = slice(r * PER_ROW, (r + 1) * PER_ROW)
        gap[:, s] = temp[:, s] - np.median(temp[:, s], axis=1, keepdims=True)
    return gap


def peer(temp, z=6.0, learn=MIN_PER_DAY):
    """Alarm when a rack's gap to its row median is far from what it was during the first day."""
    g = peer_gap(temp)
    g = np.apply_along_axis(lambda x: np.convolve(x, np.ones(10) / 10, "same"), 0, g)  # 10-min mean
    mu = g[:learn].mean(0)
    sd = g[:learn].std(0) + 0.05
    return np.abs(g - mu) / sd > z


def peer_cusum(temp, learn=MIN_PER_DAY, k=1.0, h=60.0):
    """CUSUM on the standardized gap: small steady drifts accumulate. Also flags frozen sensors
    (a reading that doesn't change at all for 30 minutes), and runs a row-vs-row CUSUM so a
    whole row warming up isn't hidden by the peer comparison."""
    g = peer_gap(temp)
    mu, sd = g[:learn].mean(0), g[:learn].std(0) + 0.05
    zt = (g - mu) / sd
    alarm = np.zeros_like(temp, bool)
    hi = np.zeros(N)
    lo = np.zeros(N)
    for i in range(len(temp)):
        hi = np.maximum(0, hi + zt[i] - k)
        lo = np.maximum(0, lo - zt[i] - k)
        alarm[i] = (hi > h) | (lo > h)
        hi[alarm[i]] = 0; lo[alarm[i]] = 0
    flat = np.zeros_like(alarm)
    d = np.abs(np.diff(temp, axis=0)) < 1e-9
    run = np.zeros(N)
    for i in range(1, len(temp)):
        run = np.where(d[i - 1], run + 1, 0)
        flat[i] = run >= 30
    # whole-row problems: compare each row's median to the other row's, same CUSUM idea
    med = np.stack([np.median(temp[:, r * PER_ROW:(r + 1) * PER_ROW], 1) for r in range(ROWS)], 1)
    rg = med - med[:, ::-1]
    rmu, rsd = rg[:learn].mean(0), rg[:learn].std(0) + 0.05
    rz = (rg - rmu) / rsd
    rh = np.zeros(ROWS)
    row_alarm = np.zeros((len(temp), ROWS), bool)
    for i in range(len(temp)):
        rh = np.maximum(0, rh + rz[i] - k)       # only warming matters for a row
        row_alarm[i] = rh > h
        rh[row_alarm[i]] = 0
    row_cols = np.repeat(row_alarm, PER_ROW, axis=1)
    return alarm | flat | row_cols


def score(alarm, faults):
    """Per fault: was it caught, and how many minutes after onset? Plus false alarm episodes."""
    caught = []
    expected = np.zeros_like(alarm)
    for kind, idx, start, end in faults:
        cols = list(range(idx * PER_ROW, (idx + 1) * PER_ROW)) if kind == "row" else [idx]
        expected[start:end + 120, cols] = True
        hits = np.where(alarm[start:end + 120, cols].any(1))[0]
        caught.append((kind, int(hits[0]) if len(hits) else None))
    false = alarm & ~expected
    # count separate false-alarm episodes (rising edges), after the 1-day learning period
    edges = (false[1:] & ~false[:-1])[MIN_PER_DAY:].sum()
    return caught, edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--plot")
    a = ap.parse_args()
    dets = {"threshold 27C": threshold, "peer": peer, "peer+cusum": peer_cusum}
    res = {d: {"airflow": [], "stuck": [], "row": [], "false": 0} for d in dets}
    weeks = 0
    for s in range(a.trials):
        temp, faults = simulate(s)
        weeks += DAYS / 7
        for name, f in dets.items():
            caught, fa = score(f(temp), faults)
            res[name]["false"] += fa
            for kind, lag in caught:
                res[name][kind].append(lag)
    print(f"{'detector':>14} | {'airflow fault':>22} | {'stuck sensor':>22} | {'row-wide warming':>22} | false alarms/week")
    for name, r in res.items():
        cells = []
        for kind in ("airflow", "stuck", "row"):
            lags = r[kind]
            hit = [x for x in lags if x is not None]
            rate = len(hit) / max(len(lags), 1)
            med = f"{np.median(hit):.0f} min" if hit else "-"
            cells.append(f"{rate:>4.0%} caught, {med:>8}")
        print(f"{name:>14} | " + " | ".join(f"{c:>22}" for c in cells) + f" | {r['false'] / weeks:.1f}")
    print("(n per fault type: " + ", ".join(f"{k} {len(res['peer'][k])}" for k in ('airflow', 'stuck', 'row')) + ")")

    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        for s in range(200):
            temp, faults = simulate(s)
            if faults[0][0] == "airflow":
                break
        kind, rack, start, end = faults[0]
        w = slice(start - 6 * 60, start + 10 * 60)
        hrs = (np.arange(len(temp))[w] - start) / 60
        row = rack // PER_ROW
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
        for c in range(row * PER_ROW, (row + 1) * PER_ROW):
            a1.plot(hrs, temp[w, c], color="tab:red" if c == rack else "0.75", lw=1.5 if c == rack else 0.6)
        a1.axhline(27, ls="--", color="k", lw=0.8); a1.text(hrs[0], 27.1, "27 C threshold", fontsize=8)
        a1.set_ylabel("inlet temp (C)"); a1.set_title(f"Rack {rack} (red) loses airflow at hour 0; gray = rest of its row")
        g = peer_gap(temp)[w, rack]
        a2.plot(hrs, g, color="tab:red")
        for name, f in (("peer+cusum", peer_cusum), ("threshold 27C", threshold)):
            al = f(temp)[w, rack]
            if al.any():
                a2.axvline(hrs[np.argmax(al)], ls=":", color="tab:blue" if "cusum" in name else "k")
                a2.text(hrs[np.argmax(al)], g.max(), f" {name} alarm", fontsize=8)
        a2.set_ylabel("gap to row median (C)"); a2.set_xlabel("hours from fault onset")
        fig.savefig(a.plot, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
