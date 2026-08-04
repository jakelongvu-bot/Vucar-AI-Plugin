# Architecture and Public Boundary

## Overview

The repository is a distribution layer. It declares one remote MCP endpoint to Codex, Claude Code, and the official MCP Registry; it does not ship a local server or Vucar backend code.

```text
Codex or Claude Code
        |
        | MCP over HTTPS (Streamable HTTP)
        v
https://api.vucar.vn/mcp
        |
        | read-only public vehicle intelligence
        v
catalog search, indicative valuation, comparison
```

## Trust boundary

The public service is deliberately separate from authenticated Vucar operations. The plugin does not contain credentials and cannot grant access to private systems. Client installation adds only the documented public endpoint.

Allowed inputs are non-sensitive vehicle characteristics. Allowed outputs are public catalog data and indicative value estimates. Writes, user identity, customer records, operational workflow, and internal reporting remain outside the public boundary.

## Cross-client configuration

Claude Code automatically discovers `plugins/vucar/.mcp.json`, whose root is a direct server map. Codex's `mcpServers` manifest field points to that same `./.mcp.json` file. Both clients therefore install one shared configuration rather than parallel endpoint declarations. Offline validation proves that the shared client map and Registry metadata contain the exact same URL.

## Hosted-service controls

Controls implemented by the hosted service are not duplicated in this public repository. A production release should verify:

- HTTPS and Streamable HTTP protocol compliance.
- Exact host and origin validation.
- Small request-body limits and upstream timeouts.
- Distributed rate limiting that fails closed in production if the limiter is unavailable.
- A runtime kill switch.
- No-store responses and no search indexing.
- Tool annotations marking every operation read-only, non-destructive, and idempotent.
- Structured outputs that contain no personal or operational data.

## Versioning

Plugin and Registry versions use Semantic Versioning. MCP Registry versions are immutable after publication. A released version must agree across both plugin manifests, `server.json`, and `CHANGELOG.md`.

Tool-schema compatibility is a hosted-service concern. Removing or changing a field incompatibly requires a major release and a migration note.
