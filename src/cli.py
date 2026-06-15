import argparse
import json
import sys
from pathlib import Path

from .paths import SCRIPT_DIR


def load_config(config_path: Path | None = None) -> dict:
    """Load configuration from config.json."""
    if config_path is None:
        config_path = SCRIPT_DIR / "config.json"
    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CS2 Graphics Benchmark Automation")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.json")
    parser.add_argument("--settings-path", type=Path, default=None, help="Override Settings.coc path")
    parser.add_argument("--benchmark-path", type=Path, default=None, help="Override Benchmark.coc path")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory for results")
    parser.add_argument("--launch-method", choices=["steam", "direct"], default=None, help="How to launch the benchmark")
    parser.add_argument("--timeout", type=int, default=None, help="Benchmark timeout in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Generate random results without launching the game")
    return parser.parse_args()


def apply_args(config: dict, args: argparse.Namespace) -> dict:
    """Apply CLI overrides to config."""
    if args.launch_method:
        config["launch_method"] = args.launch_method
    if args.timeout:
        config["benchmark_timeout"] = args.timeout
    return config
