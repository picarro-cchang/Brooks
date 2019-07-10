/* bx_ascii.h
 
   Functions for handling ASCII characters.  */

#include <ctype.h>  // Provides tolower()
 
/* lowstring()
 
   Converts a string to all lower case by repeatedly calling tolower().
   This doesn't touch special characters like ? */
void lowstring(char *mixstring);
