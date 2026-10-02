# Privacy Notice

Package revision: 1 October 2026. The matching `2.0.0` backend rollout is pending.

This repository notice describes data handling specific to the public Vucar vehicle intelligence MCP integration. It supplements Vucar's [official privacy policy](https://vucar.vn/policy/chinh-sach-bao-mat-thong-tin).

## Data sent to Vucar

When an AI client calls a tool, it sends the vehicle attributes present in that request. Depending on the tool, these can include brand, model, optional variant, production year, and mileage. An offer calculation can send the gross quoted offer, an aggregate of confirmed deductions, and whether all deductions are known. An upgrade calculation can send the current and replacement vehicles and an aggregate of fully confirmed additional costs. These VND amounts are used transiently for the requested calculation; the tools do not need a private loan or expense breakdown. Selling guidance can use supported non-identifying preparation options. Catalog requests can send a partial brand/model/year hierarchy. Comparison requests may include a legacy optional label for client compatibility; the service ignores that text and derives result labels from validated, canonical vehicle attributes.

Some fields accept free-form text, so technical schema controls cannot prevent every accidental disclosure. Do not place names, phone numbers, email addresses, street addresses, account identifiers, precise location, license-plate numbers, vehicle-identification numbers, lender or loan-account details, or other identifying or unnecessary confidential information in any field. Use only the non-identifying attributes and aggregate amounts needed for the request.

## Service metadata

Vucar's hosting infrastructure (Vercel) may process standard connection metadata such as network address, request time, user agent, protocol headers, response status, and security events for delivery, abuse prevention, reliability, and debugging.

Before rate-limit identifiers are sent to Upstash, the service transforms the client network address with a secret-keyed HMAC. The rate-limit store receives the resulting pseudonymous key rather than the raw address, and those keys expire with the short rate-limit window. This does not make connection metadata anonymous at the hosting edge. Operational or security logs, if created, follow Vucar's official privacy policy and applicable legal requirements.

The planned `2.0.0` application records coarse operational events for allowlisted public tool calls: the tool name, response outcome (`tool_result`, `tool_error`, `request_error`, or `unobserved`), latency, and server version. That application event does not include arguments, quote or cost amounts, vehicle details, IP addresses, conversation content, or user identifiers. Hosting connection metadata described above is processed separately.

These outcomes describe the observed MCP response, not what an owner completed. `tool_result` does not establish a completed owner task, a clicked handoff, a lead, a sale, or an organic brand mention. Source attribution in a generated answer is not evidence of an independently observed organic mention.

## Outputs

The service returns public vehicle taxonomy, indicative valuation data, calculations from supplied amounts, and selling guidance. Values use integer VND. Valuations disclose low or unknown confidence and unverified range calibration; raw upstream coverage counts do not establish completed-sale or verified training coverage. Legacy model-comparable and savings fields are null because their upstream meaning or benefit is unverified. Unknown deductions and costs remain unresolved. It does not return customer, employee, dealer, lead, booking, inspection, auction, bid, payment, or internal reporting records.

A returned valuation report URL includes public, non-identifying vehicle attributes in its query: brand, model, year, mileage, and an optional variant. It contains no offer, deduction, cost, contact, or account data. Each view recomputes a current reference; it does not create a saved appraisal or customer record. Browser and client histories may retain the URL under their own settings.

## AI client processing

Codex, Claude Code, or another MCP client may separately process and retain prompts, tool inputs, and outputs under that provider's terms and settings. Review the privacy controls of the client you choose. Vucar does not control third-party client processing.

## Authentication and cookies

The public tools require no Vucar account, API key, or authentication cookie. Do not send credentials to the endpoint.

## Retention

The MCP application does not create user profiles or write tool inputs or outputs to a Vucar application database. It processes the supplied vehicle attributes and aggregate quote, deduction, or cost amounts to produce the response, then releases that request data when processing completes. Coarse operational events contain only the fields described above and follow the hosting account's operational-log retention settings; they do not retain those inputs or valuation report contents.

Pseudonymous rate-limit keys expire automatically after the short rate-limit window. Vucar's infrastructure providers may retain limited connection, reliability, and security metadata under Vucar's account configuration and their published terms. Vucar uses that metadata only to operate, secure, and troubleshoot the service, and does not use it to build advertising profiles.

## User choices and questions

You can stop future processing at any time by disabling or uninstalling the connector in your AI client. Because the public tools require no account and the MCP application does not persist tool inputs or outputs, there is no MCP-specific user profile to delete.

Material integration-specific changes will be recorded in this repository. To ask a non-sensitive privacy question or exercise an applicable data right concerning infrastructure metadata, use [Vucar's contact page](https://vucar.vn/contact). Use the private process in [SECURITY.md](SECURITY.md) for suspected data exposure.
