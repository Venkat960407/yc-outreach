# Odometry Square Check (Innate OS skill)

A skill for [Innate](https://innate.bot)'s MARS robot that measures how much its wheel odometry drifts, so you know when a new floor or worn wheels are throwing off navigation.

## What it does

1. Drives a square (0.5 m sides by default), steering by **odometry only**. By its own count, the robot ends exactly where it started.
2. Meanwhile it records where the **map localizer** (lidar) thinks the robot is.
3. At the end it compares the two:
   - **Drift:** how far the map says the robot really ended from where odometry thinks it ended
   - **Heading drift:** how many degrees odometry is off after four 90° turns
   - **Distance scale:** on the straight legs, map distance divided by wheel distance (1.000 is perfect)
4. Returns a plain-English summary the agent can say out loud, plus the numbers as structured data, and a verdict: good, fair, or needs calibration.

Example output:

> Square done (2.0 m path). Odometry thinks I'm 0.4 cm from the start, but the map says 10.8 cm. Odometry drift: 10.8 cm (5.4% of distance) and -17.1 degrees. On straight legs the map measured 1.000x what the wheels counted. Verdict: needs calibration.

## Install

Copy `odometry_square_check.py` into `workspace/custom_skills/`. The brain hot-reloads it, and an agent can call it as `local/odometry_square_check`. Run it in sim first.

## Why a square, and why the per-leg check

This is a classic robotics test (it's the idea behind the UMBmark method for measuring odometry error). One thing I learned building it: **a closed square can't catch a pure distance error.** If the wheels over-count every distance by 3%, the robot drives a slightly smaller square that still closes perfectly. Turn errors do show up, because four slightly wrong turns don't close. So the skill also measures each straight leg against the map, which catches the distance error separately.

## Testing without a robot

`sim_test.py` runs the skill against a tiny fake robot (no ROS, no Innate OS) whose odometry has known errors, and checks the skill catches them:

```
perfect wheels                           drift=  0.0 cm  heading= +0.0 deg  scale=1.000  -> good
wheels over-count distance 3%            drift=  0.0 cm  heading= +0.0 deg  scale=0.971  -> fair
turns over-counted 5% (slippery floor)   drift= 10.8 cm  heading=-17.1 deg  scale=1.000  -> needs calibration
both                                     drift= 10.4 cm  heading=-17.1 deg  scale=0.971  -> needs calibration
PASS
```

The numbers line up with the math: a 5% turn error over four 90° turns is 18°, and 1 / 1.03 = 0.971.

## Not yet tested

On real MARS hardware or in sim.innate.bot. The skill uses only `Mobility.send_cmd_vel`, `Odometry`, and `Pose`, following the same patterns as the shipped `turn_in_place.py`, but it should be run in the simulator before trusting it.

## How this was made

Venkat Narayanan built this with Claude in an afternoon. The controller (hold heading with a P loop, slow down near the end of each leg, P-controlled turns) is the same approach used for autonomous routines on VEX robots.
