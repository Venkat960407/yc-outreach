from laptop_grader import Battery, Disk, grade

ok = [Disk("ssd", 512, True)]


def test_healthy_laptop_is_A():
    assert grade(Battery(True, 50000, 48000, 200), ok, 16)[0] == "A"


def test_worn_battery_is_C():
    g, why = grade(Battery(True, 50000, 37000, 400), ok, 16)
    assert g == "C" and "74.0%" in why[0]


def test_dead_battery_is_D():
    assert grade(Battery(True, 50000, 25000, 900), ok, 16)[0] == "D"


def test_failing_disk_beats_good_battery():
    assert grade(Battery(True, 50000, 49000, 50), [Disk("hdd", 1000, False)], 16)[0] == "D"


def test_unknown_disk_health_is_B():
    assert grade(Battery(True, 50000, 49000, 50), [Disk("ssd", 256, None)], 16)[0] == "B"


def test_low_ram_is_C():
    assert grade(Battery(True, 50000, 49000, 50), ok, 4)[0] == "C"


def test_8gb_ram_reported_as_7_7_is_fine():
    assert grade(Battery(True, 50000, 49000, 50), ok, 7.7)[0] == "A"


def test_high_cycle_count_is_C():
    assert grade(Battery(True, 50000, 46000, 1200), ok, 16)[0] == "C"


def test_desktop_without_battery_is_not_penalized():
    g, why = grade(Battery(), ok, 16)
    assert g == "A" and "All checks passed." in why
