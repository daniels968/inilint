"""Line-by-line checks for INI files.

Every public function here takes plain text (or a Finding) and returns a
plain value. Nothing reads a file or touches the filesystem, so the whole
module can be exercised with string literals in tests.
"""

from dataclasses import dataclass
import re

_BLANK_RE = re.compile(r"^\s*$")
_COMMENT_RE = re.compile(r"^\s*[;#]")
_SECTION_RE = re.compile(r"^\s*\[(?P<name>[^]]*)\]\s*$")
# a key/value line: anything before the first '=' or ':' that isn't itself
# one of those separators, then the separator, then the (possibly empty) value
_KEY_VALUE_RE = re.compile(r"^\s*(?P<key>[^=:\s][^=:]*)\s*[=:]\s*(?P<value>.*)$")
# an inline comment has to be set off by whitespace, so `path = C:\a;b` keeps
# its semicolon but `path = C:\a ; note` does not
_INLINE_COMMENT_RE = re.compile(r"\s+[;#].*$")


@dataclass(frozen=True)
class Finding:
    line: int
    code: str
    message: str
    severity: str = "warning"


def lint(text: str) -> list[Finding]:
    """Check INI-formatted text and return every finding, in line order."""
    findings: list[Finding] = []
    current_section: str | None = None
    section_defined_at: dict[str, int] = {}
    keys_defined_at: dict[str, dict[str, int]] = {}

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if _BLANK_RE.match(raw_line) or _COMMENT_RE.match(raw_line):
            continue

        line = _INLINE_COMMENT_RE.sub("", raw_line)

        section_match = _SECTION_RE.match(line)
        if section_match:
            name = section_match.group("name").strip()
            if not name:
                findings.append(
                    Finding(lineno, "empty-section-name", "section header has no name", "error")
                )
                current_section = None
                continue
            if name in section_defined_at:
                findings.append(
                    Finding(
                        lineno,
                        "duplicate-section",
                        f"section '{name}' was already defined on line {section_defined_at[name]}",
                    )
                )
            else:
                section_defined_at[name] = lineno
                keys_defined_at.setdefault(name, {})
            current_section = name
            continue

        kv_match = _KEY_VALUE_RE.match(line)
        if kv_match:
            key = kv_match.group("key").strip()
            if current_section is None:
                findings.append(
                    Finding(
                        lineno,
                        "key-outside-section",
                        f"key '{key}' appears before any section header",
                        "error",
                    )
                )
                continue
            keys = keys_defined_at.setdefault(current_section, {})
            if key in keys:
                findings.append(
                    Finding(
                        lineno,
                        "duplicate-key",
                        f"key '{key}' was already set on line {keys[key]} in section [{current_section}]",
                    )
                )
            else:
                keys[key] = lineno
            continue

        findings.append(
            Finding(
                lineno,
                "malformed-line",
                "line is not blank, a comment, a section header, or a key/value pair",
                "error",
            )
        )

    return findings


def format_finding(path: str, finding: Finding) -> str:
    """Render one finding the way a compiler would: path:line: severity: message."""
    return f"{path}:{finding.line}: {finding.severity}: {finding.message} [{finding.code}]"
