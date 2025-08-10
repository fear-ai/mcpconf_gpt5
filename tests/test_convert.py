from __future__ import annotations
import json
from pathlib import Path

from mcpconf.convert import load_config, to_mcpServers_json, to_github_servers_json, to_claude_cli


def load_example():
    return load_config(str(Path(__file__).parents[1] / "examples" / "mcp-servers.example.yaml"))


def test_to_mcpServers_json_contains_local_entries():
    cfg = load_example()
    out = to_mcpServers_json(cfg)
    m = out["mcpServers"]
    assert "weather" in m
    assert m["weather"]["command"] == "uv"
    assert "everything" in m
    assert m["everything"]["command"] == "npx"


def test_to_mcpServers_json_contains_remote_urls_when_available():
    cfg = load_example()
    out = to_mcpServers_json(cfg)
    m = out["mcpServers"]
    assert m["sentry"]["url"].startswith("https://")


def test_to_github_servers_json_skips_local_and_maps_remote():
    cfg = load_example()
    out = to_github_servers_json(cfg)
    servers = out["servers"]
    assert "weather" not in servers
    assert "github" in servers
    assert servers["github"]["type"] == "http"
    assert servers["github"]["url"].startswith("https://")
    assert "Authorization" in servers["github"]["headers"]


def test_to_claude_cli_generates_both_remote_and_local_commands():
    cfg = load_example()
    script = to_claude_cli(cfg)
    assert "claude mcp add --transport http sentry https://mcp.sentry.dev/mcp" in script
    assert "claude mcp add-json everything" in script
