import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/sync_rulesets.py"
spec = importlib.util.spec_from_file_location("sync_rulesets", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def entry(name):
    return {"name": name, "url": f"https://example.org/{name}.json", "license": "GPL-3.0"}


def source(domain):
    return json.dumps({"version": 2, "rules": [{"domain": [domain]}]}).encode()


class RegistrySynchronizationTests(unittest.TestCase):
    def test_valid_singbox_single_value_shorthand(self):
        text, count = sync.convert({"version": 2, "rules": [{"domain": "one.example", "domain_suffix": "two.example", "domain_keyword": "three"}]})
        self.assertEqual(count, 3)
        self.assertIn('"DOMAIN,one.example"', text)
        self.assertIn('"DOMAIN-SUFFIX,two.example"', text)
        self.assertIn('"DOMAIN-KEYWORD,three"', text)

    def test_two_unrelated_registered_sets_have_separate_outputs(self):
        outputs, counts = sync.prepare_outputs([entry("Alpha"), entry("Beta")], lambda e: source(e["name"].lower() + ".example"))
        self.assertEqual(counts, {"Alpha": 1, "Beta": 1})
        self.assertEqual(len(outputs), 6)
        self.assertIn('"DOMAIN,alpha.example"', outputs["rules/Alpha.yaml"])
        self.assertNotIn("beta.example", outputs["rules/Alpha.yaml"])
        self.assertEqual(json.loads(outputs["sources/Beta.provenance.json"])["source_url"], "https://example.org/Beta.json")

    def test_registry_entry_alone_enrolls_a_future_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "registry.json"
            snapshots = root / "input"
            snapshots.mkdir()
            registry.write_text(json.dumps({"version": 1, "rulesets": [entry("Alpha"), entry("Future")]}))
            (snapshots / "Alpha.json").write_bytes(source("alpha.example"))
            (snapshots / "Future.json").write_bytes(source("future.example"))
            command = [sys.executable, str(SCRIPT), "--registry", str(registry), "--source-dir", str(snapshots), "--output-root", str(root / "output")]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue((root / "output/rules/Future.yaml").exists())
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("updated 0 file(s)", second.stdout)

    def test_bad_second_set_preserves_entire_existing_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "registry.json"
            registry.write_text(json.dumps({"version": 1, "rulesets": [entry("Alpha"), entry("Beta")]}))
            snapshots = root / "input"
            snapshots.mkdir()
            (snapshots / "Alpha.json").write_bytes(source("changed.example"))
            (snapshots / "Beta.json").write_text('{"version":2,"rules":[{"unsupported":true}]}')
            target = root / "output/rules/Alpha.yaml"
            target.parent.mkdir(parents=True)
            target.write_text("previous validated rules\n")
            result = subprocess.run([sys.executable, str(SCRIPT), "--registry", str(registry), "--source-dir", str(snapshots), "--output-root", str(root / "output")], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_text(), "previous validated rules\n")
            self.assertFalse((root / "output/sources").exists())

    def test_failed_second_download_prevents_batch_writes(self):
        def reader(e):
            if e["name"] == "Beta":
                raise OSError("download unavailable")
            return source("alpha.example")
        with self.assertRaisesRegex(ValueError, "Beta: download unavailable"):
            sync.prepare_outputs([entry("Alpha"), entry("Beta")], reader)

    def test_names_cannot_escape_directories_or_collide_by_case(self):
        for entries in ([entry("../outside")], [entry("Alpha"), entry("alpha")]):
            with self.subTest(entries=entries), tempfile.TemporaryDirectory() as directory:
                p = Path(directory) / "registry.json"
                p.write_text(json.dumps({"version": 1, "rulesets": entries}))
                with self.assertRaises(ValueError):
                    sync.load_registry(p)

    def test_invalid_registry_and_credentialed_urls_are_rejected(self):
        for bad in ({"version": 1, "rulesets": []}, {"version": 2, "rulesets": [entry("Alpha")]}, {"version": 1, "rulesets": [dict(entry("Alpha"), url="https://user:secret@example.org/rules")]}):
            with self.subTest(data=bad), tempfile.TemporaryDirectory() as directory:
                p = Path(directory) / "registry.json"
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    sync.load_registry(p)

    def test_unsupported_types_and_suffix_semantics_do_not_broaden_matches(self):
        for rule in ({"ip_cidr": ["192.0.2.0/24"]}, {"domain_suffix": [".example.org"]}, {"type": "logical", "mode": "and", "rules": []}):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                sync.convert({"version": 2, "rules": [rule]})

    def test_noop_does_not_rewrite_existing_files(self):
        outputs, _ = sync.prepare_outputs([entry("Alpha")], lambda e: source("alpha.example"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(len(sync.write_outputs(root, outputs)), 3)
            before = {name: (root / name).stat().st_mtime_ns for name in outputs}
            self.assertEqual(sync.write_outputs(root, outputs), [])
            self.assertEqual(before, {name: (root / name).stat().st_mtime_ns for name in outputs})
