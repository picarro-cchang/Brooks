// Functions for handling the system clock. 


//------------------------- Includes -------------------------------

/* avr/io.h
   
   Contains device-specific port definitions.
*/
#include <avr/io.h>

/*  util/delay.h
    
    Provides the _delay_loop_2 function for time delays.
*/
#include <util/delay.h>

/* avr/interrupt.h
   
   Provides cli() and sei() for turning interrupts on and off.
*/
#include <avr/interrupt.h>

#include "clock.h"

//------------------------- Functions -------------------------------

/* fosc_1mhz()

   This sets the frequency of the system clock provided by the
   internal RC oscillator to 1MHz.  Since this frequency depends on
   voltage, time, and temperature, the actual frequency is calibrated
   by comparing the resulting system clock with the 32kHz crystal
   clock source.  In the end, we'll have a 1MHz system clock to within
   about 2% 

   Arguments: none 
   Returns: none
*/
void fosc_1mhz(void) {
    unsigned char calibrate = 0; // This is zero while calibrating.
    int temp;
    unsigned char tempL;

    /* The CLKPCE bit must be written to logic one to enable changing
       the CLKPS bits.  This bit can only be written to one if the others
       in CLKPR are simultaneously written to zero.  The CLKPR bits must
       be written immediatly after changes are enabled, otherwise CLKPCE
       will be cleared by hardware in 4 cycles. 
    */
    CLKPR = (1<<CLKPCE);

    /* The atmega169 is shipped with the internal RC oscillator selected.
       This gives a system clock of ~8MHz if no prescalers are applied.
       The CKDIV8 fuse is set by default, which causes the reset
       value of CLKPR to be 0011.  This gives a factor-of-8 prescaler
       for the system clock, making it ~1MHz.  This next line just calls
       attention to this without changing any defaults. 
    */
    CLKPR = (1<<CLKPS1) | (1<<CLKPS0);

    /* Disable interrupts from timer 2 compare match and overflow */
    TIMSK2 = 0;

    /* The butterfly board has a 32kHz crystal connected between the
       TOSC1 and TOSC2 pins.  This can be used as a clock source for
       timer 2.  This is called running the timer asynchronously, and
       is set by setting the AS2 bit in ASSR while clearing all
       others.
    */
    ASSR = (1<<AS2);

    /* Set timer 2 compare value. */
    OCR2A = 200;

    /* Disable interrupts from timer 1 compare match and overflow */
    TIMSK0 = 0;

    /* Start timer 1 with the system clock source and no prescaler */
    TCCR1B = (1<<CS10);
    /* Start timer 2 with whatever clock source it has been set to
       (the 32kHz oscillator in this case).  No prescaler.
    */
    TCCR2A = (1<<CS20);

    /* Look at the asynchronous status register to figure out if timer 2
       has settled in to normal operation.  This means that the counter
       value is being automatically updated (TCN2UB = 0) and that the
       configuration register is ready to take new values (TCR2UB = 0). 
    */
    while((ASSR & 0x01) | (ASSR & 0x04));

    /* Wait for external crystal to stabilise
     
       The board has just been turned on, so we need to wait for the
       crystal to stabilize.  The _delay_loop_2 function takes a
       16-bit (the 2 is for two bytes) integer for a countdown timer.
       The timer is decremented every 4 system clocks.  So a 1MHz
       clock would give a maximum delay of 65536 * 1us * 4 = 262ms
    */
    for(int i = 0; i < 10; i++)
            _delay_loop_2(30000); // About 100ms

    while(!calibrate) {
      /* Disable all interrupts by clearing the global interrupt mask.
	 Look in avr/interrupt.h for a better description of cli() 
      */
        cli();

        /* Clear timer 1 and timer 2 interrupt flag registers.  Strangely
	   enough, bits in these registers are cleared when logic ones
	   are written to them. 
	*/
        TIFR1 = 0xFF;
        TIFR2 = 0xFF;

        /* Reset timers 1 and 2 by clearing their counting registers.
	   Timer 1 is 16-bit, and thus has two counting bytes.  Timer 2
	   is 8-bit. 
	*/
        TCNT1H = 0;
        TCNT1L = 0;
        TCNT2 = 0;

        /* The OCF2A flag will be set when timer 2 reaches the OCR2A
	   compare value. Busy loop until timer 2 reaches this
	   value. An OCR2A value of 200 should cause a 6104us delay
	*/
        while ( !(TIFR2 && (1<<OCF2A)) );

        TCCR1B = 0; // Stop timer 1
        sei(); // Enable all interrupts again.

        /* If timer 1 overflowed, it's going way too fast. Set temp to
	   the maximum value to avoid having to deal with it.  If it
	   didn't overflow, read the value into temp.
	*/
        if ( (TIFR1 && (1<<TOV1)) ) {
            temp = 0xFFFF;
        }
        else {
            tempL = TCNT1L;
            temp = TCNT1H;
            temp = (temp << 8);
            temp += tempL;
        }

        /* These timer boundaries are somewhat mysterious.  A 1MHz
	   clock should give 6104 counts in temp for OCR2A=200.  But
	   there's some extra cycles spent between when timer 2
	   overflows and when timer 1 can be stopped.
	*/
        if (temp > 6250) {
            OSCCAL--;   // The internRC oscillator runs to fast,
			// decrease the OSCCAL
        }
        else if (temp < 6120) {
            OSCCAL++;   // The internRC oscillator runs to slow,
			// increase the OSCCAL
        }
        else
            calibrate = 1;//TRUE;   // the interRC is correct

        TCCR1B = (1<<CS10); // Restart timer 1
    }
}

/* fosc_8mhz()

   This sets the frequency of the system clock provided by the
   internal RC oscillator to 8MHz. No calibration is applied.  

   Arguments: none 
   Returns: none
*/
void fosc_8mhz(void) {

    /* The CLKPCE (clock prescale change enable) bit must be written
       to logic one to enable changing the CLKPS (clock prescale)
       bits.  This bit can only be written to one if the others in the
       CLKPR register are simultaneously written to zero.  The CLKPR
       bits must be written immediatly after changes are enabled,
       otherwise CLKPCE will be cleared by hardware in 4 cycles.
    */ 
    CLKPR = ( 1<<CLKPCE );

    /* The atmega169 is shipped with the internal RC oscillator
       selected.  This gives a system clock of ~8MHz if no prescalers
       are applied.  The CKDIV8 fuse is set by default, which causes
       the reset value of the CLKPR register to be 0011.  This gives a
       factor-of-8 prescaler for the system clock, making it ~1MHz.
       Readjust this for unity scaling.
    */
    CLKPR = (0<<CLKPS1) | (0<<CLKPS0);
} // end fosc_8mhz()

void fosc_16MHz() {
  // Set the system clock to use the clock directly from the 16MHz
  // crystal or external clock.

  // The CLKPCE (clock prescale change enable) bit must be written to
  // logic one to enable changing the CLKPS (clock prescale) bits.  This
  // bit can only be written to one if the others in the CLKPR register
  // are simultaneously written to zero.  The CLKPR bits must be written
  // immediatly after changes are enabled, otherwise CLKPCE will be
  // cleared by hardware in 4 cycles.
  CLKPR = _BV(CLKPCE);

  // Clear all bits to set unity frequency scaling
  CLKPR = 0;
}
