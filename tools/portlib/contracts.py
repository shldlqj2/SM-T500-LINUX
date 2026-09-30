"""Strict collection v1 reader/writer checks, including evidence references."""
from datetime import datetime
import json
import math
from pathlib import Path, PurePosixPath
import re

from .errors import ERRORS, PROBE_STATUSES, RUN_STATUSES, PortError
from .probes import ALL, BASIC, EXTENDED
from .records import sha256

RUN_ID = r"\d{8}T\d{6}Z-[0-9a-f]{8}"
HASH = r"[0-9a-f]{64}"


def require(condition):
    if not condition:
        raise PortError("invalid_schema", 2)


def obj(value, keys):
    require(type(value) is dict and set(value) == set(keys.split()))


def string(value, nullable=False):
    require((nullable and value is None) or type(value) is str)


def integer(value, nullable=False, minimum=None):
    require((nullable and value is None) or (type(value) is int and (minimum is None or value >= minimum)))


def timestamp(value):
    string(value)
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise PortError("invalid_schema", 2) from None
    require(parsed.utcoffset().total_seconds() == 0)
    return parsed


def error_code(value):
    require(value is None or (type(value) is str and value in ERRORS))


def json_value(value, depth=0):
    require(depth <= 32)
    if value is None or type(value) in {str, bool, int}:
        return
    if type(value) is float:
        require(math.isfinite(value))
    elif type(value) is list:
        for item in value:
            json_value(item, depth + 1)
    elif type(value) is dict:
        for key, item in value.items():
            string(key)
            json_value(item, depth + 1)
    else:
        require(False)


def _validate_run(record):
    obj(record, "object_kind schema_version run_id started_at finished_at tool_revision host device_alias target profile allow_root status error_code probes facts limitations")
    require(record["object_kind"] == "device_collection" and type(record["schema_version"]) is int and record["schema_version"] == 1)
    require(type(record["run_id"]) is str and re.fullmatch(RUN_ID, record["run_id"]))
    require(timestamp(record["finished_at"]) >= timestamp(record["started_at"]))
    require(type(record["device_alias"]) is str and re.fullmatch(r"[a-z0-9-]{1,32}", record["device_alias"]))
    require(record["profile"] in {"basic", "extended"} and type(record["allow_root"]) is bool)
    require(not record["allow_root"] or record["profile"] == "extended")
    require(record["status"] in RUN_STATUSES)
    error_code(record["error_code"])
    require((record["status"] == "complete") == (record["error_code"] is None))
    revision = record["tool_revision"]
    obj(revision, "git_commit dirty source_files")
    require(revision["git_commit"] is None or (type(revision["git_commit"]) is str and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision["git_commit"])))
    require(type(revision["dirty"]) is bool and type(revision["source_files"]) is list)
    source_paths = set()
    for digest in revision["source_files"]:
        obj(digest, "path size_bytes sha256")
        path = relative_path(digest["path"])
        require(path not in source_paths)
        source_paths.add(path)
        integer(digest["size_bytes"], minimum=0)
        require(type(digest["sha256"]) is str and re.fullmatch(HASH, digest["sha256"]))
    obj(record["host"], "os python_version adb_path adb_version cwd")
    for value in record["host"].values():
        string(value)
    obj(record["target"], "serial adb_state")
    for value in record["target"].values():
        string(value, nullable=True)
    require(type(record["probes"]) is list and type(record["facts"]) is list and type(record["limitations"]) is list)
    ids, captures = set(), set()
    total_bytes = 0
    for probe in record["probes"]:
        obj(probe, "id parser_version required status error_code attempts")
        require(type(probe["id"]) is str and probe["id"] in ALL and probe["id"] not in ids)
        ids.add(probe["id"])
        integer(probe["parser_version"], minimum=1)
        require(probe["parser_version"] == 1 and type(probe["required"]) is bool and probe["required"] == ALL[probe["id"]].required)
        require(probe["status"] in PROBE_STATUSES)
        error_code(probe["error_code"])
        require((probe["status"] == "ok") == (probe["error_code"] is None))
        require(type(probe["attempts"]) is list and len(probe["attempts"]) <= 2)
        if probe["status"] == "ok":
            require(bool(probe["attempts"]))
        probe_bytes = 0
        for index, attempt in enumerate(probe["attempts"]):
            obj(attempt, "privilege argv started_at duration_ms host_exit_code remote_exit_code status error_code stdout stderr")
            require(attempt["privilege"] in {"shell", "root"})
            require(type(attempt["argv"]) is list and bool(attempt["argv"]) and all(type(arg) is str and "\0" not in arg for arg in attempt["argv"]))
            timestamp(attempt["started_at"])
            integer(attempt["duration_ms"], minimum=0)
            integer(attempt["host_exit_code"], nullable=True)
            integer(attempt["remote_exit_code"], nullable=True)
            require(attempt["status"] in PROBE_STATUSES)
            error_code(attempt["error_code"])
            require((attempt["status"] == "ok") == (attempt["error_code"] is None))
            for stream in ("stdout", "stderr"):
                capture = attempt[stream]
                if capture is None:
                    require(attempt["status"] == "skipped")
                    continue
                obj(capture, "path size_bytes sha256 content_type truncated")
                path = relative_path(capture["path"])
                require(path == f"raw/{probe['id']}/{index}.{stream}" and path not in captures)
                captures.add(path)
                integer(capture["size_bytes"], minimum=0)
                require(type(capture["sha256"]) is str and re.fullmatch(HASH, capture["sha256"]))
                require(capture["content_type"] in {"text", "binary"} and type(capture["truncated"]) is bool)
                probe_bytes += capture["size_bytes"]
        require(probe_bytes <= 8 * 1024 * 1024)
        total_bytes += probe_bytes
    require(total_bytes <= 64 * 1024 * 1024)
    fact_keys = set()
    for fact in record["facts"]:
        obj(fact, "key value unit source_probe evidence reason annotation")
        string(fact["key"])
        require(fact["key"] not in fact_keys)
        fact_keys.add(fact["key"])
        string(fact["unit"], nullable=True)
        string(fact["reason"], nullable=True)
        require(fact["source_probe"] is None or (type(fact["source_probe"]) is str and fact["source_probe"] in ids))
        require(fact["evidence"] in {"observed", "manual"})
        if fact["evidence"] == "manual":
            obj(fact["annotation"], "author at basis")
            string(fact["annotation"]["author"])
            string(fact["annotation"]["basis"])
            timestamp(fact["annotation"]["at"])
        else:
            require(fact["annotation"] is None)
        json_value(fact["value"])
    for limitation in record["limitations"]:
        obj(limitation, "code item_id note")
        error_code(limitation["code"])
        require(limitation["code"] is not None)
        string(limitation["item_id"], nullable=True)
        string(limitation["note"])
    if record["status"] in {"complete", "partial"}:
        observed = {fact["key"]: fact for fact in record["facts"]}
        entries = {probe["id"]: probe for probe in record["probes"]}
        for key, value in (("identity.model", "SM-T500"), ("identity.codename", "gta4lwifi")):
            require(key in entries and entries[key]["status"] == "ok" and key in observed)
            require(observed[key]["value"] == value and observed[key]["source_probe"] == key and observed[key]["evidence"] == "observed")
    if record["status"] == "complete":
        expected = {probe.id for probe in BASIC + (EXTENDED if record["profile"] == "extended" else ())}
        require(expected <= ids and all(probe["status"] == "ok" for probe in record["probes"]))
        require({"host.adb_version", "transport.devices", "transport.shell_ok", "transport.shell_fail"} <= ids)
    return record


