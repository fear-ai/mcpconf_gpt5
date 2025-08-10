from __future__ import annotations
import argparse
import json
import sys
from .convert import load_config, to_mcpServers_json, to_github_servers_json, to_claude_cli


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        import jsonschema  # type: ignore
        import yaml  # type: ignore
    except Exception:  # pragma: no cover
        print("Install extras: PyYAML and jsonschema", file=sys.stderr)
        return 2
    cfg = load_config(args.config)
    schema = json.load(open(args.schema, "r", encoding="utf-8"))
    jsonschema.validate(instance=cfg, schema=schema)
    print("OK")
    return 0


def cmd_convert(args: argparse.Namespace) -> int:
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
        print("Unsupported target", file=sys.stderr)
        return 2
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="mcpconf", description="MCP server configuration toolkit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate a config against the schema")
    p_val.add_argument("config")
    p_val.add_argument("--schema", default="mcp-servers.schema.json")
    p_val.set_defaults(func=cmd_validate)

    p_conv = sub.add_parser("convert", help="Convert a config to a target output format")
    p_conv.add_argument("config")
    p_conv.add_argument("--to", required=True, choices=["mcpServers-json", "github-servers-json", "claude-cli"]) 
    p_conv.set_defaults(func=cmd_convert)

    args = parser.parse_args()
    raise SystemExit(args.func(args))
