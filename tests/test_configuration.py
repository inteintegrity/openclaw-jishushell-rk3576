import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "configure", Path(__file__).parents[1] / "scripts" / "configure-openclaw.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConfigurationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "openclaw.json"
        self.original = {
            "gateway": {"auth": {"token": "test-only-token"},
                        "controlUi": {"allowedOrigins": ["http://localhost:8090"]}},
            "models": {"providers": {"example": {"apiKey": "test-only-key"}}},
            "agents": {"defaults": {"model": "example/model", "compaction": {"reserveTokens": 1000}}},
        }
        self.path.write_text(json.dumps(self.original))

    def test_preserves_credentials_model_and_unrelated_settings(self):
        module.configure(self.path, ["http://board.example:8090"])
        current = json.loads(self.path.read_text())
        self.assertEqual(current["models"], self.original["models"])
        self.assertEqual(current["gateway"]["auth"], self.original["gateway"]["auth"])
        self.assertEqual(current["agents"]["defaults"]["model"], "example/model")
        self.assertEqual(current["agents"]["defaults"]["compaction"]["reserveTokens"], 1000)
        self.assertEqual(current["gateway"]["controlUi"]["allowedOrigins"],
                         ["http://localhost:8090", "http://board.example:8090"])
        backups = list(self.path.parent.glob("*.before-rk-setup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(json.loads(backups[0].read_text()), self.original)

    def test_dry_run_does_not_write_or_create_backup(self):
        before = self.path.read_bytes()
        module.configure(self.path, ["http://board.example:8090"], dry_run=True)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.before-rk-setup-*")), [])

    def test_repeated_configuration_does_not_rewrite_or_back_up_again(self):
        module.configure(self.path, ["http://board.example:8090"])
        before = self.path.read_bytes()
        self.assertIn("Already configured", module.configure(self.path, ["http://board.example:8090"]))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(len(list(self.path.parent.glob("*.before-rk-setup-*"))), 1)

    def test_invalid_origin_leaves_configuration_untouched(self):
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            module.configure(self.path, ["http://user:password@board.example/private"])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.before-rk-setup-*")), [])


if __name__ == "__main__":
    unittest.main()