def validate_run(record):
    try:
        return _validate_run(record)
    except (TypeError, AttributeError, KeyError, ValueError, RecursionError):
        raise PortError("invalid_schema", 2) from None


def relative_path(value):
    string(value)
    path = PurePosixPath(value)
    if not value or path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")) or "\\" in value or ":" in value or "\0" in value:
        raise PortError("unsafe_path", 5)
    return value


def evidence_path(root, relative):
    relative_path(relative)
    path = root
    for part in relative.split("/"):
        path = path / part
        if path.is_symlink():
            raise PortError("unsafe_path", 5)
    if not path.resolve().is_relative_to(root.resolve()):
        raise PortError("unsafe_path", 5)
    return path


def read_limited(path, limit):
    if path.is_symlink() or not path.is_file():
        raise PortError("unsafe_path" if path.is_symlink() else "artifact_missing", 5)
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise PortError("invalid_schema", 2)
    return data


def decode_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("nonfinite value")

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (UnicodeError, ValueError, RecursionError):
        raise PortError("invalid_schema", 2) from None


def load_run(root):
    record = validate_run(decode_json(read_limited(root / "run.json", 32 * 1024 * 1024)))
    require(root.name == record["run_id"])
    for probe in record["probes"]:
        for attempt in probe["attempts"]:
            for capture in (attempt["stdout"], attempt["stderr"]):
                if capture is None:
                    continue
                data = read_limited(evidence_path(root, capture["path"]), 8 * 1024 * 1024)
                if len(data) != capture["size_bytes"] or sha256(data) != capture["sha256"]:
                    raise PortError("artifact_mismatch", 5)
    return record
