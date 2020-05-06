/* bx_clock.h
   
   Functions for handling the system clock. */
 
/* fosc_1mhz(void)
 
   This sets the frequency of the system clock provided by the internal
   RC oscillator.  Since this frequency depends on voltage, time, and
   temperature, the actual frequency is calibrated by comparing the
   resulting system clock with the 32kHz crystal clock source.  In the
   end, we'll have a 1MHz system clock to within about 2% 
*/
void fosc_1mhz(void);

/* fosc_8mhz()

   This sets the frequency of the system clock provided by the
   internal RC oscillator to 8MHz.  No calibration is applied. 

   Arguments: none 
   Returns: none
*/
void fosc_8mhz(void);

// This clears all the clock prescalers to give unity clock frequency
// scaling.  The use of a 16MHz crystal or oscillator is implied.
void fosc_16MHz(void);

