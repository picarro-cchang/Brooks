#include <std.h>
#include <log.h>

#include "i2c_dsp.h"
#include "ds1631.h"

extern far LOG_Obj trace;

void main()
{
    dspI2CInit();
	ds1631_init();
//    ds1631_reset();
    LOG_printf(&trace,"%x",ds1631_readConfig());
//    ds1631_startConvert();
//    LOG_printf(&trace,"%x",ds1631_readConfig());
    LOG_printf(&trace,"%f",ds1631_readTemperatureAsFloat());
    return;
}
