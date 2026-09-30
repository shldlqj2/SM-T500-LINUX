#!/usr/bin/env python3
"""Repository-local entry point; Python 3.11+, standard library only."""
import sys

if sys.version_info < (3, 11):
    print("Python 3.11 이상이 필요합니다.", file=sys.stderr)
    raise SystemExit(3)

from portlib.cli import main

if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    raise SystemExit(main())
