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

    def test_inline_comment_after_value_is_stripped(self):
        text = "[server]\nhost = localhost ; the main host\n"
        self.assertEqual(lint(text), [])

    def test_inline_comment_with_hash_is_stripped(self):
        text = "[server]\nhost = localhost # the main host\n"
        self.assertEqual(lint(text), [])

    def test_inline_comment_on_section_header_is_stripped(self):
        text = "[server] ; the main server\nhost = localhost\n"
        self.assertEqual(lint(text), [])

    def test_comment_marker_without_leading_space_is_kept_in_value(self):
        text = "[server]\npath = C:\\a;b\n"
        findings = lint(text)
        self.assertEqual(findings, [])

    def test_duplicate_key_still_detected_with_trailing_comment(self):
        text = "[server]\nhost = a ; first\nhost = b ; second\n"
        findings = lint(text)
        dup = next(f for f in findings if f.code == "duplicate-key")
        self.assertEqual(dup.line, 3)

    def test_lint_does_not_mutate_its_input(self):
        text = "[server]\nhost = localhost\n"
        before = text
        lint(text)
        self.assertEqual(text, before)

    def test_disabled_code_is_left_out_of_the_results(self):
        text = "[server]\nhost = a\n[server]\nhost = b\n"
        findings = lint(text, disabled=frozenset({"duplicate-section"}))
        codes = [f.code for f in findings]
        self.assertNotIn("duplicate-section", codes)
        self.assertIn("duplicate-key", codes)

    def test_disabling_empty_section_name_does_not_change_later_checks(self):
        # even with the finding itself suppressed, the header still resets
        # the current section, so a key right after it is still outside one
        text = "[]\nhost = localhost\n"
        findings = lint(text, disabled=frozenset({"empty-section-name"}))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "key-outside-section")


if __name__ == "__main__":
    unittest.main()
