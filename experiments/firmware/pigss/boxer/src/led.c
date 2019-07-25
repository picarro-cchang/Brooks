
#include <stdio.h>


// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// ----------------------- Functions ----------------------------------

void LED_init(void) {
  // Debug LED is on PB7.  Set this port pin to be an output.
  DDRB |= _BV(DDB7);
}

void debug_LED_on() {
  PORTB |= _BV(PORTB7);
}

void debug_LED_off() {
  PORTB &= ~(_BV(PORTB7));
}

void debug_LED_toggle() {
  if ( bit_is_set(PORTB,PORTB7) )
    debug_LED_off();
  else
    debug_LED_on();
}

