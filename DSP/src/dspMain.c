#include <std.h>
#include <csl.h>
#include <csl_i2c.h>
#include <csl_cache.h>
#include <csl_irq.h>
#include <csl_hpi.h>
#include <log.h>
#include <sem.h>
#include <prd.h>
#include "dspMaincfg.h"

#include "configDsp.h"
#include "i2c_dsp.h"
#include "ds1631.h"
#include "dspAutogen.h"
#include "dspData.h"
#include "fpga.h"
#include "interface.h"
#include "rdFitting.h"
#include "rdHandlers.h"
#include "registers.h"
#include "dspMain.h"
#include "scheduler.h"
#include "spectrumCntrl.h"
#include "valveCntrl.h"

extern far LOG_Obj trace;

void schedulerPrdFunc(void)
{
    SEM_post(&SEM_scheduler);
}

void timestampPrdFunc(void)
{
    //DataType d;
    timestamp = timestamp + 1LL;
    SEM_postBinary(&SEM_waitForRdMan);
}

void sentryHandlerPrdFunc(void)
{
    SEM_post(&SEM_sentryHandler);
}

main(int argc, char *argv[])
{
    // Set up DSP configuration
    configDsp();
    // Initialize communtications between DSP and host
    init_comms();
    // Initialize ringdown buffers, scheme tables, scheme sequencer, virtual laser parameters
    dspDataInit();
    // Clear scheduler tables
    clear_scheduler_tables();
    // Initialize all registers
    initRegisters();
    // Initialize I2C
    dspI2CInit();
    // Turn off high power TECs, pump and close all valves
    // write_valve_pump_tec(0);
    // Initialize DS1631 for continuous measurements
    ds1631_init(&das_temp_sensor_I2C);
    // Initialize ringdown fitting module
    rdFittingInit();
    // Initialize EDMA handling
    edmaInit();
    // Clear DSPINT bit in HPIC
    HPI_setDspint(1);
    IRQ_resetAll();
    // Enable the interrupts
    IRQ_enable(IRQ_EVT_DSPINT);
    // Ringdown occured interrupt
    IRQ_enable(IRQ_EVT_EXTINT4);
    // Ringdown acquisition done interrupt
    IRQ_enable(IRQ_EVT_EXTINT5);
    // EDMA interrupt
    IRQ_enable(IRQ_EVT_EDMAINT);
    return 0;
}
/* The dspMain.c file may be compiled either for the DSP, or using a host based compiler to run a simulation.

    It contains the routines which interface with the DSP software register, user register and host message areas.

    When run on the DSP, these areas are accessed by the host using HPI transfers which take place through the USB.
    When run in simulation mode, the host program which normally communicates with the AnalyzerUsb object communicates
      instead with a SimulatorUsb object. Both of these are written in Python: whereas AnalyzerUsb interfaces to
      LibUsb, SimulatorUsb has a DspSimulator object (defined in the file dspMainSim.py) which talks to
      dspMain.dll, the compiled version of this file.

    Since this file makes use of DSP libraries which are not available on the host, the files dspMainSim.c/h
      are present, to provide stubs for these calls. They also provide the readMem and writeMem functions which allow
      the host to access the (simulated) DSP memory map. As we improve the simulation of the DSP, code needs to be
      added here to handle accesses to the memory space of the simulated DSP.

*/
