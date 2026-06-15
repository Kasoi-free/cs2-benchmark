from typing import Any


def _find_setting_obj(qs_array: list, type_suffix: str) -> dict | None:
    """Find a quality setting object by its @type suffix."""
    for obj in qs_array:
        if isinstance(obj, dict):
            atype = obj.get("@type", "")
            if atype.endswith(type_suffix):
                return obj
    return None


def apply_variant(qs_array: list, setting_def: dict, variant_name: str) -> None:
    """Apply a specific variant's values to the matching setting object."""
    obj = _find_setting_obj(qs_array, setting_def["type"])
    if obj and variant_name in setting_def["variants"]:
        variant = setting_def["variants"][variant_name]
        for k, v in variant.items():
            obj[k] = v
    if setting_def.get("requires_fog"):
        fog_obj = _find_setting_obj(qs_array, "FogQualitySettings")
        if fog_obj:
            fog_obj["enabled"] = True


def apply_baseline(qs_array: list, setting_def: dict) -> None:
    """Apply baseline values to the matching setting object."""
    obj = _find_setting_obj(qs_array, setting_def["type"])
    if obj and "baseline" in setting_def:
        for k, v in setting_def["baseline"].items():
            obj[k] = v


def disable_drs(qs_array: list) -> None:
    """Disable Dynamic Resolution Scaling."""
    for obj in qs_array:
        if isinstance(obj, dict) and "DynamicResolutionScaleSettings" in obj.get("@type", ""):
            obj["enabled"] = False


def _apply_all_settings(
    qs_array: list,
    settings_list: list[dict],
    value_map: dict[str, dict],
    non_tested: dict[str, dict],
) -> None:
    """Generic helper to apply values to all quality settings.

    Args:
        qs_array: List of quality setting objects from Settings.coc
        settings_list: List of setting definitions from config
        value_map: Dict of type_suffix -> values to apply (for max quality or similar)
        non_tested: Dict of type_suffix -> default values for non-tested settings
    """
    for obj in qs_array:
        if not isinstance(obj, dict) or "@type" not in obj:
            continue
        atype = obj.get("@type", "")
        if "DynamicResolutionScaleSettings" in atype:
            obj["enabled"] = False
            continue
        matched = False
        for type_suffix, vals in value_map.items():
            if atype.endswith(type_suffix):
                for k, v in vals.items():
                    obj[k] = v
                matched = True
                break
        if not matched:
            for type_suffix, vals in non_tested.items():
                if atype.endswith(type_suffix):
                    for k, v in vals.items():
                        obj[k] = v
                    break


def set_all_baseline(qs_array: list, config: dict) -> None:
    """Set all settings to their baseline values."""
    settings_list = config["settings"]
    non_tested = config.get("non_tested_defaults", {})
    value_map = {sd["type"]: sd["baseline"] for sd in settings_list if "baseline" in sd}
    _apply_all_settings(qs_array, settings_list, value_map, non_tested)


def set_all_max_quality(qs_array: list, config: dict) -> None:
    """Set all settings to their maximum quality values."""
    max_values = config.get("max_quality_values", {})
    non_tested = config.get("non_tested_defaults", {})
    _apply_all_settings(qs_array, config["settings"], max_values, non_tested)
