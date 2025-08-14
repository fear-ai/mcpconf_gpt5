from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .convert import load_config


@dataclass
class DiscoveryContext:
    """Holds search roots for configuration discovery.

    When a field is None, platform defaults and environment variables are used.
    Tests can override these to provide isolated directories.
    """

    project_root: Optional[Path] = None
    env_config_path: Optional[Path] = None
    user_config_dir: Optional[Path] = None
    system_config_dir: Optional[Path] = None


def _candidate_filenames() -> List[str]:
    return [
        "mcp-servers.yaml",
        "mcpservers.yaml",
        "mcp-servers.json",
        "mcpservers.json",
    ]


def _project_candidates(project_root: Path) -> List[Path]:
    return [project_root / name for name in _candidate_filenames()]


def _default_user_config_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "mcp"
    if os.name == "nt":
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(appdata) / "mcp"
    # Linux and other POSIX
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "mcp"


def _default_system_config_dir() -> Path:
    if sys.platform == "darwin":
        return Path("/Library/Application Support/mcp")
    if os.name == "nt":
        programdata = os.environ.get("PROGRAMDATA") or "C:/ProgramData"
        return Path(programdata) / "mcp"
    # Linux and other POSIX
    return Path("/etc/mcp")


def _first_existing_file(paths: Iterable[Path]) -> Optional[Path]:
    for p in paths:
        if p.is_file():
            return p
    return None


def discover_layered_paths(context: Optional[DiscoveryContext] = None) -> List[Tuple[str, Path]]:
    """Return existing config file paths by layer from lowest to highest precedence.

    Order: system, user, env, project
    """
    ctx = context or DiscoveryContext()

    # System layer
    system_dir = ctx.system_config_dir or _default_system_config_dir()
    system_file = _first_existing_file(
        [system_dir / "mcp-servers.yaml", system_dir / "mcpservers.yaml", system_dir / "mcp-servers.json", system_dir / "mcpservers.json"]
    )

    # User layer
    user_dir = ctx.user_config_dir or _default_user_config_dir()
    user_file = _first_existing_file(
        [user_dir / "mcp-servers.yaml", user_dir / "mcpservers.yaml", user_dir / "mcp-servers.json", user_dir / "mcpservers.json"]
    )

    # Env var layer
    env_path = ctx.env_config_path
    if env_path is None:
        env_value = os.environ.get("MCP_SERVERS_CONFIG")
        env_path = Path(env_value) if env_value else None
    env_file = env_path if (env_path and env_path.is_file()) else None

    # Project layer
    project_root = ctx.project_root or Path.cwd()
    project_file = _first_existing_file(_project_candidates(project_root))

    layered: List[Tuple[str, Path]] = []
    if system_file:
        layered.append(("system", system_file))
    if user_file:
        layered.append(("user", user_file))
    if env_file:
        layered.append(("env", env_file))
    if project_file:
        layered.append(("project", project_file))
    return layered


def _index_by_id(items: List[Dict[str, Any]], id_key: str = "id") -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for item in items:
        item_id = item.get(id_key)
        if not item_id:
            # Skip invalid entries silently; schema validation should catch these elsewhere
            continue
        index[item_id] = item
    return index


def merge_configs_low_to_high(configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple config dicts from low to high precedence.

    - Servers: override entire server entry by id from later (higher precedence) configs
    - Inputs: override entire input entry by id from later (higher precedence) configs
    - Version: must match across configs if present; otherwise take from highest-precedence config
    """
    if not configs:
        return {"version": "1.0", "servers": []}

    version: Optional[str] = None
    servers_index: Dict[str, Dict[str, Any]] = {}
    inputs_index: Dict[str, Dict[str, Any]] = {}

    for cfg in configs:
        cfg_version = cfg.get("version")
        if cfg_version:
            if version is None:
                version = cfg_version
            elif version != cfg_version:
                raise ValueError(f"Version mismatch during merge: {version} vs {cfg_version}")

        for sid, server in _index_by_id(cfg.get("servers", [])).items():
            servers_index[sid] = server

        for iid, input_item in _index_by_id(cfg.get("inputs", [])).items():
            inputs_index[iid] = input_item

    merged: Dict[str, Any] = {
        "version": version or "1.0",
        "servers": list(servers_index.values()),
    }
    if inputs_index:
        merged["inputs"] = list(inputs_index.values())
    return merged


def discover_and_merge(context: Optional[DiscoveryContext] = None) -> Dict[str, Any]:
    """Discover layered configs (system -> user -> env -> project) and merge them."""
    layered_paths = discover_layered_paths(context)
    configs: List[Dict[str, Any]] = []
    for _, path in layered_paths:
        configs.append(load_config(str(path)))
    return merge_configs_low_to_high(configs)
