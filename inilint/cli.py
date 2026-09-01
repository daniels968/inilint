import argparse
import json
import os
import sys
from dataclasses import asdict

from .linter import CODES, format_finding, lint

CONFIG_FILENAME = ".inilintrc.json"


def _load_disabled_codes(config_path: str | None) -> frozenset[str]:
    """Read the 'disable' list out of a JSON config file.

    With no explicit --config, fall back to .inilintrc.json in the current
    directory if it happens to exist; an explicit --config that's missing
    is a real error, since the user pointed at it by name.
    """
    if config_path is None:
        if not os.path.isfile(CONFIG_FILENAME):
            return frozenset()
        config_path = CONFIG_FILENAME

    with open(config_path, "r", encoding="utf-8") as handle:
        config = json.load(handle)

    disabled = config.get("disable", [])
    unknown = sorted(set(disabled) - CODES)
    if unknown:
        raise ValueError(f"unknown check code(s) in config: {', '.join(unknown)}")
    return frozenset(disabled)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inilint", description="Lint an INI file")
    parser.add_argument("path", help="path to the .ini file to check")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--config",
        help=f"path to a JSON config file with a 'disable' list of check codes "
        f"(default: {CONFIG_FILENAME} in the current directory, if present)",
    )
    parser.add_argument(
        "--disable",
        action="append",
        default=[],
        choices=sorted(CODES),
        metavar="CODE",
        help="disable a check by code; can be passed more than once",
    )
    args = parser.parse_args(argv)

    disabled = _load_disabled_codes(args.config) | frozenset(args.disable)

    with open(args.path, "r", encoding="utf-8") as handle:
        text = handle.read()

    findings = lint(text, disabled=disabled)
    if args.format == "json":
        payload = [{"path": args.path, **asdict(finding)} for finding in findings]
        print(json.dumps(payload, indent=2))
    else:
        for finding in findings:
            print(format_finding(args.path, finding))

    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
