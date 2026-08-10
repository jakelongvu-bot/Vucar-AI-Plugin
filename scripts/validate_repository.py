#!/usr/bin/env python3
"""Deterministic, dependency-free validation for this public plugin repository."""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "vucar"
ENDPOINT = "https://api.vucar.vn/mcp"
VERSION = "1.0.0"
REPOSITORY = "https://github.com/jakelongvu-bot/Vucar-AI-Plugin"

REQUIRED_FILES = {
    ".agents/plugins/marketplace.json",
    ".claude-plugin/marketplace.json",
    ".github/workflows/live-smoke.yml",
    ".github/workflows/validate.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".gitignore",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "NOTICE",
    "PRIVACY.md",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "TERMS.md",
    "docs/ARCHITECTURE.md",
    "docs/MARKETPLACE-SUBMISSION.md",
    "docs/RELEASE.md",
    "plugins/vucar/.claude-plugin/plugin.json",
    "plugins/vucar/.codex-plugin/plugin.json",
    "plugins/vucar/.mcp.json",
    "plugins/vucar/LICENSE",
    "plugins/vucar/NOTICE",
    "plugins/vucar/README.md",
    "plugins/vucar/SECURITY.md",
    "plugins/vucar/assets/icon.png",
    "plugins/vucar/assets/logo.png",
    "scripts/smoke_test_mcp.py",
    "scripts/validate_repository.py",
    "server.json",
    "tests/test_repository.py",
}

