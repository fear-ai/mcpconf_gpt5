from __future__ import annotations
import json
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def load_config_text(text: str, *, is_yaml: bool | None = None) -> Dict[str, Any]:
    if is_yaml is None:
        # Heuristic: YAML has version: and top-level arrays without braces
        is_yaml = text.lstrip().startswith("version:") or not text.lstrip().startswith("{")
    if is_yaml:
        if yaml is None:
            raise RuntimeError("PyYAML not installed")
        return yaml.safe_load(text)
    return json.loads(text)


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    is_yaml = path.endswith('.yaml')
    return load_config_text(text, is_yaml=is_yaml)


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
            if "url" in srv and srv["url"]:
                result["mcpServers"][sid] = {"url": srv["url"]}
    return result


def to_github_servers_json(cfg: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"servers": {}, "inputs": cfg.get("inputs", [])}
    for srv in cfg.get("servers", []):
        sid = srv["id"]
        if srv["deployment"] != "remote":
            continue
        entry: Dict[str, Any] = {"type": "http", "url": srv.get("url", "")}
        headers: Dict[str, str] = {}
        # Static headers first
        for k, v in (srv.get("headers") or {}).items():
            headers[k] = v
        # Auth mapping
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
    return out


def to_claude_cli(cfg: Dict[str, Any]) -> str:
    lines = []
    for srv in cfg.get("servers", []):
        sid = srv["id"]
        if srv["deployment"] == "remote":
            url = srv.get("url", "")
            transport = srv.get("transport", "http")
            if transport in ("http", "sse") and url:
                lines.append(f"claude mcp add --transport http {sid} {url}")
        else:
            payload = {"command": srv["command"]}
            if "args" in srv:
                payload["args"] = srv["args"]
            if "env" in srv:
                payload["env"] = srv["env"]
            json_payload = json.dumps(payload, separators=(",", ":"))
            lines.append(f"claude mcp add-json {sid} '{json_payload}'")
    return "\n".join(lines)
