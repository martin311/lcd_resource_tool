from __future__ import annotations

from pathlib import Path
from typing import Any

from utils import ToolError, load_json, require_dict, require_list_field


REQUIRED_TARGET_FIELDS = {
    "target",
    "lcd_bus",
    "color_formats",
    "image_formats",
    "ram_kb",
    "flash_kb",
    "psram",
    "lvgl",
}


def load_target_profiles(path: Path) -> list[dict[str, Any]]:
    data = require_dict(load_json(path), path)
    targets = require_list_field(data, "targets", path)

    profiles: list[dict[str, Any]] = []
    for index, item in enumerate(targets):
        if not isinstance(item, dict):
            raise ToolError(f"Target profile #{index} in {path} must be an object")
        missing = sorted(REQUIRED_TARGET_FIELDS - item.keys())
        if missing:
            raise ToolError(
                f"Target profile #{index} in {path} is missing fields: {', '.join(missing)}"
            )
        profiles.append(item)

    return profiles


def find_target(profiles: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    for profile in profiles:
        if profile["target"] == target_name:
            return profile
    raise ToolError(f"Target profile not found: {target_name}")


def check_lcd_target_compatibility(
    lcd: dict[str, Any], target: dict[str, Any]
) -> list[str]:
    errors: list[str] = []

    target_name = str(target["target"])
    supported_targets = lcd["supported_targets"]
    if not isinstance(supported_targets, list) or target_name not in supported_targets:
        errors.append(
            f"LCD {lcd['variant_id']} does not list target '{target_name}' in supported_targets"
        )

    lcd_bus = target["lcd_bus"]
    if not isinstance(lcd_bus, list) or lcd["interface"] not in lcd_bus:
        errors.append(
            f"Target '{target_name}' does not support LCD interface '{lcd['interface']}'"
        )

    color_formats = target["color_formats"]
    if not isinstance(color_formats, list) or lcd["color_format"] not in color_formats:
        errors.append(
            f"Target '{target_name}' does not support color format '{lcd['color_format']}'"
        )

    return errors
