"""Run fixed scripts on a synthetic tree only; never on real /proc or /sys."""
import gzip
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from portlib.parsers import config, dt, sysfs
from portlib.probes import CONFIG, DRIVERS, DT, POWER, RESOLVED, THERMAL


@unittest.skipIf(os.name == "nt", "POSIX shell execution runs in Linux/WSL")
class RemoteScriptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="portctl-shell-")
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def file(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def execute(self, script):
        for prefix in ("/proc/", "/sys/", "/dev/block/"):
            script = script.replace(prefix, str(self.root) + prefix)
        return subprocess.run(["sh", "-c", script], capture_output=True, timeout=3)

    def test_config_and_dt_binary_frames_have_real_lengths_and_cells(self):
        self.file("proc/config.gz", gzip.compress(b"CONFIG_ARM64=y\n", mtime=0))
        result = self.execute(CONFIG)
        self.assertEqual(config(result.stdout).value, {"CONFIG_ARM64": "y"})
        for key, value in (("model", b"synthetic\0"), ("compatible", b"fixture,tablet\0qcom,fixture\0"),
                           ("#address-cells", b"\0\0\0\2"), ("#size-cells", b"\0\0\0\1")):
            self.file("sys/firmware/devicetree/base/" + key, value)
        result = self.execute(DT)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = dt(result.stdout)
        self.assertEqual(parsed.status, "ok")
        self.assertEqual(parsed.value["compatible"]["value"], ["fixture,tablet", "qcom,fixture"])
        self.assertEqual(parsed.value["#size-cells"]["value"], 1)

    def test_fixed_power_attributes_and_thermal_zone_filter(self):
        for name, value in (("type", b"Battery\n"), ("status", b"Discharging\n"), ("capacity", b"75\n"),
                            ("voltage_now", b"3800000\n"), ("current_now", b"-1200\n"), ("temp", b"250\n")):
            self.file("sys/class/power_supply/battery/" + name, value)
        self.file("sys/class/power_supply/battery/serial_number", b"must-not-read")
        result = self.execute(POWER)
        parsed = sysfs(result.stdout)
        self.assertEqual(parsed.status, "ok", result.stderr)
        self.assertNotIn(b"must-not-read", result.stdout)
        self.file("sys/class/thermal/thermal_zone0/type", b"fixture\n")
        self.file("sys/class/thermal/thermal_zone0/temp", b"25000\n")
        self.file("sys/class/thermal/cooling_device0/type", b"not-a-zone\n")
        parsed = sysfs(self.execute(THERMAL).stdout)
        self.assertEqual(parsed.status, "ok")
        self.assertEqual(len(parsed.value), 2)

    def test_driver_links_are_observed_without_reading_their_contents(self):
        for name in ("input", "drm", "graphics", "backlight", "net"):
            (self.root / "sys/class" / name).mkdir(parents=True, exist_ok=True)
        device = self.root / "sys/class/input/event0/device"
        device.mkdir(parents=True)
        target = self.file("sys/bus/i2c/drivers/fixture", b"must-not-read-driver-file")
        (device / "driver").symlink_to(target)
        (device / "of_node").symlink_to(target)
        result = self.execute(DRIVERS)
        parsed = sysfs(result.stdout)
        self.assertEqual(parsed.status, "ok", result.stderr)
        self.assertNotIn(b"must-not-read-driver-file", result.stdout)
        self.assertEqual(len(parsed.value), 2)

    def test_discovery_cap_blocks_name_injection(self):
        directory = self.root / "sys/class/power_supply"
        directory.mkdir(parents=True)
        for index in range(129):
            (directory / f"battery{index:03d}").mkdir()
        result = self.execute(POWER)
        parsed = sysfs(result.stdout)
        self.assertTrue(any(item.get("reason") == "output_limit" for item in parsed.value))
        self.assertEqual(sum(item.get("attribute") == "type" for item in parsed.value), 128)
        injected = directory / "$(touch injected)"
        injected.mkdir()
        result = self.execute(POWER)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "injected").exists())
        self.assertFalse((ROOT / "injected").exists())

    def test_resolve_partitions_never_reads_block_content(self):
        target = self.file("dev/block/mmcblk0p15", b"must-not-read-block-content")
        for directory in ("dev/block/by-name", "dev/block/bootdevice/by-name"):
            path = self.root / directory
            path.mkdir(parents=True)
            (path / "boot").symlink_to(target)
        self.file("sys/class/block/mmcblk0p15/dev", b"179:15\n")
        self.file("sys/class/block/mmcblk0p15/size", b"65536\n")
        result = self.execute(RESOLVED)
        # The real parser enforces /dev/block; map fixture-only path values back.
        encoded = result.stdout.replace(str(self.root).encode(), b"")
        parsed = sysfs(encoded)
        self.assertEqual(parsed.status, "ok", result.stderr)
        self.assertEqual(parsed.value[0]["size_bytes"], 33554432)
        self.assertNotIn(b"must-not-read-block-content", result.stdout)
