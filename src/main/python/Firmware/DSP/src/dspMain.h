#ifndef _REGISTER_TEST_H_
#define _REGISTER_TEST_H_

void hwiHpiInterrupt(unsigned int funcArg, unsigned int eventId);
void schedulerPrdFunc(void);
void timestampPrdFunc(void);
void sentryHandlerPrdFunc(void);
int  main(int argc, char *argv[]);

#endif /* _REGISTER_TEST_H_ */
