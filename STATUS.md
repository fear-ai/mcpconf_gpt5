### Project status
- Summary: chore: initial import of mcpconf implementation, schema, docs, examples, tests
- Date: 2025-08-10

- GitHub setup: Steps 1–4 in `GITHUB.md` completed; further Git/GitHub tasks (PRs, protections, releases) are deprioritized for now.

### Artifacts
- Package: `src/mcpconf` with CLI (`python3 -m mcpconf.cli`)
- Schema: `mcp-servers.schema.json`
- Docs: `README.md`, `SERVERS.md`, `MCPCONF.md`, `DESIGN.md`, `GITHUB.md`
- Examples: `examples/mcp-servers.example.yaml` with generated outputs in `examples/outputs/`
- Tests: `pytest -q` (5 tests passing)

### Next steps
- CLI smoke tests, helpful error messages, `--output` path, and `--format` autodetect for inputs, all `--to` targets
- Validate edge cases: missing required fields, invalid `transport`, bad URLs, unknown auth schemes.
- Extend converters: add DXT manifest emitter; refine remote URL handling (SSE vs HTTP) where clients differ
- Implement discovery loader in library and CLI (project/user/system locations and `MCP_SERVERS_CONFIG`)
- Finalize discovery and precedence model (project > env var > user > system) with clear override semantics
- Add header merge precedence and auth schemes (bearer/api_key/basic) including custom header names
- Update docs with discovery details and examples; add security best practices
- Round-trip loader tests (YAML/JSON)
- Refine SSE/HTTP handling
- Clarify auth/header merge rules and placeholders (`${input:...}`, `${env:...}`) across targets, expand tests and error cases 

- Documentation:
  - Expand `MCPCONF.md` with concrete discovery examples per OS and env var
  - Document transport support matrix and behavior for `stdio`, `http`, `sse`
  - Add migration/usage examples for common servers (Everything, Sentry, Cloudflare, GitHub)
  - Add security guidance examples for `${input:...}` vs `${env:...}`
  - Defer GitHub-specific workflows/badges until CI is reinstated
