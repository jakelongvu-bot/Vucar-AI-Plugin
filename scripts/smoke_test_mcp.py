#!/usr/bin/env python3
"""Opt-in production MCP protocol and abuse-boundary smoke test."""

from __future__ import annotations

import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any


ENDPOINT = "https://api.vucar.vn/mcp"
EXPECTED_SERVER = "vucar-vehicle-intelligence"
EXPECTED_VERSION = "2.0.0"
EXPECTED_TOOLS = {
    "compare_vehicle_values",
    "estimate_vehicle_value",
    "search_vehicle_catalog",
    "check_seller_offer",
    "plan_vehicle_upgrade",
    "get_selling_guidance",
}
PROTOCOL_VERSION = "2025-03-26"
MAX_AMOUNT_VND = 100_000_000_000
VEHICLE = {
    "brand": "Toyota",
    "model": "Vios",
    "year": 2020,
    "mileage_km": 50_000,
    "variant": "1.5G",
}
REPLACEMENT_VEHICLE = {
    "brand": "Toyota", "model": "Corolla Cross", "year": 2023,
    "mileage_km": 30_000, "variant": "1.8G",
}
EXPECTED_CANONICAL_VEHICLE = {
    **VEHICLE,
    "brand": "toyota",
    "model": "vios",
}
PERSONAL_DATA_SENTINEL = "synthetic-personal-data-sentinel"
MODEL_SENTINEL = "DefinitelyNotARealModel"
COMPARISON_LABEL_SENTINEL = "caller-label-must-not-be-reflected"
MAX_REQUEST_COST = 25
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_RATE_LIMIT_RETRIES = 2
MAX_RATE_LIMIT_WAIT_SECONDS = 120
RESET_SAFETY_SECONDS = 0.5


class RateLimitAwareOpener:
    """Respect the public weighted budget without weakening HTTP error gates."""

    def __init__(self, *, opener=None, clock=None, sleeper=None):
        self.opener = opener
        self.clock = clock
        self.sleeper = sleeper
        self.remaining: float | None = None
        self.reset: float | None = None

    def _now(self) -> float:
        return (self.clock or time.time)()

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) and number >= 0 else None

    def _observe(self, headers: Any) -> None:
        if headers is None:
            return
        remaining = self._number(headers.get("RateLimit-Remaining"))
        reset = self._number(headers.get("RateLimit-Reset"))
        if remaining is not None:
            self.remaining = remaining
            # Vucar emits the reset as Unix seconds, not a relative duration.
            self.reset = reset

    def _wait(self, delay: float) -> None:
        if delay <= 0:
            return
        if not math.isfinite(delay) or delay > MAX_RATE_LIMIT_WAIT_SECONDS:
            raise RuntimeError("rate-limit wait exceeds the smoke test's bounded wait budget")
        print(f"Waiting {delay:.1f}s for the public rate-limit window.", flush=True)
        (self.sleeper or time.sleep)(delay)

    def _pause_for_budget(self) -> None:
        if self.remaining is not None and self.remaining < MAX_REQUEST_COST:
            delay = (self.reset - self._now() + RESET_SAFETY_SECONDS
                     if self.reset is not None else RATE_LIMIT_WINDOW_SECONDS + RESET_SAFETY_SECONDS)
            self._wait(delay)
            self.remaining = self.reset = None

    def _retry_delay(self, headers: Any) -> float:
        raw_retry = headers.get("Retry-After") if headers is not None else None
        retry = self._number(raw_retry)
        if retry is None and raw_retry is not None:
            try:
                retry = max(0.0, parsedate_to_datetime(raw_retry).timestamp() - self._now())
            except (TypeError, ValueError, OverflowError):
                pass
        reset_delay = max(0.0, self.reset - self._now()) if self.reset is not None else None
        known_delays = [value for value in (retry, reset_delay) if value is not None]
        return max(1.0, *known_delays) + RESET_SAFETY_SECONDS if known_delays else RATE_LIMIT_WINDOW_SECONDS + RESET_SAFETY_SECONDS

    def open(self, request: Any, *, timeout: float = 20):
        for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
            self._pause_for_budget()
            try:
                response = (self.opener or urllib.request.urlopen)(request, timeout=timeout)
            except urllib.error.HTTPError as error:
                self._observe(error.headers)
                if error.code != 429 or attempt == MAX_RATE_LIMIT_RETRIES:
                    raise
                delay = self._retry_delay(error.headers)
                error.close()
                self._wait(delay)
                self.remaining = self.reset = None
            else:
                self._observe(response.headers)
                return response


