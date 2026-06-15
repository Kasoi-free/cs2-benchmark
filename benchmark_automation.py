#!/usr/bin/env python3
"""CS2 Graphics Benchmark Automation — entry point."""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `src` package is importable
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import main  # noqa: E402


if __name__ == "__main__":
    main()
