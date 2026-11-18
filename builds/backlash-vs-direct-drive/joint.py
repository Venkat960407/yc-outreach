"""What does gearbox backlash do to a robot joint under PID, compared with direct drive?

One robot link (an arm segment) driven by a motor, either through a gearbox with backlash (a small
dead zone where the motor turns but the output doesn't) and some friction, or directly with no
gearbox. A PID controller reads the OUTPUT angle (an encoder on the joint) and tries to follow
a target.

Two tests:
  1. Hold a position against a small disturbance (does it settle, or hunt back and forth?)
  2. Track a smooth back-and-forth motion (how big is the error, especially at each reversal?)

Usage:
  python joint.py                 # prints the tables
  python joint.py --plot out.png  # also saves the comparison plot
"""
import argparse
import numpy as np

DT = 0.0005   # 2 kHz control and simulation


def simulate(backlash_deg, gear=True, test="track", t_end=4.0, kp=None, kd=None, ki=None,
             encoder_counts=2**14, seed=0):
    rng = np.random.default_rng(seed)
    # plant: link inertia and gravity-free (horizontal), with output-side viscous friction
    J_link = 0.02            # kg m^2
    b_link = 0.02
    if gear:
        N, J_motor, b_motor, coulomb = 30.0, 2e-5, 1e-4, 0.15   # 30:1 gearbox, output friction 0.15 Nm
        k_mesh = 400.0                                       # gear mesh stiffness, Nm/rad (output side)
        tau_max = 15.0                                       # small motor x 30
    else:
        N, J_motor, b_motor, coulomb = 1.0, 0.004, 1e-3, 0.02   # big flat motor, its own inertia
        k_mesh = None                                        # rigid
        tau_max = 12.0                                       # direct-drive motor, similar output torque
    gap = np.radians(backlash_deg) / 2 if gear else 0.0
    kp = 60.0 if kp is None else kp
    kd = 3.0 if kd is None else kd
    ki = 30.0 if ki is None else ki
    q_m = q_l = w_m = w_l = 0.0     # motor angle (output-referred) and link angle
    integ = 0.0
    n = int(t_end / DT)
    log = np.zeros((n, 3))
    res = 2 * np.pi / encoder_counts
    prev_meas = 0.0
    dfilt = 0.0
    alpha = DT / (DT + 1 / (2 * np.pi * 100))       # 100 Hz low-pass on the derivative
    for i in range(n):
        t = i * DT
        if test == "track":
            target = np.radians(20) * np.sin(2 * np.pi * 0.5 * t)
            dist = 0.0
        else:
            target = np.radians(10) * min(t / 0.5, 1.0)     # move to 10 deg, then hold
            dist = 0.3 if 1.0 < t < 1.05 else 0.0           # a short bump
        meas = np.round(q_l / res) * res                    # joint encoder
        e = target - meas
        integ = np.clip(integ + e * DT, -0.05, 0.05)
        dfilt += alpha * ((meas - prev_meas) / DT - dfilt)
        prev_meas = meas
        u = np.clip(kp * e + ki * integ - kd * dfilt, -tau_max, tau_max)   # output-side torque
        fric = coulomb * np.tanh(w_l / 0.01)
        if not gear:
            # direct drive: motor and link are one rigid body
            a_l = (u - (b_link + b_motor) * w_l - fric + dist) / (J_link + J_motor)
            w_l += a_l * DT; q_l += w_l * DT
        else:
            delta = q_m - q_l
            if delta > gap:
                t_mesh = k_mesh * (delta - gap) + 0.5 * (w_m - w_l)
            elif delta < -gap:
                t_mesh = k_mesh * (delta + gap) + 0.5 * (w_m - w_l)
            else:
                t_mesh = 0.0
            Jm = J_motor * N * N                              # reflected motor inertia
            a_m = (u - t_mesh - b_motor * N * N * w_m) / Jm
            a_l = (t_mesh - b_link * w_l - fric + dist) / J_link
            w_m += a_m * DT; q_m += w_m * DT
            w_l += a_l * DT; q_l += w_l * DT
        log[i] = (t, target, q_l)
    return log


def stats(log, test):
    t, tgt, q = log.T
    err = np.degrees(q - tgt)
    if test == "track":
        m = t > 1.0
        rms = np.sqrt(np.mean(err[m] ** 2))
        # error right after each reversal (target velocity sign change), within 50 ms
        v = np.gradient(tgt)
        rev = np.where(np.diff(np.sign(v)) != 0)[0]
        peaks = [np.abs(err[r:r + 100]).max() for r in rev if t[r] > 1.0]
        return rms, max(peaks) if peaks else np.nan
    m = t > 2.0
    # hunting: peak-to-peak wobble after the disturbance has died out
    return np.abs(err[m]).mean(), np.ptp(err[m])


def tune(backlash_deg, gear):
    """Grid-search PID gains for this joint: lowest tracking error among gain sets that hold
    position without wobbling more than 0.2 deg."""
    best = None
    for kp in (30, 60, 120, 240):
        for kd in (0.5, 1.0, 2.0, 3.0):
            for ki in (0, 30, 100):
                r, p = stats(simulate(backlash_deg, gear, "track", t_end=3.0, kp=kp, kd=kd, ki=ki), "track")
                if not np.isfinite(r):
                    continue
                me, pp = stats(simulate(backlash_deg, gear, "hold", t_end=3.0, kp=kp, kd=kd, ki=ki), "hold")
                score = r if pp < 0.2 else r + 100
                if best is None or score < best[0]:
                    best = (score, kp, kd, ki)
    return best[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot")
    a = ap.parse_args()
    cases = [("direct drive", 0.0, False)] + [(f"gearbox, {b} deg backlash", b, True) for b in (0.0, 0.5, 1.0, 2.0)]
    print("Each joint gets its own best PID gains (grid search):")
    print(f"{'joint':>28} | {'gains kp/kd/ki':>14} | {'tracking RMS':>12} | {'worst at reversal':>17} | {'hold: wobble p-p':>16}")
    logs = {}
    for name, b, g in cases:
        kp, kd, ki = tune(b, g)
        lt = simulate(b, g, "track", kp=kp, kd=kd, ki=ki); lh = simulate(b, g, "hold", kp=kp, kd=kd, ki=ki)
        logs[name] = lt
        r, p = stats(lt, "track"); me, pp = stats(lh, "hold")
        print(f"{name:>28} | {kp:>5}/{kd}/{ki:<4} | {r:>8.3f} deg | {p:>13.3f} deg | {pp:>12.3f} deg")
    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 4))
        for name in ("direct drive", "gearbox, 0.0 deg backlash", "gearbox, 2.0 deg backlash"):
            t, tgt, q = logs[name].T
            m = (t > 1.4) & (t < 2.6)
            ax.plot(t[m], np.degrees(q - tgt)[m], label=name)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_xlabel("time (s)"); ax.set_ylabel("tracking error (deg)")
        ax.set_title("Tracking a 20 deg, 0.5 Hz back-and-forth motion (each joint with its best gains)")
        ax.legend(fontsize=8); fig.savefig(a.plot, dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()
