#ifndef LED_H
#define LED_H

#define LED_ERROR_PULSE_MS 200

#define LED_ARDUINO_PULSE_MS 200

#define LED_DEBUG_PULSE_MS 200

typedef struct led_state_struct {
  // Error (red) LED off task
  uint8_t error_led_off_task_number;

  // Arduino LED off task
  uint8_t arduino_led_off_task_number;

  // Debug LED off task
  uint8_t debug_led_off_task_number;

  // Arduino LED on
  bool arduino_led_on;

  // Error (red) LED on
  bool error_led_on;

  // Debug LED on
  bool debug_led_on;

  // Green LED on
  bool green_led_on;

  // Blue LED on
  bool blue_led_on;

} led_state_t;

void led_init(void);

// Our arduino LED is on PB7
void led_set_arduino_led(bool setting);

// Pulse the arduino LED
void led_pulse_arduino_led(void);

// Turn the arduino LED off
void led_arduino_led_off_task(void);

// The debug LED is on PC4
void led_set_debug_led(bool setting);

// Pulse the debug LED
void led_pulse_debug_led(void);

// Turn the debug LED off
void led_debug_led_off_task(void);

// Set the error LED
//
// Arguments:
//   setting -- True for on, False for off
void led_set_error_led(bool setting);

// Pulse the error LED
void led_pulse_error_led(void);

// Turn the error LED off
void led_error_led_off_task(void);

// Turn the error LED off
void led_error_led_off_task(void);

// Set the green LED
//
// Arguments:
//   setting -- True for on, False for off
void led_set_green_led(bool setting);

// Set the blue LED
//
// Arguments:
//   setting -- True for on, False for off
void led_set_blue_led(bool setting);

#endif // End the include guard
