from __future__ import annotations

import struct


def encode_rgb565_rle(rgb565_le: bytes) -> bytes:
    if len(rgb565_le) % 2 != 0:
        raise ValueError("RGB565 byte length must be even")

    encoded = bytearray()
    pixel_count = len(rgb565_le) // 2
    index = 0

    while index < pixel_count:
        pixel = rgb565_le[index * 2 : index * 2 + 2]
        run_length = 1
        while (
            index + run_length < pixel_count
            and run_length < 0xFFFF
            and rgb565_le[(index + run_length) * 2 : (index + run_length) * 2 + 2]
            == pixel
        ):
            run_length += 1

        pixel_value = pixel[0] | (pixel[1] << 8)
        encoded.extend(struct.pack("<HH", run_length, pixel_value))
        index += run_length

    return bytes(encoded)
