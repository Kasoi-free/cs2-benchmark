"""Main orchestration module — the benchmark loop."""
import sys
import time
from pathlib import Path

from .cli import load_config, parse_args, apply_args
from .coc import read_coc, write_coc, get_quality_settings, extract_game_version
from .launcher import (
    backup_settings,
    restore_settings,
    run_benchmark_test,
    kill_game,
)
from .ods import (
    init_ods,
    update_ods_baseline,
    update_ods_variant,
    update_ods_max_quality,
    write_ods,
)
from .paths import resolve_paths
from .settings import (
    apply_variant,
    disable_drs,
    set_all_baseline,
    set_all_max_quality,
)
from .text_report import create_txt
from .utils import generate_random_result, get_fps


def _print_header(dry_run: bool) -> None:
    print("=" * 60)
    print("CS2 Graphics Settings Benchmark Automation")
    if dry_run:
        print("MODE: DRY RUN (random results, no game launch)")
    print("=" * 60)


def _print_summary_table(results: dict, settings_list: list[dict], base_fps: float) -> None:
    print(f"\n{'Setting':<25} {'Variant':<12} {'FPS':>6} {'Drop':>8}")
    print("-" * 55)
    for sd in settings_list:
        name = sd["name"]
        col_order = sd.get("col_order", ["HIGH", "MEDIUM", "LOW"])
        fps_data = results.get(name, {})
        for variant in col_order:
            d = fps_data.get(variant)
            fps = get_fps(d)
            if fps > 0:
                drop = (1 - fps / base_fps) * 100
                print(f"{name:<25} {variant:<12} {fps:>6.1f} {drop:>7.2f}%")
        print()

    max_data = results.get("Max quality", {}).get("HIGH")
    max_fps = get_fps(max_data)
    if max_fps > 0:
        drop = (1 - max_fps / base_fps) * 100
        print(f"{'Max quality':<25} {'ALL':<12} {max_fps:>6.1f} {drop:>7.2f}%")


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    config = apply_args(config, args)

    settings_list = config["settings"]
    timeout = config.get("benchmark_timeout", 600)
    dry_run = args.dry_run

    # Resolve paths first to get Benchmark.coc location
    _sp, _bp, _, _ = resolve_paths(args.settings_path, args.benchmark_path, args.output_dir)
    version = "unknown"
    if _bp and Path(_bp).exists():
        version = extract_game_version(_bp)

    settings_path, benchmark_path, output_ods, output_txt = resolve_paths(
        args.settings_path, args.benchmark_path, args.output_dir, version,
    )

    _print_header(dry_run)

    if not settings_path:
        print("ERROR: Could not determine Settings.coc path.")
        print("  Set LOCALAPPDATA environment variable or place the script in the game directory.")
        sys.exit(1)
    if not settings_path.exists():
        print(f"ERROR: Settings.coc not found at {settings_path}")
        print("  Make sure Cities Skylines II has been launched at least once.")
        sys.exit(1)

    # Backup
    print("\n[0] Backing up Settings.coc...")
    backup = backup_settings(settings_path)

    # Read settings
    print("\n[0] Reading Settings.coc...")
    sections = read_coc(settings_path)
    qs_array = get_quality_settings(sections)

    if not qs_array:
        print("ERROR: Could not find qualitySettings in Graphics Settings")
        sys.exit(1)

    print(f"  Found {len(qs_array)} quality setting objects")

    total_tests = 1 + sum(len(sd.get("col_order", ["HIGH", "MEDIUM", "LOW"])) for sd in settings_list) + 1
    test_num = 0
    failed_tests: list[str] = []
    results: dict = {}
    baseline_data = None

    # Initialize ODS
    print("\n[0] Initializing ODS structure...")
    ods_state = init_ods(settings_list, output_ods)

    # --- BASELINE ---
    test_num += 1
    print(f"\n[{test_num}/{total_tests}] Running BASELINE (all lowest, DRS disabled)...")

    if dry_run:
        import random
        baseline_data = generate_random_result(110, impact_range=(0, 0))
        baseline_data["averageFps"] = round(random.uniform(105, 115), 1)
    else:
        set_all_baseline(qs_array, config)
        disable_drs(qs_array)
        gs = sections.get("Graphics Settings", {})
        gs["dlssQuality"] = "Off"
        write_coc(settings_path, sections)
        time.sleep(1)
        baseline_data = run_benchmark_test(config, benchmark_path, timeout, "BASELINE")

    if baseline_data is None:
        print("  ERROR: No benchmark result captured for BASELINE")
        print("  Attempting recovery...")
        kill_game()
        time.sleep(3)
        restore_settings(settings_path, backup)
        sys.exit(1)

    base_fps = baseline_data["averageFps"]
    baseline_data["testLabel"] = "BASELINE"
    print(
        f"  BASELINE FPS: {base_fps:.1f} | "
        f"gpuFps avg: {baseline_data['gpuFpsAvg']:.1f} "
        f"p95: {baseline_data['gpuFpsP95']:.1f} | "
        f"frames: {baseline_data['framesRendered']}"
    )

    update_ods_baseline(ods_state, baseline_data)
    write_ods(ods_state)

    # Impact ranges per variant position
    impact_ranges = {
        0: (-0.40, -0.02),
        1: (-0.20, -0.01),
        2: (-0.10, -0.005),
        3: (-0.05, -0.002),
    }

    # --- Individual setting variants ---
    for sd in settings_list:
        name = sd["name"]
        col_order = sd.get("col_order", ["HIGH", "MEDIUM", "LOW"])
        results[name] = {}

        for idx, variant in enumerate(col_order):
            test_num += 1
            print(f"\n[{test_num}/{total_tests}] Testing: {name} - {variant}")

            if dry_run:
                ir = impact_ranges.get(idx, (-0.15, -0.01))
                bench_data = generate_random_result(base_fps, impact_range=ir)
            else:
                set_all_baseline(qs_array, config)
                disable_drs(qs_array)
                apply_variant(qs_array, sd, variant)
                gs = sections.get("Graphics Settings", {})
                gs["dlssQuality"] = "Off"
                write_coc(settings_path, sections)
                time.sleep(1)
                bench_data = run_benchmark_test(config, benchmark_path, timeout, name, variant)

            if bench_data is None:
                print(f"  ERROR: No benchmark result for {name} {variant}")
                failed_tests.append(f"{name} {variant}")
                kill_game()
                time.sleep(3)
                continue

            bench_data["testLabel"] = variant
            results[name][variant] = bench_data
            print(
                f"  {name} {variant} FPS: {bench_data['averageFps']:.1f} | "
                f"gpuFps avg: {bench_data['gpuFpsAvg']:.1f} "
                f"p95: {bench_data['gpuFpsP95']:.1f} | "
                f"frames: {bench_data['framesRendered']}"
            )

            update_ods_variant(ods_state, name, variant, bench_data, baseline_data)
            write_ods(ods_state)

    # --- Max quality ---
    test_num += 1
    print(f"\n[{test_num}/{total_tests}] Testing: Max quality (all highest, TAA AA)...")

    if dry_run:
        max_data = generate_random_result(base_fps, impact_range=(-0.75, -0.55))
    else:
        set_all_max_quality(qs_array, config)
        disable_drs(qs_array)
        gs = sections.get("Graphics Settings", {})
        gs["dlssQuality"] = "Off"
        write_coc(settings_path, sections)
        time.sleep(1)
        max_data = run_benchmark_test(config, benchmark_path, timeout, "Max quality")

    if max_data is None:
        print("  ERROR: No benchmark result for Max quality")
        failed_tests.append("Max quality")
        kill_game()
        time.sleep(3)
    else:
        results["Max quality"] = {"HIGH": max_data}
        max_data["testLabel"] = "Max"
        print(
            f"  Max quality FPS: {max_data['averageFps']:.1f} | "
            f"gpuFps avg: {max_data['gpuFpsAvg']:.1f} "
            f"p95: {max_data['gpuFpsP95']:.1f} | "
            f"frames: {max_data['framesRendered']}"
        )
        update_ods_max_quality(ods_state, max_data, baseline_data)
        write_ods(ods_state)

    restore_settings(settings_path, backup)

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    if failed_tests:
        print(f"\nWARNING: {len(failed_tests)} test(s) failed:")
        for ft in failed_tests:
            print(f"  - {ft}")
        print("\nResults above do not include failed tests.")
    print(f"\nODS: {output_ods}")
    print(f"TXT: {output_txt}")
    print("=" * 60)

    create_txt(results, base_fps, output_txt, settings_list)
    _print_summary_table(results, settings_list, base_fps)
