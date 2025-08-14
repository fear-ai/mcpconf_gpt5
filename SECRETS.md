## Secrets management for MCP server configs (MCPCONF)

### Executive summary
- Never commit plaintext secrets. Use placeholders that clients or your runtime resolve securely.
- Prefer interactive, OS-secured storage for local use; prefer environment injection from a secrets manager for CI/headless.
- In MCPCONF, reference secrets via `${input:...}` (interactive/keychain) or `${env:...}` (environment).

### Core principles
- Minimize blast radius: least-privilege tokens, per-environment separation.
- Avoid persistence in plaintext: rely on OS keychain or ephemeral env injection.
- Make rotation easy: swap values in secret stores without changing committed config.
- Log hygiene: never print tokens; redact headers in logs.

---

## Methods and techniques

### 1) Interactive prompt + OS keychain (recommended for local dev)
- Use `${input:<id>}` in `auth` and define an input with `password: true`.
- The client (e.g., Copilot, IDE, or orchestrator) prompts once and stores the secret in the OS keychain (macOS Keychain, Windows Credential Manager, GNOME Keyring), reusing it subsequently.

MCPCONF:
```yaml
version: "1.0"
servers:
  - id: github
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

Notes:
- Clients decide the exact storage location and encryption; your config remains secret-free.

### 2) Environment variables (recommended for CI and headless)
- Use `${env:<VAR>}` in `auth` and inject the env var at process startup (never commit the value).

MCPCONF:
```yaml
version: "1.0"
servers:
  - id: github
    deployment: remote
    transport: http
    url: "https://api.githubcopilot.com/mcp/"
    auth:
      scheme: bearer
      header: Authorization
      token: "${env:GITHUB_MCP_PAT}"
```

Injection examples:
- GitHub Actions: define repo secret `GITHUB_MCP_PAT`, then
  ```yaml
  env:
    GITHUB_MCP_PAT: ${{ secrets.GITHUB_MCP_PAT }}
  ```
- 1Password CLI: `export GITHUB_MCP_PAT=$(op read op://Vault/Item/field)`
- AWS Secrets Manager: `export GITHUB_MCP_PAT=$(aws secretsmanager get-secret-value ...)`

### 3) Secrets managers (backing env or keychain)
- Use a manager to source secrets, but surface to apps as inputs or env vars.
- Common: GitHub Actions Secrets, 1Password, HashiCorp Vault, AWS/GCP Secret Manager, Azure Key Vault.

### 4) Local files (.env) with strict controls (last resort)
- If needed, keep `.env.local` out of VCS and set permissions (e.g., `chmod 600`). Load into env with a tool like `direnv`.
- Do not commit `.env` files; keep them listed in `.gitignore`.

---

## Precedence and resolution

- File precedence when discovering configs in this project: `system < user < env < project` (higher overrides by `id`).
- Secret resolution (client recommendation): `env value` > `stored secret (from prior input)` > `interactive prompt` > fail in headless.
- Header construction: `auth`-derived header overwrites a static header of the same name when converting to target formats.

---

## Applying to mcpconf

### How placeholders flow
- `auth.token`, `auth.username`, `auth.password` may contain `${input:...}` or `${env:...}`.
- Converters (`to_github_servers_json`, `to_mcpServers_json`) pass placeholders through into headers or env, without resolving values.
- Clients interpret placeholders: prompt the user (and store securely) or read from env at runtime.

### Example: GitHub Copilot http-only JSON
Input config:
```yaml
version: "1.0"
servers:
  - id: github
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
Converted with `mcpconf`:
```json
{
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {"Authorization": "Bearer ${input:github_mcp_pat}"}
    }
  },
  "inputs": [
    {"type": "promptString", "id": "github_mcp_pat", "description": "GitHub Personal Access Token", "password": true}
  ]
}
```

### Example: Claude CLI command generation
- Remote servers: no secret material in commands; server reads headers at client side.
- Local servers: put non-secret config in `env`; inject secrets at runtime via shell env.

Local server with env placeholder:
```yaml
servers:
  - id: brave-search
    deployment: local
    transport: stdio
    command: npx
    args: ["-y", "brave-search-mcp"]
    env:
      BRAVE_API_KEY: "${env:BRAVE_API_KEY}"
```
Runtime:
```bash
export BRAVE_API_KEY=$(op read op://Vault/Brave/API-KEY)
claude mcp add-json brave-search '{"command":"npx","args":["-y","brave-search-mcp"],"env":{"BRAVE_API_KEY":"${env:BRAVE_API_KEY}"}}'
```

### Layered overrides to switch storage method
Base (user layer) uses input/keychain:
```yaml
servers:
  - id: github
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
    password: true
```
Project or env layer overrides to env-based in CI:
```yaml
servers:
  - id: github
    deployment: remote
    transport: http
    url: "https://api.githubcopilot.com/mcp/"
    auth:
      scheme: bearer
      header: Authorization
      token: "${env:GITHUB_MCP_PAT}"
```
`discover_and_merge()` will produce a final config where the higher layer replaces the `github` server by `id`.

---

## Scenarios and step-by-step

### A) Local developer on macOS/Windows/Linux (Claude Desktop or IDE)
1. In MCPCONF, use `${input:...}` and define the input with `password: true`.
2. Start client; it prompts and stores in the OS keychain. No env needed.
3. Rotate by updating the stored secret in the client UI or keychain.

### B) CI job generating GitHub servers config
1. Store token in the CI secrets store (e.g., GitHub Actions Secrets).
2. In MCPCONF (project layer), reference `${env:GITHUB_MCP_PAT}`.
3. In workflow, set `env.GITHUB_MCP_PAT: ${{ secrets.GITHUB_MCP_PAT }}`.
4. Run conversion:
   ```bash
   python3 -m mcpconf.cli convert path/to/config.yaml --to github-servers-json > github-servers.json
   ```

### C) Team repository with layered overrides
1. User layer (`~/.config/mcp/mcp-servers.yaml`) defines servers using `${input:...}`.
2. Project adds `mcp-servers.yaml` overriding only servers that require CI automation with `${env:...}`.
3. Use `discover_and_merge()` to combine; project overrides win by `id`.

### D) Local CLI server needing API key
1. MCPCONF defines local server with `env` key pointing to `${env:API_KEY}`.
2. Developer exports `API_KEY` from a password manager in their shell session.
3. Launch client or run CLI command with exported env variable.

---

## Do/Don’t checklist
- Do: use `${input:...}` for interactive local use; `${env:...}` for headless/CI.
- Do: source env vars from a proper secret manager.
- Do: enforce least-privilege scopes; prefer short-lived tokens if supported.
- Don’t: commit plaintext tokens or `.env` files.
- Don’t: print tokens; scrub logs, especially headers like `Authorization`.

---

## Rotation and auditing
- Rotate tokens by updating secret manager entries or re-entering inputs in the client (keychain updated).
- Prefer secrets with expiry; monitor access logs in your provider.
- Keep conversion outputs (`*.json`) out of VCS if they may contain unresolved placeholders referencing secrets.

---

## References
- Model Context Protocol: `https://modelcontextprotocol.io/quickstart/server`
- GitHub Copilot MCP server: `https://github.com/github/github-mcp-server`
- 1Password CLI: `https://developer.1password.com/docs/cli/`
- AWS Secrets Manager: `https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html`
- HashiCorp Vault: `https://www.vaultproject.io/docs`
