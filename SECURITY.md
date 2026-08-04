# Security Policy

## Supported versions

Security fixes are provided for the latest published release.

| Version | Supported |
| --- | --- |
| 1.x | Yes |
| Earlier or unreleased forks | No |

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or include exploit details, credentials, personal data, or customer information in a public report.

Use GitHub's private vulnerability reporting feature for this repository:

1. Open the repository's **Security** tab.
2. Choose **Report a vulnerability**.
3. Include the affected version, impact, reproducible steps, and the minimum proof needed to confirm the issue.

If private vulnerability reporting is temporarily unavailable, use [Vucar's contact page](https://vucar.vn/contact) to request a private security channel. Do not include exploit details, credentials, or personal data in that initial request.

Maintainers will acknowledge a complete report as soon as reasonably possible, investigate it, and coordinate remediation and disclosure. Please allow time for a fix before publishing details.

## Scope

In scope:

- Marketplace and plugin manifest behavior.
- Unexpected tools, privileges, or data returned by the Vucar public MCP endpoint.
- Authentication or authorization bypasses.
- Injection, request-smuggling, cross-origin, denial-of-service, or sensitive-data exposure affecting the endpoint.

Out of scope:

- High-volume automated testing or traffic that affects service availability.
- Social engineering, physical attacks, or testing third-party AI clients.
- Vehicle-estimate accuracy disagreements that do not involve a security flaw.

Never test with real personal information. Use synthetic vehicle data only.
