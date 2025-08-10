from __future__ import annotations
import sys
from pathlib import Path

# Ensure the package in the src/ layout is importable during tests
root = Path(__file__).parents[1]
src_path = root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
