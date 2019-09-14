#include <stdio.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Convenience functions for busy-wait loops
#include <util/delay.h>

// Functions for working with UART interfaces.
// Definition of LINE_TERMINATION_CHARACTERS
#include "usart.h"

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"

// Provides setter and getter functions for the system state structure
#include "system.h"

#include "aloha.h"

int8_t aloha_init(void) {
  int8_t retval = 0;

  // Aloha uses USART2 in SPI mode

  // As in the datasheet, we start initializing the MSPIM by setting the baud rate to 0
  UBRR2 = 0;

  // Make the clock pin an output, which also enables master mode
  DDRH |= _BV(DDH2);

  // Set MSPIM mode of operation
  UCSR2C |= ( _BV(UMSEL21) | _BV(UMSEL20) );

  // The clock idles low  (UCPOL = 0)
  UCSR2C &= ~(_BV(UCPOL2));

  // The data is sampled by whatever receiver on the clock's rising
  // edge (UCPHA = 0).  The UCSZ20 and UCPHA2 bits have the same
  // position in the UCSR2C register.
  UCSR2C &= ~(_BV(UCSZ20));

  // Data sent MSB first.  The UCSZ21 and UDORD2 bits have the same
  // position in the UCSR2C register.
  UCSR2C &= ~(_BV(UCSZ21));

  // Enable receiver and transmitter
  UCSR2B = ( _BV(RXEN2) | _BV(TXEN2) );
  logger_msg_p("aloha", log_level_DEBUG, PSTR("UCSR2B is 0x%x"),UCSR2B);
  logger_msg_p("aloha", log_level_DEBUG, PSTR("UCSR2C is 0x%x"),UCSR2C);
  // Set the baud rate *after* the transmitter is enabled.  There's no
  // 2x mode for MSPIM.
  //
  // UBRR is a combination of two 8-bit registers.
  //
  // Baud = fosc / ( 2(UBRR + 1))

  // |------------+-------+------------|
  // | fosc (MHz) | UBRR2 | baud (kHz) |
  // |------------+-------+------------|
  // |    14.7456 |    75 |         97 |
  // |    14.7456 |     6 |       1000 |
  // |------------+-------+------------|
  UBRR2 = 6;

  // Make PH4 an output initialized high for (not) output enable
  PORTH |= _BV(PORTH4);
  DDRH |= _BV(DDH4);

  // Make PH3 an output initialized high for (not) chip select
  PORTH |= _BV(PORTH3);
  DDRH |= _BV(DDH3);

  // Initialize the board
  aloha_write(0UL);

  // Bring output enable low
  aloha_set_noe(0);

  return retval;
}

int8_t aloha_set_cs( uint8_t data ) {
  int8_t retval = 0;
  switch( data ) {
  case 1:
    PORTH |= _BV(PORTH3);
    break;
  case 0:
    PORTH &= ~(_BV(PORTH3));
    break;
  default:
    break;
  }
  return retval;
}

int8_t aloha_set_noe( uint8_t data ) {
  int8_t retval = 0;
  switch( data ) {
  case 1:
    PORTH |= _BV(PORTH4);
    break;
  case 0:
    PORTH &= ~(_BV(PORTH4));
    break;
  default:
    break;
  }
  return retval;
}

int8_t aloha_show_clean_leds(void) {
  aloha_blank_channel_leds();
  uint32_t new_led_value = system_state_get_fp_led_value();
  new_led_value |= ( (uint32_t) 1<<CH1_BLUE |
		     (uint32_t) 1<<CH2_BLUE |
		     (uint32_t) 1<<CH3_BLUE |
		     (uint32_t) 1<<CH4_BLUE |
		     (uint32_t) 1<<CH5_BLUE |
		     (uint32_t) 1<<CH6_BLUE |
		     (uint32_t) 1<<CH7_BLUE |
		     (uint32_t) 1<<CH8_BLUE
		     );
  aloha_write(new_led_value);
  return 0;
}

