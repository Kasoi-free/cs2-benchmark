import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .coc import read_coc


def backup_settings(settings_path: Path) -> Path:
    """Create a backup of Settings.coc."""
    import shutil

    backup = settings_path.with_suffix(".coc.bak")
    shutil.copy2(settings_path, backup)
    print(f"  Backed up Settings.coc -> {backup}")
    return backup


def restore_settings(settings_path: Path, backup: Path) -> None:
    """Restore Settings.coc from backup."""
    import shutil

    shutil.copy2(backup, settings_path)
    print(f"  Restored Settings.coc from backup")


def launch_benchmark(config: dict, benchmark_path: Path) -> None:
    """Launch the game benchmark."""
    if benchmark_path.exists():
        benchmark_path.unlink()
    method = config.get("launch_method", "steam")
    if method == "direct":
        exe = config.get("game_exe")
        if not exe:
            print("ERROR: 'game_exe' not set in config for direct launch")
            sys.exit(1)
        print(f"  Launching directly: {exe} -benchmark")
        subprocess.Popen(f'start "" "{exe}" -benchmark', shell=True)
    else:
        app_id = config.get("steam_app_id", "949230")
        print(f"  Launching via Steam (AppID: {app_id})...")
        subprocess.Popen(f'start steam://launch/{app_id}/dialog', shell=True)
    time.sleep(5)


def wait_for_benchmark(benchmark_path: Path, timeout: int = 600) -> dict | None:
    """Poll Benchmark.coc until FPS data is available or timeout."""
    print("  Polling Benchmark.coc for results...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            if not benchmark_path.exists():
                time.sleep(2)
                continue
            data = read_coc(benchmark_path)
            for section_data in data.values():
                if isinstance(section_data, dict):
                    latest = section_data.get("latestResult", {})
                    if isinstance(latest, dict):
                        fps = latest.get("averageFps")
                        if fps is not None and float(fps) > 0:
                            gpu_fps = latest.get("gpuFps", {})
                            return {
                                "averageFps": float(fps),
                                "framesRendered": latest.get("framesRendered", 0),
                                "gpuFpsAvg": gpu_fps.get("average", 0) if isinstance(gpu_fps, dict) else 0,
                                "gpuFpsP95": gpu_fps.get("p95", 0) if isinstance(gpu_fps, dict) else 0,
                                "cpuGameFrameTimes": latest.get("cpuGameFrameTimes", []),
                                "gpuFrameTimes": latest.get("gpuFrameTimes", []),
                            }
        except Exception:
            pass
        time.sleep(2)
    return None


def kill_game() -> None:
    """Force-kill the game process."""
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "Cities2.exe"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = result.stdout.strip() or result.stderr.strip()
        print(f"  Killed Cities2.exe: {out}")
    except Exception as e:
        print(f"  Warning killing process: {e}")


def run_benchmark_test(
    config: dict,
    benchmark_path: Path,
    timeout: int,
    name: str = "",
    variant: str | None = None,
) -> dict | None:
    """Run a single benchmark test: launch, wait, kill. Returns result dict or None."""
    launch_benchmark(config, benchmark_path)
    data = wait_for_benchmark(benchmark_path, timeout=timeout)
    kill_game()
    time.sleep(3)
    return data