TEXT_SUFFIXES = {"", ".json", ".md", ".py", ".svg", ".txt", ".yml", ".yaml"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[opurs]_[A-Za-z0-9]{20,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "generic bearer token": re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{20,}\b", re.I),
    "private filesystem path": re.compile(r"/(?:Users|home)/[^/\s]+/"),
    "private network URL": re.compile(
        r"https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|"
        r"192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)(?::\d+)?",
        re.I,
    ),
    "phone-like fixture": re.compile(r"\b0(?:3|5|7|8|9)\d{8}\b"),
}
FORBIDDEN_FILE_SUFFIXES = {".env", ".key", ".p12", ".pfx", ".pem"}


class ValidationFailure(RuntimeError):
    """Raised when one or more repository invariants fail."""


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationFailure(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_without_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"{relative_path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationFailure(f"{relative_path}: root must be an object")
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def nested_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        result: list[str] = []
        for child in value.values():
            result.extend(nested_strings(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(nested_strings(child))
        return result
    return []


def validate_filesystem(errors: list[str]) -> None:
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }
    for relative_path in sorted(REQUIRED_FILES - actual):
        errors.append(f"missing required file: {relative_path}")

    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        relative_path = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            errors.append(f"symlinks are not allowed: {relative_path}")
        if path.is_file() and path.stat().st_size > 512_000:
            errors.append(f"unexpectedly large public file: {relative_path}")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_FILE_SUFFIXES:
            errors.append(f"credential-like file type is not allowed: {relative_path}")


def validate_codex(errors: list[str]) -> None:
    catalog = load_json(".agents/plugins/marketplace.json")
    require(catalog.get("name") == "vucar", "Codex marketplace name must be vucar", errors)
    require(catalog.get("interface") == {"displayName": "Vucar"}, "Codex marketplace interface changed", errors)
    plugins = catalog.get("plugins")
    require(isinstance(plugins, list) and len(plugins) == 1, "Codex marketplace must contain one plugin", errors)
    if isinstance(plugins, list) and len(plugins) == 1 and isinstance(plugins[0], dict):
        entry = plugins[0]
        require(entry.get("name") == "vucar", "Codex marketplace plugin name changed", errors)
        require(
            entry.get("source") == {"source": "local", "path": "./plugins/vucar"},
            "Codex marketplace source must be ./plugins/vucar",
            errors,
        )
        require(
            entry.get("policy") == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "Codex marketplace policy changed",
            errors,
        )

    manifest = load_json("plugins/vucar/.codex-plugin/plugin.json")
    require(manifest.get("name") == "vucar", "Codex plugin name must match its folder", errors)
    require(manifest.get("version") == VERSION, "Codex plugin version mismatch", errors)
    require(manifest.get("repository") == REPOSITORY, "Codex repository URL mismatch", errors)
    require(manifest.get("license") == "Apache-2.0", "Codex license must be Apache-2.0", errors)
    require(
        manifest.get("mcpServers") == "./.mcp.json",
        "Codex must reference the shared .mcp.json server map",
        errors,
    )
    interface = manifest.get("interface")
    require(isinstance(interface, dict), "Codex interface metadata is required", errors)
    if isinstance(interface, dict):
        require(interface.get("capabilities") == ["Read"], "Codex capability must be Read only", errors)
        prompts = interface.get("defaultPrompt")
        require(isinstance(prompts, list) and 1 <= len(prompts) <= 3, "Codex requires one to three prompts", errors)
        if isinstance(prompts, list):
            for index, prompt in enumerate(prompts):
                require(isinstance(prompt, str) and len(prompt) <= 128, f"Codex prompt {index + 1} exceeds 128 characters", errors)
        for asset_key in ("composerIcon", "logo"):
            value = interface.get(asset_key)
            require(isinstance(value, str) and value.startswith("./assets/"), f"Codex {asset_key} must be a local asset", errors)
            if isinstance(value, str):
                require((PLUGIN / value).is_file(), f"Codex {asset_key} does not exist: {value}", errors)


def validate_claude(errors: list[str]) -> None:
    catalog = load_json(".claude-plugin/marketplace.json")
    require(catalog.get("name") == "vucar", "Claude marketplace name must be vucar", errors)
    require(catalog.get("owner") == {"name": "Vucar"}, "Claude marketplace owner changed", errors)
    plugins = catalog.get("plugins")
    require(isinstance(plugins, list) and len(plugins) == 1, "Claude marketplace must contain one plugin", errors)
    if isinstance(plugins, list) and len(plugins) == 1 and isinstance(plugins[0], dict):
        require(plugins[0].get("name") == "vucar", "Claude marketplace plugin name changed", errors)
        require(plugins[0].get("source") == "./plugins/vucar", "Claude marketplace source must be ./plugins/vucar", errors)

    manifest = load_json("plugins/vucar/.claude-plugin/plugin.json")
    require(manifest.get("name") == "vucar", "Claude plugin name must match its folder", errors)
    require(manifest.get("version") == VERSION, "Claude plugin version mismatch", errors)
    require(manifest.get("repository") == REPOSITORY, "Claude repository URL mismatch", errors)
    require(manifest.get("license") == "Apache-2.0", "Claude license must be Apache-2.0", errors)

    mcp_config = load_json("plugins/vucar/.mcp.json")
    require(
        mcp_config == {"vucar": {"type": "http", "url": ENDPOINT}},
        "Claude must declare exactly one public Vucar MCP server",
        errors,
    )


def validate_registry(errors: list[str]) -> None:
    server = load_json("server.json")
    require(
        server.get("$schema") == "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "MCP Registry schema version changed unexpectedly",
        errors,
    )
    require(server.get("name") == "io.github.vucarvn/vucar", "MCP Registry namespace mismatch", errors)
    require(server.get("version") == VERSION, "MCP Registry version mismatch", errors)
    description = server.get("description")
    require(isinstance(description, str) and 1 <= len(description) <= 100, "MCP Registry description must be 1 to 100 characters", errors)
    require(
        server.get("repository") == {"url": REPOSITORY, "source": "github"},
        "MCP Registry repository mismatch",
        errors,
    )
    require(
        server.get("remotes") == [{"type": "streamable-http", "url": ENDPOINT}],
        "MCP Registry must declare exactly one Streamable HTTP endpoint",
        errors,
    )


def validate_public_safety(errors: list[str]) -> None:
    json_paths = sorted(path for path in ROOT.rglob("*.json") if ".git" not in path.parts)
    configured_mcp_urls: list[str] = []
    for path in json_paths:
        document = load_json(path.relative_to(ROOT).as_posix())
        for value in nested_strings(document):
            if value.startswith("http") and (value.endswith("/mcp") or "/mcp?" in value):
                configured_mcp_urls.append(value)
        serialized = json.dumps(document).lower()
        for forbidden in ("authorization", "bearer_token", "api_key", "client_secret", "password"):
            require(forbidden not in serialized, f"credential field found in {path.relative_to(ROOT)}: {forbidden}", errors)

    require(
        configured_mcp_urls == [ENDPOINT, ENDPOINT],
        "the shared client config and Registry manifest must use only the production endpoint",
        errors,
    )

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", "NOTICE", "Makefile"}:
            continue
        relative_path = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            errors.append(f"public text file is not UTF-8: {relative_path}")
            continue
        require(text.endswith("\n"), f"text file must end with newline: {relative_path}", errors)
        placeholder_markers = ("[TO" + "DO:", "REPLACE" + "_ME")
        require(not any(marker in text for marker in placeholder_markers), f"placeholder found: {relative_path}", errors)
        for label, pattern in SECRET_PATTERNS.items():
            require(pattern.search(text) is None, f"{label} pattern found in {relative_path}", errors)

    expected_png_sizes = {"icon.png": (192, 192), "logo.png": (512, 512)}
    for filename, expected_size in expected_png_sizes.items():
        asset = PLUGIN / "assets" / filename
        if not asset.is_file():
            continue
        data = asset.read_bytes()
        require(data.startswith(b"\x89PNG\r\n\x1a\n"), f"invalid PNG signature: {asset.relative_to(ROOT)}", errors)
        if len(data) >= 24:
            actual_size = struct.unpack(">II", data[16:24])
            require(actual_size == expected_size, f"unexpected PNG dimensions for {asset.relative_to(ROOT)}: {actual_size}", errors)


def validate_version_and_docs(errors: list[str]) -> None:
    require(re.fullmatch(r"\d+\.\d+\.\d+", VERSION) is not None, "version must use strict semantic versioning", errors)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    require(f"## [{VERSION}]" in changelog, "current version is missing from CHANGELOG.md", errors)
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for phrase in ("read-only", "vehicle catalog", "indicative", "cannot access", "no api key"):
        require(phrase in root_readme, f"README safety statement missing: {phrase}", errors)
    require("database" not in root_readme and "customer records" in root_readme, "README must describe the boundary without backend internals", errors)
    require("Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8"), "Apache License text is incomplete", errors)
    require(
        (PLUGIN / "LICENSE").read_text(encoding="utf-8")
        == (ROOT / "LICENSE").read_text(encoding="utf-8"),
        "installed plugin LICENSE must match the repository license",
        errors,
    )
    require(
        (PLUGIN / "NOTICE").read_text(encoding="utf-8")
        == (ROOT / "NOTICE").read_text(encoding="utf-8"),
        "installed plugin NOTICE must match the repository notice",
        errors,
    )
    require(
        "vucar--v1.0.0" in (ROOT / "docs" / "RELEASE.md").read_text(encoding="utf-8"),
        "release instructions must use the Claude-compatible plugin tag",
        errors,
    )
    architecture = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    require(
        "same `./.mcp.json` file" in architecture and "incompatible" not in architecture,
        "architecture must describe the shared cross-client MCP map",
        errors,
    )
    smoke = (ROOT / "scripts" / "smoke_test_mcp.py").read_text(encoding="utf-8")
    for annotation in (
        "readOnlyHint",
        "destructiveHint",
        "idempotentHint",
        "openWorldHint",
        "inputSchema",
        "outputSchema",
    ):
        require(annotation in smoke, f"live smoke assertion missing: {annotation}", errors)
    workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
    for gate in (
        "- 2.1.177",
        "- 2.1.220",
        "@anthropic-ai/claude-code@${{ matrix.claude_version }}",
        "@openai/codex@0.146.0",
        "mcp-publisher\" validate",
    ):
        require(gate in workflow, f"CI release gate missing: {gate}", errors)


def validate_repository() -> None:
    errors: list[str] = []
    validate_filesystem(errors)
    validate_codex(errors)
    validate_claude(errors)
    validate_registry(errors)
    validate_public_safety(errors)
    validate_version_and_docs(errors)
    if errors:
        bullet_list = "\n".join(f"- {message}" for message in errors)
        raise ValidationFailure(f"repository validation failed:\n{bullet_list}")


def main() -> int:
    try:
        validate_repository()
    except ValidationFailure as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Validated Vucar plugin {VERSION}: dual marketplaces, dual manifests, one shared read-only MCP endpoint, and public-safety checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
