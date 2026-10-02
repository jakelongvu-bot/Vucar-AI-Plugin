# Changelog

All notable changes to this project are documented here. This project follows Semantic Versioning for published plugin metadata.

## [Unreleased]

### Fixed

- Use an explicit HTTPS repository URL for Claude marketplace installation so consumers do not need GitHub SSH keys.

## [2.0.0] - Prepared 2026-10-01

### Added

- Four owner and seller skills for valuation/report explanation, offer and net proceeds, upgrade cash gap, and sale preparation.
- Review metadata with five positive and three negative scenarios, Vietnam availability, current Vucar policy links, and source artwork.
- A deterministic OpenAI review ZIP builder and separate checks for the wrapped upload configuration and client marketplace configuration.

### Changed

- Prepare for six read-only tools while preserving catalog, valuation, and comparison.
- Preserve low/unknown confidence, unverified range calibration, factual source/report attribution, and incomplete costs rather than inventing final amounts.
- Keep unverified legacy coverage/savings fields null and document transient aggregate calculations, recomputed public report URLs, and coarse operational events without downstream outcome claims.
- Replace the obsolete standalone submission packet with manifest-owned review metadata.

### Pending

- Backend rollout, live contract/review verification, and an accessible reviewer video. This package has not been submitted or published by these changes.

## [1.0.1] - 2026-08-21

### Security

- Require case-insensitive exact catalog matches before valuation and return only canonical vehicle attributes.
- Accept legacy comparison labels for compatibility but ignore and never reflect caller-provided label text.
- Add bounded shared catalog caching and weighted upstream-work limits to reduce request amplification.

### Changed

- Replace unsupported example variants with catalog-supported `1.5G` fixtures.
- Add marketplace-ready, search-aware listing copy and stronger live regression checks.
- Round VND outputs to 1 million, expose model-data confidence, and include input indexes plus mileage in computed comparison labels.

## [1.0.0] - 2026-08-04

### Added

- Initial Codex and Claude Code marketplace catalogs.
- Dual plugin manifests for the Vucar read-only vehicle intelligence integration.
- Remote Streamable HTTP MCP configuration for the public Vucar endpoint.
- Official MCP Registry metadata.
- OpenAI plugin submission import packet with five positive and three negative review cases.
- Offline repository validation, deterministic tests, and an opt-in live protocol smoke test.
- Security, privacy, terms, support, contribution, release, and conduct policies, including integration-specific retention and user controls.

[Unreleased]: https://github.com/jakelongvu-bot/Vucar-AI-Plugin/compare/vucar--v1.0.1...HEAD
[1.0.1]: https://github.com/jakelongvu-bot/Vucar-AI-Plugin/compare/vucar--v1.0.0...vucar--v1.0.1
[1.0.0]: https://github.com/jakelongvu-bot/Vucar-AI-Plugin/releases/tag/vucar--v1.0.0
