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
VERSION = "2.0.0"
REPOSITORY = "https://github.com/jakelongvu-bot/Vucar-AI-Plugin"
EXPECTED_TOOLS = {
    "search_vehicle_catalog", "estimate_vehicle_value", "compare_vehicle_values",
    "check_seller_offer", "plan_vehicle_upgrade", "get_selling_guidance",
}
EXPECTED_SKILLS = {
    "vehicle-value": {"search_vehicle_catalog", "estimate_vehicle_value", "compare_vehicle_values"},
    "seller-offer": {"check_seller_offer"},
    "vehicle-upgrade": {"search_vehicle_catalog", "plan_vehicle_upgrade"},
    "sale-preparation": {"get_selling_guidance"},
}
PUBLIC_URLS = {
    "websiteURL": "https://vucar.vn/",
    "supportURL": "https://vucar.vn/contact",
    "privacyPolicyURL": "https://vucar.vn/policy/chinh-sach-bao-mat-thong-tin",
    "termsOfServiceURL": "https://vucar.vn/policy/quy-che-hoat-dong",
}

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
    "plugins/vucar/PRIVACY.md",
    "plugins/vucar/README.md",
    "plugins/vucar/SECURITY.md",
    "plugins/vucar/SUPPORT.md",
    "plugins/vucar/TERMS.md",
    "plugins/vucar/assets/icon.png",
    "plugins/vucar/assets/logo.png",
    "scripts/smoke_test_mcp.py",
    "scripts/build_review_zip.py",
    "scripts/validate_repository.py",
    "server.json",
    "tests/test_repository.py",
}
REQUIRED_FILES.update(f"plugins/vucar/skills/{name}/SKILL.md" for name in EXPECTED_SKILLS)
REQUIRED_FILES.add("plugins/vucar/references/owner-tool-boundary.md")

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


def validate_submission_manifest(manifest: dict[str, Any], errors: list[str]) -> None:
    """Check current submission fields without depending on a live portal or server."""
    require(manifest.get("skills") == "./skills/", "Codex must declare the bundled skills", errors)
    for forbidden in ("$schema", "apps", "hooks", "test_credentials", "reviewer_instructions"):
        require(forbidden not in manifest, f"unsupported public manifest field: {forbidden}", errors)
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("submission interface must be an object")
        return
    for key, maximum in {"displayName": 30, "shortDescription": 30, "longDescription": 4000, "developerName": 80}.items():
        value = interface.get(key)
        require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum,
                f"submission {key} must be nonempty and at most {maximum} characters", errors)
        if key != "longDescription" and isinstance(value, str):
            require(not any(character in value for character in "\n\r\t"), f"submission {key} must be one line", errors)
    require(interface.get("category") == "Data & Analytics", "submission category must be Data & Analytics", errors)
    for key, url in PUBLIC_URLS.items():
        require(interface.get(key) == url, f"submission {key} must use the current Vucar URL", errors)
    capabilities = interface.get("capabilities")
    require(capabilities == ["Read"], "public capabilities must be Read only", errors)
    extensions = manifest.get("extensions")
    openai = extensions.get("com.openai") if isinstance(extensions, dict) else None
    if not isinstance(openai, dict):
        errors.append("extensions.com.openai must be an object")
        return
    require(set(openai) <= {"review", "publication"}, "unsupported OpenAI extension field", errors)
    review = openai.get("review")
    if not isinstance(review, dict):
        errors.append("OpenAI review metadata must be an object")
        return
    require(set(review) <= {"test_cases", "demo_recording_url", "commerce", "commerce_description"},
            "unsupported review field or credentials in public manifest", errors)
    require(review.get("commerce") is False, "public plugin commerce declaration must be false", errors)
    require(isinstance(review.get("commerce_description"), str) and bool(review["commerce_description"].strip()),
            "commerce description must explain the read-only boundary", errors)
    if "demo_recording_url" in review:
        demo = review["demo_recording_url"]
        require(isinstance(demo, str) and demo.startswith("https://") and "example." not in demo,
                "demo recording must be a real HTTPS URL or be omitted", errors)
    test_cases = review.get("test_cases")
    if not isinstance(test_cases, dict):
        errors.append("review.test_cases must be an object")
        return
    require(set(test_cases) == {"positive", "negative"}, "review must contain positive and negative lists", errors)
    triggered_tools: set[str] = set()
    for kind, expected_count in (("positive", 5), ("negative", 3)):
        cases = test_cases.get(kind)
        require(isinstance(cases, list) and len(cases) == expected_count,
                f"review requires exactly {expected_count} {kind} cases", errors)
        if not isinstance(cases, list):
            continue
        for index, case in enumerate(cases, 1):
            label = f"{kind} review case {index}"
            if not isinstance(case, dict):
                errors.append(f"{label} must be an object")
                continue
            require(set(case) <= {"description", "prompt", "tools_triggered", "expected_behavior", "file_attachment_urls", "expected_output_url"},
                    f"{label} has obsolete or unsupported fields", errors)
            for key in ("description", "prompt", "expected_behavior"):
                value = case.get(key)
                require(isinstance(value, str) and bool(value.strip()), f"{label} needs {key}", errors)
            tools = case.get("tools_triggered")
            require(isinstance(tools, str), f"{label} needs a tools_triggered string", errors)
            if isinstance(tools, str):
                names = {value.strip() for value in tools.split(",") if value.strip()}
                require(names <= EXPECTED_TOOLS, f"{label} declares an unsupported tool", errors)
                if kind == "positive":
                    require(bool(names), f"{label} must trigger a supported tool", errors)
                    triggered_tools.update(names)
                else:
                    require(not names, f"{label} must not trigger tools", errors)
    require(triggered_tools == EXPECTED_TOOLS, "positive review cases must cover all six public tools", errors)
    publication = openai.get("publication")
    if not isinstance(publication, dict):
        errors.append("OpenAI publication metadata must be an object")
        return
    require(set(publication) <= {"countries", "release_notes", "translations"}, "unsupported publication field", errors)
    require(publication.get("countries") == ["VN"], "publication market must be Vietnam", errors)
    notes = publication.get("release_notes")
    require(isinstance(notes, str) and bool(notes.strip()), "publication release notes are required", errors)
    translations = publication.get("translations", {})
    require(isinstance(translations, dict), "translations must be an object", errors)
    if isinstance(translations, dict):
        for locale, translation in translations.items():
            require(bool(locale.strip()) and isinstance(translation, dict), "translation must have a locale and object", errors)
            if isinstance(translation, dict):
                require(set(translation) <= {"subtitle", "description"}, "unsupported translation field", errors)
                for key, limit in (("subtitle", 30), ("description", 4000)):
                    if key in translation:
                        value = translation[key]
                        require(isinstance(value, str) and bool(value.strip()) and len(value) <= limit,
                                f"translation {locale} {key} is invalid", errors)


