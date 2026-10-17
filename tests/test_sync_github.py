import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/sync_github.py"
spec = importlib.util.spec_from_file_location("sync_github", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class ConversionSafetyTests(unittest.TestCase):
    def test_domain_rules_preserve_values_and_order(self):
        data = {"version": 2, "rules": [{"domain": ["api.example.com"], "domain_suffix": ["example.org"], "domain_keyword": ["example"]}]}
        text, count = sync.convert(data)
        expected = ["DOMAIN,api.example.com", "DOMAIN-SUFFIX,example.org", "DOMAIN-KEYWORD,example"]
        import json
        actual = [json.loads(line[4:]) for line in text.splitlines() if line.startswith("  - ")]
        self.assertEqual(actual, expected)
        self.assertEqual(count, len(expected))

    def test_unsupported_field_is_not_silently_dropped(self):
        with self.assertRaises(ValueError):
            sync.convert({"version": 2, "rules": [{"domain_suffix": ["github.com"], "invert": True}]})

    def test_empty_source_and_unknown_version_are_rejected(self):
        for data in ({"version": 2, "rules": []}, {"version": 3, "rules": [{"domain_suffix": ["github.com"]}]}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                sync.convert(data)

    def test_duplicate_keys_and_rule_delimiters_are_rejected(self):
        with self.assertRaises(ValueError):
            sync.parse_source(b'{"version":2,"version":2,"rules":[]}')
        for value in ("github.com,Proxy", "github.com\nMATCH,DIRECT"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                sync.convert({"version": 2, "rules": [{"domain_suffix": [value]}]})

    def test_invalid_download_leaves_existing_ruleset_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "rules/GitHub.yaml"
            target.parent.mkdir()
            target.write_text("previous validated content\n")
            source = root / "bad.json"
            source.write_text('{"version":2,"rules":[{"unknown":["github.com"]}]}')
            result = subprocess.run([sys.executable, str(SCRIPT), "--source-file", str(source), "--output-root", str(root)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_text(), "previous validated content\n")


if __name__ == "__main__":
    unittest.main()
