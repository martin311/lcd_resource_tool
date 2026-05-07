from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils import ToolError, load_json, require_dict, require_list_field


@dataclass(frozen=True)
class GeneratedCode:
    header_path: Path
    source_path: Path


def generate_lcd_code(lcd: dict[str, Any], project_root: Path, target: str) -> GeneratedCode:
    init_path = project_root / "init_sequences" / str(lcd["init_sequence"])
    init_data = load_init_sequence(init_path)
    if init_data["driver_ic"] != lcd["driver_ic"]:
        raise ToolError(
            f"Init sequence driver_ic '{init_data['driver_ic']}' does not match "
            f"LCD driver_ic '{lcd['driver_ic']}' for {init_path}"
        )

    output_dir = project_root / "output" / target
    output_dir.mkdir(parents=True, exist_ok=True)

    header_path = output_dir / "lcd_config_generated.h"
    source_path = output_dir / "lcd_init_generated.c"

    write_text(header_path, render_lcd_config_header(lcd))
    write_text(source_path, render_lcd_init_source(init_data))

    return GeneratedCode(header_path=header_path, source_path=source_path)


def load_init_sequence(path: Path) -> dict[str, Any]:
    data = require_dict(load_json(path), path)
    driver_ic = data.get("driver_ic")
    if not isinstance(driver_ic, str) or not driver_ic:
        raise ToolError(f"Expected string field 'driver_ic' in {path}")

    sequence = require_list_field(data, "sequence", path)
    data["_source_file"] = path.name
    for index, item in enumerate(sequence):
        if not isinstance(item, dict):
            raise ToolError(f"Init sequence item #{index} in {path} must be an object")
        require_u8_string(item, "cmd", index, path)
        data_items = item.get("data")
        if not isinstance(data_items, list):
            raise ToolError(f"Init sequence item #{index} in {path} needs list field 'data'")
        for data_index, value in enumerate(data_items):
            parse_u8(value, f"data[{data_index}]", index, path)
        delay_ms = item.get("delay_ms")
        if not isinstance(delay_ms, int) or delay_ms < 0 or delay_ms > 0xFFFF:
            raise ToolError(
                f"Init sequence item #{index} in {path} needs uint16 field 'delay_ms'"
            )
    return data


def render_lcd_config_header(lcd: dict[str, Any]) -> str:
    return f"""/* AUTO-GENERATED FILE. DO NOT EDIT.
 * Generated from database/lcd_database.json.
 */

#ifndef LCD_CONFIG_GENERATED_H
#define LCD_CONFIG_GENERATED_H

#define LCD_VARIANT_ID \"{c_string(str(lcd["variant_id"]))}\"
#define LCD_PART_NUMBER \"{c_string(str(lcd["lcd_pn"]))}\"
#define LCD_VENDOR_CODE \"{c_string(str(lcd["vendor_code"]))}\"
#define LCD_DRIVER_IC \"{c_string(str(lcd["driver_ic"]))}\"
#define LCD_INTERFACE \"{c_string(str(lcd["interface"]))}\"

#define LCD_H_RES {int(lcd["h_res"])}
#define LCD_V_RES {int(lcd["v_res"])}
#define LCD_COLOR_FORMAT \"{c_string(str(lcd["color_format"]))}\"
#define LCD_RGB_ORDER \"{c_string(str(lcd["rgb_order"]))}\"

#define LCD_MIRROR_X {c_bool(lcd["mirror_x"])}
#define LCD_MIRROR_Y {c_bool(lcd["mirror_y"])}
#define LCD_SWAP_XY {c_bool(lcd["swap_xy"])}
#define LCD_INVERT_COLOR {c_bool(lcd["invert_color"])}

#define LCD_X_GAP {int(lcd["x_gap"])}
#define LCD_Y_GAP {int(lcd["y_gap"])}

#endif /* LCD_CONFIG_GENERATED_H */
"""


def render_lcd_init_source(init_data: dict[str, Any]) -> str:
    sequence = init_data["sequence"]
    data_arrays: list[str] = []
    table_rows: list[str] = []

    for index, item in enumerate(sequence):
        source_path = Path(str(init_data.get("_source_file", "init_sequence.json")))
        cmd = parse_u8(item["cmd"], "cmd", index, source_path)
        data_values = [
            parse_u8(value, f"data[{data_index}]", index, source_path)
            for data_index, value in enumerate(item["data"])
        ]
        delay_ms = int(item["delay_ms"])

        if data_values:
            array_name = f"lcd_init_data_{index}"
            data_literal = ", ".join(to_hex_u8(value) for value in data_values)
            data_arrays.append(f"static const uint8_t {array_name}[] = {{{data_literal}}};")
            data_ref = array_name
        else:
            data_ref = "NULL"

        table_rows.append(
            f"    {{{to_hex_u8(cmd)}, {data_ref}, {len(data_values)}, {delay_ms}}},"
        )

    arrays_text = "\n".join(data_arrays)
    if arrays_text:
        arrays_text += "\n\n"
    rows_text = "\n".join(table_rows)

    return f"""/* AUTO-GENERATED FILE. DO NOT EDIT.
 * Generated from init_sequences/{c_string(str(init_data["_source_file"]))}.
 */

#include \"lcd_config_generated.h\"

#include <stddef.h>
#include <stdint.h>

typedef struct {{
    uint8_t cmd;
    const uint8_t *data;
    uint8_t data_len;
    uint16_t delay_ms;
}} lcd_init_cmd_t;

{arrays_text}const lcd_init_cmd_t lcd_init_sequence[] = {{
{rows_text}
}};

const uint32_t lcd_init_sequence_count =
    (uint32_t)(sizeof(lcd_init_sequence) / sizeof(lcd_init_sequence[0]));
"""


def write_text(path: Path, content: str) -> None:
    try:
        path.write_text(content, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise ToolError(f"Failed to write generated code file {path}: {exc}") from exc


def c_bool(value: Any) -> int:
    if not isinstance(value, bool):
        raise ToolError(f"Expected boolean LCD config value, got {value!r}")
    return 1 if value else 0


def c_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def require_u8_string(item: dict[str, Any], field: str, index: int, path: Path) -> int:
    return parse_u8(item.get(field), field, index, path)


def parse_u8(value: Any, field: str, index: int, path: Path) -> int:
    if not isinstance(value, str):
        raise ToolError(f"Init item #{index} field '{field}' in {path} must be a string")
    try:
        parsed = int(value, 0)
    except ValueError as exc:
        raise ToolError(
            f"Init item #{index} field '{field}' in {path} is not an integer: {value}"
        ) from exc
    if parsed < 0 or parsed > 0xFF:
        raise ToolError(f"Init item #{index} field '{field}' in {path} must fit uint8")
    return parsed


def to_hex_u8(value: int) -> str:
    return f"0x{value:02X}"
