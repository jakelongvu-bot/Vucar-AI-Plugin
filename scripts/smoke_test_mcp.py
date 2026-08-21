#!/usr/bin/env python3
"""Opt-in production MCP protocol and abuse-boundary smoke test."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any


ENDPOINT = "https://api.vucar.vn/mcp"
EXPECTED_SERVER = "vucar-vehicle-intelligence"
EXPECTED_VERSION = "1.0.1"
EXPECTED_TOOLS = {
    "compare_vehicle_values",
    "estimate_vehicle_value",
    "search_vehicle_catalog",
}
PROTOCOL_VERSION = "2025-03-26"
VEHICLE = {
    "brand": "Toyota",
    "model": "Vios",
    "year": 2020,
    "mileage_km": 50_000,
    "variant": "1.5G",
}
EXPECTED_CANONICAL_VEHICLE = {
    **VEHICLE,
    "brand": "toyota",
    "model": "vios",
}
PERSONAL_DATA_SENTINEL = "synthetic-personal-data-sentinel"
MODEL_SENTINEL = "DefinitelyNotARealModel"
COMPARISON_LABEL_SENTINEL = "caller-label-must-not-be-reflected"


def parse_response(body: bytes, content_type: str) -> dict[str, Any]:
    text = body.decode("utf-8")
    if "text/event-stream" in content_type:
        data_lines = [
            line.removeprefix("data: ")
            for line in text.splitlines()
            if line.startswith("data: ")
        ]
        if not data_lines:
            raise RuntimeError("SSE response contained no data event")
        text = data_lines[-1]
    value = json.loads(text)
    if not isinstance(value, dict):
        raise RuntimeError("MCP response root was not an object")
    if "error" in value:
        raise RuntimeError(f"MCP error: {value['error']}")
    return value


def request_headers(origin: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
        "User-Agent": "vucar-agent-plugins-smoke/1.0.1",
    }
    if origin is not None:
        headers["Origin"] = origin
    return headers


def post(
    payload: Any,
    session_id: str | None = None,
    origin: str | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    headers = request_headers(origin)
    if session_id:
        headers["MCP-Session-Id"] = session_id
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        next_session = response.headers.get("MCP-Session-Id") or session_id
        body = response.read()
        if response.status in (202, 204) or not body:
            return None, next_session
        return (
            parse_response(body, response.headers.get("Content-Type", "")),
            next_session,
        )


def expect_http_error(
    payload: Any,
    expected_status: int,
    expected_code: int,
    origin: str | None = None,
) -> None:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers=request_headers(origin),
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=20)
    except urllib.error.HTTPError as exc:
        body = exc.read()
        if exc.code != expected_status:
            raise RuntimeError(
                f"expected HTTP {expected_status}, received {exc.code}: {body[:300]!r}"
            ) from exc
        if not body:
            raise RuntimeError(f"HTTP {expected_status} response had no JSON-RPC body")
        value = json.loads(body)
        error = value.get("error") if isinstance(value, dict) else None
        if not isinstance(error, dict) or error.get("code") != expected_code:
            raise RuntimeError(
                f"HTTP {expected_status} response did not contain JSON-RPC code "
                f"{expected_code}: {value!r}"
            )
        return
    raise RuntimeError(f"expected HTTP {expected_status}, request succeeded")


def tool_result(response: dict[str, Any] | None, tool_name: str) -> dict[str, Any]:
    if response is None or not isinstance(response.get("result"), dict):
        raise RuntimeError(f"{tool_name} returned no result")
    result = response["result"]
    if result.get("isError") is True:
        raise RuntimeError(f"{tool_name} returned a tool error")
    structured = result.get("structuredContent")
    if not isinstance(structured, dict):
        raise RuntimeError(f"{tool_name} returned no structured content")
    return structured


def main() -> int:
    try:
        initialized, session_id = post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "vucar-agent-plugins-smoke",
                        "version": EXPECTED_VERSION,
                    },
                },
            }
        )
        if initialized is None or not isinstance(initialized.get("result"), dict):
            raise RuntimeError("initialize returned no result")
        server_info = initialized["result"].get("serverInfo")
        if (
            not isinstance(server_info, dict)
            or server_info.get("name") != EXPECTED_SERVER
            or server_info.get("version") != EXPECTED_VERSION
        ):
            raise RuntimeError(f"unexpected server identity: {server_info}")
        if initialized["result"].get("protocolVersion") != PROTOCOL_VERSION:
            raise RuntimeError("server negotiated an unexpected MCP protocol version")

        post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            session_id,
        )
        listed, session_id = post(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            session_id,
        )
        if listed is None or not isinstance(listed.get("result"), dict):
            raise RuntimeError("tools/list returned no result")
        tools = listed["result"].get("tools")
        if not isinstance(tools, list):
            raise RuntimeError("tools/list result did not contain a tool array")
        names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
        if names != EXPECTED_TOOLS:
            raise RuntimeError(
                f"unexpected public tool set: {sorted(str(name) for name in names)}"
            )
        for tool in tools:
            annotations = tool.get("annotations", {})
            if annotations.get("readOnlyHint") is not True:
                raise RuntimeError(f"{tool.get('name')} is not annotated read-only")
            if annotations.get("destructiveHint") is not False:
                raise RuntimeError(
                    f"{tool.get('name')} is not annotated non-destructive"
                )
            if annotations.get("idempotentHint") is not True:
                raise RuntimeError(f"{tool.get('name')} is not annotated idempotent")
            if annotations.get("openWorldHint") is not False:
                raise RuntimeError(f"{tool.get('name')} has an unexpected open-world hint")
            input_schema = tool.get("inputSchema")
            output_schema = tool.get("outputSchema")
            if (
                not isinstance(input_schema, dict)
                or input_schema.get("additionalProperties") is not False
                or not isinstance(output_schema, dict)
            ):
                raise RuntimeError(f"{tool.get('name')} schema boundary is incomplete")
            if not isinstance(tool.get("title"), str) or not tool["title"].strip():
                raise RuntimeError(f"{tool.get('name')} has no title")
            if not isinstance(tool.get("description"), str) or not tool[
                "description"
            ].startswith("Use this when"):
                raise RuntimeError(f"{tool.get('name')} has an incomplete description")

        catalog, session_id = post(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search_vehicle_catalog",
                    "arguments": {},
                },
            },
            session_id,
        )
        catalog_data = tool_result(catalog, "search_vehicle_catalog")
        if catalog_data.get("level") != "brands" or not catalog_data.get(
            "supported_values"
        ):
            raise RuntimeError("catalog smoke returned no supported brands")

        estimate, session_id = post(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "estimate_vehicle_value",
                    "arguments": VEHICLE,
                },
            },
            session_id,
        )
        estimate_data = tool_result(estimate, "estimate_vehicle_value")
        if (
            estimate_data.get("currency") != "VND"
            or not isinstance(estimate_data.get("estimated_market_value_vnd"), int)
            or estimate_data["estimated_market_value_vnd"] <= 0
        ):
            raise RuntimeError("estimate smoke returned an invalid VND value")
        estimate_range = estimate_data.get("estimated_range_vnd")
        range_fields = (
            "conservative_low_vnd",
            "below_average_vnd",
            "above_average_vnd",
            "optimistic_high_vnd",
        )
        if (
            not isinstance(estimate_range, dict)
            or not all(isinstance(estimate_range.get(field), int) for field in range_fields)
            or not isinstance(estimate_data.get("depreciation_projection"), list)
            or not isinstance(estimate_data.get("similar_vehicles_in_model_data"), int)
            or not isinstance(estimate_data.get("notice"), str)
            or not estimate_data["notice"].strip()
        ):
            raise RuntimeError("estimate smoke returned an incomplete result shape")

        canonicalized, session_id = post(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "estimate_vehicle_value",
                    "arguments": {
                        **VEHICLE,
                        "brand": "toyota",
                        "model": "vios",
                        "variant": "1.5g",
                    },
                },
            },
            session_id,
        )
        canonicalized_data = tool_result(canonicalized, "estimate_vehicle_value")
        if canonicalized_data.get("vehicle") != EXPECTED_CANONICAL_VEHICLE:
            raise RuntimeError("case-insensitive inputs were not returned canonically")

        comparison, session_id = post(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "compare_vehicle_values",
                    "arguments": {
                        "vehicles": [
                            {"label": COMPARISON_LABEL_SENTINEL, **VEHICLE},
                            {
                                "label": f"{COMPARISON_LABEL_SENTINEL}-second",
                                **VEHICLE,
                                "mileage_km": 80_000,
                            },
                        ]
                    },
                },
            },
            session_id,
        )
        comparison_data = tool_result(comparison, "compare_vehicle_values")
        if len(comparison_data.get("comparisons", [])) != 2:
            raise RuntimeError("comparison smoke did not return two vehicles")
        if COMPARISON_LABEL_SENTINEL in json.dumps(comparison):
            raise RuntimeError("caller-provided comparison label was reflected")
        expected_labels = {
            "2020 toyota vios 1.5G · 50,000 km",
            "2020 toyota vios 1.5G · 80,000 km",
        }
        comparisons = comparison_data["comparisons"]
        if {item.get("label") for item in comparisons} != expected_labels:
            raise RuntimeError("comparison labels were not computed canonically")
        if (
            [item.get("rank_by_estimated_value") for item in comparisons] != [1, 2]
            or {item.get("input_index") for item in comparisons} != {0, 1}
            or not all(
                isinstance(item.get("estimated_market_value_vnd"), int)
                and item["estimated_market_value_vnd"] > 0
                and item.get("confidence") in {"low", "medium"}
                and isinstance(item.get("conservative_low_vnd"), int)
                and isinstance(item.get("optimistic_high_vnd"), int)
                for item in comparisons
            )
            or not isinstance(comparison_data.get("notice"), str)
            or not comparison_data["notice"].strip()
        ):
            raise RuntimeError("comparison smoke returned an incomplete result shape")

        unsupported, _ = post(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "name": "estimate_vehicle_value",
                    "arguments": {**VEHICLE, "model": MODEL_SENTINEL},
                },
            },
            session_id,
        )
        if (
            unsupported is None
            or not isinstance(unsupported.get("result"), dict)
            or unsupported["result"].get("isError") is not True
            or MODEL_SENTINEL in json.dumps(unsupported)
        ):
            raise RuntimeError("unsupported vehicle did not fail without reflection")

        missing_mileage, _ = post(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "estimate_vehicle_value",
                    "arguments": {
                        key: value
                        for key, value in VEHICLE.items()
                        if key != "mileage_km"
                    },
                },
            },
            session_id,
        )
        if (
            missing_mileage is None
            or not isinstance(missing_mileage.get("result"), dict)
            or missing_mileage["result"].get("isError") is not True
        ):
            raise RuntimeError("missing mileage did not fail schema validation")

        invalid, _ = post(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "estimate_vehicle_value",
                    "arguments": {**VEHICLE, "phone": PERSONAL_DATA_SENTINEL},
                },
            },
            session_id,
        )
        if (
            invalid is None
            or not isinstance(invalid.get("result"), dict)
            or invalid["result"].get("isError") is not True
            or PERSONAL_DATA_SENTINEL in json.dumps(invalid)
        ):
            raise RuntimeError("unknown-field boundary did not fail safely")

        expect_http_error(
            [
                {"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {}},
                {"jsonrpc": "2.0", "id": 8, "method": "tools/list", "params": {}},
            ],
            400,
            -32600,
        )
        expect_http_error(
            {"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": {}},
            403,
            -32002,
            origin="https://attacker.example",
        )
        expect_http_error(
            {"jsonrpc": "2.0", "id": 10, "method": "tools/list", "padding": "x" * (65 * 1024)},
            413,
            -32013,
        )

        print(
            f"Live MCP release gate passed: {server_info['name']} exposed exactly "
            f"{len(tools)} read-only tools; 6 positive and 7 negative checks passed."
        )
        return 0
    except (
        RuntimeError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
    ) as exc:
        print(f"Live MCP release gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
