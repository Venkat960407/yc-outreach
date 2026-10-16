"""Offline test: runs the skill against a tiny fake robot, no ROS or Innate OS.

The fake robot moves as a simple unicycle. Its wheel odometry over-counts
distance by `scale_err` and over-counts turning by `turn_err`, like a robot on
a slippery or carpeted floor. The fake localizer reports the true pose.

    python sim_test.py
"""
import math
import sys
import types


# ---- a stand-in for the `innate` package, just enough to run the skill ----
class SkillFailed(Exception):
    pass


class FakeWorld:
    def __init__(self, scale_err=0.0, turn_err=0.0):
        self.true = [0.0, 0.0, 0.0]   # x, y, theta
        self.odo = [0.0, 0.0, 0.0]
        self.v = self.w = 0.0
        self.scale_err, self.turn_err = scale_err, turn_err
        self.t = 0.0

    def step(self, dt):
        for p, k_v, k_w in ((self.true, 1.0, 1.0), (self.odo, 1 + self.scale_err, 1 + self.turn_err)):
            p[0] += self.v * k_v * math.cos(p[2]) * dt
            p[1] += self.v * k_v * math.sin(p[2]) * dt
            p[2] = (p[2] + self.w * k_w * dt + math.pi) % (2 * math.pi) - math.pi
        self.t += dt


class P:
    def __init__(self, arr):
        self.x, self.y, self.theta = arr


def make_innate(world):
    m = types.ModuleType("innate")

    class Skill:
        def __init__(self):
            pass

        @property
        def odom(self):
            return P(world.odo)

        @property
        def pose(self):
            return P(world.true)

        def sleep(self, dt):
            world.step(dt)

        def fail(self, msg):
            raise SkillFailed(msg)

    class Mobility:
        def send_cmd_vel(self, linear_x=0.0, angular_z=0.0, duration=None):
            world.v, world.w = linear_x, angular_z

        def stop(self):
            world.v = world.w = 0.0

    class SkillOutput:
        def __init__(self, message, data=None):
            self.message, self.data = message, data

    m.Skill, m.Mobility, m.SkillOutput = Skill, Mobility, SkillOutput
    m.Odometry = m.Pose = object
    m.SkillReturn = object
    return m


def run(scale_err, turn_err):
    world = FakeWorld(scale_err, turn_err)
    sys.modules["innate"] = make_innate(world)
    sys.modules.pop("odometry_square_check", None)
    import odometry_square_check as sq
    import time as _time
    sq.time = types.SimpleNamespace(time=lambda: world.t)  # use sim time for deadlines
    skill = sq.OdometrySquareCheck()
    skill.mobility = sys.modules["innate"].Mobility()
    out = skill.execute(0.5)
    return out


if __name__ == "__main__":
    cases = [("perfect wheels", 0.0, 0.0),
             ("wheels over-count distance 3%", 0.03, 0.0),
             ("turns over-counted 5% (slippery floor)", 0.0, 0.05),
             ("both", 0.03, 0.05)]
    ok = True
    for name, se, te in cases:
        r = run(se, te).data
        print(f"{name:<40} drift={r.drift_m*100:5.1f} cm  heading={r.drift_heading_deg:+5.1f} deg  "
              f"scale={r.distance_scale:.3f}  -> {r.verdict}")
        if se == te == 0.0:
            ok &= r.verdict == "good"
        else:
            ok &= r.verdict != "good"
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
