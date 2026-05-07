from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from rle_encoder import encode_rgb565_rle
from utils import ToolError, load_json, require_dict, require_list_field


SUPPORTED_IMAGE_SUFFIXES = {".png", ".bmp", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class ConvertedImage:
    resource_id: str
    source_path: Path
    output_path: Path
    width: int
    height: int
    format_name: str
    raw_size: int
    output_size: int


def ensure_test_image(images_dir: Path) -> Path:
    images_dir.mkdir(parents=True, exist_ok=True)
    existing_images = [
        path
        for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    ]
    if existing_images:
        return existing_images[0]

    test_image_path = images_dir / "boot_logo.png"
    image = Image.new("RGB", (64, 64))
    pixels = image.load()
    for y in range(64):
        for x in range(64):
            red = (x * 4) & 0xFF
            green = (y * 4) & 0xFF
            blue = ((x + y) * 2) & 0xFF
            pixels[x, y] = (red, green, blue)
    try:
        image.save(test_image_path)
    except OSError as exc:
        raise ToolError(f"Failed to create test image {test_image_path}: {exc}") from exc
    return test_image_path


def convert_image_to_rgb565_le(image_path: Path) -> tuple[bytes, int, int]:
    if not image_path.exists():
        raise ToolError(f"Image file not found: {image_path}")
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
        raise ToolError(
            f"Unsupported image format for {image_path}; expected PNG, BMP, or JPG"
        )

    try:
        with Image.open(image_path) as image:
            rgb_image = image.convert("RGB")
            width, height = rgb_image.size
            output = bytearray(width * height * 2)
            offset = 0
            for red, green, blue in rgb_image.getdata():
                value = ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)
                output[offset] = value & 0xFF
                output[offset + 1] = (value >> 8) & 0xFF
                offset += 2
            return bytes(output), width, height
    except OSError as exc:
        raise ToolError(f"Failed to read image {image_path}: {exc}") from exc


def convert_manifest_images(
    manifest_path: Path, project_root: Path, target: str
) -> list[ConvertedImage]:
    ensure_test_image(project_root / "assets" / "images")

    data = require_dict(load_json(manifest_path), manifest_path)
    resources = require_list_field(data, "resources", manifest_path)
    output_dir = project_root / "output" / target / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    converted: list[ConvertedImage] = []
    for index, resource in enumerate(resources):
        if not isinstance(resource, dict):
            raise ToolError(f"Resource #{index} in {manifest_path} must be an object")
        if resource.get("type") != "image":
            continue

        converted.append(
            convert_resource_image(resource, index, project_root, output_dir, manifest_path)
        )

    if not converted:
        raise ToolError(f"No image resources found in {manifest_path}")
    return converted


def convert_resource_image(
    resource: dict[str, Any],
    index: int,
    project_root: Path,
    output_dir: Path,
    manifest_path: Path,
) -> ConvertedImage:
    resource_id = require_string(resource, "resource_id", index, manifest_path)
    source = project_root / require_string(resource, "path", index, manifest_path)
    format_name = resolve_output_format(resource, index, manifest_path)

    raw_rgb565, width, height = convert_image_to_rgb565_le(source)
    if format_name == "raw_rgb565":
        output_bytes = raw_rgb565
        suffix = "raw_rgb565"
    elif format_name == "rgb565_rle":
        output_bytes = encode_rgb565_rle(raw_rgb565)
        suffix = "rgb565_rle"
    else:
        raise ToolError(f"Unsupported target_format '{format_name}' for resource #{index}")

    output_path = output_dir / f"{resource_id}.{suffix}.bin"
    try:
        output_path.write_bytes(output_bytes)
    except OSError as exc:
        raise ToolError(f"Failed to write converted image {output_path}: {exc}") from exc

    return ConvertedImage(
        resource_id=resource_id,
        source_path=source,
        output_path=output_path,
        width=width,
        height=height,
        format_name=format_name,
        raw_size=len(raw_rgb565),
        output_size=len(output_bytes),
    )


def resolve_output_format(resource: dict[str, Any], index: int, manifest_path: Path) -> str:
    target_format = require_string(resource, "target_format", index, manifest_path)
    compression = str(resource.get("compression", "none")).lower()

    if target_format in {"raw_rgb565", "rgb565_rle"}:
        return target_format
    if target_format == "rgb565" and compression == "none":
        return "raw_rgb565"
    if target_format == "rgb565" and compression == "rle":
        return "rgb565_rle"

    raise ToolError(
        f"Resource #{index} has unsupported target_format/compression: "
        f"{target_format}/{compression} in {manifest_path} fields "
        f"'target_format'/'compression'"
    )


def require_string(resource: dict[str, Any], field: str, index: int, manifest_path: Path) -> str:
    value = resource.get(field)
    if not isinstance(value, str) or not value:
        raise ToolError(f"Resource #{index} in {manifest_path} is missing string field '{field}'")
    return value
