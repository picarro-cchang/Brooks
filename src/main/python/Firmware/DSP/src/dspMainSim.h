#ifndef _REGISTER_TEST_SIM_H_
#define _REGISTER_TEST_SIM_H_
#define far /**/
#include <mem.h>

#define IRQ_EVT_DSPINT (13)
#define CACHE_CE00 (0)
#define CACHE_64KCACHE (0)

typedef void* LOG_Obj;
void IRQ_resetAll(void);
void IRQ_enable(unsigned int eventId);
unsigned int IRQ_globalDisable(void);
void IRQ_clear(unsigned int eventId);

void IRQ_globalRestore(unsigned int eventId);
void CSL_init(void);
void CACHE_reset(void);
void CACHE_enableCaching(unsigned int block);
void CACHE_setL2Mode(unsigned int mode);
void HPI_setDspint(unsigned int value);

__declspec(dllexport) void hwiHpiInterrupt(unsigned int funcArg, unsigned int eventId);
__declspec(dllexport) void simReadRegMem(unsigned int regNum, unsigned int numInt, unsigned int *data);
__declspec(dllexport) void simWriteHostMem(unsigned int address, unsigned int numInt, unsigned int *data);
__declspec(dllexport) int simReadUser(void);

#endif /* _REGISTER_TEST_SIM_H_ */
