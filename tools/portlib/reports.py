"""Offline reports: explicit allowlist and no raw strings in shareable output."""
import html
import json
from pathlib import Path
import re

from .contracts import RUN_ID, decode_json, load_run, read_limited, require, timestamp
from .errors import ERRORS, PortError
from .probes import ALL
from .records import mkdir_private, new_id, write_new

PUBLIC_FACTS = {"identity.model", "identity.codename", "identity.rom_build",
                "identity.vendor_build", "identity.bootloader", "kernel.release", "memory.total_bytes"}
SENSITIVE = re.compile(r"(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{16,}|\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:serial(?:no)?|ssid|password|token|account)\s*[=:]|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:/home/|/Users/|/data/|/storage/|/mnt/|[A-Za-z]:[\\/])", re.I)


def escape(value, limit=1600):
    rendered = value if type(value) is str else json.dumps(value, ensure_ascii=False, allow_nan=False)
    rendered = rendered[:limit].replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|~-])", r"\\\1", html.escape(rendered))


def public_value(value, record):
    if type(value) is int:
        return str(value)
    if type(value) is not str or len(value) > 256 or not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return "withheld (형식 또는 길이)"
    blocked = [record["target"]["serial"], record["host"]["cwd"], record["host"]["adb_path"]]
    if SENSITIVE.search(value) or any(secret and secret.casefold() in value.casefold() for secret in blocked):
        return "withheld (식별자 또는 경로)"
    return escape(value, 256)


def private_report(record):
    lines = [f"# 기기 조사 — {record['status']} (비공개)", "",
             f"실행 ID: {record['run_id']} / 별칭: {escape(record['device_alias'])}", "",
             f"시각: {record['started_at']} → {record['finished_at']}", "",
             f"기록 도구: {escape(record['tool_revision'])}", "",
             f"실행 환경: {escape(record['host'])}", "",
             "[전체 실행 JSON](../run.json). 긴 관측 값은 이 보고서에서 요약하며 전체 값과 원본은 JSON·증거 파일을 확인하세요.", "",
             "관측 자료는 하드웨어 실동작·부팅·복구 시험 결과와 별도로 확인해야 합니다."]
    facts = {fact["source_probe"]: [] for fact in record["facts"]}
    for fact in record["facts"]:
        facts[fact["source_probe"]].append(fact)
    for probe in record["probes"]:
        definition = ALL[probe["id"]]
        lines += ["", f"## {probe['id']}", "", f"목적: {definition.purpose}", "",
                  f"실행 결과: {probe['status']} / {ERRORS.get(probe['error_code'], '관측 완료')}"]
        for index, attempt in enumerate(probe["attempts"]):
            lines += ["", f"시도 {index + 1}: {attempt['privilege']}, host exit={attempt['host_exit_code']}, remote exit={attempt['remote_exit_code']}, {attempt['duration_ms']}ms, {attempt['status']}",
                      "", f"명령: {escape(attempt['argv'], 2400)}"]
            for stream in ("stdout", "stderr"):
                capture = attempt[stream]
                if capture:
                    lines += ["", f"원본 {stream}: [파일](../{capture['path']}), {capture['size_bytes']} bytes, SHA-256 {capture['sha256']}"]
        for fact in facts.get(probe["id"], []):
            lines += ["", f"관측 {escape(fact['key'])}: {escape(fact['value'])}"]
        lines += ["", f"의미: {definition.meaning}", "",
                  "한계: 수집 권한·등록 상태·값의 단위와 실제 사용 시험을 대조하세요."]
    if record["limitations"]:
        lines += ["", "## 실행 한계", ""]
        lines += [f"- {ERRORS[item['code']]} ({escape(item['item_id'])})" for item in record["limitations"]]
    lines += ["", "## 다음 행동", "", "1. 실패·접근 제한 항목과 원본을 검토한다.",
              "2. ROM·kernel·vendor와 소스 commit의 대응 근거를 정리한다.",
              "3. 복구 계획에 따라 정상 이미지·백업 확보 대상을 정한다."]
    return "\n".join(lines) + "\n"


