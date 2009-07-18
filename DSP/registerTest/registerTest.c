#ifdef SIMULATION
#include "registerTestSim.h"
#else
#include <std.h>
#include <csl.h>
#include <csl_i2c.h>
#include <csl_cache.h>
#include <csl_irq.h>
#include <csl_hpi.h>
#include <log.h>
#include <sem.h>
#include <prd.h>
#include "registerTestcfg.h"
#endif

#include "configDsp.h"
#include "i2c_dsp.h"
#include "ds1631.h"
#include "dspAutogen.h"
#include "interface.h"
#include "rdFitting.h"
#include "registerTest.h"
#include "scheduler.h"
#include "registers.h"
#include "dspData.h"

extern far LOG_Obj trace;
#ifdef SIMULATION
void scheduler(void)
{
    DataType d;
    timestamp = timestamp + 100LL;
    readRegister(SCHEDULER_CONTROL_REGISTER,&d);
    if (d.asInt) do_groups(timestamp);
}

#else
void schedulerPrdFunc(void)
{
    SEM_post(&SEM_scheduler);
}

void scheduler(void)
{
    DataType d;
    while (1)
    {
        SEM_pend(&SEM_scheduler,SYS_FOREVER);
        readRegister(SCHEDULER_CONTROL_REGISTER,&d);
        if (d.asInt) do_groups(timestamp);
    }
}

void timestampPrdFunc(void)
{
    timestamp = timestamp + 1LL;
}
#endif

#ifdef SIMULATION
#pragma argsused
#endif

main(int argc, char *argv[])
{
    // Set up DSP configuration
    configDsp();
    // Initialize communtications between DSP and host
    init_comms();
    // Clear scheduler tables
    clear_scheduler_tables();
    // Initialize all registers
    initRegisters();
    // Initialize I2C
    dspI2CInit();
    // Initialize DS1631 for continuous measurements
    ds1631_init();
    // Initialize DS1631 for continuous measurements
    rdFittingInit();

    // Clear DSPINT bit in HPIC
    HPI_setDspint(1);
    IRQ_resetAll();
    // Enable the interrupts
    IRQ_enable(IRQ_EVT_DSPINT);
    // Ringdown occured interrupt
    IRQ_enable(IRQ_EVT_EXTINT4);
    // Ringdown acquisition done interrupt
    IRQ_enable(IRQ_EVT_EXTINT5);
    return 0;
}
/* The registerTest.c file may be compiled either for the DSP, or using a host based compiler to run a simulation.

    It contains the routines which interface with the DSP software register, user register and host message areas.

    When run on the DSP, these areas are accessed by the host using HPI transfers which take place through the USB.
    When run in simulation mode, the host program which normally communicates with the AnalyzerUsb object communicates
      instead with a SimulatorUsb object. Both of these are written in Python: whereas AnalyzerUsb interfaces to
      LibUsb, SimulatorUsb has a DspSimulator object (defined in the file registerTestSim.py) which talks to
      registerTest.dll, the compiled version of this file.

    Since this file makes use of DSP libraries which are not available on the host, the files registerTestSim.c/h
      are present, to provide stubs for these calls. They also provide the readMem and writeMem functions which allow
      the host to access the (simulated) DSP memory map. As we improve the simulation of the DSP, code needs to be
      added here to handle accesses to the memory space of the simulated DSP.

*/
