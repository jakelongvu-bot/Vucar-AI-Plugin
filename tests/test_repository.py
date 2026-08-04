from __future__ import annotations

import importlib.util
import json
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_repository.py"
SPEC = importlib.util.spec_from_file_location("validate_repository", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load repository validator")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class RepositoryMetadataTest(unittest.TestCase):
    def test_complete_repository_validation(self) -> None:
        VALIDATOR.validate_repository()

    def test_all_json_is_canonical_and_newline_terminated(self) -> None:
        for path in sorted(ROOT.rglob("*.json")):
            if ".git" in path.parts:
                continue
            original = path.read_text(encoding="utf-8")
            parsed = json.loads(original)
            canonical = json.dumps(parsed, ensure_ascii=False, indent=2) + "\n"
            self.assertEqual(original, canonical, path.relative_to(ROOT).as_posix())

    def test_exact_mcp_endpoint_in_all_machine_readable_metadata(self) -> None:
        endpoint_pattern = re.compile(r"https://[^\s\"']+/mcp(?:\?[^\s\"']*)?")
        urls: list[str] = []
        for path in sorted(ROOT.rglob("*.json")):
            if ".git" in path.parts:
                continue
            urls.extend(endpoint_pattern.findall(path.read_text(encoding="utf-8")))
        self.assertEqual(urls, [VALIDATOR.ENDPOINT, VALIDATOR.ENDPOINT])

    def test_dual_clients_share_identity_and_version(self) -> None:
        codex = VALIDATOR.load_json("plugins/vucar/.codex-plugin/plugin.json")
        claude = VALIDATOR.load_json("plugins/vucar/.claude-plugin/plugin.json")
        registry = VALIDATOR.load_json("server.json")
        self.assertEqual(codex["name"], claude["name"])
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["version"], registry["version"])
        self.assertEqual(codex["license"], claude["license"])
        self.assertEqual(codex["mcpServers"], "./.mcp.json")

    def test_public_documentation_states_excluded_capabilities(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        for term in ("customer records", "phone numbers", "bookings", "auctions", "payments", "cannot create"):
            self.assertIn(term, text)

    def test_artwork_is_expected_png(self) -> None:
        expected = {"icon.png": (192, 192), "logo.png": (512, 512)}
        asset_root = ROOT / "plugins" / "vucar" / "assets"
        self.assertEqual({path.name for path in asset_root.iterdir()}, set(expected))
        for filename, dimensions in expected.items():
            data = (asset_root / filename).read_bytes()
            self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertEqual(struct.unpack(">II", data[16:24]), dimensions)

    def test_installed_plugin_contains_legal_and_security_files(self) -> None:
        plugin = ROOT / "plugins" / "vucar"
        self.assertEqual((plugin / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())
        self.assertEqual((plugin / "NOTICE").read_bytes(), (ROOT / "NOTICE").read_bytes())
        self.assertTrue((plugin / "SECURITY.md").is_file())
        self.assertNotIn("../../", (plugin / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
