"""Can a controller tune its own PID loop? Relay autotuning vs hand tuning on industrial plants.

The relay method (Astrom and Hagglund, 1984): replace the controller with an on/off relay for a
few cycles. The loop settles into a steady oscillation, and its period and amplitude give the
"ultimate" gain and period of the process. Classic tuning rules then turn those into PID gains.
It's how many industrial controllers auto-tune with one button.

This script runs that on simulated processes that look like real plant loops (a first-order lag
plus a dead time, the standard model for temperature, level and flow loops), with sensor noise,
and compares:
  - Ziegler-Nichols rules from the relay test (the textbook choice)
  - Tyreus-Luyben rules from the same test (more conservative)
  - "ideal" gains found by brute-force search with full knowledge of the plant

Scored on a setpoint step and a load disturbance: integrated absolute error, overshoot, and
whether the loop stays stable when the plant drifts 30% from what was tuned.

Usage:
  python autotune.py                 # prints the tables
  python autotune.py --plot out.png  # also saves an example
"""
import argparse
import numpy as np

DT = 0.05


class Plant:
    """K * exp(-L s) / (T s + 1), simulated with a delay buffer, plus measurement noise."""
    def __init__(self, K, T, L, noise=0.005, seed=0):
        self.K, self.T, self.L, self.noise = K, T, L, noise
        self.buf = [0.0] * max(1, int(round(L / DT)))
        self.y = 0.0
        self.rng = np.random.default_rng(seed)

    def step(self, u, load=0.0):
        self.buf.append(u + load)
        ud = self.buf.pop(0)
        self.y += DT / self.T * (self.K * ud - self.y)
        return self.y + self.rng.normal(0, self.noise)


