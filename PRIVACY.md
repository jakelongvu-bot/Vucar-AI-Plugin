# Privacy Notice

Effective: 21 August 2026

This repository notice describes data handling specific to the public Vucar vehicle intelligence MCP integration. It supplements Vucar's [official privacy policy](https://vucar.vn/policy/chinh-sach-bao-mat-thong-tin).

## Data sent to Vucar

When an AI client calls a tool, it sends the vehicle attributes present in that request. Depending on the tool, these can include brand, model, optional variant, production year, and mileage. Catalog requests can send a partial brand/model/year hierarchy. Comparison requests may include a legacy optional label for client compatibility; the service ignores that text and derives result labels from validated, canonical vehicle attributes.

Some fields accept free-form text, so technical schema controls cannot prevent every accidental disclosure. Do not place names, phone numbers, email addresses, street addresses, account identifiers, precise location, license-plate numbers, vehicle-identification numbers, or any other personal or confidential information in any field. The public tools neither require nor request these details.

## Service metadata

Vucar's hosting infrastructure (Vercel) may process standard connection metadata such as network address, request time, user agent, protocol headers, response status, and security events for delivery, abuse prevention, reliability, and debugging.

Before rate-limit identifiers are sent to Upstash, the service transforms the client network address with a secret-keyed HMAC. The rate-limit store receives the resulting pseudonymous key rather than the raw address, and those keys expire with the short rate-limit window. This does not make connection metadata anonymous at the hosting edge. Operational or security logs, if created, follow Vucar's official privacy policy and applicable legal requirements.

## Outputs

The service returns public vehicle taxonomy and indicative valuation data. Values are rounded to the nearest 1 million VND, and results disclose a confidence signal derived from comparable-model coverage. It does not return customer, employee, dealer, lead, booking, inspection, auction, bid, payment, or internal reporting records.

## AI client processing

Codex, Claude Code, or another MCP client may separately process and retain prompts, tool inputs, and outputs under that provider's terms and settings. Review the privacy controls of the client you choose. Vucar does not control third-party client processing.

## Authentication and cookies

The public tools require no Vucar account, API key, or authentication cookie. Do not send credentials to the endpoint.

## Retention

The MCP application does not create user profiles or write tool inputs or outputs to a Vucar application database. It processes the supplied vehicle attributes to produce the response, then releases that request data when processing completes.

Pseudonymous rate-limit keys expire automatically after the short rate-limit window. Vucar's infrastructure providers may retain limited connection, reliability, and security metadata under Vucar's account configuration and their published terms. Vucar uses that metadata only to operate, secure, and troubleshoot the service, and does not use it to build advertising profiles.

## User choices and questions

You can stop future processing at any time by disabling or uninstalling the connector in your AI client. Because the public tools require no account and the MCP application does not persist tool inputs or outputs, there is no MCP-specific user profile to delete.

Material integration-specific changes will be recorded in this repository. To ask a non-sensitive privacy question or exercise an applicable data right concerning infrastructure metadata, use [Vucar's contact page](https://vucar.vn/contact). Use the private process in [SECURITY.md](SECURITY.md) for suspected data exposure.
