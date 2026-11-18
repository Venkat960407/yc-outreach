"""Can a solar aircraft stay up all night? An energy balance by latitude and season.

A solar-powered aircraft flying at ~20 km has to collect enough energy in daylight to fly through
the night on batteries. Whether it can depends mostly on two things: how long the night is and how
low the sun is, both set by latitude and day of year.

For each latitude and day, this script integrates sunlight over 24 hours on a horizontal wing
(plus an option for wings that tilt toward the sun), subtracts the power needed to fly, and finds
the smallest battery that lets the aircraft finish the night with a reserve. A design "works" on
a given day if that battery fits in its mass budget.

The aircraft numbers are a made-up but plausible small HALE design, not any real vehicle.

Usage:
  python endurance.py                 # prints the tables
  python endurance.py --plot out.png  # also saves the feasibility map
"""
import argparse
import numpy as np

S0 = 1361.0          # solar constant, W/m^2

DESIGN = dict(
    wing_area=20.0,        # m^2 of solar cells
    cell_eff=0.24,         # solar cell efficiency
    mppt_eff=0.95,         # charge electronics
    fly_power=900.0,       # W needed to stay level at altitude (aero + payload + avionics)
    batt_wh_per_kg=400.0,  # pack-level specific energy
    batt_eff=0.95,         # round trip, one way each
    batt_budget_kg=45.0,   # mass available for batteries
    reserve=0.15,          # keep 15% at dawn
)


def sun_elevation(lat_deg, day, hour):
    """Solar elevation angle (radians) from a standard declination + hour-angle formula."""
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + day) / 365)
    ha = np.radians(15 * (hour - 12))
    lat = np.radians(lat_deg)
    s = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(ha)
    return np.arcsin(np.clip(s, -1, 1))


def irradiance_at_altitude(elev):
    """Direct sun at ~20 km. Above most of the atmosphere, so only a thin air-mass correction."""
    am = 1 / np.maximum(np.sin(elev), 0.03)
    return np.where(elev > 0, S0 * 0.97 ** (am * 0.06), 0.0)   # ~6% of sea-level air mass above 20 km


def day_energy(lat, day, d=DESIGN, tilt=False, dt_h=0.05):
    """Return (Wh collected, Wh needed overnight from battery, hours of usable sun)."""
    hours = np.arange(0, 24, dt_h)
    elev = sun_elevation(lat, day, hours)
    G = irradiance_at_altitude(elev)
    incidence = np.ones_like(elev) if tilt else np.sin(np.clip(elev, 0, None))
    p_solar = G * incidence * d["wing_area"] * d["cell_eff"] * d["mppt_eff"]
    surplus = p_solar - d["fly_power"]
    # battery state over a day starting at solar midnight; find the deficit run through the night
    e = np.cumsum(np.where(surplus > 0, surplus * d["batt_eff"], surplus / d["batt_eff"]) * dt_h)
    # night energy = largest drop from any peak to a later trough, wrapping around midnight
    e2 = np.concatenate([e, e + e[-1]])
    run_max = np.maximum.accumulate(e2)
    night = (run_max - e2).max()
    return p_solar.sum() * dt_h, night, (surplus > 0).sum() * dt_h, e[-1]


def feasible(lat, day, d=DESIGN, tilt=False):
    collected, night, sun_h, net = day_energy(lat, day, d, tilt)
    need_kg = night / (1 - d["reserve"]) / d["batt_wh_per_kg"]
    return net >= 0 and need_kg <= d["batt_budget_kg"], need_kg, net


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot")
    a = ap.parse_args()
    d = DESIGN
    print("Design:", ", ".join(f"{k}={v}" for k, v in d.items()))
    days = {"Mar 21": 80, "Jun 21": 172, "Sep 22": 265, "Dec 21": 355}
    lats = [0, 15, 30, 40, 47.6, 55]
    print("\nBattery mass needed to get through the night (kg); budget is "
          f"{d['batt_budget_kg']:.0f} kg. '-' = not enough sun even to break even:")
    print(f"{'latitude':>9} " + " ".join(f"{k:>8}" for k in days))
    for lat in lats:
        cells = []
        for day in days.values():
            ok, kg, net = feasible(lat, day)
            cells.append(f"{kg:>7.0f}{'*' if ok else ' '}" if net >= 0 else f"{'-':>8}")
        name = "47.6 Sea" if lat == 47.6 else f"{lat:.0f}"
        print(f"{name:>9} " + " ".join(cells))
    print("(* = works with this design)")

    lat_grid = np.arange(0, 66, 1.0)
    day_grid = np.arange(1, 366, 3)
    for tilt in (False, True):
        F = np.array([[feasible(l, dd, tilt=tilt)[0] for dd in day_grid] for l in lat_grid])
        year_round = lat_grid[F.all(1)]
        print(f"\n{"Ideal sun-tracking wing (upper bound)" if tilt else "Flat wing"}: flies all year up to "
              f"{year_round.max() if len(year_round) else 'no'} deg latitude; "
              f"Seattle (47 deg) works {F[47].mean():.0%} of the year.")
        if not tilt:
            Fflat = F

    print("\nWhat moves the all-year latitude limit (flat wing):")
    for name, change in [("+25% battery energy (500 Wh/kg)", dict(batt_wh_per_kg=500)),
                         ("-20% flying power", dict(fly_power=720)),
                         ("+25% wing area", dict(wing_area=25.0)),
                         ("30% cells", dict(cell_eff=0.30))]:
        dd = {**d, **change}
        F = np.array([[feasible(l, x, dd)[0] for x in day_grid] for l in lat_grid])
        yr = lat_grid[F.all(1)]
        print(f"  {name:<34} {yr.max() if len(yr) else 'none':>4} deg")

    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.imshow(Fflat, origin="lower", aspect="auto", cmap="Greens",
                  extent=[day_grid[0], day_grid[-1], lat_grid[0], lat_grid[-1]])
        ax.axhline(47.6, color="k", ls="--", lw=0.8); ax.text(5, 48.5, "Seattle", fontsize=8)
        ax.set_xlabel("day of year"); ax.set_ylabel("latitude (deg)")
        ax.set_title("Green: the example design can fly through the night (flat wing)")
        fig.savefig(a.plot, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
