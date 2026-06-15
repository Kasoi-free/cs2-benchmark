"""Plain-text report generation."""
from pathlib import Path
from typing import Any

from .utils import get_fps


def create_txt(results: dict[str, Any], base_fps: float, output_path: Path, settings_list: list[dict]) -> None:
    """Generate a plain-text summary of benchmark results."""
    lines: list[str] = []
    lines.append(f"Baseline result: {int(base_fps)} FPS")
    lines.append("")

    for sd in settings_list:
        name = sd["name"]
        labels = sd["labels"]
        col_order = sd.get("col_order", ["HIGH", "MEDIUM", "LOW"])
        fps_data = results.get(name, {})

        worst_fps: float | None = None
        for v in col_order:
            d = fps_data.get(v)
            f = get_fps(d)
            if f > 0:
                if worst_fps is None or f < worst_fps:
                    worst_fps = f

        for i, variant in enumerate(col_order):
            d = fps_data.get(variant)
            fps = get_fps(d)
            label = labels[i] if i < len(labels) else variant
            if fps <= 0:
                continue
            line = f"{name} {label}: {int(fps)} FPS"
            if i == 0 and worst_fps and base_fps > 0:
                reduction = (base_fps - worst_fps) / base_fps * 100
                line += f" ({reduction:.0f}% reduction)"
            lines.append(line)

        baseline_label = labels[-1] if labels else "BASELINE"
        lines.append(f"{name} {baseline_label}")
        lines.append("")

    max_data = results.get("Max quality", {}).get("HIGH")
    max_fps = get_fps(max_data)
    if max_fps > 0:
        max_reduction = (base_fps - max_fps) / base_fps * 100
        lines.append(f"Max quality: {int(max_fps)} FPS ({max_reduction:.0f}% reduction)")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  TXT written to {output_path}")
