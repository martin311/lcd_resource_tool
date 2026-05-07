# AGENTS.md

## Project

This repository is the MVP of an LCD and resource integration tool for toy embedded products.

## Goal

Build only the first-stage MVP:

- Read JSON LCD database.
- Read JSON target profile.
- Read JSON resource manifest.
- Convert images to RGB565.
- Optionally RLE-compress RGB565.
- Generate res.bin.
- Generate ESP32-S3 lcd_config_generated.h.
- Generate ESP32-S3 lcd_init_generated.c.
- Generate memory and compatibility reports.

## Do not build

- No GUI.
- No Excel parser.
- No YAML parser.
- No LVGL integration.
- No audio encoder.
- No full cross-platform HAL.
- No real JieLi/Nuvoton/Bluetrum SDK integration.
- No complex logging framework.

## Rules

- Use Python 3.11+.
- Use only standard library plus Pillow.
- Keep modules small.
- Use pathlib for paths.
- Use struct for binary packing.
- Use zlib.crc32 for CRC.
- Fail loudly with clear error messages.
- Put all generated files in output/<target>/.

## Commands

Expected MVP commands:

```bash
python tools/main.py check --target esp32s3 --lcd-id 0x01
python tools/main.py pack --target esp32s3
python tools/main.py build --target esp32s3 --lcd-id 0x01