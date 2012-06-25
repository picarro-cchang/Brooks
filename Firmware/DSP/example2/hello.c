#include <std.h>
#include <log.h>

#include "i2c_dsp.h"
#include "ds1631.h"
#include "pcf8563.h"
#include "pca9547.h"
#include "ltc2485.h"
#include "ltc2499.h"
#include "configDsp.h"

extern far LOG_Obj trace;

void main()
{
    unsigned int year, month, day;
    unsigned int hours, minutes, seconds;
    unsigned int weekday;
    int flags, result;

    configDsp();
    // Clear DSPINT bit in HPIC
    HPI_setDspint(1);
    IRQ_resetAll();
    // Enable the interrupt
    IRQ_enable(IRQ_EVT_DSPINT);

    dspI2CInit();
    ds1631_init();
    LOG_printf(&trace,"%x",ds1631_readConfig());
    LOG_printf(&trace,"%f",ds1631_readTemperatureAsFloat());

    pcf8563_init();
    pcf8563_set_time(2009,5,7,21,35,0,4);
    pcf8563_get_time(&year,&month,&day,&hours,&minutes,
                     &seconds,&weekday);

    LOG_printf(&trace,"I2C0 mode: %x",getI2CMode(hI2C0));
    LOG_printf(&trace,"I2C0 status: %x",getI2CStatus(hI2C0));
    LOG_printf(&trace,"I2C1 mode: %x",getI2CMode(hI2C1));
    LOG_printf(&trace,"I2C1 status: %x",getI2CStatus(hI2C1));

    while (1)
    {
        setI2C0Mux(2);
        LOG_printf(&trace,"MUX channel: %d",fetchI2C0Mux());
        result = ltc2485_getData(&flags);
        LOG_printf(&trace,"ADC data: %d",result);
        LOG_printf(&trace,"I2C0 mode: %x",getI2CMode(hI2C0));
        LOG_printf(&trace,"I2C0 status: %x",getI2CStatus(hI2C0));
        LOG_printf(&trace,"I2C1 mode: %x",getI2CMode(hI2C1));
        LOG_printf(&trace,"I2C1 status: %x",getI2CStatus(hI2C1));

        setI2C0Mux(3);
        LOG_printf(&trace,"MUX channel: %d",fetchI2C0Mux());
        result = ltc2485_getData(&flags);
        LOG_printf(&trace,"ADC data: %d",result);
        LOG_printf(&trace,"I2C0 mode: %x",getI2CMode(hI2C0));
        LOG_printf(&trace,"I2C0 status: %x",getI2CStatus(hI2C0));
        LOG_printf(&trace,"I2C1 mode: %x",getI2CMode(hI2C1));
        LOG_printf(&trace,"I2C1 status: %x",getI2CStatus(hI2C1));
    }

    ltc2499_configure(0,0,0,0,0);
    ltc2499_getData(&flags);
    ltc2499_configure(0,8,0,0,0);
    LOG_printf(&trace,"ADC data (ch0-ch1): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,1,0,0,0);
    LOG_printf(&trace,"ADC data (ch1-ch0): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,9,0,0,0);
    LOG_printf(&trace,"ADC data (ch2-ch3): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,2,0,0,0);
    LOG_printf(&trace,"ADC data (ch3-ch2): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,10,0,0,0);
    LOG_printf(&trace,"ADC data (ch4-ch5): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,3,0,0,0);
    LOG_printf(&trace,"ADC data (ch5-ch4): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,11,0,0,0);
    LOG_printf(&trace,"ADC data (ch6-ch7): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,0,0,0,0);
    LOG_printf(&trace,"ADC data (ch7-ch6): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,8,0,0,0);
    LOG_printf(&trace,"ADC data (ch0-ch1): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,1,0,0,0);
    LOG_printf(&trace,"ADC data (ch1-ch0): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,9,0,0,0);
    LOG_printf(&trace,"ADC data (ch2-ch3): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,2,0,0,0);
    LOG_printf(&trace,"ADC data (ch3-ch2): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,10,0,0,0);
    LOG_printf(&trace,"ADC data (ch4-ch5): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,3,0,0,0);
    LOG_printf(&trace,"ADC data (ch5-ch4): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,11,0,0,0);
    LOG_printf(&trace,"ADC data (ch6-ch7): %d",ltc2499_getData(&flags));
    ltc2499_configure(0,0,0,0,0);
    LOG_printf(&trace,"ADC data (ch7-ch6): %d",ltc2499_getData(&flags));

    LOG_printf(&trace,"Flags: %d",flags);

    setI2C0Mux(4);
    setI2C1Mux(6);
    LOG_printf(&trace,"%d",fetchI2C0Mux());
    LOG_printf(&trace,"%d",fetchI2C1Mux());
    return;
}
