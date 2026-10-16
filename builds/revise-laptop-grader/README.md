# Laptop Resale Grader

A small script for refurbishing lines. It checks a laptop's battery, disks, RAM, and CPU, then gives it a resale grade (A to D) with the reasons, and saves a JSON report so every unit can be logged.

Built for [Revise Robotics](https://www.reviserobotics.com) as an example of the kind of testing step a refurbishing robot could run on each laptop.

## Run it

```
pip install psutil
python laptop_grader.py
```

Works on Windows, macOS, and Linux. No admin rights needed on Windows or macOS. On Linux, install `smartmontools` for disk health.

## What it checks

| Check | Windows | macOS | Linux |
|---|---|---|---|
| Battery health (full charge vs design capacity) | `powercfg /batteryreport` | `ioreg AppleSmartBattery` | `/sys/class/power_supply` |
| Battery cycle count | same | same | same |
| Disk health | `Get-PhysicalDisk` HealthStatus | `smartctl` | `smartctl` |
| RAM, CPU cores, OS | `psutil` | `psutil` | `psutil` |

## How grading works

Every laptop starts at **A** and gets knocked down by the worst problem found:

| Problem | Grade |
|---|---|
| Battery 80 to 90% of design capacity | B |
| Disk health can't be read | B |
| Battery 60 to 80%, or over 1000 cycles | C |
| Under 8 GB RAM | C |
| Battery under 60% | D |
| Disk failing its health check | D |

The 80% battery line comes from common refurb practice, where batteries below that are usually flagged for replacement. All thresholds are in one function (`grade()`), so they're easy to change.

## Example output

```
RESALE GRADE: C

OS:       Windows 11
CPU:      Intel64 Family 6 Model 140 (4 cores)
RAM:      16.0 GB
Battery:  74.0% of design, 412 cycles
Disks:
  - NVMe SAMSUNG MZVLB512: 512.1 GB, health: OK

Why:
  - Battery at 74.0% of design capacity. Disclose or replace.
```

## Tests

`test_grader.py` covers the grading rules (healthy laptop, worn battery, failing disk, low RAM, desktops with no battery, and so on). Run with `pytest`.

## How this was made

Venkat Narayanan built this with Claude in an afternoon. The interesting part was picking signals that a robot can read without opening the laptop: the battery's own reported capacity and the drive's built-in health check.
