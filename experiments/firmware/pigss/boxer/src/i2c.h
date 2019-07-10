#ifndef I2C_H
#define I2C_H


// Maximal number of iterations to wait for a device to respond for a
// selection.  Should be large enough to allow for a pending write to
// complete, but low enough to properly abort an infinite loop in case
// a slave is broken or not present at all.  With 100 kHz TWI clock,
// transfering the start condition and SLA+R/W packet takes about 10
// µs.  The longest write period is supposed to not exceed ~ 10 ms.
// Thus, normal operation should not require more than 100 iterations
// to get the device to respond to a selection.
#define MAX_I2C_TRIES 200

void i2c_init(void);

#endif
