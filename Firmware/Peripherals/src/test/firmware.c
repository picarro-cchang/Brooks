#if ARDUINO < 100
#include <WProgram.h>
#else /* ARDUINO < 100 */
#include <Arduino.h>
#endif /* ARDUINO < 100 */


int LED = 13;


void setup(void)
{
    pinMode(LED, OUTPUT);
}


void loop(void)
{
    digitalWrite(LED, HIGH);
    delay(5000);
    digitalWrite(LED, LOW);
    delay(5000);
}
