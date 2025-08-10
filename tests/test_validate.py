from __future__ import annotations
import json
from pathlib import Path

import yaml  # type: ignore
from jsonschema import validate


def test_example_validates_against_schema():
    schema = json.load(open(str(Path(__file__).parents[1] / "mcp-servers.schema.json")))
    cfg = yaml.safe_load(open(str(Path(__file__).parents[1] / "examples" / "mcp-servers.example.yaml")))
    validate(instance=cfg, schema=schema)
