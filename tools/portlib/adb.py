from dataclasses import dataclass
import os
from pathlib import Path
import re
import shlex
import shutil

from .errors import PortError
from .parsers import Parsed, ReadIssue, text


def resolve_adb(explicit=None):
    candidate = str(Path(explicit).resolve()) if explicit else shutil.which("adb")
    if not candidate or not Path(candidate).is_file():
        raise PortError("tool_missing")
    path = Path(candidate)
    if os.name == "nt" and path.suffix.lower() != ".exe":
        raise PortError("tool_failed")
    if os.name != "nt" and not os.access(path, os.X_OK):
        raise PortError("tool_failed")
    return Adb([str(path)])


@dataclass(frozen=True)
class Device:
    serial: str
    state: str
    transport_id: str | None


def devices(data):
    lines = text(data).splitlines()
    if not lines or lines[0].strip() != "List of devices attached":
        raise ReadIssue("parse_error", "parse_error")
    found = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ReadIssue("parse_error", "parse_error")
        serial, state = parts[:2]
        ids = [part.split(":", 1)[1] for part in parts[2:] if part.startswith("transport_id:")]
        if len(ids) > 1 or (ids and (not ids[0].isdecimal() or int(ids[0]) <= 0)):
            raise ReadIssue("parse_error", "parse_error")
        if any(row["serial"] == serial for row in found):
            raise ReadIssue("parse_error", "parse_error")
        found.append({"serial": serial, "state": state, "transport_id": ids[0] if ids else None})
    return Parsed(found)


def select_device(rows, serial=None):
    if serial is not None:
        selected = [row for row in rows if row["serial"] == serial]
        if not selected:
            raise PortError("no_device")
    else:
        if not rows:
            raise PortError("no_device")
        if len(rows) != 1:
            raise PortError("multiple_devices")
        selected = rows
    device = Device(**selected[0])
    if device.state != "device":
        code = device.state if device.state in {"unauthorized", "offline"} else "unsupported_device_state"
        error = PortError(code)
        error.device = device
        raise error
    return device


def command_error(stderr):
    value = stderr.decode("utf-8", errors="replace").lower()
    # ADB client transport messages, not a keyword search through the kernel log.
    if re.search(r"(?m)^(?:adb: )?error: (?:device .*not found|device offline|no devices/emulators found|closed|transport .*not found|failed to read)", value):
        return "failed", "device_disconnected"
    if "permission denied" in value or "operation not permitted" in value:
        return "permission_denied", "permission_denied"
    if "no such file or directory" in value or "not found" in value:
        return "unavailable", "path_unavailable"
    return "failed", "command_failed"


class Adb:
    def __init__(self, prefix):
        # Prefix injection is internal to fixture tests, not a CLI arbitrary-command API.
        self.prefix = list(prefix)
        self.device = None
        self.protocol_verified = False

    def host(self, *args):
        return self.prefix + list(args)

    def remote(self, command, *, binary=False, root=False):
        if self.device is None:
            raise PortError("identity_unverified")
        selected = ["-s", self.device.serial]
        if self.device.transport_id is not None:
            selected += ["-t", self.device.transport_id]
        if binary:
            # exec-out's raw stream has no remote exit frame; format checking is required.
            args = ["exec-out", "su" if root else "sh", "-c", command]
        else:
            remote_command = "su -c " + shlex.quote(command) if root else command
            args = ["shell", "-T", "-n", remote_command]
        return self.prefix + selected + args
