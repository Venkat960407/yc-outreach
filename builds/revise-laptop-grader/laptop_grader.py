"""Laptop health check for refurbishing.

Collects battery wear, disk health, RAM, CPU, and OS info, then assigns a resale
grade (A/B/C/D) with the reasons behind it. Works on Windows, macOS, and Linux.
Outputs a readable report and a JSON file, so a refurbishing line can log every unit.

Usage:
    python laptop_grader.py              # prints a report, writes report.json
    python laptop_grader.py --json-only  # JSON to stdout
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict

try:
    import psutil
except ImportError:  # psutil is the only dependency
    sys.exit("Install the one dependency first:  pip install psutil")


def run(cmd: list[str], timeout: int = 30) -> str:
    """Run a command and return stdout, or '' if it fails or isn't installed."""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return out.stdout if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


# ---------- battery ----------

@dataclass
class Battery:
    present: bool = False
    design_mwh: float | None = None
    full_mwh: float | None = None
    cycles: int | None = None

    @property
    def health_pct(self) -> float | None:
        if self.design_mwh and self.full_mwh:
            return round(100 * self.full_mwh / self.design_mwh, 1)
        return None


def battery_windows() -> Battery:
    # powercfg writes an XML battery report with design and full-charge capacity.
    path = os.path.join(tempfile.gettempdir(), "battery_report.xml")
    run(["powercfg", "/batteryreport", "/xml", "/output", path])
    if not os.path.exists(path):
        return Battery()
    xml = open(path, encoding="utf-8", errors="ignore").read()
    design = re.search(r"<DesignCapacity>(\d+)</DesignCapacity>", xml)
    full = re.search(r"<FullChargeCapacity>(\d+)</FullChargeCapacity>", xml)
    cycles = re.search(r"<CycleCount>(\d+)</CycleCount>", xml)
    if not design:
        return Battery()
    return Battery(True, float(design.group(1)), float(full.group(1)) if full else None,
                   int(cycles.group(1)) if cycles else None)


def battery_mac() -> Battery:
    out = run(["ioreg", "-r", "-c", "AppleSmartBattery"])
    if not out:
        return Battery()
    def num(key):
        m = re.search(rf'"{key}" = (\d+)', out)
        return float(m.group(1)) if m else None
    design, full, cycles = num("DesignCapacity"), num("AppleRawMaxCapacity") or num("MaxCapacity"), num("CycleCount")
    return Battery(design is not None, design, full, int(cycles) if cycles else None)


def battery_linux() -> Battery:
    base = "/sys/class/power_supply"
    if not os.path.isdir(base):
        return Battery()
    for name in os.listdir(base):
        d = os.path.join(base, name)
        if open(os.path.join(d, "type")).read().strip() != "Battery":
            continue
        def read(f):
            p = os.path.join(d, f)
            return float(open(p).read().strip()) if os.path.exists(p) else None
        design = read("energy_full_design") or read("charge_full_design")
        full = read("energy_full") or read("charge_full")
        cycles = read("cycle_count")
        return Battery(True, design, full, int(cycles) if cycles else None)
    return Battery()


def get_battery() -> Battery:
    return {"Windows": battery_windows, "Darwin": battery_mac}.get(platform.system(), battery_linux)()


# ---------- disks ----------

@dataclass
class Disk:
    name: str
    size_gb: float | None
    healthy: bool | None  # None = could not read SMART


def disks_windows() -> list[Disk]:
    out = run(["powershell", "-NoProfile", "-Command",
               "Get-PhysicalDisk | Select FriendlyName,Size,HealthStatus | ConvertTo-Json"])
    if not out:
        return []
    data = json.loads(out)
    data = data if isinstance(data, list) else [data]
    return [Disk(d.get("FriendlyName", "disk"), round(d.get("Size", 0) / 1e9, 1),
                 {"Healthy": True, "Warning": False, "Unhealthy": False}.get(d.get("HealthStatus")))
            for d in data]


