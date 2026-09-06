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

    def test_disable_flag_suppresses_a_check(self):
        path = self._write("[server]\nhost = a\n[server]\nhost = b\n")
        exit_code, out = self._run(path, "--disable", "duplicate-section")
        self.assertEqual(out, "")
        self.assertEqual(exit_code, 0)

    def test_disable_flag_rejects_an_unknown_code(self):
        path = self._write("[server]\nhost = a\n")
        with self.assertRaises(SystemExit):
            main([path, "--disable", "not-a-real-code"])

    def test_config_file_disables_a_check(self):
        path = self._write("[server]\nhost = a\n[server]\nhost = b\n")
        handle, config_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            json.dump({"disable": ["duplicate-section"]}, f)
        self.addCleanup(os.remove, config_path)
        exit_code, out = self._run(path, "--config", config_path)
        self.assertEqual(out, "")
        self.assertEqual(exit_code, 0)

    def test_multiple_paths_are_checked_and_reported_separately(self):
        clean_path = self._write("[server]\nhost = a\n")
        broken_path = self._write("host = a\n[server]\n")
        exit_code, out = self._run(clean_path, broken_path, "--format", "json")
        findings = json.loads(out)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["path"], broken_path)
        self.assertEqual(findings[0]["code"], "key-outside-section")
        self.assertEqual(exit_code, 1)

    def test_config_file_with_unknown_code_raises(self):
        path = self._write("[server]\nhost = a\n")
        handle, config_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            json.dump({"disable": ["not-a-real-code"]}, f)
        self.addCleanup(os.remove, config_path)
        with self.assertRaises(ValueError):
            main([path, "--config", config_path])


if __name__ == "__main__":
    unittest.main()
