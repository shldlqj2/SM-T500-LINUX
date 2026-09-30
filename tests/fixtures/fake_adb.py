#!/usr/bin/env python3
"""Synthetic ADB. No USB, Android services, device files or real root access."""
import gzip
import json
import os
from pathlib import Path
import shlex
import signal
import sys
import time

root = Path(os.environ.get("PORTCTL_FAKE_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(root / "tools"))
from portlib.probes import BASIC, EXTENDED

SCENARIO = os.environ.get("PORTCTL_FAKE_SCENARIO", "ok")
SERIAL = "SYNTHETIC-serial-123"


def dt_fixture():
    result = b"PORTCTL-DT1\n"
    for key, body in (("model", b"Fixture tablet\0"), ("compatible", b"fixture,tablet\0qcom,fixture\0"),
                      ("#address-cells", b"\0\0\0\2"), ("#size-cells", b"\0\0\0\2")):
        if SCENARIO == "bad_dt" and key == "#address-cells":
            body = b"\0\2"
        result += f"{key} ok {len(body)}\n".encode("ascii") + body + b"\n"
    return result


def emit(data=b"", stderr=b"", code=0):
    sys.stdout.buffer.write(data)
    sys.stderr.buffer.write(stderr)
    raise SystemExit(code)


def main():
    args = sys.argv[1:]
    log = os.environ.get("PORTCTL_FAKE_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(args) + "\n")
    if args == ["version"]:
        emit(b"Android Debug Bridge version 1.0.41\nVersion fixture\n")
    if args == ["devices", "-l"]:
        header = b"List of devices attached\n"
        if SCENARIO == "none":
            emit(header)
        state = SCENARIO if SCENARIO in {"unauthorized", "offline", "recovery", "sideload"} else "device"
        rows = f"{SERIAL}\t{state} product:fixture transport_id:7\n".encode()
        if SCENARIO == "multiple":
            rows += b"other-serial\toffline transport_id:8\n"
        emit(header + rows)
    if args[:2] != ["-s", SERIAL]:
        emit(stderr=b"adb: error: device not found\n", code=1)
    index = 2
    if args[index:index + 2] == ["-t", "7"]:
        index += 2
    if args[index:index + 3] == ["shell", "-T", "-n"]:
        command = args[index + 3]
        root_read = command.startswith("su -c ")
        if root_read:
            command = shlex.split(command)[2]
    elif args[index] == "exec-out":
        root_read = args[index + 1] == "su"
        command = args[index + 3]
    else:
        emit(stderr=b"unexpected fake command", code=2)
    if command == "id -u":
        if SCENARIO == "root_denied":
            emit(stderr=b"su: Permission denied\n", code=1)
        emit(b"0\n")
    if command.startswith("exit "):
        emit(code=0 if SCENARIO == "protocol" else int(command.split()[1]))
    matches = [probe for probe in BASIC + EXTENDED if probe.command == command]
    if len(matches) != 1:
        emit(stderr=b"unknown fixed probe\n", code=2)
    probe = matches[0]
    data = {
        "identity.model": b"SM-T500\n",
        "identity.codename": b"gta4lwifi\n",
        "identity.rom_build": b"samsung/gta4lwifi/fixture:11/build/fixture:user/release-keys\n",
        "identity.vendor_build": b"samsung/gta4lwifi/vendor:11/build/fixture:user/release-keys\n",
        "identity.bootloader": b"T500FIXTURE\n",
        "boot.verified_state": b"orange\n",
        "boot.vbmeta_state": b"unlocked\n",
        "kernel.release": b"4.19.0-fixture\n",
        "kernel.version": b"Linux version 4.19.0-fixture (synthetic)\n",
        "boot.cmdline": f"androidboot.serialno={SERIAL} mac=12:34:56:78:9a:bc path=/home/fixture/private\n".encode(),
        "memory.info": b"MemTotal:       262144 kB\nMemAvailable: 131072 kB\nHugePages_Total: 0\n",
        "storage.partitions": b"major minor  #blocks  name\n179 0 1048576 mmcblk0\n179 15 32768 mmcblk0p15\n",
        "storage.mounts": b"/dev/block/fixture /data/secret ext4 rw 0 0\n",
        "storage.by_name": b"DIR\t/dev/block/by-name\nlrwxrwxrwx 1 root root 21 fixture boot -> /dev/block/mmcblk0p15\nDIR\t/dev/block/bootdevice/by-name\nlrwxrwxrwx 1 root root 21 fixture boot -> /dev/block/mmcblk0p15\n",
        "kernel.modules": b"",
        "input.devices": b'I: Bus=0018 Vendor=0000 Product=0000 Version=0000\nN: Name="touch 12:34:56:78:9a:bc"\nH: Handlers=event0\n\n',
        "kernel.config": gzip.compress(b"# fixture only\nCONFIG_ARM64=y\n# CONFIG_TEST is not set\n", mtime=0),
        "dt.identity": dt_fixture(),
        "storage.resolved": b"PORTCTL-SYS1\nPART\t/dev/block/by-name\tboot\t/dev/block/mmcblk0p15\t179:15\t65536\n",
        "drivers.bindings": b"PORTCTL-SYS1\nATTR\tinput\tevent0\tdriver\t/sys/bus/i2c/drivers/fixture\n",
        "power.supplies": b"PORTCTL-SYS1\nATTR\tpower_supply\tbattery\ttype\tBattery\nATTR\tpower_supply\tbattery\tcapacity\t75\n",
        "thermal.zones": b"PORTCTL-SYS1\nATTR\tthermal\tthermal_zone0\ttype\tsynthetic\nATTR\tthermal\tthermal_zone0\ttemp\t25000\n",
        "kernel.log": b"[0.000] fixture only, no hardware validation\n",
    }[probe.id]
    if SCENARIO == "model" and probe.id == "identity.model":
        data = b"SM-T505\n"
    if SCENARIO == "codename" and probe.id == "identity.codename":
        data = b"gta4l\n"
    if SCENARIO == "identity_empty" and probe.id == "identity.model":
        data = b"\n"
    if SCENARIO == "identity_permission" and probe.id == "identity.model":
        emit(stderr=b"getprop: Permission denied\n", code=1)
    if SCENARIO == "missing" and probe.id == "identity.vendor_build":
        data = b"\n"
    if SCENARIO == "kernel_missing" and probe.id == "kernel.release":
        emit(stderr=b"uname: not found\n", code=127)
    if SCENARIO in {"permission", "root_denied"} and probe.id == "kernel.config" and not root_read:
        data = b"PORTCTL-ERROR permission_denied\n"
    if SCENARIO == "config_missing" and probe.id == "kernel.config":
        data = b"PORTCTL-ERROR path_unavailable\n"
    if SCENARIO == "corrupt_gzip" and probe.id == "kernel.config":
        data = data[:-8] + bytes([data[-8] ^ 255]) + data[-7:]
    if SCENARIO == "invalid_utf8" and probe.id == "kernel.version":
        data = b"original-\xff-\x80\n"
    if SCENARIO == "disconnect" and probe.id == "kernel.version":
        emit(stderr=f"adb: error: device '{SERIAL}' not found\n".encode(), code=1)
    if SCENARIO == "client_error" and probe.id == "kernel.version":
        emit(stderr=b"adb: error: failed to query feature set\n", code=1)
    if SCENARIO == "timeout" and probe.id == "kernel.version":
        time.sleep(3)
    if SCENARIO == "interrupt" and probe.id == "kernel.version":
        os.kill(os.getppid(), signal.SIGINT)
        time.sleep(3)
    if SCENARIO == "flood" and probe.id == "kernel.version":
        data = b"x" * (2 * 1024 * 1024)
    emit(data)


if __name__ == "__main__":
    main()
