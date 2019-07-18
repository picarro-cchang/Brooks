#include <stdio.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Watchdog timer
#include <avr/wdt.h>

// Provides macros and functions for saving and reading data out of
// flash.
#include <avr/pgmspace.h>

// Provides logger_msg and logger_msg_p for log messages tagged with a
// system and severity.
#include "logger.h"

int8_t watchdog_init(void) {
  // Enable resets after timer expiration
  WDTCSR |= _BV(WDE);
  // Set timeout to 1 second
  wdt_enable(WDTO_1S);
  return 0;
}
