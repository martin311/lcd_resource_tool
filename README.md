# LCD Resource Tool MVP

This repository is the first-stage MVP for an LCD and resource integration
tool used by toy embedded products.

## Scope

Current stage:

- Read JSON LCD database.
- Read JSON target profile.
- Read JSON resource manifest sample.
- Run a compatibility check between one LCD and one target.
- Convert manifest image resources to intermediate RGB565 files.

Not included in this stage:

- GUI
- Excel or YAML parsing
- LVGL integration
- Audio encoding
- `res.bin` packing
- Cross-platform HAL

## Requirements

- Python 3.11+
- Standard library only for this stage

Pillow is planned for a later image conversion stage, but it is not required by
the current `check` command.

## Run

From the repository root:

```bash
python tools/main.py check --target esp32s3 --lcd-id 0x01
```

If the LCD and target are compatible, the tool prints an LCD summary. If the
LCD id, target, interface, or color format is invalid, the tool exits with a
clear error message.

To convert image resources from the manifest and pack them into `res.bin`:

```bash
python tools/main.py pack --target esp32s3
```

This writes intermediate image files to `output/esp32s3/images/`, then generates
`output/esp32s3/res.bin` and `output/esp32s3/resource_table.json`. If
`assets/images/` has no PNG, BMP, or JPG files, the tool creates a 64x64 RGB
test image first.

To check one LCD and generate C config/init files:

```bash
python tools/main.py build --target esp32s3 --lcd-id 0x01
```

This writes `lcd_config_generated.h` and `lcd_init_generated.c` to
`output/esp32s3/`. It does not generate a full ESP-IDF project.

## Data Files

- `database/lcd_database.json`: LCD variants.
- `database/target_profiles.json`: target capabilities.
- `database/resource_manifest.json`: minimal resource manifest placeholder.
- `init_sequences/st7789_vendor_a.json`: sample ST7789 init sequence.
- `init_sequences/ili9341_vendor_b.json`: sample ILI9341 init sequence.
