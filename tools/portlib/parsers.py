"""Pure byte parsers; source candidates and hardware support are not inferred."""
from dataclasses import dataclass, field
import gzip
import io
import re
import zlib


class ReadIssue(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


@dataclass
class Parsed:
    value: object
    status: str = "ok"
    error_code: str | None = None
    extras: dict = field(default_factory=dict)


def fail():
    raise ReadIssue("parse_error", "parse_error")


def text(data):
    try:
        value = data.decode("utf-8")
    except UnicodeError:
        fail()
    if "\0" in value:
        fail()
    return value


def scalar(data):
    value = text(data).strip()
    if not value:
        raise ReadIssue("unavailable", "path_unavailable")
    return Parsed(value)


def uid(data):
    if text(data).strip() != "0":
        raise ReadIssue("permission_denied", "root_unavailable")
    return Parsed(0)


def version(data):
    value = scalar(data)
    if not value.value.startswith("Android Debug Bridge version "):
        fail()
    return value


def memory(data):
    rows = {}
    for line in text(data).splitlines():
        match = re.fullmatch(r"([A-Za-z_()]+):\s*(\d+)(?:\s+(kB))?", line)
        if not match or match[1] in rows:
            fail()
        rows[match[1]] = {"value": int(match[2]) * (1024 if match[3] else 1),
                          "unit": "bytes" if match[3] else "count"}
    if "MemTotal" not in rows or rows["MemTotal"]["unit"] != "bytes":
        fail()
    return Parsed(rows, extras={"memory.total_bytes": (rows["MemTotal"]["value"], "bytes")})


def partitions(data):
    rows = []
    for line in text(data).splitlines():
        if not line.strip() or line.split() == ["major", "minor", "#blocks", "name"]:
            continue
        parts = line.split()
        if len(parts) != 4 or not all(part.isdecimal() for part in parts[:3]):
            fail()
        rows.append({"major": int(parts[0]), "minor": int(parts[1]),
                     "blocks_kib": int(parts[2]), "size_bytes": int(parts[2]) * 1024,
                     "name": parts[3]})
    return Parsed(rows)


def mounts(data):
    rows = []
    for line in text(data).splitlines():
        parts = line.split()
        if len(parts) != 6 or not all(part.isdecimal() for part in parts[4:]):
            fail()
        rows.append(dict(zip(("source", "mountpoint", "type", "options", "dump", "pass"), parts)))
    return Parsed(rows)


def modules(data):
    rows = []
    for line in text(data).splitlines():
        parts = line.split()
        if len(parts) < 6 or not parts[1].isdecimal() or not parts[2].isdecimal():
            fail()
        rows.append({"name": parts[0], "size_bytes": int(parts[1]),
                     "refcount": int(parts[2]), "dependencies": parts[3],
                     "state": parts[4], "address": parts[5]})
    return Parsed(rows)


def inputs(data):
    rows = []
    for block in re.split(r"\n\s*\n", text(data).strip()):
        if not block.strip():
            continue
        name = re.search(r'^N: Name="(.*)"$', block, re.MULTILINE)
        if not name:
            fail()
        bus = re.search(r"^I: (.*)$", block, re.MULTILINE)
        handlers = re.search(r"^H: Handlers=(.*)$", block, re.MULTILINE)
        rows.append({"name": name[1], "bus": bus[1] if bus else None,
                     "handlers": handlers[1].split() if handlers else []})
    return Parsed(rows)


def config(data):
    binary_error(data)
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            decoded = stream.read(16 * 1024 * 1024 + 1)
        if len(decoded) > 16 * 1024 * 1024:
            raise ReadIssue("truncated", "output_limit")
    except (OSError, EOFError, zlib.error):
        fail()
    rows = {}
    for line in text(decoded).splitlines():
        match = re.fullmatch(r"(CONFIG_[A-Za-z0-9_]+)=(.+)", line)
        disabled = re.fullmatch(r"# (CONFIG_[A-Za-z0-9_]+) is not set", line)
        if match or disabled:
            key, value = (match[1], match[2]) if match else (disabled[1], "n")
            if key in rows:
                fail()
            rows[key] = value
        elif line and not line.startswith("#"):
            fail()
    if not rows:
        fail()
    return Parsed(rows)


def binary_error(data):
    if data == b"PORTCTL-ERROR path_unavailable\n":
        raise ReadIssue("unavailable", "path_unavailable")
    if data == b"PORTCTL-ERROR permission_denied\n":
        raise ReadIssue("permission_denied", "permission_denied")


def aggregate(value, codes):
    if "permission_denied" in codes:
        return Parsed(value, "permission_denied", "permission_denied")
    if "output_limit" in codes:
        return Parsed(value, "truncated", "output_limit")
    if "command_failed" in codes:
        return Parsed(value, "failed", "command_failed")
    if codes:
        return Parsed(value, "unavailable", "path_unavailable")
    return Parsed(value)


def dt(data):
    if not data.startswith(b"PORTCTL-DT1\n"):
        fail()
    remaining = data[len(b"PORTCTL-DT1\n"):]
    rows, codes = {}, []
    for key in ("model", "compatible", "#address-cells", "#size-cells"):
        header, sep, tail = remaining.partition(b"\n")
        try:
            name, state, size_text = header.decode("ascii").split()
            size = int(size_text)
        except (UnicodeError, ValueError):
            fail()
        if not sep or name != key or state not in {"ok", "missing", "denied"} or not 0 <= size <= 1048576:
            fail()
        if len(tail) < size + 1 or tail[size:size + 1] != b"\n":
            fail()
        body, remaining = tail[:size], tail[size + 1:]
        if state != "ok":
            if size != 0:
                fail()
            reason = "permission_denied" if state == "denied" else "path_unavailable"
            codes.append(reason)
            rows[key] = {"value": None, "reason": reason}
            continue
        if key.startswith("#"):
            if len(body) != 4:
                fail()
            value = int.from_bytes(body, "big")
        else:
            if not body or not body.endswith(b"\0"):
                fail()
            try:
                strings = body[:-1].decode("utf-8").split("\0")
            except UnicodeError:
                fail()
            if not all(strings) or (key == "model" and len(strings) != 1):
                fail()
            value = strings[0] if key == "model" else strings
        rows[key] = {"value": value, "reason": None}
    if remaining:
        fail()
    return aggregate(rows, codes)


def by_name(data):
    rows, codes, current = [], [], None
    for line in text(data).splitlines():
        if line.startswith("DIR\t"):
            path = line.split("\t")[1]
            if path not in {"/dev/block/by-name", "/dev/block/bootdevice/by-name"}:
                fail()
            current = {"directory": path, "links": [], "status": "ok"}
            rows.append(current)
        elif line in {"MISSING", "DENIED", "FAILED"}:
            if current is None:
                fail()
            code = {"MISSING": "path_unavailable", "DENIED": "permission_denied", "FAILED": "command_failed"}[line]
            current["status"] = code
            codes.append(code)
        elif line.startswith("total ") or not line:
            continue
        else:
            if current is None:
                fail()
            match = re.search(r"\s([^\s]+) -> (.+)$", line)
            if not match:
                fail()
            current["links"].append({"name": match[1], "target": match[2]})
    if len(rows) != 2 or len({row["directory"] for row in rows}) != 2:
        fail()
    return aggregate(rows, codes)


def sysfs(data):
    lines = text(data).splitlines()
    if not lines or lines[0] != "PORTCTL-SYS1":
        fail()
    rows, codes = [], []
    attrs = {"driver", "of_node", "type", "status", "capacity", "voltage_now", "current_now", "temp"}
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) == 2 and parts[0] in {"MISSING", "DENIED", "LIMIT", "FAILED"}:
            code = {"MISSING": "path_unavailable", "DENIED": "permission_denied", "LIMIT": "output_limit", "FAILED": "command_failed"}[parts[0]]
            codes.append(code)
            rows.append({"scope": parts[1], "reason": code})
        elif len(parts) == 5 and parts[0] == "ATTR":
            _, group, name, attr, value = parts
            if attr not in attrs or not re.fullmatch(r"[A-Za-z0-9_.:+-]+", name):
                fail()
            reason = None
            if value == "!missing":
                reason = "path_unavailable"
            elif value == "!denied":
                reason = "permission_denied"
            elif value.endswith("!failed"):
                reason = "command_failed"
            if reason:
                codes.append(reason)
                value = None
            elif attr in {"capacity", "voltage_now", "current_now", "temp"}:
                try:
                    value = int(value)
                except ValueError:
                    fail()
            rows.append({"class": group, "name": name, "attribute": attr,
                         "value": value, "reason": reason})
        elif len(parts) == 6 and parts[0] == "PART":
            _, directory, name, target, dev, sectors = parts
            if not re.fullmatch(r"\d+:\d+", dev) or not sectors.isdecimal() or not target.startswith("/dev/block/"):
                fail()
            major, minor = map(int, dev.split(":"))
            rows.append({"directory": directory, "name": name, "target": target,
                         "major": major, "minor": minor, "sectors_512": int(sectors),
                         "size_bytes": int(sectors) * 512})
        else:
            fail()
    return aggregate(rows, codes)


PARSERS = {"scalar": scalar, "version": version, "uid": uid, "memory": memory,
           "partitions": partitions, "mounts": mounts, "modules": modules,
           "inputs": inputs, "by_name": by_name, "config": config, "dt": dt, "sysfs": sysfs}