def relay_test(K, T, L, h=1.0, hyst=0.02, seed=0, t_max=None):
    """Relay feedback test. Returns (Ku, Pu) estimated from the limit cycle."""
    p = Plant(K, T, L, seed=seed)
    t_max = t_max or 40 * (T + L)
    n = int(t_max / DT)
    y = 0.0
    u = h
    ys, crossings = [], []
    for i in range(n):
        e = -y                        # setpoint 0, start the relay high
        if e > hyst:
            u = h
        elif e < -hyst:
            u = -h
        y_new = p.step(u)
        if i > 0 and ys[-1] < 0 <= y_new:
            crossings.append(i * DT)
        ys.append(y_new)
        y = y_new
    ys = np.array(ys)
    tail = ys[len(ys) // 2:]
    a = (tail.max() - tail.min()) / 2
    periods = np.diff(crossings[len(crossings) // 2:])
    Pu = periods.mean()
    Ku = 4 * h / (np.pi * np.sqrt(max(a ** 2 - hyst ** 2, 1e-12)))
    return Ku, Pu


def true_ultimate(K, T, L):
    """Exact Ku, Pu for K e^{-Ls}/(Ts+1): phase -180 deg where w*L + atan(w*T) = pi."""
    lo, hi = 1e-4, 100.0
    for _ in range(200):
        w = 0.5 * (lo + hi)
        if w * L + np.arctan(w * T) < np.pi:
            lo = w
        else:
            hi = w
    return np.sqrt(1 + (w * T) ** 2) / K, 2 * np.pi / w


def rules(Ku, Pu, kind):
    if kind == "ZN":
        Kp, Ti, Td = 0.6 * Ku, 0.5 * Pu, 0.125 * Pu
    else:  # Tyreus-Luyben
        Kp, Ti, Td = 0.45 * Ku, 2.2 * Pu, Pu / 6.3
    return Kp, Kp / Ti, Kp * Td


def run_loop(K, T, L, gains, t_end=None, seed=1):
    """Setpoint step at t=0 to 1.0, load disturbance of -0.5 halfway. Returns metrics and trace."""
    kp, ki, kd = gains
    p = Plant(K, T, L, seed=seed)
    t_end = t_end or 30 * (T + L)
    n = int(t_end / DT)
    integ, prev, dfilt = 0.0, 0.0, 0.0
    alpha = DT / (DT + 0.1 * max(T, 0.5))
    y = 0.0
    tr = np.zeros(n)
    for i in range(n):
        sp = 1.0
        e = sp - y
        dfilt += alpha * ((-(y - prev)) / DT - dfilt)   # derivative on measurement
        prev = y
        u = kp * e + ki * integ + kd * dfilt
        if abs(u) < 10:                                 # simple anti-windup
            integ += e * DT
        u = np.clip(u, -10, 10)
        load = -0.5 if i * DT > t_end / 2 else 0.0
        y = p.step(u, load)
        tr[i] = y
        if not np.isfinite(y) or abs(y) > 1e3:
            return dict(iae=np.inf, over=np.inf, stable=False), tr
    half = n // 2
    iae = np.sum(np.abs(1.0 - tr)) * DT
    over = max(tr[:half].max() - 1.0, 0)
    tail = tr[int(0.9 * n):]
    stable = np.ptp(tail) < 0.2
    return dict(iae=iae, over=over, stable=stable), tr


def best_gains(K, T, L):
    """Brute-force search for the gains with lowest IAE and under 10% overshoot."""
    best = None
    for kp in np.geomspace(0.05, 20, 18) / K:
        for ti in np.geomspace(0.2, 5, 10) * T:
            for td in (0.0, 0.1 * L, 0.25 * L, 0.5 * L):
                g = (kp, kp / ti, kp * td)
                m, _ = run_loop(K, T, L, g)
                if m["stable"] and m["over"] < 0.10 and (best is None or m["iae"] < best[0]):
                    best = (m["iae"], g)
    return best[1]


PLANTS = {
    "fast flow loop": (1.0, 2.0, 0.3),
    "level loop": (2.0, 10.0, 1.0),
    "temperature loop": (1.5, 8.0, 4.0),
    "dead-time heavy": (1.0, 2.0, 4.0),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot")
    a = ap.parse_args()
    print("Relay test accuracy (estimated vs exact ultimate gain / period):")
    for name, (K, T, L) in PLANTS.items():
        Ku, Pu = relay_test(K, T, L); Kt, Pt = true_ultimate(K, T, L)
        print(f"  {name:>18}: Ku {Ku:.2f} vs {Kt:.2f} ({Ku / Kt - 1:+.0%}),  Pu {Pu:.2f} vs {Pt:.2f} s ({Pu / Pt - 1:+.0%})")
    print()
    print(f"{'process':>18} | {'tuning':>14} | {'IAE':>7} | {'overshoot':>9} | {'stable if plant drifts +30%':>27}")
    traces = {}
    for name, (K, T, L) in PLANTS.items():
        Ku, Pu = relay_test(K, T, L)
        opts = {"relay + ZN": rules(Ku, Pu, "ZN"), "relay + TL": rules(Ku, Pu, "TL"), "brute force": best_gains(K, T, L)}
        for tn, g in opts.items():
            m, tr = run_loop(K, T, L, g)
            m2, _ = run_loop(K * 1.3, T, L * 1.3, g)        # gain and dead time both 30% worse
            print(f"{name:>18} | {tn:>14} | {m['iae']:>7.2f} | {m['over']:>8.0%} | {'yes' if m2['stable'] else 'NO':>27}")
            traces[(name, tn)] = tr
        print("-" * 90)
    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        name = "temperature loop"
        K, T, L = PLANTS[name]
        t = np.arange(len(traces[(name, 'relay + ZN')])) * DT
        fig, ax = plt.subplots(figsize=(9, 4))
        for tn in ("relay + ZN", "relay + TL", "brute force"):
            ax.plot(t, traces[(name, tn)], label=tn, lw=1)
        ax.axhline(1, color="k", lw=0.5)
        ax.set_xlabel("time (s)"); ax.set_ylabel("process value")
        ax.set_title(f"{name}: setpoint step, then a load disturbance halfway")
        ax.legend(fontsize=8); fig.savefig(a.plot, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