int8_t aloha_clear_clean_leds(void) {
  uint32_t new_led_value = system_state_get_fp_led_value();
  new_led_value &= ( ~( (uint32_t) 1<<CH1_BLUE ) &
		     ~( (uint32_t) 1<<CH2_BLUE ) &
		     ~( (uint32_t) 1<<CH3_BLUE ) &
		     ~( (uint32_t) 1<<CH4_BLUE ) &
		     ~( (uint32_t) 1<<CH5_BLUE ) &
		     ~( (uint32_t) 1<<CH6_BLUE ) &
		     ~( (uint32_t) 1<<CH7_BLUE ) &
		     ~( (uint32_t) 1<<CH8_BLUE )
		     );
  aloha_write(new_led_value);
  return 0;
}

uint32_t aloha_clear_clean_led_bits(uint32_t led_value) {
  led_value &= ( ~( (uint32_t) 1<<CH1_BLUE ) &
		 ~( (uint32_t) 1<<CH2_BLUE ) &
		 ~( (uint32_t) 1<<CH3_BLUE ) &
		 ~( (uint32_t) 1<<CH4_BLUE ) &
		 ~( (uint32_t) 1<<CH5_BLUE ) &
		 ~( (uint32_t) 1<<CH6_BLUE ) &
		 ~( (uint32_t) 1<<CH7_BLUE ) &
		 ~( (uint32_t) 1<<CH8_BLUE )
		 );
  return led_value;
}

int8_t aloha_blank_channel_leds(void) {
  uint32_t new_led_value = system_state_get_fp_led_value();
  new_led_value &= ( ~( (uint32_t) 1<<CH1_RED ) &
		     ~( (uint32_t) 1<<CH1_GREEN) &
		     ~( (uint32_t) 1<<CH1_BLUE) &
		     ~( (uint32_t) 1<<CH2_RED ) &
		     ~( (uint32_t) 1<<CH2_GREEN) &
		     ~( (uint32_t) 1<<CH2_BLUE) &
		     ~( (uint32_t) 1<<CH3_RED ) &
		     ~( (uint32_t) 1<<CH3_GREEN) &
		     ~( (uint32_t) 1<<CH3_BLUE) &
		     ~( (uint32_t) 1<<CH4_RED ) &
		     ~( (uint32_t) 1<<CH4_GREEN) &
		     ~( (uint32_t) 1<<CH4_BLUE) &
		     ~( (uint32_t) 1<<CH5_RED ) &
		     ~( (uint32_t) 1<<CH5_GREEN) &
		     ~( (uint32_t) 1<<CH5_BLUE) &
		     ~( (uint32_t) 1<<CH6_RED ) &
		     ~( (uint32_t) 1<<CH6_GREEN) &
		     ~( (uint32_t) 1<<CH6_BLUE) &
		     ~( (uint32_t) 1<<CH7_RED ) &
		     ~( (uint32_t) 1<<CH7_GREEN) &
		     ~( (uint32_t) 1<<CH7_BLUE) &
		     ~( (uint32_t) 1<<CH8_RED ) &
		     ~( (uint32_t) 1<<CH8_GREEN) &
		     ~( (uint32_t) 1<<CH8_BLUE)
		     );
  aloha_write(new_led_value);
  return 0;

}

int8_t aloha_write( uint32_t data ) {
  int8_t retval = 0;

  // Copy the data to the system structure
  retval += system_state_set_fp_led_value(data);

  union {
    uint8_t b[4];
    uint32_t w;
  } data_union;

  data_union.w = data;

  // Pull chip-select low
  aloha_set_cs(0);

  for (int8_t bytenum = 3; bytenum >= 0; bytenum--) {
    // Wait for empty transmit buffer
    while ( !( UCSR2A & (_BV(UDRE2)) ) );
    // Put data into buffer, which also sends the data
    UDR2 = data_union.b[bytenum];
    // Wait for return to be received
    while ( !( UCSR2A & (_BV(UDRE2)) ) );
    logger_msg_p("aloha", log_level_DEBUG, PSTR("Wrote 0x%x"),data_union.b[bytenum]);
  }
  // This delay has to stay to prevent cs from coming up early
  _delay_ms(1);
  // Return chip-select high
  aloha_set_cs(1);
  return retval;
}
