"""Sequential collection: identity gate, private attempts, and fixed root adapter."""
from pathlib import Path
import platform

from .adb import command_error, devices, resolve_adb, select_device
from .errors import PortError
from .parsers import PARSERS, Parsed, ReadIssue
from .process import Runner
from .probes import BASIC, EXTENDED, DIAGNOSTICS
from .records import Store, WorkspaceLock, tool_revision, utc_now


def fact(key, value, source, reason=None, unit=None):
    return {"key": key, "value": value, "unit": unit, "source_probe": source,
            "evidence": "observed", "reason": reason, "annotation": None}


class Collector:
    def __init__(self, workspace, alias, profile, *, allow_root=False, serial=None,
                 adb_path=None, adb=None, runner=None, timeout=15.0,
                 binary_timeout=30.0, probe_limit=8 * 1024 * 1024,
                 total_limit=64 * 1024 * 1024, progress=None):
        self.workspace, self.alias, self.profile = Path(workspace), alias, profile
        self.allow_root, self.serial, self.adb_path = allow_root, serial, adb_path
        self.adb, self.runner = adb, runner or Runner()
        self.timeout, self.binary_timeout = timeout, binary_timeout
        self.probe_limit, self.remaining = probe_limit, total_limit
        self.progress = progress or (lambda message: None)
        self.requested = BASIC + (EXTENDED if profile == "extended" else ())
        self.root_available = None
        self.identity_passed = False

    def attempt(self, probe, entry, argv, *, root=False, parser=None, expected_exit=0, remote=True):
        used = sum((capture or {}).get("size_bytes", 0)
                   for attempt in entry["attempts"] for capture in (attempt["stdout"], attempt["stderr"]))
        limit = min(self.probe_limit - used, self.remaining)
        if limit <= 0:
            code = "output_budget" if self.remaining <= 0 else "output_limit"
            return Parsed(None, "skipped", code)
        self.store.event("attempt_started", probe.id, "started")
        result = self.runner.run(argv, timeout=self.binary_timeout if probe.binary or root or probe.id == "privilege.root" else self.timeout,
                                 limit=limit)
        self.remaining -= len(result.stdout) + len(result.stderr)
        status, code = "ok", None
        parsed = Parsed(None)
        if result.error_code:
            code = result.error_code
            if code == "output_limit" and self.remaining <= 0:
                code = "output_budget"
            status = {"timeout": "timeout", "output_limit": "truncated",
                      "output_budget": "truncated"}.get(code, "failed")
        elif result.exit_code != expected_exit:
            status, code = command_error(result.stderr)
        elif probe.id in {"transport.shell_ok", "transport.shell_fail"}:
            if result.stdout or result.stderr:
                status, code = "failed", "protocol_unsupported"
        else:
            try:
                parsed = (parser or PARSERS[probe.parser])(result.stdout)
                status, code = parsed.status, parsed.error_code
            except ReadIssue as error:
                status, code = error.status, error.code
            except (ValueError, UnicodeError, OverflowError):
                status, code = "parse_error", "parse_error"
        truncated = result.error_code in {"timeout", "output_limit", "user_interrupted"}
        client_error = result.stderr.lstrip().startswith((b"adb:", b"error:"))
        index = len(entry["attempts"])
        attempt = {"privilege": "root" if root else "shell", "argv": argv,
                   "started_at": result.started_at, "duration_ms": result.duration_ms,
                   "host_exit_code": result.exit_code,
                   "remote_exit_code": result.exit_code if remote and not probe.binary and self.adb.protocol_verified and not result.error_code and not client_error and code != "device_disconnected" else None,
                   "status": status, "error_code": code,
                   "stdout": self.store.capture(probe.id, index, "stdout", result.stdout, "binary" if probe.binary else "text", truncated),
                   "stderr": self.store.capture(probe.id, index, "stderr", result.stderr, "text", truncated)}
        entry["attempts"].append(attempt)
        self.store.event("attempt_finished", probe.id, status, code)
        if remote and result.cleanup_unconfirmed:
            self.record["limitations"].append({"code": "cleanup_unconfirmed", "item_id": probe.id,
                                               "note": "로컬 ADB 종료만 확인 가능하며 원격 명령 종료는 미확인."})
        if code == "user_interrupted":
            entry.update(status=status, error_code=code)
            raise PortError(code, 130)
        if code == "device_disconnected":
            entry.update(status=status, error_code=code)
            raise PortError(code, 4 if self.identity_passed else 3)
        return Parsed(parsed.value, status, code, parsed.extras)

    def entry(self, probe):
        entry = {"id": probe.id, "parser_version": 1, "required": probe.required,
                 "status": "skipped", "error_code": None, "attempts": []}
        self.record["probes"].append(entry)
        return entry

    def observe(self, probe, argv=None, *, parser=None, expected_exit=0, remote=True):
        self.progress(f"수집: {probe.id} — {probe.purpose}")
        entry = self.entry(probe)
        if argv is None:
            argv = self.adb.remote(probe.command, binary=probe.binary)
        parsed = self.attempt(probe, entry, argv, parser=parser,
                              expected_exit=expected_exit, remote=remote)
        if parsed.status == "permission_denied" and self.allow_root and self.identity_passed and probe.id not in DIAGNOSTICS:
            if self.root_available is None and self.remaining > 0:
                root_probe = DIAGNOSTICS["privilege.root"]
                root_entry = self.entry(root_probe)
                self.progress("기존 su의 UID 0 권한 확인 중 — 기기의 승인 화면을 확인하세요.")
                checked = self.attempt(root_probe, root_entry, self.adb.remote(root_probe.command), root=True)
                root_entry.update(status=checked.status, error_code=checked.error_code)
                self.record["facts"].append(fact(root_probe.id, checked.value, root_probe.id, checked.error_code))
                self.root_available = checked.status == "ok"
                if not self.root_available:
                    self.record["limitations"].append({"code": "root_unavailable", "item_id": probe.id,
                                                       "note": "root 확인 실패; shell 관측을 계속함."})
            if self.root_available:
                retried = self.attempt(probe, entry, self.adb.remote(probe.command, binary=probe.binary, root=True), root=True)
                if retried.status in {"ok", "unavailable", "parse_error", "truncated"}:
                    parsed = retried
        entry.update(status=parsed.status, error_code=parsed.error_code)
        self.record["facts"].append(fact(probe.id, parsed.value, probe.id, parsed.error_code))
        for key, (value, unit) in parsed.extras.items():
            self.record["facts"].append(fact(key, value, probe.id, parsed.error_code, unit))
        return parsed

    def skipped(self, code):
        existing = {entry["id"] for entry in self.record["probes"]}
        for probe in self.requested:
            if probe.id not in existing:
                entry = self.entry(probe)
                entry["error_code"] = code
                self.record["facts"].append(fact(probe.id, None, probe.id, code))
                self.store.event("probe_skipped", probe.id, "skipped", code)

    def run(self):
        from .contracts import validate_run
        from .reports import write_report

        with WorkspaceLock(self.workspace, self.alias) as lock:
            self.store = Store(lock.private)
            self.record = {"object_kind": "device_collection", "schema_version": 1,
                           "run_id": self.store.run_id, "started_at": utc_now(), "finished_at": None,
                           "tool_revision": tool_revision(),
                           "host": {"os": platform.system(), "python_version": platform.python_version(),
                                    "adb_path": "", "adb_version": "", "cwd": str(Path.cwd())},
                           "device_alias": self.alias, "target": {"serial": None, "adb_state": None},
                           "profile": self.profile, "allow_root": self.allow_root,
                           "status": "failed", "error_code": None, "probes": [], "facts": [], "limitations": []}
            exit_code = 0
            self.store.event("run_started", None, "started")
            try:
                self.adb = self.adb or resolve_adb(self.adb_path)
                self.record["host"]["adb_path"] = self.adb.prefix[0]
                version = self.observe(DIAGNOSTICS["host.adb_version"], self.adb.host("version"), remote=False)
                if version.status != "ok":
                    raise PortError("tool_failed")
                self.record["host"]["adb_version"] = version.value
                listed = self.observe(DIAGNOSTICS["transport.devices"], self.adb.host("devices", "-l"), parser=devices, remote=False)
                if listed.status != "ok":
                    raise PortError(listed.error_code)
                try:
                    self.adb.device = select_device(listed.value, self.serial)
                except PortError as error:
                    if hasattr(error, "device"):
                        self.record["target"].update(serial=error.device.serial, adb_state=error.device.state)
                    raise
                self.record["target"].update(serial=self.adb.device.serial, adb_state=self.adb.device.state)
                for key, expected in (("transport.shell_ok", 0), ("transport.shell_fail", 37)):
                    checked = self.observe(DIAGNOSTICS[key], expected_exit=expected)
                    if checked.status != "ok":
                        raise PortError("protocol_unsupported")
                self.adb.protocol_verified = True
                for entry in self.record["probes"]:
                    if entry["id"] in {"transport.shell_ok", "transport.shell_fail"}:
                        entry["attempts"][0]["remote_exit_code"] = entry["attempts"][0]["host_exit_code"]
                model = self.observe(BASIC[0])
                codename = self.observe(BASIC[1])
                if model.status != "ok" or codename.status != "ok":
                    raise PortError("identity_unverified")
                if (model.value, codename.value) != ("SM-T500", "gta4lwifi"):
                    raise PortError("model_mismatch")
                self.identity_passed = True
                for probe in self.requested[2:]:
                    if self.remaining <= 0:
                        self.skipped("output_budget")
                        break
                    self.observe(probe)
                failed = [entry for entry in self.record["probes"] if entry["status"] != "ok"]
                self.record["status"] = "partial" if failed else "complete"
                self.record["error_code"] = failed[0]["error_code"] if failed else None
                exit_code = 4 if failed else 0
            except PortError as error:
                self.record["status"] = "interrupted" if error.exit_code == 130 else ("partial" if self.identity_passed else "failed")
                self.record["error_code"] = error.code
                exit_code = error.exit_code
                self.skipped(error.code)
            except KeyboardInterrupt:
                self.record.update(status="interrupted", error_code="user_interrupted")
                exit_code = 130
                self.skipped("user_interrupted")
            except Exception:
                self.record.update(status="failed", error_code="internal_error")
                exit_code = 1
                self.skipped("internal_error")
            finally:
                self.record["finished_at"] = utc_now()
                self.store.event("run_finished", None, self.record["status"], self.record["error_code"])
                validate_run(self.record)
                self.store.finish(self.record)
            report_path = write_report(self.store.path, "private")
            self.progress(f"결과: {self.record['status']} / {self.store.path / 'run.json'}")
            self.progress(f"설명 보고서: {report_path}")
            self.progress("다음 단계: 제한된 항목과 ROM·커널 소스 대응 근거를 검토하세요.")
            return exit_code, self.store.path
