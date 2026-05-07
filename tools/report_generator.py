from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from resource_packer import PackResult
from utils import ToolError


@dataclass(frozen=True)
class GeneratedReports:
    memory_report_path: Path
    target_report_path: Path


def generate_reports(
    lcd: dict[str, Any],
    target: dict[str, Any],
    pack_result: PackResult,
    output_dir: Path,
) -> GeneratedReports:
    output_dir.mkdir(parents=True, exist_ok=True)
    memory_report_path = output_dir / "memory_report.txt"
    target_report_path = output_dir / "target_report.txt"

    total_raw_size = sum(entry.raw_size for entry in pack_result.entries)
    total_packed_size = sum(entry.compressed_size for entry in pack_result.entries)
    compression_ratio = calculate_ratio(total_packed_size, total_raw_size)

    write_text(
        memory_report_path,
        render_memory_report(
            lcd=lcd,
            target=target,
            pack_result=pack_result,
            total_raw_size=total_raw_size,
            total_packed_size=total_packed_size,
            compression_ratio=compression_ratio,
        ),
    )
    write_text(
        target_report_path,
        render_target_report(
            lcd=lcd,
            target=target,
            pack_result=pack_result,
            total_raw_size=total_raw_size,
            total_packed_size=total_packed_size,
            compression_ratio=compression_ratio,
        ),
    )

    return GeneratedReports(
        memory_report_path=memory_report_path,
        target_report_path=target_report_path,
    )


def render_memory_report(
    lcd: dict[str, Any],
    target: dict[str, Any],
    pack_result: PackResult,
    total_raw_size: int,
    total_packed_size: int,
    compression_ratio: float,
) -> str:
    lines = [
        "LCD Resource Tool Memory Report",
        "================================",
        "",
        f"LCD PN: {lcd['lcd_pn']}",
        f"Vendor Code: {lcd['vendor_code']}",
        f"Driver IC: {lcd['driver_ic']}",
        f"Interface: {lcd['interface']}",
        f"Resolution: {lcd['h_res']}x{lcd['v_res']}",
        f"Color Format: {lcd['color_format']}",
        f"RGB Order: {lcd['rgb_order']}",
        "",
        f"Resource count: {len(pack_result.entries)}",
        f"Total raw size: {total_raw_size} bytes",
        f"Total packed size: {total_packed_size} bytes",
        f"Compression ratio: {compression_ratio:.2f}%",
        f"res.bin size: {pack_result.file_size} bytes",
        "",
        "Resources:",
    ]
    for entry in pack_result.entries:
        lines.append(
            f"- {entry.resource_id}: {entry.width}x{entry.height}, "
            f"{entry.format}, raw={entry.raw_size}, packed={entry.compressed_size}, "
            f"crc32=0x{entry.crc32:08X}"
        )
    lines.extend(
        [
            "",
            f"Target RAM: {target['ram_kb']} KB",
            f"Target Flash: {target['flash_kb']} KB",
            f"Target PSRAM: {bool_text(target['psram'])}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_target_report(
    lcd: dict[str, Any],
    target: dict[str, Any],
    pack_result: PackResult,
    total_raw_size: int,
    total_packed_size: int,
    compression_ratio: float,
) -> str:
    return "\n".join(
        [
            "LCD Resource Tool Target Report",
            "===============================",
            "",
            f"Target: {target['target']}",
            f"Target RAM/Flash: {target['ram_kb']} KB RAM / {target['flash_kb']} KB Flash",
            f"Target PSRAM: {bool_text(target['psram'])}",
            f"Target LCD Bus: {', '.join(str(item) for item in target['lcd_bus'])}",
            f"Target Color Formats: {', '.join(str(item) for item in target['color_formats'])}",
            "",
            f"LCD PN: {lcd['lcd_pn']}",
            f"Vendor Code: {lcd['vendor_code']}",
            f"Driver IC: {lcd['driver_ic']}",
            f"Interface: {lcd['interface']}",
            f"Resolution: {lcd['h_res']}x{lcd['v_res']}",
            f"Color Format: {lcd['color_format']}",
            f"RGB Order: {lcd['rgb_order']}",
            f"Init Sequence: {lcd['init_sequence']}",
            "",
            "Compatibility: passed",
            f"Resource count: {len(pack_result.entries)}",
            f"Total raw size: {total_raw_size} bytes",
            f"Total packed size: {total_packed_size} bytes",
            f"Compression ratio: {compression_ratio:.2f}%",
            f"res.bin: {pack_result.res_bin_path}",
            f"resource_table.json: {pack_result.resource_table_path}",
            "",
        ]
    )


def calculate_ratio(total_packed_size: int, total_raw_size: int) -> float:
    if total_raw_size == 0:
        return 0.0
    return (total_packed_size / total_raw_size) * 100.0


def bool_text(value: Any) -> str:
    return "yes" if bool(value) else "no"


def write_text(path: Path, content: str) -> None:
    try:
        path.write_text(content, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise ToolError(f"Failed to write report file {path}: {exc}") from exc
