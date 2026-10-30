#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""고정 Linux 소스와 호스트 gcc/dtc로 DT만 컴파일하고 출처를 기록한다."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--linux", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.linux.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    board = Path(__file__).resolve().with_name("sm6115-samsung-gta4lwifi.dts")
    makefile = (source / "Makefile").read_text()
    version = ".".join(re.search(rf"^{key} = (\d+)$", makefile, re.M)[1]
                       for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL"))
    if version != "6.18.35":
        parser.error(f"검증 기준은 Linux 6.18.35이며 입력은 {version}")

    record = {
        "started": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cwd": str(Path.cwd()), "linux": str(source), "version": version,
        "scope": "DT compilation only; no kernel, modules, boot image or device test",
        "commands": [], "inputs": [
            {"path": str(Path(__file__).resolve()), "sha256": digest(Path(__file__))},
            {"path": str(source / "Makefile"), "sha256": digest(source / "Makefile")},
        ], "outputs": [],
    }

    def run(command, log):
        result = subprocess.run(command, cwd=source, capture_output=True)
        (output / log).write_bytes(result.stdout + result.stderr)
        record["commands"].append({"argv": command, "exit": result.returncode,
                                   "log": str(output / log)})
        (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
        result.check_returncode()
        return result.stdout

    record["tools"] = {
        "gcc": run(["gcc", "--version"], "gcc-version.log").decode().splitlines()[0],
        "dtc": run(["dtc", "--version"], "dtc-version.log").decode().strip(),
    }
    qcom = source / "arch/arm64/boot/dts/qcom"
    for dts in [board, qcom / "sm6115p-lenovo-j606f.dts"]:
        stem = dts.stem
        preprocessed = output / (stem + ".preprocessed.dts")
        run(["gcc", "-E", "-nostdinc", "-undef", "-D__DTS__", "-x", "assembler-with-cpp",
             "-I", str(qcom), "-I", str(source / "include"),
             "-I", str(source / "scripts/dtc/include-prefixes"),
             "-o", str(preprocessed), str(dts)], stem + "-cpp.log")
        dependencies = set(re.findall(r'^# \d+ "([^"<>]+)"', preprocessed.read_text(), re.M))
        for item in sorted(dependencies):
            path = Path(item)
            if not path.is_absolute():
                path = source / path
            if path.is_file():
                record["inputs"].append({"path": str(path), "sha256": digest(path)})
        dtb = output / (stem + ".dtb")
        run(["dtc", "-I", "dts", "-O", "dtb", "-@", "-o", str(dtb),
             str(preprocessed)], stem + "-dtc.log")
        record["outputs"].append({"path": str(dtb), "bytes": dtb.stat().st_size,
                                   "sha256": digest(dtb)})
    record["finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record["outputs"], indent=2))


if __name__ == "__main__":
    main()
