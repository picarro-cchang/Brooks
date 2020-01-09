
#include <stdio.h>

// Provides boolean datatypes
#include <stdbool.h>

// Device-specific port definitions.  Also provides special
// bit-manipulations functions like bit_is_clear and
// loop_until_bit_is_set.
#include <avr/io.h>

// Functions for maintaining a simple schedule
#include "OS.h"

#include "led.h"

led_state_t led_state;

// ----------------------- Functions ----------------------------------

void led_init(void) {
  // Arduino LED is on PB7.  Set this port pin to be an output and turn it off.
  DDRB |= _BV(DDB7);
  led_set_arduino_led( false );

  // Create a task to allow pulsing this LED
  OS_TaskCreate(&led_arduino_led_off_task, LED_ARDUINO_PULSE_MS, SUSPENDED);
  led_state.arduino_led_off_task_number = OS_get_task_number(&led_arduino_led_off_task);

  // Debug LED is on PC4.  Set this port pin to be an output and turn it off.
  DDRC |= _BV(DDC4);
  led_set_debug_led( false );

  // Create a task to allow pulsing this LED
  OS_TaskCreate(&led_debug_led_off_task, LED_DEBUG_PULSE_MS, SUSPENDED);
  led_state.debug_led_off_task_number = OS_get_task_number(&led_debug_led_off_task);

  // Tri-color LED green channel is on PC2.  Set this port pin to be
  // an output and turn it off.
  DDRC |= _BV(DDC2);
  led_set_green_led( false );

  // Tri-color LED blue channel is on PC1. Set this port pin to be an output and turn it off.
  DDRC |= _BV(DDC1);
  led_set_blue_led(false);

  // Tri-color LED red (error) channel is on PC0.  Set this port pin
  // to be an output and turn it off.
  DDRC |= _BV(DDC0);
  led_set_error_led(false);

  // Create a task to allow pulsing this LED
  OS_TaskCreate(&led_error_led_off_task, LED_ERROR_PULSE_MS, SUSPENDED);
  led_state.error_led_off_task_number = OS_get_task_number(&led_error_led_off_task);

}

void led_set_error_led( bool setting ) {
  if (setting) {
    // Turn LED on
    PORTC &= ~(_BV(PORTC0));
    led_state.error_led_on = true;
  } else {
    PORTC |= _BV(PORTC0);
    led_state.error_led_on = false;
  }
  return;
}

void led_error_led_off_task(void) {
  led_set_error_led(false);
  OS_SetTaskState(led_state.error_led_off_task_number, SUSPENDED);
}

void led_pulse_error_led(void) {
  led_set_error_led(true);
  OS_SetTaskState(led_state.error_led_off_task_number, BLOCKED);
}

void led_set_arduino_led( bool setting ) {
  if (setting) {
    // Turn LED on
    PORTB &= ~(_BV(PORTB7));
    led_state.arduino_led_on = true;
  } else {
    PORTB |= _BV(PORTB7);
    led_state.arduino_led_on = false;
  }
  return;
}

void led_arduino_led_off_task(void) {
  led_set_arduino_led( false );
  OS_SetTaskState(led_state.arduino_led_off_task_number, SUSPENDED);
}

void led_pulse_arduino_led(void) {
  led_set_arduino_led( true );
  OS_SetTaskState(led_state.arduino_led_off_task_number, BLOCKED);
}

void led_set_debug_led( bool setting ) {
  if (setting) {
    // Turn LED on
    PORTC &= ~(_BV(PORTC4));
    led_state.debug_led_on = true;
  } else {
    PORTC |= _BV(PORTC4);
    led_state.debug_led_on = false;
  }
  return;
}

void led_debug_led_off_task(void) {
  led_set_debug_led( false );
  OS_SetTaskState(led_state.debug_led_off_task_number, SUSPENDED);
}

void led_pulse_debug_led(void) {
  led_set_debug_led( true );
  OS_SetTaskState(led_state.debug_led_off_task_number, BLOCKED);
}

void led_set_green_led( bool setting ) {
  if (setting) {
    // Turn LED on
    PORTC &= ~(_BV(PORTC2));
    led_state.green_led_on = true;
  } else {
    PORTC |= _BV(PORTC2);
    led_state.green_led_on = false;
  }
  return;
}

void led_set_blue_led( bool setting ) {
  if (setting) {
    // Turn LED on
    PORTC &= ~(_BV(PORTC1));
    led_state.blue_led_on = true;
  } else {
    PORTC |= _BV(PORTC1);
    led_state.blue_led_on = false;
  }
  return;
}