_RATE_LIMITED_OPENER = RateLimitAwareOpener()


def open_request(request: Any, *, timeout: float = 20):
    return _RATE_LIMITED_OPENER.open(request, timeout=timeout)


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
        "User-Agent": f"vucar-agent-plugins-smoke/{EXPECTED_VERSION}",
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
    with open_request(request, timeout=20) as response:
        next_session = response.headers.get("MCP-Session-Id") or session_id
        body = response.read(256_001)
        if len(body) > 256_000:
            raise RuntimeError("MCP response exceeded the smoke payload budget")
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
        open_request(request, timeout=20)
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


def integer_vnd(value: Any, *, signed: bool = False, maximum: int = MAX_AMOUNT_VND) -> bool:
    return type(value) is int and -maximum <= value <= maximum and (signed or value >= 0)


def validate_source(source: Any) -> None:
    if source != {
        "publisher": "Vucar",
        "website_url": "https://vucar.vn/",
        "valuation_source_url": "https://vucar.vn/gia-xe-o-to-cu",
    }:
        raise RuntimeError("valuation source attribution is incomplete or unexpected")


def validate_report_reference(report_url: Any, estimated_at: Any) -> None:
    if not isinstance(report_url, str):
        raise RuntimeError("valuation has no report URL")
    parsed = urllib.parse.urlsplit(report_url)
    query = urllib.parse.parse_qs(parsed.query)
    if (parsed.scheme, parsed.netloc, parsed.path) != ("https", "api.vucar.vn", "/mcp/valuation"):
        raise RuntimeError("valuation report URL has an unexpected origin or path")
    if not {"brand", "model", "year", "mileage_km"} <= set(query) or not set(query) <= {"brand", "model", "year", "mileage_km", "variant"}:
        raise RuntimeError("valuation report URL has incomplete or extraneous attributes")
    try:
        timestamp = datetime.fromisoformat(estimated_at.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError("valuation estimated_at must be an ISO timestamp") from exc
    if timestamp.tzinfo is None:
        raise RuntimeError("valuation estimated_at must include a timezone")


def validate_valuation(data: dict[str, Any]) -> None:
    if data.get("currency") != "VND" or not integer_vnd(data.get("estimated_market_value_vnd")) or data["estimated_market_value_vnd"] <= 0:
        raise RuntimeError("estimate returned an invalid integer-VND value")
    ranges = data.get("estimated_range_vnd")
    fields = ("conservative_low_vnd", "below_average_vnd", "above_average_vnd", "optimistic_high_vnd")
    if not isinstance(ranges, dict) or not all(integer_vnd(ranges.get(field)) for field in fields):
        raise RuntimeError("estimate returned an incomplete integer-VND range")
    if ranges["conservative_low_vnd"] > ranges["optimistic_high_vnd"]:
        raise RuntimeError("estimate range is reversed")
    coverage = data.get("coverage")
    if not isinstance(coverage, dict) or coverage.get("source_field") != "available" or not isinstance(coverage.get("definition"), str) or not coverage["definition"].strip():
        raise RuntimeError("estimate has no raw-coverage definition")
    reported = coverage.get("reported_count")
    if reported is not None and (type(reported) is not int or reported < 0):
        raise RuntimeError("coverage count must be a nonnegative integer or null")
    expected_status = "not_reported" if reported is None else "reported_zero" if reported == 0 else "reported_count"
    expected_confidence = "low" if reported is not None and reported < 5 else "unknown"
    if coverage.get("status") != expected_status or data.get("confidence") != expected_confidence:
        raise RuntimeError("estimate misstates raw coverage or confidence")
    if any(field not in data or data[field] is not None for field in ("similar_vehicles_in_model_data", "estimated_savings_vnd")) or data.get("range_calibration") != "unverified":
        raise RuntimeError("estimate claims verified model coverage, savings, or calibrated ranges")
    if not isinstance(data.get("depreciation_projection"), list) or not isinstance(data.get("notice"), str) or not data["notice"].strip():
        raise RuntimeError("estimate returned an incomplete result")
    validate_source(data.get("source"))
    validate_report_reference(data.get("report_url"), data.get("estimated_at"))


def validate_offer(data: dict[str, Any], *, gross: int, status: str, deductions: int | None) -> None:
    if data.get("currency") != "VND" or not integer_vnd(data.get("gross_offer_vnd")) or data.get("gross_offer_vnd") != gross or data.get("deductions_status") != status or data.get("confirmed_deductions_vnd") != deductions:
        raise RuntimeError("offer calculation did not preserve the supplied amounts and completeness status")
    net = data.get("net_proceeds_vnd")
    expected_net = None if status == "unknown" else gross - (deductions or 0)
    if net != expected_net or (net is not None and not integer_vnd(net)):
        raise RuntimeError("offer calculation invented a net amount or returned wrong arithmetic")
    reference = data.get("reference_comparison")
    if reference is not None:
        if not isinstance(reference, dict) or reference.get("position") not in {"below", "within", "above"} or reference.get("confidence") not in {"low", "unknown"}:
            raise RuntimeError("offer reference has an unsupported verdict or confidence")
        value_range = reference.get("model_range_vnd")
        if not isinstance(value_range, dict) or not all(integer_vnd(value_range.get(key)) for key in ("low_vnd", "high_vnd")):
            raise RuntimeError("offer reference has an invalid model range")
    if not isinstance(data.get("notice"), str) or not data["notice"].strip():
        raise RuntimeError("offer calculation has no limitations notice")


def validate_upgrade(data: dict[str, Any], *, additional_costs: int | None) -> None:
    values = (data.get("current_vehicle_value_vnd"), data.get("replacement_vehicle_value_vnd"))
    gap = data.get("vehicle_value_gap_vnd")
    if data.get("currency") != "VND" or not all(integer_vnd(value) and value > 0 for value in values) or not integer_vnd(gap, signed=True) or gap != values[1] - values[0]:
        raise RuntimeError("upgrade result has invalid values or lost the signed gap")
    scenario = data.get("vehicle_value_gap_range_vnd")
    if not isinstance(scenario, dict) or not all(integer_vnd(scenario.get(key), signed=True) for key in ("low_vnd", "high_vnd")) or scenario["low_vnd"] > scenario["high_vnd"]:
        raise RuntimeError("upgrade scenario range is invalid")
    if data.get("confirmed_additional_costs_vnd") != additional_costs:
        raise RuntimeError("upgrade result did not preserve unknown versus confirmed costs")
    total = data.get("total_cash_needed_vnd")
    total_range = data.get("total_cash_needed_range_vnd")
    if additional_costs is None:
        if total is not None or total_range is not None:
            raise RuntimeError("upgrade result invented complete cash needed from unknown costs")
    elif not integer_vnd(total, maximum=2 * MAX_AMOUNT_VND) or not isinstance(total_range, dict) or not all(integer_vnd(value, maximum=2 * MAX_AMOUNT_VND) for value in total_range.values()) or total != max(0, gap + additional_costs) or total_range != {key: max(0, value + additional_costs) for key, value in scenario.items()}:
        raise RuntimeError("upgrade total or scenario arithmetic is invalid")
    if data.get("confidence") not in {"low", "unknown"} or not isinstance(data.get("notice"), str) or not data["notice"].strip():
        raise RuntimeError("upgrade confidence or limitations are incomplete")


def validate_guidance(data: dict[str, Any], *, goal: str) -> None:
    if data.get("language") != "vi" or data.get("goal") != goal or not isinstance(data.get("summary"), str) or not data["summary"].strip():
        raise RuntimeError("selling guidance is incomplete or misstates the goal")
    for key in ("preparation", "before_accepting_offer"):
        items = data.get(key)
        if not isinstance(items, list) or not items or not all(isinstance(item, dict) and isinstance(item.get("title"), str) and isinstance(item.get("detail"), str) and item["title"].strip() and item["detail"].strip() for item in items):
            raise RuntimeError("selling guidance has no practical preparation or acceptance checklist")
    sources = data.get("sources")
    allowed_urls = {"https://vucar.vn/for-sellers", "https://vucar.vn/for-sellers/kiem-tra-gia-chao-mua", "https://vucar.vn/gia-xe-o-to-cu", "https://vucar.vn/contact"}
    if not isinstance(sources, list) or not sources or not all(isinstance(source, dict) and source.get("url") in allowed_urls for source in sources):
        raise RuntimeError("selling guidance source attribution is missing or unexpected")
    handoff = data.get("selling_handoff")
    if goal != "sell_soon":
        if handoff is not None:
            raise RuntimeError("selling handoff was returned for a user who is not asking to sell")
    else:
        if not isinstance(handoff, dict) or handoff.get("requires_user_action") is not True:
            raise RuntimeError("seller handoff must require the user's action")
        parsed = urllib.parse.urlsplit(handoff.get("url", ""))
        query = urllib.parse.parse_qs(parsed.query)
        if (parsed.scheme, parsed.netloc, parsed.path) != ("https", "vucar.vn", "/for-sellers") or query.get("ai_referrer") != ["chatgpt"]:
            raise RuntimeError("seller handoff is not the relevant returned Vucar path")


def expect_tool_error(response: Any, *, sentinel: str | None = None) -> None:
    if not isinstance(response, dict) or not isinstance(response.get("result"), dict) or response["result"].get("isError") is not True or (sentinel is not None and sentinel in json.dumps(response)):
        raise RuntimeError("invalid tool input did not fail without reflection")


def call_tool(name: str, arguments: dict[str, Any], request_id: int, session_id: str | None) -> tuple[dict[str, Any], str | None]:
    response, next_session = post({"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, session_id)
    return tool_result(response, name), next_session


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
            if not isinstance(tool.get("description"), str) or not tool["description"].strip():
                raise RuntimeError(f"{tool.get('name')} has an incomplete description")
            properties = input_schema.get("properties", {})
            if not isinstance(properties, dict) or set(properties) & {"phone", "name", "vin", "plate", "customer_id", "email", "address", "password"}:
                raise RuntimeError(f"{tool.get('name')} exposes a personal-data field")

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
        validate_valuation(estimate_data)

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
        validate_valuation(canonicalized_data)
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
                integer_vnd(item.get("estimated_market_value_vnd"))
                and item["estimated_market_value_vnd"] > 0
                and item.get("confidence") in {"low", "unknown"}
                and integer_vnd(item.get("conservative_low_vnd"))
                and integer_vnd(item.get("optimistic_high_vnd"))
                for item in comparisons
            )
            or not isinstance(comparison_data.get("notice"), str)
            or not comparison_data["notice"].strip()
        ):
            raise RuntimeError("comparison smoke returned an incomplete result shape")
        if comparison_data.get("range_calibration") != "unverified":
            raise RuntimeError("comparison claims calibrated ranges")
        validate_source(comparison_data.get("source"))
        for item in comparisons:
            validate_report_reference(item.get("report_url"), item.get("estimated_at"))

        offer_unknown, session_id = call_tool("check_seller_offer", {
            "gross_offer_vnd": 420_000_000,
            "deductions_status": "unknown",
            "confirmed_deductions_vnd": 100_000_000,
            "vehicle": VEHICLE,
        }, 20, session_id)
        validate_offer(offer_unknown, gross=420_000_000, status="unknown", deductions=100_000_000)
        if not isinstance(offer_unknown.get("reference_comparison"), dict):
            raise RuntimeError("offer with a vehicle did not return an indicative model reference")
        if offer_unknown.get("reference_status") != "available" or not isinstance(offer_unknown.get("valuation_reference"), dict):
            raise RuntimeError("offer did not disclose its valuation-reference status")
        validate_valuation(offer_unknown["valuation_reference"])
        offer_known, session_id = call_tool("check_seller_offer", {
            "gross_offer_vnd": 420_000_000,
            "deductions_status": "known",
            "confirmed_deductions_vnd": 100_000_000,
        }, 21, session_id)
        validate_offer(offer_known, gross=420_000_000, status="known", deductions=100_000_000)
        offer_none, session_id = call_tool("check_seller_offer", {
            "gross_offer_vnd": 420_000_000,
            "deductions_status": "none",
        }, 22, session_id)
        validate_offer(offer_none, gross=420_000_000, status="none", deductions=0)
        offer_default, session_id = call_tool("check_seller_offer", {
            "gross_offer_vnd": 420_000_000,
        }, 23, session_id)
        validate_offer(offer_default, gross=420_000_000, status="unknown", deductions=None)

        upgrade_inputs = {
            "current_vehicle": VEHICLE,
            "replacement_vehicle": REPLACEMENT_VEHICLE,
        }
        upgrade_unknown, session_id = call_tool("plan_vehicle_upgrade", upgrade_inputs, 24, session_id)
        validate_upgrade(upgrade_unknown, additional_costs=None)
        upgrade_zero, session_id = call_tool("plan_vehicle_upgrade", {
            **upgrade_inputs, "confirmed_additional_costs_vnd": 0,
        }, 25, session_id)
        validate_upgrade(upgrade_zero, additional_costs=0)
        for upgrade in (upgrade_unknown, upgrade_zero):
            references = upgrade.get("references")
            if not isinstance(references, dict):
                raise RuntimeError("upgrade did not return its valuation references")
            for key in ("current_vehicle", "replacement_vehicle"):
                reference = references.get(key)
                if not isinstance(reference, dict):
                    raise RuntimeError("upgrade reference is incomplete")
                validate_valuation(reference)
        guidance_exploring, session_id = call_tool("get_selling_guidance", {}, 26, session_id)
        validate_guidance(guidance_exploring, goal="exploring")
        guidance_selling, session_id = call_tool("get_selling_guidance", {
            "goal": "sell_soon", "condition": "unknown", "has_maintenance_records": True, "assistant_source": "chatgpt",
        }, 27, session_id)
        validate_guidance(guidance_selling, goal="sell_soon")
        catalog_alias, session_id = call_tool("search_vehicle_catalog", {
            "brand": "Toyota", "model": "CorollaCross", "year": 2023,
        }, 28, session_id)
        if catalog_alias.get("level") != "variants" or catalog_alias.get("query", {}).get("model") != "corolla cross" or not catalog_alias.get("supported_values"):
            raise RuntimeError("catalog did not resolve the unique natural model alias")
        offer_reference_unavailable, session_id = call_tool("check_seller_offer", {
            "gross_offer_vnd": 420_000_000, "deductions_status": "known", "confirmed_deductions_vnd": 100_000_000,
            "vehicle": {**VEHICLE, "model": MODEL_SENTINEL},
        }, 29, session_id)
        validate_offer(offer_reference_unavailable, gross=420_000_000, status="known", deductions=100_000_000)
        if offer_reference_unavailable.get("reference_status") != "unavailable" or offer_reference_unavailable.get("valuation_reference") is not None or offer_reference_unavailable.get("reference_comparison") is not None or MODEL_SENTINEL in json.dumps(offer_reference_unavailable):
            raise RuntimeError("optional valuation failure did not preserve arithmetic without input reflection")

        report_request = urllib.request.Request(estimate_data["report_url"], headers={"User-Agent": f"vucar-agent-plugins-smoke/{EXPECTED_VERSION}"})
        with open_request(report_request, timeout=20) as report_response:
            html = report_response.read(256_001)
            if report_response.status != 200 or "text/html" not in report_response.headers.get("Content-Type", "") or "no-store" not in report_response.headers.get("Cache-Control", "") or len(html) > 256_000 or b"Vucar" not in html:
                raise RuntimeError("valuation report did not return a bounded current HTML reference")

        # Keep every original rejection below; these add the owner-calculator boundaries.
        new_rejections = [
            ("check_seller_offer", {"gross_offer_vnd": 420_000_000, "deductions_status": "known"}),
            ("check_seller_offer", {"gross_offer_vnd": 420_000_000, "deductions_status": "none", "confirmed_deductions_vnd": 1}),
            ("check_seller_offer", {"gross_offer_vnd": 420_000_000.5}),
            ("check_seller_offer", {"gross_offer_vnd": 420_000_000, "phone": PERSONAL_DATA_SENTINEL}),
            ("plan_vehicle_upgrade", {**upgrade_inputs, "confirmed_additional_costs_vnd": -1}),
            ("plan_vehicle_upgrade", {**upgrade_inputs, "phone": PERSONAL_DATA_SENTINEL}),
            ("get_selling_guidance", {"phone": PERSONAL_DATA_SENTINEL}),
        ]
        for request_id, (name, arguments) in enumerate(new_rejections, 30):
            rejected, _ = post({"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, session_id)
            expect_tool_error(rejected, sentinel=PERSONAL_DATA_SENTINEL)

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
            f"{len(tools)} read-only tools; owner arithmetic, uncertainty, sources/reports, guidance and original rejection gates passed."
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
