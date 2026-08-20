import unittest

from inilint.linter import lint


class TestLint(unittest.TestCase):
    def test_clean_file_has_no_findings(self):
        text = "[server]\nhost = localhost\nport = 8080\n"
        self.assertEqual(lint(text), [])

    def test_comments_and_blank_lines_are_ignored(self):
        text = "\n; a comment\n# also a comment\n[server]\nhost = localhost\n"
        self.assertEqual(lint(text), [])

    def test_duplicate_section_is_reported_on_the_second_line(self):
        text = "[server]\nhost = a\n[server]\nhost = b\n"
        findings = lint(text)
        codes = [f.code for f in findings]
        self.assertIn("duplicate-section", codes)
        dup = next(f for f in findings if f.code == "duplicate-section")
        self.assertEqual(dup.line, 3)

    def test_duplicate_key_is_reported_on_the_second_line(self):
        text = "[server]\nhost = a\nhost = b\n"
        findings = lint(text)
        dup = next(f for f in findings if f.code == "duplicate-key")
        self.assertEqual(dup.line, 3)

    def test_key_outside_section_is_an_error(self):
        text = "host = localhost\n[server]\nport = 8080\n"
        findings = lint(text)
        self.assertEqual(findings[0].code, "key-outside-section")
        self.assertEqual(findings[0].severity, "error")
        self.assertEqual(findings[0].line, 1)

    def test_empty_section_name_is_an_error(self):
        text = "[]\nhost = localhost\n"
        findings = lint(text)
        self.assertEqual(findings[0].code, "empty-section-name")
        self.assertEqual(findings[0].severity, "error")

    def test_malformed_line_is_reported(self):
        text = "[server]\nthis line has no separator\n"
        findings = lint(text)
        malformed = next(f for f in findings if f.code == "malformed-line")
        self.assertEqual(malformed.line, 2)

    def test_colon_is_a_valid_separator(self):
        text = "[server]\nhost: localhost\n"
        self.assertEqual(lint(text), [])

    def test_lint_does_not_mutate_its_input(self):
        text = "[server]\nhost = localhost\n"
        before = text
        lint(text)
        self.assertEqual(text, before)


if __name__ == "__main__":
    unittest.main()
