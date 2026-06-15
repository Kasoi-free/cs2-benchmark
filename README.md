# CS2 Graphics Benchmark Automation

Automated benchmarking tool for Cities: Skylines II. Tests individual graphics settings across quality variants, captures FPS metrics, and generates ODS spreadsheet reports with full frame time data.

## Requirements

- Windows 10/11
- Python 3.8+
- Cities: Skylines II (Steam AppID: 949230)
- Game must have been launched at least once to generate `Settings.coc`

## Files

| File / Directory | Purpose |
|------------------|---------|
| `benchmark_automation.py` | Thin entry point |
| `src/` | Application modules |
| `src/main.py` | Benchmark loop orchestration |
| `src/cli.py` | CLI parsing, config loading |
| `src/paths.py` | Path resolution |
| `src/coc.py` | `.coc` file parser |
| `src/settings.py` | Quality setting manipulation |
| `src/launcher.py` | Game launch, poll, kill, backup |
| `src/ods.py` | ODS spreadsheet generation |
| `src/text_report.py` | Plain-text report generation |
| `src/utils.py` | Helpers (random results, FPS extraction) |
| `config.json` | All settings, variants, and configuration |
| `styles_template.xml` | ODS styles template |
| `manifest_template.xml` | ODS manifest template |
| `meta_template.xml` | ODS metadata template |

## Quick Start

```bash
python benchmark_automation.py
```

This runs the full benchmark cycle using default settings (Steam launch, all 12 settings tested).

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config <path>` | Path to `config.json` | Same directory as script |
| `--launch-method steam\|direct` | How to launch the benchmark | `steam` (from config) |
| `--settings-path <path>` | Override `Settings.coc` location | Auto-detected from `LOCALAPPDATA` |
| `--benchmark-path <path>` | Override `Benchmark.coc` location | Auto-detected from `LOCALAPPDATA` |
| `--output-dir <path>` | Output directory for results | Same directory as script |
| `--timeout <seconds>` | Max wait time per benchmark | `600` (from config) |
| `--dry-run` | Generate random results without launching the game | Off |

### Launch Methods

- **`steam`** — Launches via `steam://launch/949230/dialog` (default)
- **`direct`** — Runs `Cities2.exe -benchmark` directly (set `game_exe` in config)

## How It Works

1. Backs up `Settings.coc`
2. Runs **baseline** (all settings at lowest/disabled, DRS off)
3. For each of 12 settings, tests each quality variant against baseline
4. Runs **max quality** (all settings at highest, TAA AA)
5. Restores original `Settings.coc`

Each test: modifies config → deletes `Benchmark.coc` → launches game → polls for results → kills game.

## Output

- `benchmark_results.ods` — LibreOffice spreadsheet with summary sheet, per-setting sheets, full frame time data, and conditional formatting
- `benchmark_results.txt` — Plain text summary with FPS and reduction percentages

## Config File

`config.json` contains:

- **`benchmark_timeout`** — Max seconds to wait per benchmark run
- **`launch_method`** — `"steam"` or `"direct"`
- **`game_exe`** — Full path to `Cities2.exe` (required for `direct` launch)
- **`steam_app_id`** — Steam AppID (949230)
- **`settings`** — Array of 12 setting definitions, each with:
  - `name` — Display name
  - `type` — JSON `@type` suffix to match in `Settings.coc`
  - `variants` — Quality levels (`HIGH`, `MEDIUM`, `LOW`, etc.) with property values
  - `baseline` — Values to apply when this setting is at baseline
  - `labels` — Display labels for each variant + baseline
  - `col_order` — Order of variants in output
  - `requires_fog` — Auto-enables Fog when testing this setting
  - `custom_pct_col` — Adds extra percentage column (used by Anti-Aliasing)
- **`non_tested_defaults`** — Settings not benchmarked but preserved (MotionBlur, Texture)
- **`recommended_values`** — Values for the "recommended settings" final test

## Paths

The script auto-detects paths from the `LOCALAPPDATA` environment variable:

```
%LOCALAPPDATA%\Colossal Order\Cities Skylines II\Settings.coc
%LOCALAPPDATA%\Colossal Order\Cities Skylines II\Benchmark.coc
```

Override with `--settings-path` and `--benchmark-path` if needed.

## Settings Tested

| Setting | Variants |
|---------|----------|
| Depth of Field | HIGH, MEDIUM, LOW |
| Global Illumination | HIGH, MEDIUM, LOW |
| Ambient Occlusion | HIGH, MEDIUM, LOW |
| Anti-Aliasing | SMAA High, SMAA Low, FXAA, Custom (TAA) |
| Clouds | HIGH, MEDIUM, LOW, VERY LOW |
| Fog | ENABLED |
| Volumetrics | HIGH, MEDIUM, LOW |
| Reflections | HIGH, MEDIUM, LOW |
| Shadow | HIGH, MEDIUM, LOW |
| Terrain | HIGH, MEDIUM, LOW |
| Water | HIGH, MEDIUM, LOW |
| Level of Detail | HIGH, MEDIUM, LOW, VERY LOW |

DRS and DLSS are disabled for all tests.

## Notes

- Game is forcefully terminated (`taskkill`) after each benchmark
- Original settings are always restored on completion
- Failed tests are tracked and reported at the end
- Full frame time data is stored in the ODS (no downsample). Dry-run uses 800 points.
