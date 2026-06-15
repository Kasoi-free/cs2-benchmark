import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
LOCALAPPDATA_LOW = os.path.join(LOCALAPPDATA, "..", "LocalLow") if LOCALAPPDATA else ""
DATA_DIR = Path(LOCALAPPDATA_LOW) / "Colossal Order" / "Cities Skylines II" if LOCALAPPDATA_LOW else None


def resolve_paths(
    settings_override: Path | None = None,
    benchmark_override: Path | None = None,
    output_dir: Path | None = None,
):
    """Return resolved paths, respecting CLI overrides."""
    settings_path = settings_override or (DATA_DIR / "Settings.coc" if DATA_DIR else None)
    benchmark_path = benchmark_override or (DATA_DIR / "Benchmark.coc" if DATA_DIR else None)
    output_ods = (output_dir or SCRIPT_DIR) / "benchmark_results.ods"
    output_txt = (output_dir or SCRIPT_DIR) / "benchmark_results.txt"
    return settings_path, benchmark_path, output_ods, output_txt
