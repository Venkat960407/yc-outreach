# Rep counter from an accelerometer

A small script that counts reps and estimates bar speed (mean concentric velocity) from a
wrist- or bar-mounted accelerometer. I built it after seeing Fort's strength-tracking wearable,
to learn how hard the problem is.

```
pip install numpy scipy
python repcount.py --demo          # 10 generated sets with known answers
python repcount.py my_set.csv      # columns: t, ax, ay, az  (m/s^2, gravity included)
```

## How it works

1. **Find "down."** A slow low-pass filter on the raw acceleration gives the gravity direction,
   so the script works however the sensor is rotated on the wrist.
2. **Vertical acceleration.** Project acceleration onto gravity, subtract g, and filter at 4 Hz.
3. **Velocity with drift removed.** Integrate to velocity. Integration drift is the usual killer,
   so velocity is pinned to zero at every turnaround (the top and bottom of each rep, where the
   bar stops for a moment) and the error is spread linearly across each phase.
4. **Reps.** Each upward phase above 0.15 m/s peak counts as one rep.

## Results on generated data

Each test set has a known number of reps and known speeds, a 25° tilted sensor, fatigue
(each rep about 4% slower), and sensor noise.

| set | true reps | found | true mean v | est. mean v | error |
|---|---|---|---|---|---|
| 0 | 5 | 5 | 0.46 | 0.47 | 1% |
| 1 | 8 | 8 | 0.58 | 0.60 | 4% |
| 2 | 3 | 3 | 0.30 | 0.33 | 10% |
| 3 | 10 | 10 | 0.49 | 0.54 | 11% |
| 4 | 6 | 6 | 0.80 | 0.82 | 2% |
| 5 | 12 | 11 | 0.35 | 0.40 | 12% |
| 6 | 4 | 4 | 0.72 | 0.68 | 5% |
| 7 | 7 | 7 | 0.46 | 0.47 | 3% |
| 8 | 9 | 9 | 0.32 | 0.37 | 15% |
| 9 | 5 | 5 | 0.92 | 0.84 | 9% |

Rep count was exact on 9 of 10 sets, and median speed error was 7%.

## What it gets wrong

- **Slow reps read too fast** (10 to 15% high under 0.35 m/s), because drift has longer to build
  up within one phase.
- **It missed one rep** in a 12-rep slow set where two reps ran together without a clear pause.
- **This is only tested on generated data.** Real wrist data adds hand rotation and arm swing
  that a bar-mounted sensor doesn't see. The next step would be a few real sets with a phone
  strapped to the bar, checked against video.

I also tried resetting velocity whenever the sensor looked still. It made results worse (reps
were missed when the pause detector misfired), so it's not in this version.

Built with help from Claude.
