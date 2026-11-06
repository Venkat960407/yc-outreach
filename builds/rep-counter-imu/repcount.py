"""Count reps and estimate bar speed from a wrist or bar-mounted accelerometer.

Input: CSV with columns t (seconds), ax, ay, az (m/s^2, gravity included).
Output: rep count, and for each rep the peak and mean concentric (lifting) velocity in m/s.

How it works:
1. Estimate gravity with a slow low-pass filter and project acceleration onto it, which gives
   vertical acceleration no matter how the sensor is rotated on the wrist or bar.
2. Low-pass the vertical signal and find reps as alternating up/down swings, using hysteresis
   so sensor noise and small wobbles don't count as extra reps.
3. Integrate vertical acceleration to velocity, then remove drift by forcing velocity to zero at
   each turnaround (the top and bottom of a rep, where the bar briefly stops).

Usage:
  python repcount.py set.csv
  python repcount.py --demo        # runs on generated sets with known answers
"""
import argparse, csv, sys
import numpy as np
from scipy.signal import butter, filtfilt

G = 9.81


def lowpass(x, fs, hz, order=2):
    b, a = butter(order, hz / (fs / 2))
    return filtfilt(b, a, x, axis=0)


def vertical_accel(t, acc):
    fs = 1 / np.median(np.diff(t))
    grav = lowpass(acc, fs, 0.3)                      # slow part is gravity
    gdir = grav / np.linalg.norm(grav, axis=1, keepdims=True)
    a_vert = np.einsum("ij,ij->i", acc, gdir) - G     # along gravity, minus gravity itself
    return fs, -a_vert                                # positive = upward


def analyze(t, acc, min_rom_s=0.35):
    fs, av = vertical_accel(t, acc)
    av = lowpass(av, fs, 4.0)
    # integrate to velocity, then position, removing linear drift over the whole set
    v = np.cumsum(av) / fs
    v -= np.polyval(np.polyfit(t, v, 1), t)
    # turnarounds are where velocity crosses zero; keep only crossings far enough apart
    sign = np.sign(v)
    zc = np.where(np.diff(sign) != 0)[0]
    keep = [zc[0]] if len(zc) else []
    for z in zc[1:]:
        if (z - keep[-1]) / fs >= min_rom_s:
            keep.append(z)
    # re-zero velocity between each pair of turnarounds (zero-velocity update)
    vz = v.copy()
    for a, b in zip(keep[:-1], keep[1:]):
        seg = slice(a, b + 1)
        vz[seg] = v[seg] - np.linspace(v[a], v[b], b - a + 1)
    reps = []
    for a, b in zip(keep[:-1], keep[1:]):
        seg = vz[a:b + 1]
        if seg.mean() > 0:  # an upward (concentric) phase
            peak, mean = seg.max(), seg[seg > 0].mean()
            if peak > 0.15:   # ignore tiny shrugs and re-grips
                reps.append({"start": float(t[a]), "end": float(t[b]), "peak_v": float(peak),
                             "mean_v": float(mean)})
    return reps


def synth_set(n_reps, mean_v, fs=100, noise=0.25, seed=0, tilt_deg=25):
    """A set with known reps: each rep lifts ~0.5 m then lowers it, with rest between."""
    rng = np.random.default_rng(seed)
    t_all, z_all, truth = [], [], []
    t0 = 0.0
    for i in range(n_reps):
        v_i = mean_v * rng.uniform(0.85, 1.1) * (1 - 0.04 * i)     # gets slower with fatigue
        rom = rng.uniform(0.45, 0.55)
        up = rom / v_i
        down = rom / (v_i * 1.3)
        rest = rng.uniform(0.3, 0.8)
        n = int((up + down + rest) * fs)
        tt = t0 + np.arange(n) / fs
        ph = tt - t0
        z = np.where(ph < up, rom * (1 - np.cos(np.pi * ph / up)) / 2,
             np.where(ph < up + down, rom * (1 + np.cos(np.pi * (ph - up) / down)) / 2, 0.0))
        truth.append(rom / up)   # mean concentric velocity
        t_all.append(tt); z_all.append(z); t0 = tt[-1] + 1 / fs
    t = np.concatenate(t_all); z = np.concatenate(z_all)
    az = np.gradient(np.gradient(z, t), t)
    # sensor frame: tilted, gravity included, plus noise
    th = np.radians(tilt_deg)
    acc = np.stack([np.sin(th) * (az + G), np.zeros_like(az), np.cos(th) * (az + G)], 1)
    acc += rng.normal(0, noise, acc.shape)
    return t, acc, truth


def demo():
    print(f"{'set':>3} {'true reps':>9} {'found':>5} {'true mean v':>11} {'est mean v':>10} {'err':>5}")
    errs, exact = [], 0
    cases = [(n, v, s) for s, (n, v) in enumerate([(5, .5), (8, .7), (3, .35), (10, .6), (6, .9),
                                                   (12, .45), (4, .8), (7, .55), (9, .4), (5, 1.0)])]
    for n, v, s in cases:
        t, acc, truth = synth_set(n, v, seed=s)
        reps = analyze(t, acc)
        est = np.mean([r["mean_v"] for r in reps]) if reps else float("nan")
        tru = float(np.mean(truth))
        e = abs(est - tru) / tru
        errs.append(e); exact += len(reps) == n
        print(f"{s:>3} {n:>9} {len(reps):>5} {tru:>11.2f} {est:>10.2f} {e:>5.0%}")
    print(f"\nrep count exact on {exact}/{len(cases)} sets; median mean-velocity error {np.median(errs):.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo or not a.csv:
        return demo()
    rows = list(csv.DictReader(open(a.csv)))
    t = np.array([float(r["t"]) for r in rows])
    acc = np.array([[float(r[k]) for k in ("ax", "ay", "az")] for r in rows])
    reps = analyze(t, acc)
    print(f"{len(reps)} reps")
    for i, r in enumerate(reps, 1):
        print(f"  rep {i}: mean {r['mean_v']:.2f} m/s, peak {r['peak_v']:.2f} m/s")


if __name__ == "__main__":
    sys.exit(main())
