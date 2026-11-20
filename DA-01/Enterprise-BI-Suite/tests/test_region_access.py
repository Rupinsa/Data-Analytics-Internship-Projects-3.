
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from security.access_control import (
    get_allowed_regions,
    check_region_access
)


def test_north_manager():
    assert get_allowed_regions("North Manager") == ["Northwest"]
    assert check_region_access("North Manager", "Northwest")
    assert not check_region_access("North Manager", "Central")


def test_central_manager():
    assert check_region_access("Central Manager", "Central")
    assert not check_region_access("Central Manager", "France")


def test_europe_manager():
    assert check_region_access("Europe Manager", "France")
    assert not check_region_access("Europe Manager", "Germany")


def test_administrator():
    assert check_region_access("Demo Administrator", "Northwest")
    assert check_region_access("Demo Administrator", "France")


if __name__ == "__main__":
    tests = [
        test_north_manager,
        test_central_manager,
        test_europe_manager,
        test_administrator
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
        passed += 1

    print(f"\nTests passed: {passed}/{len(tests)}")
