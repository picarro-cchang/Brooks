#ifndef _RDHANDLERS_H_
#define _RDHANDLERS_H_

void edmaDoneInterrupt(int tccNum);
void edmaInit(void);
void ringdownInterrupt(unsigned int funcArg, unsigned int eventId);
void acqDoneInterrupt(unsigned int funcArg, unsigned int eventId);


#endif /* _RDHANDLERS_H_ */
