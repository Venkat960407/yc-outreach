"""Bimanual workspace map for the Almond Axol.

Answers a practical setup question: where should I put the table, and the objects
on it, so that BOTH arms can reach them?

It reads the Axol URDF from the open-source SDK, samples random joint angles
within each joint's limits, runs forward kinematics to find where each gripper
ends up, and builds a voxel map of what the left arm, right arm, and both arms
can reach. Then it slices that map at different heights to find the table
height with the most two-arm workspace.

Only needs numpy and matplotlib. No robot, no JAX, no ROS.

Usage:
    python axol_workspace.py path/to/axol.urdf
    python axol_workspace.py path/to/axol.urdf --samples 400000 --voxel 0.02
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET

import numpy as np


# ---------- URDF forward kinematics (just the parts we need) ----------

def rpy_to_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def axis_angle(axis, angles):
    """Batch of rotation matrices about one fixed axis (Rodrigues' formula)."""
    a = np.asarray(axis, float); a = a / np.linalg.norm(a)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    s, c = np.sin(angles)[:, None, None], np.cos(angles)[:, None, None]
    return np.eye(3) + s * K + (1 - c) * (K @ K)


class Chain:
    """Fixed and revolute joints from the root link down to one end link."""

    def __init__(self, urdf_path: str, end_link: str):
        joints = {}
        for j in ET.parse(urdf_path).getroot().iter("joint"):
            o = j.find("origin")
            xyz = np.array([float(v) for v in o.get("xyz", "0 0 0").split()]) if o is not None else np.zeros(3)
            rpy = [float(v) for v in o.get("rpy", "0 0 0").split()] if o is not None else [0, 0, 0]
            ax = j.find("axis"); lim = j.find("limit")
            joints[j.find("child").get("link")] = dict(
                name=j.get("name"), type=j.get("type"), parent=j.find("parent").get("link"),
                xyz=xyz, R=rpy_to_matrix(*rpy),
                axis=[float(v) for v in ax.get("xyz").split()] if ax is not None else [0, 0, 1],
                lower=float(lim.get("lower")) if lim is not None else 0.0,
                upper=float(lim.get("upper")) if lim is not None else 0.0)
        chain, link = [], end_link
        while link in joints:
            chain.append(joints[link]); link = joints[link]["parent"]
        self.joints = chain[::-1]
        self.revolute = [j for j in self.joints if j["type"] == "revolute"]

    def sample(self, n, rng):
        return np.stack([rng.uniform(j["lower"], j["upper"], n) for j in self.revolute], axis=1)

    def positions(self, q):
        """End-link positions (n, 3) for a batch of joint configurations q (n, dof)."""
        n = q.shape[0]
        R = np.broadcast_to(np.eye(3), (n, 3, 3)).copy(); p = np.zeros((n, 3)); k = 0
        for j in self.joints:
            p = p + R @ j["xyz"]
            R = R @ j["R"]
            if j["type"] == "revolute":
                R = R @ axis_angle(j["axis"], q[:, k]); k += 1
        return p


# ---------- workspace analysis ----------

def voxelize(points, origin, size):
    return {tuple(v) for v in np.floor((points - origin) / size).astype(int)}


def analyze(urdf, samples=3_000_000, voxel=0.03, seed=0):
    rng = np.random.default_rng(seed)
    left, right = Chain(urdf, "left_gripper"), Chain(urdf, "right_gripper")
    L = left.positions(left.sample(samples, rng))
    R = right.positions(right.sample(samples, rng))
    origin = np.minimum(L.min(0), R.min(0))
    vl, vr = voxelize(L, origin, voxel), voxelize(R, origin, voxel)
    both = vl & vr

    # Shoulder = first revolute joint; reach = farthest gripper point from it.
    sl, sr = first_revolute_position(left), first_revolute_position(right)
    reach_l = np.linalg.norm(L - sl, axis=1).max()
    reach_r = np.linalg.norm(R - sr, axis=1).max()

    # Two-arm area at each height slice, counting only space in front of the
    # robot (x > 0), since that's where a table goes.
    front = {v for v in both if origin[0] + (v[0] + 0.5) * voxel > 0}
    zs = sorted({v[2] for v in front})
    area = {z: sum(1 for v in front if v[2] == z) * voxel ** 2 for z in zs}
    best_z = max(area, key=area.get)
    return dict(L=L, R=R, vl=vl, vr=vr, both=both, origin=origin, voxel=voxel,
                reach=(reach_l, reach_r), shoulders=(sl, sr), area=area, best_z=best_z,
                dof=(len(left.revolute), len(right.revolute)))


def first_revolute_position(chain):
    p, R = np.zeros(3), np.eye(3)
    for j in chain.joints:
        p = p + R @ j["xyz"]; R = R @ j["R"]
        if j["type"] == "revolute":
            return p
    return p


def good_band(res, frac=0.9):
    top = res["area"][res["best_z"]]
    ok = [height_of(z, res) for z, a in res["area"].items() if a >= frac * top]
    return f"{min(ok):.2f} to {max(ok):.2f} m"


def height_of(z_index, res):
    return res["origin"][2] + (z_index + 0.5) * res["voxel"]


def plot(res, path="axol_workspace.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    vox, o = res["voxel"], res["origin"]
    zi = res["best_z"]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.6), constrained_layout=True)
    colors = {"left": "#4C8BF5", "right": "#F5A04C", "both": "#2E9E5B"}

    def top_slice(ax, z_index, title):
        for name, s in (("left", res["vl"]), ("right", res["vr"]), ("both", res["both"])):
            pts = np.array([v for v in s if v[2] == z_index])
            if len(pts):
                ax.scatter(o[1] + (pts[:, 1] + .5) * vox, o[0] + (pts[:, 0] + .5) * vox,
                           s=6, marker="s", c=colors[name], linewidths=0)
        for sh in res["shoulders"]:
            ax.plot(sh[1], sh[0], "k^", ms=8)
        ax.set_title(title); ax.set_xlabel("y, left (m)"); ax.set_ylabel("x, forward (m)")
        ax.invert_xaxis(); ax.set_aspect("equal"); ax.grid(alpha=.3)

    best_h = height_of(zi, res)
    top_slice(axes[0], zi, f"Top view at z = {best_h:.2f} m (peak two-arm area)")
    lower = min(res["area"]); low_h = height_of(lower + (zi - lower) // 2, res)
    top_slice(axes[1], lower + (zi - lower) // 2, f"Top view at z = {low_h:.2f} m")

    zs = sorted(res["area"])
    axes[2].plot([res["area"][z] for z in zs], [height_of(z, res) for z in zs], color=colors["both"], lw=2)
    axes[2].axhline(best_h, ls="--", color="gray")
    axes[2].set_xlabel("two-arm area in front of robot (m²)"); axes[2].set_ylabel("height z (m)")
    axes[2].set_title("Where both arms can work, by height"); axes[2].grid(alpha=.3)

    fig.legend(handles=[Patch(color=colors["left"], label="left arm only"),
                        Patch(color=colors["right"], label="right arm only"),
                        Patch(color=colors["both"], label="both arms"),
                        plt.Line2D([], [], marker="^", color="k", ls="", label="shoulder")],
               loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Almond Axol bimanual workspace (Monte Carlo over joint limits)", fontsize=13)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    return path


def summary(res):
    rl, rr = res["reach"]; v3 = res["voxel"] ** 3
    best_h = height_of(res["best_z"], res)
    return "\n".join([
        f"Joints per arm:          {res['dof'][0]} (left), {res['dof'][1]} (right)",
        f"Max reach from shoulder: {rl*1000:.0f} mm (left), {rr*1000:.0f} mm (right)",
        f"Left-arm volume:         {len(res['vl'])*v3:.3f} m³",
        f"Right-arm volume:        {len(res['vr'])*v3:.3f} m³",
        f"Two-arm volume:          {len(res['both'])*v3:.3f} m³ "
        f"({100*len(res['both'])/len(res['vl'] | res['vr']):.0f}% of total)",
        f"Shared area in front of the robot peaks at {res['area'][res['best_z']]:.2f} m²",
        f"Heights within 90% of that peak: {good_band(res)} "
        f"(z measured from the URDF root; shoulders sit at {res['shoulders'][0][2]:.2f} m)",
    ])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    ap.add_argument("--samples", type=int, default=3_000_000)
    ap.add_argument("--voxel", type=float, default=0.03, help="voxel size in meters")
    ap.add_argument("--out", default="axol_workspace.png")
    a = ap.parse_args()
    res = analyze(a.urdf, a.samples, a.voxel)
    print(summary(res))
    print("Saved", plot(res, a.out))
