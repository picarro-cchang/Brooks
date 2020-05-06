
#include <ctype.h>  // Provides tolower()
#include "ascii.h"

void lowstring(char *mixstring) {
    while (*mixstring != '\0') {
        *mixstring = tolower(*mixstring);
        mixstring++;
    }
}
