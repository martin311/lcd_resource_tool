/* AUTO-GENERATED FILE. DO NOT EDIT.
 * Generated from init_sequences/st7789_vendor_a.json.
 */

#include "lcd_config_generated.h"

#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint8_t cmd;
    const uint8_t *data;
    uint8_t data_len;
    uint16_t delay_ms;
} lcd_init_cmd_t;

static const uint8_t lcd_init_data_2[] = {0x08};
static const uint8_t lcd_init_data_3[] = {0x55};

const lcd_init_cmd_t lcd_init_sequence[] = {
    {0x01, NULL, 0, 120},
    {0x11, NULL, 0, 120},
    {0x36, lcd_init_data_2, 1, 0},
    {0x3A, lcd_init_data_3, 1, 0},
    {0x29, NULL, 0, 20},
};

const uint32_t lcd_init_sequence_count =
    (uint32_t)(sizeof(lcd_init_sequence) / sizeof(lcd_init_sequence[0]));
