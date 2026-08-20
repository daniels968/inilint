import argparse
import json
import sys
from dataclasses import asdict

from .linter import format_finding, lint


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inilint", description="Lint an INI file")
    parser.add_argument("path", help="path to the .ini file to check")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="output format (default: text)",
    )
    args = parser.parse_args(argv)

    with open(args.path, "r", encoding="utf-8") as handle:
        text = handle.read()

    findings = lint(text)
    if args.format == "json":
        payload = [{"path": args.path, **asdict(finding)} for finding in findings]
        print(json.dumps(payload, indent=2))
    else:
        for finding in findings:
            print(format_finding(args.path, finding))

    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
