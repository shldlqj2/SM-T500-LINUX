"""Private evidence files, exclusive run IDs, atomic JSON and workspace locks."""
from contextlib import AbstractContextManager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess

from .errors import PortError

REPO_ROOT = Path(__file__).resolve().parents[2]


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_id():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + secrets.token_hex(4)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def mkdir_private(path):
    if path.is_symlink() or path.resolve() != path.absolute():
        raise PortError("unsafe_path", 5)
    path.mkdir(mode=0o700, exist_ok=True)


def write_new(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def atomic_json(path, value):
    temporary = path.with_name(path.name + "." + secrets.token_hex(4) + ".tmp")
    write_new(temporary, json_bytes(value))
    try:
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def tool_revision():
    commit = None
    dirty = True
    try:
        commit_result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                                       capture_output=True, timeout=5, check=False)
        if commit_result.returncode == 0:
            commit = commit_result.stdout.decode("ascii").strip()
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "--", "tools"],
                                cwd=REPO_ROOT, capture_output=True, timeout=5, check=False)
        dirty = status.returncode != 0 or bool(status.stdout)
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        pass
    files = []
    for path in sorted((REPO_ROOT / "tools").rglob("*.py")):
        data = path.read_bytes()
        files.append({"path": path.relative_to(REPO_ROOT).as_posix(),
                      "size_bytes": len(data), "sha256": sha256(data)})
    return {"git_commit": commit, "dirty": dirty, "source_files": files}


class WorkspaceLock(AbstractContextManager):
    def __init__(self, workspace, alias):
        self.workspace = Path(workspace).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.private = self.workspace / "private"
        mkdir_private(self.private)
        self.path = self.private / "collect.lock"
        self.data = json_bytes({"host": socket.gethostname(), "pid": os.getpid(),
                                "at": utc_now(), "device_alias": alias, "token": secrets.token_hex(16)})

    def __enter__(self):
        try:
            write_new(self.path, self.data)
        except FileExistsError:
            raise PortError("lock_busy") from None
        return self

    def __exit__(self, *args):
        if self.path.exists() and not self.path.is_symlink() and self.path.read_bytes() == self.data:
            self.path.unlink()


class Store:
    def __init__(self, private):
        parent = private / "runs"
        mkdir_private(parent)
        while True:
            self.run_id = new_id()
            self.path = parent / self.run_id
            try:
                self.path.mkdir(mode=0o700)
                break
            except FileExistsError:
                continue
        mkdir_private(self.path / "raw")
        mkdir_private(self.path / "reports")
        self.events = open(self.path / "events.jsonl", "x", encoding="utf-8", newline="\n")
        if os.name != "nt":
            os.chmod(self.path / "events.jsonl", 0o600)
        self.seq = 0

    def event(self, event, item_id, state, error_code=None):
        self.seq += 1
        value = {"seq": self.seq, "at": utc_now(), "event": event,
                 "item_id": item_id, "state": state, "error_code": error_code}
        self.events.write(json.dumps(value, ensure_ascii=False) + "\n")
        self.events.flush()

    def capture(self, probe_id, index, stream, data, content_type, truncated):
        parent = self.path / "raw" / probe_id
        mkdir_private(parent)
        path = parent / f"{index}.{stream}"
        write_new(path, data)
        return {"path": path.relative_to(self.path).as_posix(), "size_bytes": len(data),
                "sha256": sha256(data), "content_type": content_type, "truncated": truncated}

    def finish(self, record):
        atomic_json(self.path / "run.json", record)
        self.events.close()
