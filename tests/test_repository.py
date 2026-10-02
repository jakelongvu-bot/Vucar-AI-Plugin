from __future__ import annotations

import importlib.util
import json
import re
import struct
import sys
import tempfile
import unittest
import zipfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_repository.py"
SPEC = importlib.util.spec_from_file_location("validate_repository", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load repository validator")
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)
sys.path.insert(0, str(ROOT / "scripts"))
import build_review_zip as BUNDLE
import smoke_test_mcp as SMOKE


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

    def test_review_cases_cover_exact_six_tool_scope(self) -> None:
        manifest = VALIDATOR.load_json("plugins/vucar/.codex-plugin/plugin.json")
        errors: list[str] = []
        VALIDATOR.validate_submission_manifest(manifest, errors)
        self.assertEqual(errors, [])
        self.assertEqual(SMOKE.EXPECTED_TOOLS, VALIDATOR.EXPECTED_TOOLS)
        self.assertEqual(SMOKE.EXPECTED_VERSION, VALIDATOR.VERSION)

    def test_submission_validator_rejects_unsafe_or_incomplete_mutations(self) -> None:
        baseline = VALIDATOR.load_json("plugins/vucar/.codex-plugin/plugin.json")
        mutations = {
            "unsupported category": lambda value: value["interface"].update(category="SHOPPING"),
            "overlong subtitle": lambda value: value["interface"].update(shortDescription="x" * 31),
            "foreign support link": lambda value: value["interface"].update(supportURL="https://example.com/support"),
            "missing skill declaration": lambda value: value.pop("skills"),
            "insufficient positive cases": lambda value: value["extensions"]["com.openai"]["review"]["test_cases"]["positive"].pop(),
            "missing behavior": lambda value: value["extensions"]["com.openai"]["review"]["test_cases"]["positive"][0].pop("expected_behavior"),
            "unknown tool": lambda value: value["extensions"]["com.openai"]["review"]["test_cases"]["positive"][0].update(tools_triggered="create_lead"),
            "negative tool action": lambda value: value["extensions"]["com.openai"]["review"]["test_cases"]["negative"][0].update(tools_triggered="estimate_vehicle_value"),
            "fake video": lambda value: value["extensions"]["com.openai"]["review"].update(demo_recording_url="https://example.com/demo"),
            "public reviewer access": lambda value: value["extensions"]["com.openai"]["review"].update(reviewer_instructions="public instructions"),
            "foreign market": lambda value: value["extensions"]["com.openai"]["publication"].update(countries=["US"]),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                manifest = deepcopy(baseline)
                mutate(manifest)
                errors: list[str] = []
                VALIDATOR.validate_submission_manifest(manifest, errors)
                self.assertTrue(errors, label)

    def test_openai_zip_is_deterministic_and_keeps_client_map_separate(self) -> None:
        client_before = (VALIDATOR.PLUGIN / ".mcp.json").read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            first = BUNDLE.build_review_zip(Path(temporary) / "first.zip")
            second = BUNDLE.build_review_zip(Path(temporary) / "second.zip")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            BUNDLE.validate_review_zip(first)
            with zipfile.ZipFile(first) as archive:
                config = json.loads(archive.read("vucar/.mcp.json"))
                self.assertEqual(config, {"mcpServers": json.loads(client_before)})
                self.assertFalse(any(".claude-plugin/" in name or "/scripts/" in name for name in archive.namelist()))
                manifest = json.loads(archive.read("vucar/.codex-plugin/plugin.json"))
                source_manifest = VALIDATOR.load_json("plugins/vucar/.codex-plugin/plugin.json")
                self.assertEqual(manifest["extensions"]["com.openai"]["review"],
                                 source_manifest["extensions"]["com.openai"]["review"])
        self.assertEqual((VALIDATOR.PLUGIN / ".mcp.json").read_bytes(), client_before)

    def test_review_zip_retains_recording_url_without_changing_source(self) -> None:
        source_manifest = VALIDATOR.PLUGIN / ".codex-plugin" / "plugin.json"
        source_before = source_manifest.read_bytes()
        recording_url = "https://recordings.test/vucar-owner-seller.mp4"
        with tempfile.TemporaryDirectory() as temporary:
            fixture_plugin = Path(temporary) / "plugin"
            for relative in BUNDLE.BUNDLE_FILES:
                target = fixture_plugin / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((VALIDATOR.PLUGIN / relative).read_bytes())
            fixture_manifest_path = fixture_plugin / ".codex-plugin" / "plugin.json"
            fixture_manifest = json.loads(source_before)
            review = fixture_manifest["extensions"]["com.openai"]["review"]
            review["demo_recording_url"] = recording_url
            errors: list[str] = []
            VALIDATOR.validate_submission_manifest(fixture_manifest, errors)
            self.assertEqual(errors, [])
            fixture_manifest_path.write_text(json.dumps(fixture_manifest, indent=2) + "\n", encoding="utf-8")
            with patch.object(BUNDLE, "PLUGIN", fixture_plugin):
                artifact = BUNDLE.build_review_zip(Path(temporary) / "with-recording.zip")
            with zipfile.ZipFile(artifact) as archive:
                bundled_manifest = json.loads(archive.read("vucar/.codex-plugin/plugin.json"))
                self.assertEqual(bundled_manifest["extensions"]["com.openai"]["review"], review)
        self.assertEqual(source_manifest.read_bytes(), source_before)

    def test_review_zip_rejects_unexpected_entries_and_wrong_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            valid = BUNDLE.build_review_zip(Path(temporary) / "valid.zip")
            for label in ("unexpected", "config"):
                with self.subTest(label=label):
                    target = Path(temporary) / f"{label}.zip"
                    with zipfile.ZipFile(valid) as source, zipfile.ZipFile(target, "w") as altered:
                        for entry in source.infolist():
                            data = source.read(entry)
                            if label == "config" and entry.filename == "vucar/.mcp.json":
                                data = (VALIDATOR.PLUGIN / ".mcp.json").read_bytes()
                            altered.writestr(entry, data)
                        if label == "unexpected":
                            altered.writestr("vucar/private-operations.txt", "private scope")
                    with self.assertRaises(VALIDATOR.ValidationFailure):
                        BUNDLE.validate_review_zip(target)


class OwnerResultGateTest(unittest.TestCase):
    def test_unknown_deductions_do_not_become_final_net_proceeds(self) -> None:
        result = {"currency": "VND", "gross_offer_vnd": 420_000_000, "deductions_status": "unknown",
                  "confirmed_deductions_vnd": 100_000_000, "net_proceeds_vnd": None,
                  "reference_comparison": None, "notice": "Other deductions remain unknown."}
        SMOKE.validate_offer(result, gross=420_000_000, status="unknown", deductions=100_000_000)
        result["net_proceeds_vnd"] = 320_000_000
        with self.assertRaises(RuntimeError):
            SMOKE.validate_offer(result, gross=420_000_000, status="unknown", deductions=100_000_000)

    def test_upgrade_unknown_costs_and_explicit_zero_are_distinct(self) -> None:
        result = {"currency": "VND", "current_vehicle_value_vnd": 420_000_000, "replacement_vehicle_value_vnd": 400_000_000,
                  "vehicle_value_gap_vnd": -20_000_000, "vehicle_value_gap_range_vnd": {"low_vnd": -40_000_000, "high_vnd": 10_000_000},
                  "confirmed_additional_costs_vnd": None, "total_cash_needed_vnd": None, "total_cash_needed_range_vnd": None,
                  "confidence": "unknown", "notice": "Uncalibrated scenarios; costs are unknown."}
        SMOKE.validate_upgrade(result, additional_costs=None)
        zero = {**result, "confirmed_additional_costs_vnd": 0, "total_cash_needed_vnd": 0,
                "total_cash_needed_range_vnd": {"low_vnd": 0, "high_vnd": 10_000_000}}
        SMOKE.validate_upgrade(zero, additional_costs=0)
        with self.assertRaises(RuntimeError):
            SMOKE.validate_upgrade(zero, additional_costs=None)

    def test_valuation_gate_preserves_unknown_coverage_and_range_trust(self) -> None:
        result = {"currency": "VND", "estimated_market_value_vnd": 420_000_000,
                  "estimated_range_vnd": {"conservative_low_vnd": 400_000_000, "below_average_vnd": 410_000_000, "above_average_vnd": 430_000_000, "optimistic_high_vnd": 440_000_000},
                  "coverage": {"reported_count": None, "status": "not_reported", "source_field": "available", "definition": "Raw upstream count; meaning unverified."},
                  "similar_vehicles_in_model_data": None, "estimated_savings_vnd": None, "confidence": "unknown", "range_calibration": "unverified",
                  "depreciation_projection": [], "notice": "Indicative estimate.",
                  "source": {"publisher": "Vucar", "website_url": "https://vucar.vn/", "valuation_source_url": "https://vucar.vn/gia-xe-o-to-cu"},
                  "estimated_at": "2026-10-01T00:00:00.000Z", "report_url": "https://api.vucar.vn/mcp/valuation?brand=toyota&model=vios&year=2020&mileage_km=50000"}
        SMOKE.validate_valuation(result)
        for key, invalid in (("confidence", "medium"), ("similar_vehicles_in_model_data", 12), ("estimated_savings_vnd", 10_000_000), ("range_calibration", "verified"), ("estimated_market_value_vnd", SMOKE.MAX_AMOUNT_VND + 1)):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                SMOKE.validate_valuation({**result, key: invalid})

    def test_money_gate_rejects_booleans_fractions_and_negative_amounts(self) -> None:
        for invalid in (True, False, 0.5, -1, "420000000", SMOKE.MAX_AMOUNT_VND + 1):
            self.assertFalse(SMOKE.integer_vnd(invalid))
        self.assertTrue(SMOKE.integer_vnd(0))
        self.assertTrue(SMOKE.integer_vnd(-1, signed=True))


if __name__ == "__main__":
    unittest.main()
