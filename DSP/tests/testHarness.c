#include "testHarness.h"
void *SEM_startRdCycle;
void *SEM_waitForRdMan;

void SEM_postBinary(void *handle)
{}

int SEM_pendBinary(void *handle,int timeOut)
{}

void message_puts(char *message)
{
    printf("message_puts: %s\n", message);
}
