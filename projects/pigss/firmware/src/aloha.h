// Definitions and functions for Aloha (90073) boards

#ifndef ALOHA_H
#define ALOHA_H

//************************* LED bitshifts **************************//

#define CH5_GREEN 0
#define CH5_RED 1
#define CH5_BLUE 2

#define CH6_GREEN 3
#define CH6_RED 4
#define CH6_BLUE 5

#define CH7_GREEN 6
#define CH7_RED 7
#define CH7_BLUE 8

#define CH8_GREEN 9
#define CH8_RED 10
#define CH8_BLUE 11

#define COM_GREEN 12
#define COM_RED 13
#define COM_BLUE 14

#define CH1_GREEN 16
#define CH1_RED 17
#define CH1_BLUE 18

#define CH2_GREEN 19
#define CH2_RED 20
#define CH2_BLUE 21

#define CH3_GREEN 22
#define CH3_RED 23
#define CH3_BLUE 24

#define CH4_GREEN 25
#define CH4_RED 26
#define CH4_BLUE 27

#define STATUS_GREEN 28
#define STATUS_RED 29
#define STATUS_BLUE 30

//********************** Function prototypes ***********************//

// Set up Aloha
int8_t aloha_init(void);

// Set the chip-select state (1 or 0) for communication with aloha
int8_t aloha_set_cs(uint8_t data);

// Set the not output-enable state (1 or 0) for communication with aloha
int8_t aloha_set_noe(uint8_t data);

// Write data to the front panel, discarding the return
int8_t aloha_write( uint32_t data );

// Show the clean state (all channels blue)
int8_t aloha_show_clean_leds(void);

// Clear the channel blue leds
int8_t aloha_clear_clean_leds(void);

// Set red communication LED
int8_t aloha_set_com_led_red(void);

// Set green communication LED
int8_t aloha_set_com_led_green(void);

// Set red status LED
int8_t aloha_set_status_led_red(void);

// Set green status LED
int8_t aloha_set_status_led_green(void);

// Clear the channel blue leds in the led bitfield, returning the new
// bitfield.
uint32_t aloha_clear_clean_led_bits(uint32_t led_value);

// Turn off all channel LEDs
int8_t aloha_blank_channel_leds(void);

#endif
