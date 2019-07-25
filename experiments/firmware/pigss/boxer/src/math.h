// Math functions module

#ifndef MATH_H
#define MATH_H

// Fixed-point exponential moving average
//
// Arguments:
//   in -- Newest input value
//   average -- Previous output
//   alpha -- 0 to 65535 value for the amount of averaging.  Alpha values near 0
//            represent heavy averaging, while values near 65535 represent little
//            averaging.
uint32_t math_ema_ui32(uint32_t in, uint32_t average, uint16_t alpha);



#endif
