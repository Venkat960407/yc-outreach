"""How fast can a spacecraft reach another satellite, and what does speed cost in delta-v?

A chaser and a target share an orbit (GEO or LEO), with the target some angle ahead. For each
trip time, a Lambert solver finds the two-burn transfer that arrives at the target's position at
that moment, and adds up the delta-v for both burns (leave, then match the target's velocity).

Then it asks how long a vehicle needs to deliver that delta-v at a given thrust-to-mass ratio.
That's where high thrust matters: a fast trip needs a lot of delta-v, and a low-thrust engine
can't deliver it in a time that's short compared to the trip.

Usage:
  python reach.py                 # prints the tables
  python reach.py --plot out.png  # also saves the delta-v vs trip time curves
"""
import argparse
import numpy as np

MU = 3.986004418e14          # Earth, m^3/s^2
ORBITS = {"GEO": 42164e3, "LEO (500 km)": 6878e3}


def stumpff(z):
    if z > 1e-6:
        s = np.sqrt(z); return (1 - np.cos(s)) / z, (s - np.sin(s)) / s ** 3
    if z < -1e-6:
        s = np.sqrt(-z); return (np.cosh(s) - 1) / -z, (np.sinh(s) - s) / s ** 3
    return 0.5, 1 / 6


def lambert(r1, r2, tof, prograde=True):
    """Universal-variable Lambert solver (single revolution). Returns v1, v2 in m/s."""
    R1, R2 = np.linalg.norm(r1), np.linalg.norm(r2)
    cos_dnu = np.clip(r1 @ r2 / (R1 * R2), -1, 1)
    dnu = np.arccos(cos_dnu)
    if (np.cross(r1, r2)[2] < 0) == prograde:
        dnu = 2 * np.pi - dnu
    A = np.sin(dnu) * np.sqrt(R1 * R2 / (1 - np.cos(dnu)))

    def y(z):
        C, S = stumpff(z)
        return R1 + R2 + A * (z * S - 1) / np.sqrt(C)

    def F(z):
        C, S = stumpff(z)
        yz = y(z)
        if yz < 0:
            return -np.inf
        return (yz / C) ** 1.5 * S + A * np.sqrt(yz) - np.sqrt(MU) * tof

    lo, hi = -4 * np.pi ** 2, 4 * np.pi ** 2 - 1e-6     # bisection over the single-rev range
    while y(lo) < 0 or F(lo) == -np.inf:
        lo += 0.1
    if F(lo) * F(hi) > 0:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if F(lo) * F(mid) <= 0:
            hi = mid
        else:
            lo = mid
    z = 0.5 * (lo + hi)
    yz = y(z)
    f = 1 - yz / R1
    g = A * np.sqrt(yz / MU)
    gdot = 1 - yz / R2
    v1 = (r2 - f * r1) / g
    v2 = (gdot * r2 - r1) / g
    return v1, v2


def circ(r, theta):
    v = np.sqrt(MU / r)
    return (np.array([r * np.cos(theta), r * np.sin(theta), 0.0]),
            np.array([-v * np.sin(theta), v * np.cos(theta), 0.0]))


def trip_dv(r, lead_deg, tof):
    """Total delta-v (m/s) to catch a target lead_deg ahead on the same circular orbit."""
    n = np.sqrt(MU / r ** 3)
    r1, v_chaser = circ(r, 0.0)
    r2, v_target = circ(r, np.radians(lead_deg) + n * tof)    # where the target will be
    if lead_deg + np.degrees(n * tof) > 355:   # target would lap back past the start; use phasing
        return np.nan
    ang = np.degrees(np.arccos(np.clip(r1 @ r2 / r ** 2, -1, 1)))
    if ang > 179.0 or ang < 1.0:      # start and end points in line with Earth: plane undefined
        return np.nan
    best = None
    for pro in (True, False):
        sol = lambert(r1, r2, tof, pro)
        if sol is None:
            continue
        v1, v2 = sol
        dv = np.linalg.norm(v1 - v_chaser) + np.linalg.norm(v_target - v2)
        best = dv if best is None else min(best, dv)
    return best


