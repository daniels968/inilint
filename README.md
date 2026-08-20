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

Early. The checks above cover the common ways an INI file goes wrong, but
there's no config for which checks to run, and no handling yet for
multi-line values or the `[section.subsection]` conventions some tools use.

## license

MIT, see LICENSE.
