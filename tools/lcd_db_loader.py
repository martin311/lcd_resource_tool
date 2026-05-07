from __future__ import annotations

from pathlib import Path
from typing import Any

from utils import ToolError, load_json, require_dict, require_list_field


REQUIRED_LCD_FIELDS = {
    "variant_id",
    "lcd_pn",
    "vendor_code",
    "driver_ic",
    "interface",
    "hw_id",
    "h_res",
    "v_res",
    "color_format",
    "rgb_order",
    "mirror_x",
    "mirror_y",
    "swap_xy",
    "invert_color",
    "x_gap",
    "y_gap",
    "init_sequence",
    "supported_targets",
    "status",
}


def load_lcd_database(path: Path) -> list[dict[str, Any]]:
    data = require_dict(load_json(path), path)
    lcds = require_list_field(data, "lcds", path)

    records: list[dict[str, Any]] = []
    for index, item in enumerate(lcds):
        if not isinstance(item, dict):
            raise ToolError(f"LCD record #{index} in {path} must be an object")
        missing = sorted(REQUIRED_LCD_FIELDS - item.keys())
        if missing:
            raise ToolError(
                f"LCD record #{index} in {path} is missing fields: {', '.join(missing)}"
            )
        records.append(item)

    return records


def find_lcd_by_id(lcds: list[dict[str, Any]], lcd_id: str) -> dict[str, Any]:
    normalized_id = normalize_lcd_id(lcd_id)
    for lcd in lcds:
        if normalize_lcd_id(str(lcd["variant_id"])) == normalized_id:
            return lcd
    raise ToolError(f"LCD id not found: {lcd_id}")


def normalize_lcd_id(lcd_id: str) -> str:
    try:
        return f"0x{int(lcd_id, 0):02X}"
    except ValueError as exc:
        raise ToolError(f"Invalid LCD id '{lcd_id}', expected integer like 0x01") from exc
