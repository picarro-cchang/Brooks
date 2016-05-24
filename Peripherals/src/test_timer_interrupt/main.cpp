#if ARDUINO < 100
#include <WProgram.h>
#else /* ARDUINO < 100 */
#include <Arduino.h>
#endif /* ARDUINO < 100 */

#include <stdint.h>

#include <avr/interrupt.h>


#define TICK 62.5e-9
#define TICK_PRESCALE_8 500.0e-9

volatile uint8_t DO_INTERRUPT_TASK = 0;

void setup(void);
void loop(void);


ISR(TIMER1_COMPA_vect)
{
    DO_INTERRUPT_TASK = 1;
}


void setup(void)
{
    Serial.begin(9600);
    Serial.println("Starting test...");

    /* Timer1 CTC mode, don't drive any output pins and signal an
     * interrupt.
     */
    cli();
    TCCR1B = _BV(WGM12) | _BV(CS11);
    OCR1A = 0xC350;
    TIMSK1 = _BV(OCIE1A);
    TCNT1 = 0;
    sei();
}


void loop(void)
{
    if (DO_INTERRUPT_TASK) {
	DO_INTERRUPT_TASK = 0;
        Serial.print("Interrupt @ ");
        Serial.println(millis());
    }

    delay(1);
}
