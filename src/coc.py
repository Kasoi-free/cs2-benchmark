import json
import re
from typing import Any


def read_coc(path: str | Any) -> dict[str, Any]:
    """Parse a .coc file into a dict of section_name -> parsed JSON."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    sections: dict[str, Any] = {}
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if (
            line
            and not line.startswith("{")
            and not line.startswith("}")
            and not line.startswith('"')
            and not line.startswith("]")
        ):
            section_name = line
            json_lines: list[str] = []
            i += 1
            brace_depth = 0
            started = False
            while i < len(lines):
                cl = lines[i]
                brace_depth += cl.count("{") - cl.count("}")
                if "{" in cl:
                    started = True
                if started:
                    json_lines.append(cl)
                if started and brace_depth <= 0:
                    i += 1
                    break
                i += 1
            json_str = "\n".join(json_lines)
            json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
            try:
                sections[section_name] = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"  Warning: Failed to parse section '{section_name}': {e}")
            continue
        i += 1
    return sections


def write_coc(path: str | Any, sections: dict[str, Any]) -> None:
    """Write a dict of sections back to a .coc file."""
    with open(path, "w", encoding="utf-8") as f:
        for name, data in sections.items():
            f.write(f"{name}\n")
            f.write(json.dumps(data, indent=4, ensure_ascii=False))
            f.write("\n")


def get_quality_settings(sections: dict[str, Any]) -> list:
    """Extract the qualitySettings array from the Graphics Settings section."""
    gs = sections.get("Graphics Settings", {})
    return gs.get("qualitySettings", [])
