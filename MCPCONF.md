## MCP Server Access Configuration (MCPCONF)

### Executive summary
- **Goal**: Provide a portable, tool-agnostic way to externalize definitions of MCP server access for Clients and LLM-based tools.
- **Why**: Today, client ecosystems (e.g., Claude Desktop/CLI `mcpServers`, vendor remote endpoints, GitHub http-only servers, DXT manifests) use similar but non-identical formats. A consolidated, validated configuration improves portability, security, and automation.
- **How**: Define a small, versioned data model that distinguishes local (spawned, stdio) vs remote (http/sse) servers, captures command/args/env or URL/headers, abstracts authentication and inputs, and is trivially transpilable to existing formats.

### Scope and non-goals
- **In scope**: Configuration for discovering and connecting to MCP servers; client-side auth/header/env injection; compatibility generation; discovery/precedence; validation.
- **Out of scope**: Server implementation details, tool schemas, transport-level protocol behavior, central registry governance.

### Terminology
- **Client**: An application that connects to MCP servers (e.g., Claude Desktop/CLI, IDE plugins, orchestrators).
- **Server**: An MCP server, local (spawned process using stdio) or remote (network transport such as HTTP/SSE).
- **Externalized config**: File-based, declarative definitions that can be shared, versioned, or deployed.

## Requirements

### Functional
- **R1 Local vs Remote**: Must represent both local servers (spawn command via stdio) and remote servers (http/sse URL).
- **R2 Process invocation**: For local servers, capture `command`, `args`, optional `env`, and optional working directory.
- **R3 Remote connection**: For remote servers, capture `url`, optional static `headers`, and transport type (`http`, `sse`).
- **R4 Authentication**: Express auth schemes (bearer, api key, basic, none) with placeholders referencing inputs or environment.
- **R5 Inputs**: Define user prompts (e.g., secret tokens) for clients that support prompting and secure storage.
- **R6 Metadata**: Include optional human-friendly `name`, `description`, `tags`, and `source` (repo, license, vendor, availability).
- **R7 Versioning**: A top-level `version` for schema evolution; clients MUST validate.
- **R8 Cross-platform**: Express without OS-specific path requirements; allow absolute paths when necessary; suggest discovery rules per OS.
- **R9 Compatibility**: Must losslessly generate:
  - Claude Desktop/CLI `mcpServers` JSON for local and some remote URL use-cases
  - GitHub Copilot-style http-only server config
  - Claude CLI commands (`claude mcp add` and `claude mcp add-json`)
  - Embed-friendly DXT-like manifests (when used within an extension)
- **R10 Discovery**: Support layered discovery: per-project, per-user, system; define precedence.
- **R11 Validation**: Provide JSON Schema; clients SHOULD validate and fail fast with actionable errors.
- **R12 Extensibility**: Leave room for new transports (e.g., websocket/grpc), auth methods, and policy hints.

### Security
- **S1 Secret handling**: No plaintext secrets in committed files. Support `${input:...}` and `${env:...}` references.
- **S2 Prompting**: Mark inputs as `password` where appropriate; clients SHOULD mask and store securely (e.g., OS keychain).
- **S3 Principle of least privilege**: For local servers, encourage allowlists (e.g., working directories) and sane timeouts.
- **S4 Header injection safety**: Carefully construct headers; avoid logging secrets; clients SHOULD redact.
- **S5 Supply chain**: Prefer pinned command invocations (e.g., `uvx` locked envs, npx with explicit packages) and signed binaries when available.

### Operability
- **O1 Health and errors**: Clients SHOULD surface connection errors and health checks distinctly (spawn vs HTTP errors).
- **O2 Logging**: Clients SHOULD provide per-server logging controls. Secrets MUST be redacted.
- **O3 Timeouts/retries**: Config MAY include timeouts; clients SHOULD implement sensible defaults.
- **O4 Overrides**: Per-project overrides of global config SHOULD be supported without editing the global file.

## Data model (MCPCONF)

A concise, versioned model that captures local and remote forms and maps to existing ecosystems. A full schema is provided in `mcp-servers.schema.json` and an example in `examples/mcp-servers.example.yaml`.

### Top-level
- **version**: Schema version string (e.g., `"1.0"`).
- **servers**: Array of server entries.
- **inputs**: Array of input prompts referenced by servers (optional).

### Server entry
- **id**: Stable identifier (used as key in generated configs).
- **name**: Human-readable name (optional).
- **deployment**: `local` | `remote`.
- **transport**: `stdio` | `http` | `sse`.
- **type**: Informational runtime packaging (e.g., `python`, `node`, `binary`, `http`).
- For `local`:
  - **command**: Executable name/path (e.g., `uv`, `uvx`, `python`, `node`, `npx`).
  - **args**: Array of args (optional).
  - **env**: Key/value map of environment variables (optional).
  - **working_directory**: Path for process start (optional).
