from __future__ import annotations

import argparse
import sys
from typing import Any

from code_generator import generate_lcd_code
from image_converter import convert_manifest_images
from lcd_db_loader import find_lcd_by_id, load_lcd_database
from report_generator import generate_reports
from resource_packer import pack_converted_images
from target_checker import (
    check_lcd_target_compatibility,
    find_target,
    load_target_profiles,
)
from utils import ToolError, project_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LCD resource tool MVP command line interface"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check", help="Check LCD compatibility with a target profile"
    )
    check_parser.add_argument("--target", required=True, help="Target name, e.g. esp32s3")
    check_parser.add_argument("--lcd-id", required=True, help="LCD variant id, e.g. 0x01")

    pack_parser = subparsers.add_parser(
        "pack", help="Convert image resources to intermediate RGB565 files"
    )
    pack_parser.add_argument("--target", required=True, help="Target name, e.g. esp32s3")

    build_parser = subparsers.add_parser(
        "build", help="Check LCD compatibility and generate LCD C files"
    )
    build_parser.add_argument("--target", required=True, help="Target name, e.g. esp32s3")
    build_parser.add_argument("--lcd-id", required=True, help="LCD variant id, e.g. 0x01")

    return parser


def load_lcd_and_target(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    root = project_root()
    lcds = load_lcd_database(root / "database" / "lcd_database.json")
    targets = load_target_profiles(root / "database" / "target_profiles.json")

    lcd = find_lcd_by_id(lcds, args.lcd_id)
    target = find_target(targets, args.target)
    errors = check_lcd_target_compatibility(lcd, target)
    if errors:
        raise ToolError("Compatibility check failed:\n" + "\n".join(f"- {e}" for e in errors))
    return lcd, target


def command_check(args: argparse.Namespace) -> int:
    lcd, target = load_lcd_and_target(args)

    print_lcd_summary(lcd, target)
    return 0


def pack_resources(target_name: str):
    root = project_root()
    converted = convert_manifest_images(
        root / "database" / "resource_manifest.json", root, target_name
    )
    packed = pack_converted_images(converted, root / "output" / target_name)
    return converted, packed


def command_pack(args: argparse.Namespace) -> int:
    converted, packed = pack_resources(args.target)

    print(f"Pack completed for target: {args.target}")
    for item in converted:
        print(
            f"- {item.resource_id}: {item.width}x{item.height}, "
            f"{item.format_name}, raw={item.raw_size} bytes, "
            f"out={item.output_size} bytes, file={item.output_path}"
        )
    print(f"res.bin: {packed.res_bin_path} ({packed.file_size} bytes)")
    print(f"resource_table.json: {packed.resource_table_path}")
    return 0


def command_build(args: argparse.Namespace) -> int:
    lcd, target = load_lcd_and_target(args)
    target_name = str(target["target"])
    converted, packed = pack_resources(target_name)
    generated = generate_lcd_code(lcd, project_root(), target_name)
    reports = generate_reports(lcd, target, packed, project_root() / "output" / target_name)

    print("Build completed")
    print(f"Target: {target['target']}")
    print(f"LCD ID: {lcd['variant_id']}")
    print(f"Resource count: {len(packed.entries)}")
    print(f"res.bin: {packed.res_bin_path} ({packed.file_size} bytes)")
    print(f"Header: {generated.header_path}")
    print(f"Source: {generated.source_path}")
    print(f"Memory report: {reports.memory_report_path}")
    print(f"Target report: {reports.target_report_path}")
    return 0


def print_lcd_summary(lcd: dict[str, Any], target: dict[str, Any]) -> None:
    print("Compatibility check passed")
    print(f"Target: {target['target']}")
    print(f"LCD ID: {lcd['variant_id']}")
    print(f"LCD PN: {lcd['lcd_pn']}")
    print(f"Vendor: {lcd['vendor_code']}")
    print(f"Driver IC: {lcd['driver_ic']}")
    print(f"Resolution: {lcd['h_res']}x{lcd['v_res']}")
    print(f"Interface: {lcd['interface']}")
    print(f"Color format: {lcd['color_format']}")
    print(f"RGB order: {lcd['rgb_order']}")
    print(f"Init sequence: {lcd['init_sequence']}")
    print(f"Status: {lcd['status']}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "check":
            return command_check(args)
        if args.command == "pack":
            return command_pack(args)
        if args.command == "build":
            return command_build(args)
        raise ToolError(f"Unsupported command: {args.command}")
    except ToolError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
