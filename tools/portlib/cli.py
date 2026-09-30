import argparse
from pathlib import Path
import re
import sys

from .adb import resolve_adb
from .collector import Collector
from .errors import ERRORS, PortError
from .parsers import ReadIssue, version
from .process import Runner
from .records import REPO_ROOT
from .reports import write_report


def alias(value):
    if not re.fullmatch(r"[a-z0-9-]{1,32}", value):
        raise argparse.ArgumentTypeError("별칭은 소문자·숫자·하이픈 1~32자로 지정하세요.")
    return value


def serial(value):
    if not value or len(value) > 256 or any(ord(char) < 32 for char in value):
        raise argparse.ArgumentTypeError("유효한 ADB 식별자를 지정하세요.")
    return value


def parser():
    root = argparse.ArgumentParser(description="SM-T500 읽기 전용 조사 도구 (Python 3.11+)")
    commands = root.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="ADB 설치·버전 검사")
    doctor.add_argument("--scope", choices=["collect"], required=True)
    doctor.add_argument("--adb")
    collect = commands.add_parser("collect", help="대상 식별 후 지정한 조사 수행")
    collect.add_argument("--device-alias", type=alias, required=True)
    collect.add_argument("--profile", choices=["basic", "extended"], required=True)
    collect.add_argument("--allow-root", action="store_true")
    collect.add_argument("--serial", type=serial)
    collect.add_argument("--adb")
    collect.add_argument("--workspace", type=Path, default=REPO_ROOT)
    report = commands.add_parser("report", help="기존 실행의 새 설명 보고서 생성")
    report.add_argument("--run", type=Path, required=True)
    report.add_argument("--view", choices=["private", "shareable"], required=True)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            adb = resolve_adb(args.adb)
            result = Runner().run(adb.host("version"), limit=65536)
            if result.error_code or result.exit_code != 0:
                raise PortError("tool_failed")
            try:
                version(result.stdout)
            except ReadIssue:
                raise PortError("tool_failed") from None
            print(f"ADB 실행·버전 확인 완료: {adb.prefix[0]}")
            print("다음 단계: USB 연결·인증을 준비하고 basic 수집을 실행하세요.")
            return 0
        if args.command == "collect":
            if args.allow_root and args.profile != "extended":
                raise PortError("invalid_arguments", 2)
            code, _ = Collector(args.workspace, args.device_alias, args.profile,
                                allow_root=args.allow_root, serial=args.serial,
                                adb_path=args.adb, progress=print).run()
            return code
        path = write_report(args.run, args.view)
        print(f"보고서 생성: {path}")
        if args.view == "shareable":
            print("공개 전 사람이 내용을 검토하세요.")
        return 0
    except PortError as error:
        print(f"{error.code}: {ERRORS[error.code]}", file=sys.stderr)
        return error.exit_code
    except KeyboardInterrupt:
        print(ERRORS["user_interrupted"], file=sys.stderr)
        return 130
    except Exception:
        # Private raw diagnostics must not accidentally become console/shareable errors.
        print(ERRORS["internal_error"], file=sys.stderr)
        return 1
