#!/usr/bin/env python3
"""Build and inspect the OpenAI upload artifact without changing client configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import struct
import sys
import zipfile
from pathlib import Path

from validate_repository import (
    ENDPOINT, EXPECTED_SKILLS, PLUGIN, SECRET_PATTERNS, VERSION,
    ValidationFailure, _object_without_duplicate_keys,
    validate_repository, validate_submission_manifest,
)


BUNDLE_FILES = {
    ".codex-plugin/plugin.json", ".mcp.json",
    "LICENSE", "NOTICE", "PRIVACY.md", "README.md", "SECURITY.md", "SUPPORT.md", "TERMS.md",
    "assets/icon.png", "assets/logo.png", "references/owner-tool-boundary.md",
    *(f"skills/{name}/SKILL.md" for name in EXPECTED_SKILLS),
}


def validate_review_zip(path: Path) -> None:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        expected = {f"vucar/{name}" for name in BUNDLE_FILES}
        if {entry.filename for entry in entries} != expected or len(entries) != len(expected):
            errors.append("review ZIP must contain exactly the public allowlisted package files")
        documents: dict[str, bytes] = {}
        for entry in entries:
            if entry.filename not in expected:
                continue
            if entry.file_size > 512_000 or stat.S_ISLNK(entry.external_attr >> 16):
                errors.append(f"unsafe ZIP entry: {entry.filename}")
                continue
            documents[entry.filename] = archive.read(entry)
        for name, data in documents.items():
            if not name.endswith(".png"):
                try:
                    text = data.decode("utf-8")
                except UnicodeError:
                    errors.append(f"ZIP text is not UTF-8: {name}")
                    continue
                for label, pattern in SECRET_PATTERNS.items():
                    if pattern.search(text):
                        errors.append(f"{label} pattern found in ZIP: {name}")
        try:
            manifest = json.loads(documents["vucar/.codex-plugin/plugin.json"],
                                  object_pairs_hook=_object_without_duplicate_keys)
            if not isinstance(manifest, dict):
                raise ValidationFailure("ZIP manifest must be an object")
            validate_submission_manifest(manifest, errors)
            if manifest.get("version") != VERSION or manifest.get("mcpServers") != "./.mcp.json":
                errors.append("ZIP identity or MCP config reference differs from the release")
            config = json.loads(documents["vucar/.mcp.json"],
                                object_pairs_hook=_object_without_duplicate_keys)
            if config != {"mcpServers": {"vucar": {"type": "http", "url": ENDPOINT}}}:
                errors.append("OpenAI ZIP needs exactly one public server inside mcpServers")
            for name, dimensions in (("icon.png", (192, 192)), ("logo.png", (512, 512))):
                data = documents[f"vucar/assets/{name}"]
                if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 24 or struct.unpack(">II", data[16:24]) != dimensions:
                    errors.append(f"ZIP artwork must be the included square PNG: {name}")
        except (KeyError, json.JSONDecodeError, UnicodeError) as exc:
            errors.append(f"ZIP is missing or has invalid metadata: {exc}")
    if errors:
        raise ValidationFailure("review ZIP validation failed:\n" + "\n".join(f"- {error}" for error in errors))


def build_review_zip(output: Path) -> Path:
    validate_repository()
    output = output.resolve()
    if output.is_relative_to(PLUGIN.resolve()):
        raise ValidationFailure("review ZIP output must be outside the plugin source directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".partial")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative in sorted(BUNDLE_FILES):
                source = PLUGIN / relative
                if relative == ".mcp.json":
                    client_map = json.loads(source.read_text(encoding="utf-8"),
                                            object_pairs_hook=_object_without_duplicate_keys)
                    data = (json.dumps({"mcpServers": client_map}, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
                else:
                    data = source.read_bytes()
                entry = zipfile.ZipInfo(f"vucar/{relative}", date_time=(2026, 10, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        validate_review_zip(temporary)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Review ZIP path outside the plugin source directory")
    args = parser.parse_args()
    try:
        output = build_review_zip(args.output)
    except (ValidationFailure, OSError, zipfile.BadZipFile) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"Built and validated {output} ({output.stat().st_size} bytes; SHA256 {digest}).")
    print("Prepared review package only: backend rollout, live cases, and accessible demo recording remain pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
