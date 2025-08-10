### mcpconf

Unified configuration and conversion for MCP server definitions.

- Schema: `mcp-servers.schema.json`
- Example: `examples/mcp-servers.example.yaml`
- CLI: `mcpconf`

Quick start:

```bash
pip install -e .
# validate
python3 -m mcpconf.cli validate examples/mcp-servers.example.yaml --schema mcp-servers.schema.json
# convert to Claude Desktop/CLI JSON
python3 -m mcpconf.cli convert examples/mcp-servers.example.yaml --to mcpServers-json > examples/outputs/mcpServers.json
# convert to GitHub Copilot http-only
python3 -m mcpconf.cli convert examples/mcp-servers.example.yaml --to github-servers-json > examples/outputs/github-servers.json
# generate Claude CLI commands
python3 -m mcpconf.cli convert examples/mcp-servers.example.yaml --to claude-cli > examples/outputs/claude-cli.sh
```

### Running tests

```bash
pip install -e .
pytest -q
```

If you prefer using the CLI script name `mcpconf`, ensure your Python environment's bin directory is on `PATH` after installation. Otherwise, you can always use the module entry point as shown above with `python3 -m mcpconf.cli`.
