import copy
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from portlib.adb import Adb, resolve_adb
from portlib.collector import Collector
from portlib.contracts import decode_json, load_run, validate_run
from portlib.errors import PortError
from portlib.parsers import ReadIssue, config, dt, sysfs
from portlib.process import Runner
from portlib.probes import BASIC, EXTENDED
from portlib.records import WorkspaceLock, json_bytes, sha256
from portlib.reports import write_report


def invokes_su(call):
    if "exec-out" in call:
        return call[call.index("exec-out") + 1] == "su"
    return call[-1].startswith("su -c ")


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="portctl-한글 경로-")
        self.workspace = Path(self.temporary.name)
        self.log = self.workspace / "fake-argv.jsonl"
        fake = self.workspace / "가짜 adb.py"
        shutil.copyfile(ROOT / "tests/fixtures/fake_adb.py", fake)
        self.adb = Adb([sys.executable, str(fake)])
        self.environment = patch.dict(os.environ, {"PORTCTL_FAKE_ROOT": str(ROOT),
                                      "PORTCTL_FAKE_LOG": str(self.log), "PORTCTL_FAKE_SCENARIO": "ok"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.temporary.cleanup)

    def collect(self, scenario="ok", profile="basic", **kwargs):
        os.environ["PORTCTL_FAKE_SCENARIO"] = scenario
        self.adb.protocol_verified = False
        self.adb.device = None
        code, run = Collector(self.workspace, "tablet-a", profile, adb=self.adb, **kwargs).run()
        self.run_path = run
        self.record = load_run(run)
        self.calls = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.probes = {probe["id"]: probe for probe in self.record["probes"]}
        return code

    def test_basic_complete_and_evidence_hashes(self):
        self.assertEqual(self.collect(), 0)
        self.assertEqual(self.record["status"], "complete")
        self.assertEqual(self.probes["kernel.modules"]["status"], "ok")
        self.assertFalse(any(invokes_su(call) for call in self.calls))
        facts = {item["key"]: item["value"] for item in self.record["facts"]}
        self.assertEqual(facts["memory.total_bytes"], 268435456)
        for call in self.calls[2:]:
            self.assertEqual(call[:4], ["-s", "SYNTHETIC-serial-123", "-t", "7"])
        self.assertEqual(self.probes["transport.shell_fail"]["attempts"][0]["remote_exit_code"], 37)
        self.assertFalse((self.workspace / "private/collect.lock").exists())

    def test_extended_binary_and_sector_units(self):
        self.assertEqual(self.collect(profile="extended"), 0)
        facts = {item["key"]: item["value"] for item in self.record["facts"]}
        self.assertEqual(facts["dt.identity"]["#address-cells"]["value"], 2)
        self.assertEqual(facts["storage.resolved"][0]["size_bytes"], 33554432)
        self.assertEqual(facts["kernel.config"]["CONFIG_TEST"], "n")
        self.assertIsNone(self.probes["kernel.config"]["attempts"][0]["remote_exit_code"])

    def test_selection_failures_do_not_issue_remote_reads(self):
        for scenario, expected in (("none", "no_device"), ("multiple", "multiple_devices"),
                                   ("unauthorized", "unauthorized"), ("offline", "offline"),
                                   ("recovery", "unsupported_device_state"), ("sideload", "unsupported_device_state")):
            with self.subTest(scenario=scenario):
                self.log.unlink(missing_ok=True)
                self.assertEqual(self.collect(scenario), 3)
                self.assertEqual(self.record["status"], "failed")
                self.assertEqual(self.record["error_code"], expected)
                self.assertEqual(len(self.calls), 2)

    def test_explicit_serial_selection_and_mismatch(self):
        self.assertEqual(self.collect("multiple", serial="SYNTHETIC-serial-123"), 0)
        self.assertEqual(self.collect(serial="not-connected;$(ignored)"), 3)
        self.assertEqual(self.record["error_code"], "no_device")

    def test_identity_and_protocol_gates(self):
        for scenario, expected in (("model", "model_mismatch"), ("codename", "model_mismatch"),
                                   ("identity_empty", "identity_unverified"), ("protocol", "protocol_unsupported")):
            with self.subTest(scenario=scenario):
                self.log.unlink(missing_ok=True)
                self.assertEqual(self.collect(scenario), 3)
                self.assertEqual(self.record["error_code"], expected)
                self.assertEqual(self.probes["kernel.release"]["status"], "skipped")
                self.assertFalse(any(call[-1] == "uname -r" for call in self.calls))

    def test_permission_does_not_invoke_su_without_flag(self):
        self.assertEqual(self.collect("permission", "extended"), 4)
        self.assertEqual(self.probes["kernel.config"]["status"], "permission_denied")
        self.assertNotIn("privilege.root", self.probes)
        self.assertFalse(any(invokes_su(call) for call in self.calls))

    def test_unverified_identity_never_requests_root_even_with_flag(self):
        self.assertEqual(self.collect("identity_permission", "extended", allow_root=True), 3)
        self.assertEqual(self.record["error_code"], "identity_unverified")
        self.assertNotIn("privilege.root", self.probes)
        self.assertFalse(any(invokes_su(call) for call in self.calls))

    def test_root_retry_retains_first_permission_attempt(self):
        self.assertEqual(self.collect("permission", "extended", allow_root=True), 0)
        attempts = self.probes["kernel.config"]["attempts"]
        self.assertEqual([item["status"] for item in attempts], ["permission_denied", "ok"])
        self.assertEqual([item["privilege"] for item in attempts], ["shell", "root"])
        self.assertEqual(self.probes["privilege.root"]["status"], "ok")

    def test_root_denied_and_missing_are_not_retried(self):
        self.assertEqual(self.collect("root_denied", "extended", allow_root=True), 4)
        self.assertEqual(len(self.probes["kernel.config"]["attempts"]), 1)
        self.assertEqual(self.probes["kernel.log"]["status"], "ok")
        self.assertEqual(self.collect("config_missing", "extended", allow_root=True), 4)
        self.assertNotIn("privilege.root", self.probes)

    def test_missing_and_required_kernel_failure_are_partial(self):
        for scenario, key in (("missing", "identity.vendor_build"), ("kernel_missing", "kernel.release")):
            with self.subTest(scenario=scenario):
                self.assertEqual(self.collect(scenario), 4)
                self.assertEqual(self.record["status"], "partial")
                self.assertEqual(self.probes[key]["status"], "unavailable")
                self.assertEqual(self.probes["input.devices"]["status"], "ok")

    def test_corrupt_binary_and_utf8_preserve_raw_bytes(self):
        for scenario, key, profile in (("corrupt_gzip", "kernel.config", "extended"),
                                       ("bad_dt", "dt.identity", "extended"),
                                       ("invalid_utf8", "kernel.version", "basic")):
            with self.subTest(scenario=scenario):
                self.assertEqual(self.collect(scenario, profile), 4)
                self.assertEqual(self.probes[key]["status"], "parse_error")
                capture = self.probes[key]["attempts"][0]["stdout"]
                raw = (self.run_path / capture["path"]).read_bytes()
                self.assertEqual(sha256(raw), capture["sha256"])
                if scenario == "invalid_utf8":
                    self.assertIn(b"\xff", raw)

    def test_disconnect_stops_remaining_commands(self):
        self.assertEqual(self.collect("disconnect"), 4)
        self.assertEqual(self.record["error_code"], "device_disconnected")
        self.assertEqual(self.probes["kernel.release"]["status"], "ok")
        self.assertEqual(self.probes["memory.info"]["error_code"], "device_disconnected")
        self.assertEqual(self.calls[-1][-1], "cat /proc/version")

    def test_client_error_does_not_claim_remote_exit_status(self):
        self.assertEqual(self.collect("client_error"), 4)
        attempt = self.probes["kernel.version"]["attempts"][0]
        self.assertEqual(attempt["status"], "failed")
        self.assertEqual(attempt["host_exit_code"], 1)
        self.assertIsNone(attempt["remote_exit_code"])

    def test_timeout_does_not_kill_server_and_preserves_prior_results(self):
        self.assertEqual(self.collect("timeout", timeout=0.75), 4)
        self.assertEqual(self.probes["kernel.version"]["status"], "timeout")
        self.assertEqual(self.probes["kernel.release"]["status"], "ok")
        self.assertTrue(any(item["code"] == "cleanup_unconfirmed" for item in self.record["limitations"]))
        self.assertFalse(any("kill-server" in call for call in self.calls))

    def test_output_limit_and_total_budget(self):
        self.assertEqual(self.collect("flood", probe_limit=4096), 4)
        self.assertEqual(self.probes["kernel.version"]["status"], "truncated")
        self.assertEqual(self.probes["input.devices"]["status"], "ok")
        self.assertEqual(self.collect("flood", total_limit=1800), 4)
        self.assertEqual(self.probes["input.devices"]["status"], "skipped")
        self.assertEqual(self.probes["input.devices"]["error_code"], "output_budget")
        total = sum(capture["size_bytes"] for probe in self.record["probes"] for attempt in probe["attempts"] for capture in (attempt["stdout"], attempt["stderr"]))
        self.assertLessEqual(total, 1800)

    @unittest.skipIf(os.name == "nt", "real SIGINT parent delivery is POSIX-specific")
    def test_sigint_writes_interrupted_run_and_keeps_completed_probe(self):
        self.assertEqual(self.collect("interrupt"), 130)
        self.assertEqual(self.record["status"], "interrupted")
        self.assertEqual(self.probes["kernel.release"]["status"], "ok")
        self.assertEqual(self.probes["input.devices"]["error_code"], "user_interrupted")

    def test_new_runs_and_reports_never_overwrite(self):
        self.collect()
        first = self.run_path
        before = (first / "run.json").read_bytes()
        report1 = write_report(first, "private")
        report2 = write_report(first, "private")
        self.assertNotEqual(report1, report2)
        self.collect()
        self.assertNotEqual(first, self.run_path)
        self.assertEqual(before, (first / "run.json").read_bytes())

    def test_shareable_allowlist_and_injected_public_strings(self):
        self.collect("missing")
        self.record["facts"].append({"key": "input.reviewed_names", "value": ["normal touch", "12:34:56:78:9a:bc", "SYNTHETIC-serial-123", "/home/fixture/private", "x\n# injected"],
                                    "unit": None, "source_probe": None, "evidence": "manual", "reason": None,
                                    "annotation": {"author": "fixture", "at": self.record["started_at"], "basis": "synthetic privacy test"}})
        for fact in self.record["facts"]:
            if fact["key"] == "identity.rom_build":
                fact["value"] = "[click](https://example.invalid) <script>"
            if fact["key"] == "identity.bootloader":
                fact["value"] = "contains SYNTHETIC-serial-123"
        (self.run_path / "run.json").write_bytes(json_bytes(self.record))
        report = write_report(self.run_path, "shareable").read_text(encoding="utf-8")
        for secret in ("SYNTHETIC-serial-123", "12:34:56:78:9a:bc", "/home/fixture/private", "/data/secret", "androidboot.serialno", str(self.workspace)):
            self.assertNotIn(secret, report)
        self.assertIn("partial", report)
        self.assertIn("withheld", report)
        self.assertNotIn("[click](", report)
        self.assertNotIn("<script>", report)

    def test_tampered_and_unsafe_evidence_is_rejected(self):
        self.collect()
        capture = self.probes["kernel.release"]["attempts"][0]["stdout"]
        path = self.run_path / capture["path"]
        path.write_bytes(b"changed")
        with self.assertRaises(PortError) as context:
            write_report(self.run_path, "shareable")
        self.assertEqual(context.exception.code, "artifact_mismatch")
        capture["path"] = "../escape"
        with self.assertRaises(PortError) as context:
            validate_run(self.record)
        self.assertEqual(context.exception.code, "unsafe_path")

    def test_workspace_lock_not_removed_or_overwritten(self):
        with WorkspaceLock(self.workspace, "owner") as lock:
            saved = lock.path.read_bytes()
            with self.assertRaises(PortError) as context:
                Collector(self.workspace, "tablet-a", "basic", adb=self.adb).run()
            self.assertEqual(context.exception.code, "lock_busy")
            self.assertEqual(lock.path.read_bytes(), saved)

    @unittest.skipIf(os.name == "nt", "unprivileged directory symlinks checked in Linux/WSL")
    def test_symlink_output_tree_is_rejected_before_adb(self):
        target = self.workspace / "other"
        target.mkdir()
        (self.workspace / "private").symlink_to(target, target_is_directory=True)
        with self.assertRaises(PortError) as context:
            Collector(self.workspace, "tablet-a", "basic", adb=self.adb).run()
        self.assertEqual(context.exception.code, "unsafe_path")
        self.assertFalse(self.log.exists())

    def test_contract_rejects_unknown_fields_bool_size_and_probe_injection(self):
        self.collect()
        mutations = [lambda value: value.update(extra=True),
                     lambda value: value.update(schema_version=True),
                     lambda value: value.update(schema_version=2),
                     lambda value: value.update(profile=[]),
                     lambda value: value.update(started_at="2026-09-30Z"),
                     lambda value: value["probes"][4].update(status="failed", error_code="identity_unverified"),
                     lambda value: value["probes"][0].update(id="injected | serial=value"),
                     lambda value: value["probes"][0]["attempts"][0]["stdout"].update(size_bytes=True)]
        for mutation in mutations:
            value = copy.deepcopy(self.record)
            mutation(value)
            with self.assertRaises(PortError):
                validate_run(value)

    def test_unfinished_events_do_not_become_completed_facts(self):
        self.collect()
        (self.run_path / "run.json").unlink()
        with (self.run_path / "events.jsonl").open("ab") as stream:
            stream.write(b'{"seq":999')
        report = write_report(self.run_path, "shareable").read_text(encoding="utf-8")
        self.assertIn("미종결", report)
        self.assertIn("무시: 예", report)
        self.assertNotIn("SM-T500", report)

    def test_missing_explicit_adb_never_falls_back(self):
        with self.assertRaises(PortError) as context:
            resolve_adb(str(self.workspace / "missing adb.exe"))
        self.assertEqual(context.exception.code, "tool_missing")

    def test_cli_doctor_missing_adb_is_prerequisite_failure(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/portctl.py"), "doctor", "--scope", "collect", "--adb", str(self.workspace / "absent.exe")], capture_output=True)
        self.assertEqual(result.returncode, 3)
        self.assertIn(b"tool_missing", result.stderr)
        self.assertIn("필요한 실행 파일", result.stderr.decode("utf-8"))
        self.assertFalse(self.log.exists())

    def test_missing_adb_collection_records_failed_run(self):
        code, run = Collector(self.workspace, "tablet-a", "basic", adb_path=str(self.workspace / "absent.exe")).run()
        record = load_run(run)
        self.assertEqual(code, 3)
        self.assertEqual(record["error_code"], "tool_missing")
        self.assertTrue(all(probe["status"] == "skipped" for probe in record["probes"]))

    def test_cli_invalid_root_and_alias_do_not_run_collection(self):
        for args in (["collect", "--device-alias", "bad;name", "--profile", "basic"],
                     ["collect", "--device-alias", "tablet-a", "--profile", "basic", "--allow-root"]):
            result = subprocess.run([sys.executable, str(ROOT / "tools/portctl.py"), *args], capture_output=True)
            self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())


class ProcessAndParserTests(unittest.TestCase):
    def test_concurrent_stdout_stderr_no_deadlock_and_combined_limit(self):
        script = "import os,threading; t=threading.Thread(target=lambda:os.write(2,b'e'*1048576));t.start();os.write(1,b'o'*1048576);t.join()"
        result = Runner().run([sys.executable, "-c", script], timeout=3, limit=3 * 1048576)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(result.stdout), 1048576)
        self.assertEqual(len(result.stderr), 1048576)
        capped = Runner().run([sys.executable, "-c", script], timeout=3, limit=16384)
        self.assertEqual(capped.error_code, "output_limit")
        self.assertEqual(len(capped.stdout) + len(capped.stderr), 16384)

    def test_keyboard_interrupt_returns_bounded_result(self):
        with patch("portlib.process.queue.Queue.get", side_effect=KeyboardInterrupt):
            result = Runner().run([sys.executable, "-c", "import time;time.sleep(3)"], timeout=4)
        self.assertEqual(result.error_code, "user_interrupted")
        self.assertTrue(result.cleanup_unconfirmed)

    def test_gzip_truncated_crc_and_decompression_limit(self):
        data = gzip.compress(b"CONFIG_TEST=y\n", mtime=0)
        for invalid in (data[:-3], data[:-8] + bytes([data[-8] ^ 255]) + data[-7:]):
            with self.assertRaises(ReadIssue) as context:
                config(invalid)
            self.assertEqual(context.exception.status, "parse_error")
        with self.assertRaises(ReadIssue) as context:
            config(gzip.compress(b"x" * (16 * 1048576 + 1), mtime=0))
        self.assertEqual(context.exception.status, "truncated")

    def test_sysfs_denied_missing_limits_and_raw_integer(self):
        parsed = sysfs(b"PORTCTL-SYS1\nATTR\tpower_supply\tbattery\tcurrent_now\t-1200\nATTR\tpower_supply\tusb\tcapacity\t!missing\n")
        self.assertEqual(parsed.value[0]["value"], -1200)
        self.assertEqual(parsed.status, "unavailable")
        self.assertEqual(sysfs(b"PORTCTL-SYS1\nDENIED\t/sys/class/net\n").status, "permission_denied")
        self.assertEqual(sysfs(b"PORTCTL-SYS1\nLIMIT\t/sys/class/net\n").status, "truncated")

    def test_duplicate_json_and_nonfinite_values(self):
        for data in (b'{"a":1,"a":2}', b'{"a":NaN}'):
            with self.assertRaises(PortError):
                decode_json(data)

    @unittest.skipIf(os.name == "nt", "POSIX shell syntax check runs in Linux/WSL")
    def test_all_fixed_remote_scripts_have_valid_shell_syntax(self):
        for probe in BASIC + EXTENDED:
            with self.subTest(probe=probe.id):
                result = subprocess.run(["sh", "-n", "-c", probe.command], capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