def disks_smartctl() -> list[Disk]:
    if not shutil.which("smartctl"):
        return []
    scan = run(["smartctl", "--scan", "-j"])
    if not scan:
        return []
    disks = []
    for dev in json.loads(scan).get("devices", []):
        info = run(["smartctl", "-H", "-i", "-j", dev["name"]])
        if not info:
            disks.append(Disk(dev["name"], None, None)); continue
        j = json.loads(info)
        cap = j.get("user_capacity", {}).get("bytes")
        disks.append(Disk(j.get("model_name", dev["name"]), round(cap / 1e9, 1) if cap else None,
                          j.get("smart_status", {}).get("passed")))
    return disks


def get_disks() -> list[Disk]:
    disks = disks_windows() if platform.system() == "Windows" else disks_smartctl()
    if disks:
        return disks
    # Fallback: we can still report size, just not health.
    total = psutil.disk_usage(os.path.abspath(os.sep)).total
    return [Disk("system disk", round(total / 1e9, 1), None)]


# ---------- grading ----------

@dataclass
class Report:
    os: str
    cpu: str
    cores: int
    ram_gb: float
    battery: dict
    disks: list[dict]
    grade: str = ""
    reasons: list[str] = field(default_factory=list)


def grade(battery: Battery, disks: list[Disk], ram_gb: float) -> tuple[str, list[str]]:
    """Start at A and knock the grade down for each problem found.

    Thresholds follow common refurb practice: batteries under 80% of design
    capacity are usually flagged for replacement, under 60% is a fail.
    """
    order = "ABCD"
    level = 0
    reasons = []

    def drop(to: str, why: str):
        nonlocal level
        level = max(level, order.index(to))
        reasons.append(why)

    h = battery.health_pct
    if not battery.present:
        reasons.append("No battery detected (desktop, or battery missing). Battery not graded.")
    elif h is None:
        drop("B", "Battery present but capacity unreadable. Test manually.")
    elif h < 60:
        drop("D", f"Battery at {h}% of design capacity. Needs replacement before resale.")
    elif h < 80:
        drop("C", f"Battery at {h}% of design capacity. Disclose or replace.")
    elif h < 90:
        drop("B", f"Battery at {h}% of design capacity.")
    if battery.cycles and battery.cycles > 1000:
        drop("C", f"Battery has {battery.cycles} charge cycles.")

    for d in disks:
        if d.healthy is False:
            drop("D", f"Disk '{d.name}' is failing its health check. Replace before resale.")
        elif d.healthy is None:
            drop("B", f"Could not read health for '{d.name}'. Run a manual disk test.")

    if ram_gb < 7.5:  # 8 GB modules report as ~7.6-7.9 GB
        drop("C", f"Only {ram_gb} GB RAM. Lower resale value.")

    if not reasons or all("not graded" in r for r in reasons):
        reasons.append("All checks passed.")
    return order[level], reasons


def collect() -> Report:
    battery = get_battery()
    disks = get_disks()
    ram_gb = round(psutil.virtual_memory().total / 1024**3, 1)
    cpu = platform.processor() or platform.machine()
    r = Report(os=f"{platform.system()} {platform.release()}", cpu=cpu,
               cores=psutil.cpu_count(logical=False) or 0, ram_gb=ram_gb,
               battery={**asdict(battery), "health_pct": battery.health_pct},
               disks=[asdict(d) for d in disks])
    r.grade, r.reasons = grade(battery, disks, ram_gb)
    return r


def render(r: Report) -> str:
    b = r.battery
    batt = "none" if not b["present"] else f"{b['health_pct']}% of design" + \
        (f", {b['cycles']} cycles" if b["cycles"] else "")
    disks = "\n".join(f"  - {d['name']}: {d['size_gb']} GB, health: "
                      f"{ {True: 'OK', False: 'FAILING', None: 'unknown'}[d['healthy']] }" for d in r.disks)
    reasons = "\n".join(f"  - {x}" for x in r.reasons)
    return (f"RESALE GRADE: {r.grade}\n\n"
            f"OS:       {r.os}\nCPU:      {r.cpu} ({r.cores} cores)\nRAM:      {r.ram_gb} GB\n"
            f"Battery:  {batt}\nDisks:\n{disks}\n\nWhy:\n{reasons}\n")


if __name__ == "__main__":
    report = collect()
    if "--json-only" in sys.argv:
        print(json.dumps(asdict(report), indent=2))
    else:
        print(render(report))
        with open("report.json", "w") as f:
            json.dump(asdict(report), f, indent=2)
        print("Saved report.json")