- For `remote`:
  - **url**: Base URL (e.g., `https://.../mcp` or SSE endpoint).
  - **headers**: Static header map (optional).
- **auth** (optional):
  - **scheme**: `bearer` | `api_key` | `basic` | `none`.
  - **token**, **header**, **env_ref**, **input_ref**, **username**, **password**: As appropriate for the scheme.
- **source** (optional):
  - **repository**, **license**, **available** (bool), **vendor**.
- **tags**, **notes** (optional).

### Inputs
- **type**: `promptString` | `secret` | `boolean` | `number`.
- **id**: Reference identifier.
- **description**: Help text (optional).
- **password**: Masked entry (boolean; for string inputs).
- **default**: Default value (optional).

## Compatibility mapping

### Claude Desktop/CLI (`mcpServers` JSON)
- Local servers map to `{ command, args?, env? }` under `mcpServers[id]`.
- Some remote servers map to `{ url }` where supported by clients.
- Example (from quickstart python weather):

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/PARENT/FOLDER/weather", "run", "weather.py"]
    }
  }
}
```

### Claude CLI convenience
- Remote: `claude mcp add --transport http <id> <url>`
- Local: `claude mcp add-json <id> '{"command":"...","args":[...],"env":{...}}'`

### GitHub Copilot http-only config
- Remote servers map to:

```json
{
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${input:github_mcp_pat}" }
    }
  },
  "inputs": [
    { "type": "promptString", "id": "github_mcp_pat", "description": "GitHub Personal Access Token", "password": true }
  ]
}
```

### DXT manifests (embedding within extensions)
- When the server is packaged with an extension, an `mcp_config` block similar to:

```json
{
  "server": {
    "type": "python",
    "entry_point": "server/main.py",
    "mcp_config": {
      "command": "python",
      "args": ["${__dirname}/server/main.py"],
      "env": {"PYTHONPATH": "${__dirname}/server/lib"}
    }
  }
}
```

### Remote SSE (e.g., Cloudflare)
- Remote servers defined by SSE endpoints can map to `url: https://.../sse` and be consumed by clients that support SSE.

## Discovery and precedence
- **Locations**: Clients SHOULD search in order:
  - Project: `./mcp-servers.{yaml,json}` or `./mcpservers.{yaml,json}`
  - User: `~/.config/mcp/mcp-servers.{yaml,json}` (Linux), `~/Library/Application Support/mcp/mcp-servers.{yaml,json}` (macOS), `%APPDATA%\mcp\mcp-servers.{yaml,json}` (Windows)
  - System: `/etc/mcp/mcp-servers.{yaml,json}` (Linux), machine-wide equivalents on other OSes
- **Environment override**: `MCP_SERVERS_CONFIG` path wins.
- **Precedence**: Project > Env var > User > System. Later layers override by `id`.

## Validation and tooling
- **Schema**: See `mcp-servers.schema.json` (JSON Schema, Draft 2020-12).
- **Example**: See `examples/mcp-servers.example.yaml` covering local, remote, auth, inputs, metadata.
- **Converters**: `convert_mcp_config.py` generates:
  - Claude Desktop/CLI `mcpServers` JSON
  - GitHub http-only `servers` JSON
  - Claude CLI commands

## Security guidance
- Prefer `${input:...}` references for secrets and let the client handle prompting and secure storage.
- Avoid committing real tokens; use environment references `${env:VAR}` when automation is required.
- For local servers, prefer sandboxed execution, explicit allowlists, and conservative timeouts.

## Future directions
- Additional transports (websocket, grpc), richer auth (OIDC), dynamic discovery via well-known URLs.
- Policy hints (e.g., tool allowlists/denylists), per-project consent prompts.
- Signed manifests and provenance metadata.

## Minimal example (YAML)

```yaml
version: "1.0"
servers:
  - id: sentry
    name: Sentry
    deployment: remote
    transport: http
    url: "https://mcp.sentry.dev/mcp"
  - id: everything
    name: Everything (Node)
    deployment: local
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-everything"]
  - id: github
    name: GitHub MCP
    deployment: remote
    transport: http
    url: "https://api.githubcopilot.com/mcp/"
    auth:
      scheme: bearer
      header: Authorization
      token: "${input:github_mcp_pat}"
inputs:
  - type: promptString
    id: github_mcp_pat
    description: GitHub Personal Access Token
    password: true
```

## References (authoritative)
- Model Context Protocol quickstart and examples (official): `https://modelcontextprotocol.io/quickstart/server`
- Everything server reference (official repo): `https://github.com/modelcontextprotocol/servers`
- Cloudflare MCP servers (SSE endpoints): `https://github.com/cloudflare/mcp-server-cloudflare`
- GitHub MCP server config (Copilot): `https://github.com/github/github-mcp-server`
- DXT manifest examples: `https://github.com/anthropics/dxt`
