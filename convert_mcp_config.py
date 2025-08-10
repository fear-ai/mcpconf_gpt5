#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".yaml") or path.endswith(".yml"):
        if yaml is None:
            print("PyYAML not installed. Run: pip install -r requirements.txt", file=sys.stderr)
            sys.exit(2)
        return yaml.safe_load(text)
    return json.loads(text)


def to_mcpServers_json(cfg: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"mcpServers": {}}
    for srv in cfg.get("servers", []):
        sid = srv["id"]
        if srv["deployment"] == "local":
            entry: Dict[str, Any] = {"command": srv["command"]}
            if "args" in srv:
                entry["args"] = srv["args"]
            if "env" in srv:
                entry["env"] = srv["env"]
            result["mcpServers"][sid] = entry
        else:
            # Remote: prefer url key if supported
            if "url" in srv:
                result["mcpServers"][sid] = {"url": srv["url"]}
            else:
                # Fallback to npx mcp-remote if URL missing (unlikely)
                result["mcpServers"][sid] = {"command": "npx", "args": ["mcp-remote", srv.get("url", "")]}
    return result


def to_github_servers_json(cfg: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"servers": {}, "inputs": cfg.get("inputs", [])}
    for srv in cfg.get("servers", []):
        sid = srv["id"]
        if srv["deployment"] == "remote":
            entry: Dict[str, Any] = {"type": "http", "url": srv.get("url", "")}
            headers: Dict[str, str] = {}
            # Build Authorization header when possible
            auth = srv.get("auth") or {}
            if auth:
                scheme = auth.get("scheme", "none")
                header_name = auth.get("header", "Authorization")
                if scheme == "bearer":
                    token = auth.get("token", "${input:token}")
                    headers[header_name] = f"Bearer {token}"
                elif scheme == "api_key":
                    token = auth.get("token", "${input:api_key}")
                    headers[header_name] = token
                elif scheme == "basic":
                    user = auth.get("username", "${input:username}")
                    pwd = auth.get("password", "${input:password}")
                    headers[header_name] = f"Basic {user}:{pwd}"
            if headers:
                entry["headers"] = headers
            out["servers"][sid] = entry
        else:
            # Local servers are not directly representable in GitHub's http-only format; skip
            continue
    return out


def to_claude_cli(cfg: Dict[str, Any]) -> str:
    lines = []
    for srv in cfg.get("servers", []):
        sid = srv["id"]
        if srv["deployment"] == "remote":
            # Claude CLI supports http transport add
            url = srv.get("url", "")
            transport = srv.get("transport", "http")
            if transport in ("http", "sse"):
                lines.append(f"claude mcp add --transport http {sid} {url}")
            else:
                # Unknown remote transport; skip
                continue
        else:
            # Local: use json payload variant
            payload = {"command": srv["command"]}
            if "args" in srv:
                payload["args"] = srv["args"]
            if "env" in srv:
                payload["env"] = srv["env"]
            json_payload = json.dumps(payload, separators=(",", ":"))
            lines.append(f"claude mcp add-json {sid} '{json_payload}'")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert consolidated MCP servers config to various target formats")
    parser.add_argument("config", help="Path to mcp-servers YAML or JSON file")
    parser.add_argument("--to", required=True, choices=["mcpServers-json", "github-servers-json", "claude-cli"], help="Target output format")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.to == "mcpServers-json":
        out = to_mcpServers_json(cfg)
        print(json.dumps(out, indent=2))
    elif args.to == "github-servers-json":
        out = to_github_servers_json(cfg)
        print(json.dumps(out, indent=2))
    elif args.to == "claude-cli":
        print(to_claude_cli(cfg))
    else:
        parser.error("Unsupported target")


if __name__ == "__main__":
    main()
