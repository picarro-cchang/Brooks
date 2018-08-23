#ifndef _TEST_HARNESS_H_
#define _TEST_HARNESS_H_

#define SYS_FOREVER (0)
extern void *SEM_startRdCycle;
extern void *SEM_waitForRdMan;

void SEM_postBinary(void *handle);
int SEM_pendBinary(void *handle,int timeOut);

#endif /* _TEST_HARNESS_H_ */
