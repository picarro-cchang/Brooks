#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "CuTest.h"
#include "dspData.h"
#include "fpga.h"
#include "interface.h"
#include "spectrumCntrl.h"
#include "registers.h"

#ifdef TESTING
	#include "testHarness.h"
#else
	#include "dspMaincfg.h"
#endif

CuSuite* SpectCntrlGetSuite(void);
extern SpectCntrlParams spectCntrlParams;

void *registerAddr(unsigned int regNum) {
    return NULL;
}

void TestDummy(CuTest *tc) {
    CuAssertIntEquals_Msg(tc,"Unexpected failure in TestDummy",2+2,4);
}

void TestInitialization(CuTest *tc) {
    SpectCntrlParams *s=&spectCntrlParams;
//    CuAssertPtrEquals_Msg(tc,"Incorrect address for state",s->state_,(unsigned int *)registerAddr(SPECT_CNTRL_STATE_REGISTER));
/*
    s->state_ = (unsigned int *)registerAddr(SPECT_CNTRL_STATE_REGISTER); 
    s->mode_  = (unsigned int *)registerAddr(SPECT_CNTRL_MODE_REGISTER); 
    s->active_= (unsigned int *)registerAddr(SPECT_CNTRL_ACTIVE_SCHEME_REGISTER); 
    s->next_  = (unsigned int *)registerAddr(SPECT_CNTRL_NEXT_SCHEME_REGISTER);
    s->iter_  = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ITER_REGISTER);
    s->row_   = (unsigned int *)registerAddr(SPECT_CNTRL_SCHEME_ROW_REGISTER); 
    s->dwell_ = (unsigned int *)registerAddr(SPECT_CNTRL_DWELL_COUNT_REGISTER);
*/    
}

CuSuite* SpectCntrlGetSuite() {
    CuSuite* suite = CuSuiteNew();
    SUITE_ADD_TEST(suite,TestDummy);
    SUITE_ADD_TEST(suite,TestInitialization);
    return suite;
}

void RunAllTests(void) {
    CuString *output = CuStringNew();
    CuSuite *suite = CuSuiteNew();
    CuSuiteAddSuite(suite,SpectCntrlGetSuite());
    CuSuiteRun(suite);
    CuSuiteSummary(suite,output);
    CuSuiteDetails(suite,output);
    printf("%s\n",output->buffer);
}

int main(void) {
    RunAllTests();
    return 0;
}

