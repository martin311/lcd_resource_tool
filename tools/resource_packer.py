from __future__ import annotations

import json
import struct
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path

from image_converter import ConvertedImage
from utils import ToolError


MAGIC = b"LRES"
VERSION = 1
HEADER_STRUCT = struct.Struct("<4sIIIII")
ENTRY_STRUCT = struct.Struct("<IHHHHIIII")

RESOURCE_TYPE_IMAGE = 1
FORMAT_RAW_RGB565 = 1
FORMAT_RGB565_RLE = 2


@dataclass(frozen=True)
class PackedResource:
    resource_id: str
    resource_id_hash: int
    type: str
    type_code: int
    format: str
    format_code: int
    width: int
    height: int
    offset: int
    compressed_size: int
    raw_size: int
    crc32: int
    source_path: str
    intermediate_path: str


@dataclass(frozen=True)
class PackResult:
    res_bin_path: Path
    resource_table_path: Path
    file_size: int
    entries: list[PackedResource]


def pack_converted_images(converted_images: list[ConvertedImage], output_dir: Path) -> PackResult:
    if not converted_images:
        raise ToolError("No converted images to pack")

    output_dir.mkdir(parents=True, exist_ok=True)
    index_offset = HEADER_STRUCT.size
    data_offset = index_offset + ENTRY_STRUCT.size * len(converted_images)

    data_blobs: list[bytes] = []
    entries: list[PackedResource] = []
    current_offset = data_offset

    for image in converted_images:
        blob = read_intermediate_file(image.output_path)
        format_code = format_name_to_code(image.format_name)
        resource_hash = zlib.crc32(image.resource_id.encode("utf-8")) & 0xFFFFFFFF
        crc = zlib.crc32(blob) & 0xFFFFFFFF

        entries.append(
            PackedResource(
                resource_id=image.resource_id,
                resource_id_hash=resource_hash,
                type="image",
                type_code=RESOURCE_TYPE_IMAGE,
                format=image.format_name,
                format_code=format_code,
                width=image.width,
                height=image.height,
                offset=current_offset,
                compressed_size=len(blob),
                raw_size=image.raw_size,
                crc32=crc,
                source_path=str(image.source_path),
                intermediate_path=str(image.output_path),
            )
        )
        data_blobs.append(blob)
        current_offset += len(blob)

    file_size = current_offset
    res_bin = build_res_bin(entries, data_blobs, index_offset, data_offset, file_size)
    res_bin_path = output_dir / "res.bin"
    table_path = output_dir / "resource_table.json"

    write_bytes(res_bin_path, res_bin)
    write_resource_table(table_path, entries, index_offset, data_offset, file_size)

    return PackResult(
        res_bin_path=res_bin_path,
        resource_table_path=table_path,
        file_size=file_size,
        entries=entries,
    )


def build_res_bin(
    entries: list[PackedResource],
    data_blobs: list[bytes],
    index_offset: int,
    data_offset: int,
    file_size: int,
) -> bytes:
    output = bytearray()
    output.extend(
        HEADER_STRUCT.pack(MAGIC, VERSION, len(entries), index_offset, data_offset, file_size)
    )

    for entry in entries:
        output.extend(
            ENTRY_STRUCT.pack(
                entry.resource_id_hash,
                entry.type_code,
                entry.format_code,
                entry.width,
                entry.height,
                entry.offset,
                entry.compressed_size,
                entry.raw_size,
                entry.crc32,
            )
        )

    for blob in data_blobs:
        output.extend(blob)

    return bytes(output)


def write_resource_table(
    path: Path,
    entries: list[PackedResource],
    index_offset: int,
    data_offset: int,
    file_size: int,
) -> None:
    data = {
        "magic": MAGIC.decode("ascii"),
        "version": VERSION,
        "endianness": "little",
        "entry_count": len(entries),
        "index_offset": index_offset,
        "data_offset": data_offset,
        "file_size": file_size,
        "entries": [asdict(entry) for entry in entries],
    }
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        raise ToolError(f"Failed to write resource table {path}: {exc}") from exc


def read_intermediate_file(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ToolError(f"Failed to read intermediate resource {path}: {exc}") from exc


def write_bytes(path: Path, data: bytes) -> None:
    try:
        path.write_bytes(data)
    except OSError as exc:
        raise ToolError(f"Failed to write {path}: {exc}") from exc


def format_name_to_code(format_name: str) -> int:
    if format_name == "raw_rgb565":
        return FORMAT_RAW_RGB565
    if format_name == "rgb565_rle":
        return FORMAT_RGB565_RLE
    raise ToolError(f"Unsupported packed resource format: {format_name}")
