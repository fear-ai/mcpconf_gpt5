### MCPCONF Design

This document captures the design choices made for externalizing MCP server definitions and how they align with official Model Context Protocol materials and linked examples.

### Objectives
- Provide a single, validated source of truth for MCP server connection details consumable by diverse clients and LLM tools.
- Preserve fidelity for local (stdio) and remote (http/sse) servers.
- Map cleanly to existing formats (Claude Desktop/CLI `mcpServers`, GitHub http-only, DXT manifests) without loss of essential information.

### Core model
- Top-level keys: `version`, `servers`, `inputs`.
- Server:
  - Identity and UX: `id`, `name`, optional `tags`, `notes`.
  - Deployment: `deployment` in {`local`, `remote`} and `transport` in {`stdio`, `http`, `sse`}.
  - Local specifics: `command`, `args[]`, `env{}`, `working_directory`.
  - Remote specifics: `url`, optional `headers{}`.
  - Auth abstraction: `auth.scheme` in {`bearer`, `api_key`, `basic`, `none`} with `token`/`header`/`username`/`password` and references `${input:...}` or `${env:...}`.
  - Provenance: `source.repository`, `source.license`, `source.available`, `source.vendor`.
- Inputs: prompt metadata including `type`, `id`, `description`, `password`, `default`.

Rationale:
- Distinguishing local vs remote mirrors official MCP client expectations (spawn stdio vs network URL).
- Transport hints enable future expansion (e.g., WebSocket/grpc) and align with HTTP vs SSE usage in linked repos.
- Auth abstraction acknowledges diversity in client secret flows while keeping conversion straightforward.

### Compatibility
- Claude Desktop/CLI `mcpServers`: local entries rendered as `{ command, args?, env? }`, remote URLs emitted as `{ url }` when supported.
- GitHub http-only config: only `remote` entries mapped; local entries skipped; `headers` merged from static and auth-derived values; `inputs` carried through.
- Claude CLI: emits `claude mcp add --transport http <id> <url>` for remote and `claude mcp add-json <id> '{...}'` for local.

Trade-offs:
- GitHub http-only format cannot represent local servers; we intentionally drop them for that target.
- Some clients may not accept SSE URLs directly; we still capture them as remote and rely on client capability.

### Validation and tooling
- JSON Schema (`mcp-servers.schema.json`) ensures structural integrity and versioned evolution.
- CLI `mcpconf` provides pure conversion and validation; no side effects or network calls.
- Tests verify conversion coverage and schema validation.

### Security posture
- Encourage placeholder references (`${input:...}`, `${env:...}`) to avoid committed secrets.
- Do not interpret or resolve secrets in the library; clients are responsible.
- Support merging explicit headers with auth-generated headers to preserve advanced cases while avoiding duplication.

### Directory and discovery (guidance)
- Suggested locations and precedence (project > env var > user > system) are documented in `MCPCONF.md` for clients to implement.
- Library does not enforce discovery; keeps concerns separated.

### Implementation alignment checklist
- Local/remote distinction present and required per schema.
- Transports supported: `stdio`, `http`, `sse`.
- Local fields supported: `command`, `args`, `env`, `working_directory`.
- Remote fields supported: `url`, `headers`.
- Auth mapping implemented for `bearer`, `api_key`, `basic`; emits standard headers; carries `inputs` in GitHub target.
- Compatibility targets implemented: Claude `mcpServers`, GitHub http-only, Claude CLI commands.
- Schema versioning (`version: "1.0"`) enforced by examples and tests.
- Tests cover: local mapping, remote URL mapping, auth header emission, CLI script generation, schema validation.

### Future extensions
- Add explicit timeouts/retry hints; add `websocket`/`grpc` transports.
- Pluggable renderers for additional client formats; config linter.
- Signed configs and trust policy metadata.
