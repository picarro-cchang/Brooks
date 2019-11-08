#ifndef LED_H
#define LED_H

// Sets the port pin directions for LEDs to be outputs.
void LED_init(void);

// Our debug LED is on PB7
void debug_LED_on(void);

void debug_LED_off(void);

void debug_LED_toggle(void);


#endif // End the include guard
