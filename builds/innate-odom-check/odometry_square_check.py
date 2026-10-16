# SPDX-License-Identifier: Apache-2.0
"""Odometry square check for MARS.

Drop this file into workspace/custom_skills/ and the brain picks it up as
local/odometry_square_check.
"""
import math
import time

from pydantic import BaseModel

from innate import Mobility, Odometry, Pose, Skill, SkillOutput, SkillReturn

# Gains for the simple P controllers. Slow and gentle on purpose: this skill
# has no obstacle awareness, so it should only run in a clear area.
DRIVE_SPEED = 0.15        # m/s cruise speed
HEADING_KP = 2.0          # rad/s of correction per rad of heading error
TURN_KP = 1.5             # rad/s per rad of remaining turn
MAX_TURN_RATE = 0.8       # rad/s
DIST_TOL = 0.01           # m
ANGLE_TOL = math.radians(1.5)
TICK = 0.05               # s


def wrap(a: float) -> float:
    """Wrap an angle to [-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


def drive_command(traveled: float, side: float, heading_err: float) -> tuple[float, float]:
    """Forward speed and turn rate while driving one side of the square.

    Slows down over the last 10 cm so it doesn't overshoot, and steers back
    toward the side's starting heading so small wheel differences don't add up.
    """
    remaining = side - traveled
    speed = DRIVE_SPEED * min(1.0, max(remaining / 0.10, 0.25))
    turn = max(-MAX_TURN_RATE, min(MAX_TURN_RATE, -HEADING_KP * heading_err))
    return speed, turn


def turn_command(remaining: float) -> float:
    """Turn rate for an in-place turn, slowing near the target angle."""
    rate = TURN_KP * remaining
    rate = math.copysign(max(abs(rate), 0.15), remaining)  # don't stall near the end
    return max(-MAX_TURN_RATE, min(MAX_TURN_RATE, rate))


class SquareCheckResult(BaseModel):
    """Structured payload so other skills or agents can act on the numbers."""

    side_m: float
    odom_end_error_m: float
    map_end_error_m: float | None
    drift_m: float | None
    drift_heading_deg: float | None
    drift_pct_of_path: float | None
    distance_scale: float | None
    """Map distance / odometry distance over the straight legs. 1.00 is perfect;
    1.03 means the wheels under-count distance by about 3%."""
    verdict: str


def compare(o0, o1, p0, p1, side_m) -> SquareCheckResult:
    """Odometry's idea of the net move vs the localizer's.

    The square closes by odometry's own count, so odometry's end error is
    small by construction. Any net move the localizer sees on top of that is
    motion odometry failed to count: drift.
    """
    odom_err = math.hypot(o1[0] - o0[0], o1[1] - o0[1])
    if p0 is None or p1 is None:
        return SquareCheckResult(side_m=side_m, odom_end_error_m=round(odom_err, 3),
                                 map_end_error_m=None, drift_m=None, drift_heading_deg=None,
                                 drift_pct_of_path=None, distance_scale=None,
                                 verdict="no map reference")
    map_err = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    # Express both net moves in their own start frames, then compare.
    def local(a0, a1):
        dx, dy = a1[0] - a0[0], a1[1] - a0[1]
        c, s = math.cos(-a0[2]), math.sin(-a0[2])
        return dx * c - dy * s, dx * s + dy * c, wrap(a1[2] - a0[2])
    ox, oy, oth = local(o0, o1)
    px, py, pth = local(p0, p1)
    drift = math.hypot(px - ox, py - oy)
    dth = math.degrees(wrap(pth - oth))
    pct = 100 * drift / (4 * side_m)
    verdict = ("good" if pct < 2 and abs(dth) < 3 else
               "fair" if pct < 5 and abs(dth) < 8 else "needs calibration")
    return SquareCheckResult(side_m=side_m, odom_end_error_m=round(odom_err, 3),
                             map_end_error_m=round(map_err, 3), drift_m=round(drift, 3),
                             drift_heading_deg=round(dth, 1), drift_pct_of_path=round(pct, 1),
                             distance_scale=None, verdict=verdict)


def describe(r: SquareCheckResult) -> str:
    if r.drift_m is None:
        return (f"Square done. Odometry thinks I'm {r.odom_end_error_m*100:.1f} cm from the start. "
                "No map pose was available, so I can't measure drift myself: compare my real "
                "position with a mark on the floor at the start spot.")
    return (f"Square done ({4*r.side_m:.1f} m path). Odometry thinks I'm "
            f"{r.odom_end_error_m*100:.1f} cm from the start, but the map says "
            f"{r.map_end_error_m*100:.1f} cm. Odometry drift: {r.drift_m*100:.1f} cm "
            f"({r.drift_pct_of_path:.1f}% of distance) and {r.drift_heading_deg:+.1f} degrees. "
            + (f"On straight legs the map measured {r.distance_scale:.3f}x what the wheels counted. "
               if r.distance_scale else "")
            + f"Verdict: {r.verdict}.")


class OdometrySquareCheck(Skill):
    """Check how much the robot's wheel odometry drifts. Drives a square
    (default 0.5 m sides, turning left) using odometry, so by its own count it
    ends where it started. Then it compares that with where the map localizer
    (lidar) says it really ended. The gap between the two is the drift. Use
    this on a new floor surface, when navigation seems off, or when asked to
    check calibration. Needs about 1 m x 1 m of clear floor and works best
    with a map loaded."""

    mobility: Mobility
    odom: Odometry
    pose: Pose | None
    """Map-frame pose from the localizer: the independent reference."""

    def guidelines(self):
        return ("Only run this in a clear area at least 1 m x 1 m. Drift is measured "
                "against the map pose, so load a map first. With no map, ask the user to "
                "mark the start spot on the floor and compare it with where the robot stops.")

    def execute(self, side_m: float = 0.5) -> SkillReturn:
        if not 0.2 <= side_m <= 1.0:
            self.fail("side_m must be between 0.2 and 1.0 meters")
        o0 = (self.odom.x, self.odom.y, self.odom.theta)
        p0 = (self.pose.x, self.pose.y, self.pose.theta) if self.pose is not None else None
        heading = o0[2]
        odo_legs, map_legs = 0.0, 0.0
        try:
            for _ in range(4):
                a, b = self._xy(self.odom), self._xy(self.pose)
                self._drive_straight(side_m, heading)
                odo_legs += math.dist(a, self._xy(self.odom))
                if b is not None and self.pose is not None:
                    map_legs += math.dist(b, self._xy(self.pose))
                heading = wrap(heading + math.pi / 2)
                self._turn_to(heading)
        finally:
            self.mobility.stop()
        self.sleep(0.5)  # let the localizer settle

        o1 = (self.odom.x, self.odom.y, self.odom.theta)
        p1 = (self.pose.x, self.pose.y, self.pose.theta) if self.pose is not None else None
        r = compare(o0, o1, p0, p1, side_m)
        if map_legs > 0 and odo_legs > 0:
            r.distance_scale = round(map_legs / odo_legs, 3)
            if abs(r.distance_scale - 1) > 0.02 and r.verdict == "good":
                r.verdict = "fair"
            if abs(r.distance_scale - 1) > 0.05:
                r.verdict = "needs calibration"
        return SkillOutput(describe(r), r)

    @staticmethod
    def _xy(p):
        return None if p is None else (p.x, p.y)

    def _drive_straight(self, side: float, heading: float) -> None:
        x0, y0 = self.odom.x, self.odom.y
        deadline = time.time() + side / (DRIVE_SPEED * 0.25) + 5
        while True:
            traveled = math.hypot(self.odom.x - x0, self.odom.y - y0)
            if traveled >= side - DIST_TOL:
                return
            if time.time() > deadline:
                self.fail(f"Stuck: drove only {traveled:.2f} of {side:.2f} m")
            v, w = drive_command(traveled, side, wrap(self.odom.theta - heading))
            self.mobility.send_cmd_vel(linear_x=v, angular_z=w, duration=0.5)
            self.sleep(TICK)

    def _turn_to(self, target: float) -> None:
        deadline = time.time() + 10
        while True:
            remaining = wrap(target - self.odom.theta)
            if abs(remaining) < ANGLE_TOL:
                self.mobility.stop()
                return
            if time.time() > deadline:
                self.fail(f"Stuck turning: {math.degrees(remaining):.0f} degrees left")
            self.mobility.send_cmd_vel(angular_z=turn_command(remaining), duration=0.5)
            self.sleep(TICK)
