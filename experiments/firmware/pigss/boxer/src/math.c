#include <stdio.h>

// Provides integer max value definitions
#include <stdint.h>

uint32_t math_ema_ui32(uint32_t in, uint32_t average, uint16_t alpha){
  uint64_t tmp0; //calcs must be done in 64-bit math to avoid overflow
  tmp0 = (uint64_t)in * (alpha) + (uint64_t)average * (65535 - alpha);
  return (uint32_t)((tmp0 + 32768) / 65536); //scale back to 32-bit (with rounding)
}
