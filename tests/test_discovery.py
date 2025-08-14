from __future__ import annotations

import json
from pathlib import Path

import yaml  # type: ignore

from mcpconf.discovery import (
    DiscoveryContext,
    discover_and_merge,
    discover_layered_paths,
    merge_configs_low_to_high,
)


def write_cfg(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix in {".yaml"}:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(data), encoding="utf-8")


def test_merge_configs_overrides_by_id(tmp_path: Path) -> None:
    low = {
        "version": "1.0",
        "servers": [
            {"id": "a", "deployment": "local", "transport": "stdio", "command": "node"},
            {"id": "b", "deployment": "remote", "transport": "http", "url": "https://x"},
        ],
        "inputs": [
            {"type": "promptString", "id": "token", "password": True},
        ],
    }
    high = {
        "version": "1.0",
        "servers": [
            {"id": "b", "deployment": "remote", "transport": "http", "url": "https://y"},
            {"id": "c", "deployment": "local", "transport": "stdio", "command": "uv"},
        ],
        "inputs": [
            {"type": "promptString", "id": "token", "description": "T", "password": True},
        ],
    }
    merged = merge_configs_low_to_high([low, high])
    ids = {s["id"] for s in merged["servers"]}
    assert ids == {"a", "b", "c"}
    # server b overridden
    server_b = next(s for s in merged["servers"] if s["id"] == "b")
    assert server_b["url"] == "https://y"
    # input overridden
    input_token = next(i for i in merged.get("inputs", []) if i["id"] == "token")
    assert input_token.get("description") == "T"


def test_discover_layered_paths_order(tmp_path: Path) -> None:
    system_dir = tmp_path / "etc" / "mcp"
    user_dir = tmp_path / "home" / "user" / ".config" / "mcp"
    project_root = tmp_path / "project"
    env_file = tmp_path / "env" / "mcp-servers.yaml"

    write_cfg(system_dir / "mcp-servers.yaml", {"version": "1.0", "servers": []})
    write_cfg(user_dir / "mcp-servers.yaml", {"version": "1.0", "servers": []})
    write_cfg(project_root / "mcp-servers.yaml", {"version": "1.0", "servers": []})
    write_cfg(env_file, {"version": "1.0", "servers": []})

    ctx = DiscoveryContext(
        project_root=project_root,
        env_config_path=env_file,
        user_config_dir=user_dir,
        system_config_dir=system_dir,
    )
    layered = discover_layered_paths(ctx)
    layers = [layer for layer, _ in layered]
    # order should be low->high: system, user, env, project
    assert layers == ["system", "user", "env", "project"]


def test_discover_and_merge_aggregates_layers(tmp_path: Path) -> None:
    system_dir = tmp_path / "etc" / "mcp"
    user_dir = tmp_path / "home" / "user" / ".config" / "mcp"
    project_root = tmp_path / "project"

    write_cfg(system_dir / "mcp-servers.yaml", {
        "version": "1.0",
        "servers": [{"id": "sys", "deployment": "remote", "transport": "http", "url": "https://sys"}],
    })
    write_cfg(user_dir / "mcp-servers.yaml", {
        "version": "1.0",
        "servers": [{"id": "user", "deployment": "local", "transport": "stdio", "command": "node"}],
    })
    write_cfg(project_root / "mcp-servers.yaml", {
        "version": "1.0",
        "servers": [
            {"id": "user", "deployment": "local", "transport": "stdio", "command": "uv"},
            {"id": "proj", "deployment": "remote", "transport": "http", "url": "https://proj"},
        ],
    })

    ctx = DiscoveryContext(
        project_root=project_root,
        user_config_dir=user_dir,
        system_config_dir=system_dir,
    )
    merged = discover_and_merge(ctx)
    ids = {s["id"] for s in merged["servers"]}
    assert ids == {"sys", "user", "proj"}
    # project overrides user for id "user"
    user_server = next(s for s in merged["servers"] if s["id"] == "user")
    assert user_server["command"] == "uv"
