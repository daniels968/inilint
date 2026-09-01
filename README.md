# inilint

A linter for INI files. It reads a file and prints every problem it finds,
one line per finding, with the line number where it happened.

## why

INI has no real spec, so every parser bends the format its own way. The
practical issue that keeps showing up: if a key or a section is defined
twice, most parsers just keep the last one and say nothing. That's fine
until you're staring at a config that isn't doing what you configured,
because a copy-pasted `[server]` block halfway down the file quietly
overwrote the one at the top. `configparser` will raise on some of these
cases if you use it strictly, but a lot of code reads INI files by hand or
with `strict=False`, and none of that tells you *where* the duplicate is.

inilint just checks the text and tells you the line number.

## what it checks

- `duplicate-section` - a `[section]` header appears more than once
- `duplicate-key` - a key is set twice in the same section
- `key-outside-section` - a `key = value` line appears before any section header
- `empty-section-name` - a header like `[]` with nothing inside the brackets
- `malformed-line` - a line that isn't blank, a comment, a section header, or a key/value pair

A `;` or `#` after a value is treated as an inline comment and ignored, as
long as it's set off from the value by whitespace: `host = localhost ; the
main one` has no `duplicate-key` or `malformed-line` surprise waiting in it.
Without that leading space it's just part of the value, so a Windows path
like `path = C:\tools;C:\bin` is left alone.

## usage

```
$ cat example.ini
[server]
host = localhost
port = 8080

[server]
host = 0.0.0.0

logging = verbose

$ python -m inilint.cli example.ini
example.ini:5: warning: section 'server' was already defined on line 1 [duplicate-section]
example.ini:8: error: key 'logging' appears before any section header [key-outside-section]
```

Exit status is 1 if any finding is an `error`, 0 otherwise.

Pass `--format json` to get the findings as a JSON array instead, one object
per finding (`path`, `line`, `code`, `message`, `severity`):

```
$ python -m inilint.cli example.ini --format json
[
  {
    "path": "example.ini",
    "line": 5,
    "code": "duplicate-section",
    "message": "section 'server' was already defined on line 1",
    "severity": "warning"
  },
  ...
]
```

## disabling checks

Pass `--disable CODE` to turn off one check, or pass it more than once to
turn off several:

```
$ python -m inilint.cli example.ini --disable duplicate-section --disable malformed-line
```

For a standing configuration, put a JSON config file next to the file
you're checking and pass its path with `--config`, or name it
`.inilintrc.json` in the current directory and it's picked up automatically:

```json
{
  "disable": ["duplicate-section"]
}
```

An unknown code in either place is an error rather than a silent no-op.
Disabling a check only removes it from the output; the linter still tracks
sections and keys underneath, so e.g. disabling `empty-section-name`
doesn't change whether later keys count as inside or outside a section.

## as a library

The checker itself is one pure function: text in, a list of findings out.
No file I/O, no global state, nothing to mock.

```python
from inilint.linter import lint

findings = lint("[a]\nx = 1\n[a]\nx = 2\n")
for f in findings:
    print(f.line, f.code, f.message)
```

## status

Early. The checks above cover the common ways an INI file goes wrong, and
individual checks can now be turned off, but there's no handling yet for
multi-line values or the `[section.subsection]` conventions some tools use.

## license

MIT, see LICENSE.