def phasing(r, lead_deg, k):
    """Catch a target lead_deg ahead by dropping into a smaller, faster orbit for k laps.
    Returns (trip time s, total delta-v m/s, perigee altitude km)."""
    n = np.sqrt(MU / r ** 3)
    T = 2 * np.pi / n
    T_ph = T - np.radians(lead_deg) / (k * n)
    a_ph = (MU * (T_ph / (2 * np.pi)) ** 2) ** (1 / 3)
    v_ph = np.sqrt(MU * (2 / r - 1 / a_ph))
    dv = 2 * abs(np.sqrt(MU / r) - v_ph)            # one burn to enter, one to leave
    return k * T_ph, dv, (2 * a_ph - r - 6378e3) / 1e3


def check():
    """Sanity check: a "transfer" along the orbit itself should cost zero."""
    r = 42164e3
    n = np.sqrt(MU / r ** 3)
    worst = 0
    for deg in (30, 120, 200, 300):
        th = np.radians(deg)
        (r1, va), (r2, vb) = circ(r, 0), circ(r, th)
        v1, v2 = lambert(r1, r2, th / n)
        worst = max(worst, np.linalg.norm(v1 - va), np.linalg.norm(v2 - vb))
    print(f"check: Lambert along a circular orbit, worst velocity error {worst:.1e} m/s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot")
    a = ap.parse_args()
    check()
    leads = (10, 45, 90)
    curves = {}
    for name, r in ORBITS.items():
        T = 2 * np.pi * np.sqrt(r ** 3 / MU)
        print(f"\n{name}, one orbit takes {T / 3600:.1f} h. Total delta-v (m/s) to reach a target ahead by:")
        print(f"{'trip':>12} " + " ".join(f"{d:>8}deg" for d in leads))
        print("  direct transfers (under one orbit):")
        for frac in (0.1, 0.3, 0.5, 0.8):
            row = [trip_dv(r, d, frac * T) for d in leads]
            print(f"{frac * T / 3600:>10.1f} h " + " ".join(f"{x:>11.0f}" if x == x else f"{'-':>11}" for x in row))
        print("  phasing orbits (k laps in a smaller orbit), delta-v (trip time):")
        for k in (1, 2, 4, 8):
            row = [phasing(r, d, k) for d in leads]
            cells = [f"{dv:>5.0f} ({t / 3600:>4.0f} h)" if alt > 200 else f"{'too low':>11}" for t, dv, alt in row]
            print(f"{k:>7} laps " + " ".join(cells))
        ts = np.linspace(0.03, 0.97, 60) * T
        direct = {d: [trip_dv(r, d, t) for t in ts] for d in leads}
        ph = {d: [phasing(r, d, k) for k in range(1, 13)] for d in leads}
        curves[name] = (ts, direct, ph)

    print("\nTime just to burn that delta-v, at different thrust-to-mass ratios:")
    accels = {"electric (Hall thruster), 0.0002 m/s^2": 2e-4,
              "small chemical thruster, 0.05 m/s^2": 0.05,
              "launch-vehicle class engine, 5 m/s^2": 5.0}
    print(f"{'delta-v':>10} " + " ".join(f"{k.split(',')[0]:>28}" for k in accels))
    for dv in (10, 100, 500, 1500, 3000):
        cells = []
        for acc in accels.values():
            s_ = dv / acc
            cells.append(f"{s_ / 86400:.1f} days" if s_ > 86400 else f"{s_ / 3600:.1f} h" if s_ > 3600 else f"{s_ / 60:.1f} min")
        print(f"{dv:>6} m/s " + " ".join(f"{c:>28}" for c in cells))

    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
        for ax, (name, (ts, direct, ph)) in zip(axs, curves.items()):
            for i, d in enumerate(leads):
                c = f"C{i}"
                ax.plot(ts / 3600, np.array(direct[d]) / 1e3, color=c, label=f"target {d} deg ahead")
                pts = [(t, dv) for t, dv, alt in ph[d] if alt > 200]
                if pts:
                    pt, pd = zip(*pts)
                    ax.plot(np.array(pt) / 3600, np.array(pd) / 1e3, "o", color=c, ms=4)
            ax.set_xscale("log"); ax.set_yscale("log")
            ax.set_xlabel("trip time (hours)"); ax.set_title(name)
            ax.grid(True, which="both", alpha=0.3)
        axs[0].set_ylabel("total delta-v (km/s)")
        axs[0].legend(fontsize=8)
        fig.suptitle("Reaching a satellite on the same orbit. Lines: direct transfers. Dots: phasing orbits.")
        fig.savefig(a.plot, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