def shareable_report(record):
    lines = [f"# 기기 조사 — {record['status']} (공유 검토용)", "",
             "공개 전 사람이 내용을 검토해야 합니다. 실제 기기 지원·기능 성공을 인증하는 문서가 아닙니다.", "",
             f"실행 ID: {record['run_id']} / schema: 1", "",
             f"별칭: {public_value(record['device_alias'], record)} / profile: {record['profile']}", "",
             f"도구 commit: {record['tool_revision']['git_commit'] or '미확인'}", "",
             "| 항목 | 상태 | 설명 |", "| --- | --- | --- |"]
    for probe in record["probes"]:
        lines.append(f"| {probe['id']} | {probe['status']} | {ERRORS.get(probe['error_code'], '관측 완료')} |")
    lines += ["", "## 허용된 관측", ""]
    for fact in record["facts"]:
        if fact["key"] in PUBLIC_FACTS:
            lines.append(f"- {fact['key']}: {public_value(fact['value'], record)}")
        elif fact["key"] == "storage.partitions" and type(fact["value"]) is list:
            for partition in fact["value"]:
                if type(partition) is dict and type(partition.get("name")) is str and re.fullmatch(r"(?:mmcblk\d+(?:p\d+)?|sd[a-z]+\d*|dm-\d+|loop\d+|ram\d+)", partition["name"]) and type(partition.get("size_bytes")) is int:
                    lines.append(f"- partition: {public_value(partition['name'], record)}, {partition['size_bytes']} bytes")
        elif fact["key"] == "input.reviewed_names" and fact["evidence"] == "manual" and type(fact["value"]) is list:
            for name in fact["value"]:
                lines.append(f"- input: {public_value(name, record)}")
    return "\n".join(lines) + "\n"


def unfinished_report(root):
    data = read_limited(root / "events.jsonl", 4 * 1024 * 1024)
    lines = data.splitlines(keepends=True)
    ignored = bool(lines and not lines[-1].endswith(b"\n"))
    if ignored:
        lines.pop()
    count = 0
    for line in lines:
        event = decode_json(line)
        require(type(event) is dict and set(event) == {"seq", "at", "event", "item_id", "state", "error_code"})
        count += 1
        require(type(event["seq"]) is int and event["seq"] == count)
        timestamp(event["at"])
        require(event["item_id"] is None or (type(event["item_id"]) is str and event["item_id"] in ALL))
        require(event["error_code"] is None or (type(event["error_code"]) is str and event["error_code"] in ERRORS))
    return ("# 기기 조사 — 미종결 실행\n\n"
            f"실행 ID: {root.name}\n\n"
            f"{ERRORS['incomplete_run']} 최종 상태와 사실을 재구성하지 않았습니다.\n\n"
            f"읽은 이벤트: {count}개. 마지막 불완전한 행 무시: {'예' if ignored else '아니오'}.\n")


def write_report(run_directory, view):
    root = Path(run_directory).absolute()
    if view not in {"private", "shareable"}:
        raise PortError("invalid_arguments", 2)
    if not re.fullmatch(RUN_ID, root.name) or root.parent.name != "runs" or root.parent.parent.name != "private":
        raise PortError("unsafe_path", 5)
    if root.resolve() != root or any(path.is_symlink() for path in (root, root.parent, root.parent.parent)):
        raise PortError("unsafe_path", 5)
    if (root / "run.json").exists() or (root / "run.json").is_symlink():
        record = load_run(root)
        content = private_report(record) if view == "private" else shareable_report(record)
    else:
        content = unfinished_report(root)
    parent = root / "reports"
    mkdir_private(parent)
    while True:
        destination = parent / f"{new_id()}.{view}.md"
        try:
            write_new(destination, content.encode("utf-8"))
            return destination
        except FileExistsError:
            continue
