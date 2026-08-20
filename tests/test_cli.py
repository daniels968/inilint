import contextlib
import io
import json
import os
import tempfile
import unittest

from inilint.cli import main


class TestCli(unittest.TestCase):
    def _write(self, text):
        handle, path = tempfile.mkstemp(suffix=".ini")
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            f.write(text)
        self.addCleanup(os.remove, path)
        return path

    def _run(self, path, *extra_args):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = main([path, *extra_args])
        return exit_code, buffer.getvalue()

    def test_json_format_reports_findings_as_a_json_array(self):
        path = self._write("[server]\nhost = a\n[server]\nhost = b\n")
        exit_code, out = self._run(path, "--format", "json")
        findings = json.loads(out)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["code"], "duplicate-section")
        self.assertEqual(findings[0]["line"], 3)
        self.assertEqual(findings[0]["path"], path)
        self.assertEqual(exit_code, 0)

    def test_json_format_with_no_findings_is_an_empty_array(self):
        path = self._write("[server]\nhost = a\n")
        exit_code, out = self._run(path, "--format", "json")
        self.assertEqual(json.loads(out), [])
        self.assertEqual(exit_code, 0)

    def test_json_format_exit_code_reflects_errors(self):
        path = self._write("host = a\n[server]\n")
        exit_code, out = self._run(path, "--format", "json")
        findings = json.loads(out)
        self.assertEqual(findings[0]["severity"], "error")
        self.assertEqual(exit_code, 1)

    def test_text_format_is_still_the_default(self):
        path = self._write("[server]\nhost = a\n[server]\nhost = b\n")
        exit_code, out = self._run(path)
        self.assertIn("duplicate-section", out)
        self.assertFalse(out.strip().startswith("["))
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
