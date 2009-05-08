#ifndef _REGISTER_TEST_H_
#define _REGISTER_TEST_H_

#ifdef SIMULATION
#define EXPORT __declspec(dllexport)
#else
#define EXPORT /**/
#endif

EXPORT void hwiHpiInterrupt(unsigned int funcArg, unsigned int eventId);
EXPORT int  main(int argc, char *argv[]);
EXPORT void scheduler(void);

#endif /* _REGISTER_TEST_H_ */
