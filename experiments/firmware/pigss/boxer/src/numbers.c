#include <stdio.h>
#include <string.h>
#include "numbers.h"
#include "usart.h" // For debugging
#include <avr/pgmspace.h> // For strings in flash

/* stdlib.h

   Provides atoi for ascii to integer conversions.
*/
#include <stdlib.h>


/* asc2num() 

   Converts an ascii character representing a hexadecimal number into
   its integer equivalent.  Accepts both upper and lower case
   characters.  Returns 0 for non-numeric arguments. */
uint8_t asc2num(char n_asc) {
    uint8_t n_int = 0;
    n_int = n_asc - 0x30; // Subtract off non-numeric beginning of table
    if ( n_int > 0x09 ) {
        // Input number is 0xa or larger.  Need to subtract off the 
        // non-numeric interval between 9 and A in the table.
        n_int -= 0x07;
    }
    if ( n_int > 0x0f ) {
        // Input number is lower case.  Need to subtract off the difference
        // between lower and upper cases.
        n_int -= 0x20;
    }
    if ( n_int > 0xf ) {
        // If the integer is still too big, this is an invalid entry.
        n_int = 0x00;
    }
    return n_int;
}

/* hex2num() 

   Converts a string of ascii characters into a decimal by repeatedly
   calling asc2num() */
uint16_t hex2num(char *hexstr) {
    uint8_t digits = 0; // Number of digits in the string
    uint16_t totval = 0; // Returned value of the string
    digits = strlen(hexstr);
    while (digits != 0) {
        totval += asc2num(hexstr[0]) << (4 * (digits - 1));
        hexstr++;
        digits--;
    }
    return totval;
}

/* uint2num( string representing unsigned integer )

   Converts a string of ascii characters into an integer.  Doesn't do
   any size checking.  If the number is larger than 65535, output will
   be undefined.
*/
uint16_t uint2num(char *uintstr) {
  uint16_t retval = atoi(uintstr);
  return retval;
}

/* sint2num( string representing signed integer )
 
   Converts a string of ascii characters into a signed integer.
   Doesn't do any size checking.  If the number is larger than 65535,
   output will be undefined.
*/
uint16_t sint2num(char *sintstr) {
  uint16_t retval = atoi(sintstr);
  return retval;
}

/* bitshifts_max8 ( 8-bit number )

   Returns the maximum power of bitshifts that will fit in the number.
*/
uint8_t bitshifts_max8 (uint8_t number) {
  uint8_t powtwo = 1;
  uint8_t shift = 0;

  while (powtwo < number) {
    powtwo <<= 1;
    shift++;
  }
    
  return shift;
}