def validate_skills(errors: list[str]) -> None:
    skill_root = PLUGIN / "skills"
    actual = {path.parent.name for path in skill_root.glob("*/SKILL.md")}
    require(actual == set(EXPECTED_SKILLS), "public package must contain exactly four owner/seller skills", errors)
    for name, tools in EXPECTED_SKILLS.items():
        path = skill_root / name / "SKILL.md"
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        header = re.match(r"\A---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n", content)
        require(header is not None and header.group(1) == name, f"skill frontmatter is invalid: {name}", errors)
        require(len(content) <= 5000, f"skill is unnecessarily large: {name}", errors)
        declared = set(re.findall(r"\b(?:search_|estimate_|compare_|check_|plan_|get_)[a-z_]+\b", content))
        require(declared == tools, f"skill tool scope is incomplete or unsupported: {name}", errors)
        links = re.findall(r"\]\(([^)]+)\)", content)
        require(bool(links), f"skill has no public-boundary reference: {name}", errors)
        for link in links:
            if link.startswith(("https://", "#")):
                continue
            target = (path.parent / link).resolve()
            require(target.is_relative_to(PLUGIN.resolve()) and target.is_file(),
                    f"skill reference escapes package or is missing: {name}: {link}", errors)


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
    validate_submission_manifest(manifest, errors)
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
    require(set(manifest) == {"name", "version", "description", "author", "homepage", "repository", "license", "keywords"},
            "Claude manifest must keep its supported identity fields separate from OpenAI metadata", errors)

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
        f"vucar--v{VERSION}" in (ROOT / "docs" / "RELEASE.md").read_text(encoding="utf-8"),
        "release instructions must use the Claude-compatible plugin tag",
        errors,
    )
    architecture = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    require("same `./.mcp.json` file" in architecture and "mcpServers" in architecture,
            "architecture must describe client and upload MCP formats", errors)
    for name in ("PRIVACY.md", "TERMS.md", "SUPPORT.md"):
        require((PLUGIN / name).read_bytes() == (ROOT / name).read_bytes(),
                f"installed plugin {name} must match the repository copy", errors)
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
    validate_skills(errors)
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
    print(f"Validated Vucar plugin {VERSION}: separate client/upload formats, four owner skills, six-tool review coverage, and public-safety checks passed. Backend rollout and review video remain separate gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
