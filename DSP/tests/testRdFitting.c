#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "CuTest.h"
#include "fpga.h"
#include "interface.h"
#include "rdFitting.h"
#include "registers.h"

#define LIGHT_SPEED 299792458.0

CuSuite* RdFittingGetSuite(void);

unsigned int readFPGA(unsigned int regNum) {
    return 0;
}

void *registerAddr(unsigned int regNum) {
    return NULL;
}

void TestDummy(CuTest *tc) {
    CuAssertIntEquals_Msg(tc,"Unexpected failure in TestDummy",2+2,4);
}

double randu()
{
    return (double)rand()/RAND_MAX;
}

void TestRdFittingSummer1(CuTest *tc) {
    int data[4096];
    float tSamp = 100e-9;
    int i, j, nSamp = 1500;
    float tau, temp;
    float ae, be, fe;
    float a, b, f;
    
    for (j=0; j<5000; j++) {
        a = 1000.0 + 15384.0*randu();
        b = 1000.0*randu();
        tau = (2.0+38.0*randu())*1.0e-6;
        f = exp(-tSamp/tau);
        temp = 1.0;
        for (i = 0; i<nSamp; i++) {
            data[i] = b + a*temp + 0.5;
            temp *= f;
        }
        rdFittingSummer(data,tSamp,nSamp,&ae,&be,&fe);
        rdFittingImprove(data,tSamp,nSamp,&ae,&be,&fe,1);
        
        CuAssertDblEquals_Msg(tc,"Incorrect value for a",a,ae,1.0);
        CuAssertDblEquals_Msg(tc,"Incorrect value for b",b,be,1.0);
        CuAssertDblEquals_Msg(tc,"Incorrect value for f",f,fe,0.001);
    }
}

void TestRdFittingDoFit1(CuTest *tc) {
    int data[4096];
    float tSamp = 100e-9;
    int i, j, nSamp=4096;
    float tau, temp;
    float ae, be, fe;
    float a, b, f;
    float loss, uncorrectedLoss, correctedLoss;
    
    float minLoss = 0.05, maxLoss = 50.0, latestLoss, fractionalThreshold = 0.85, absoluteThreshold = 9000.0;
    float maxEFoldings = 8.0;
    unsigned int improvementSteps = 1, startSample = 10, numberOfPoints = 4096;
    
    rdFittingParams.minLoss = &minLoss;
    rdFittingParams.maxLoss = &maxLoss;
    rdFittingParams.latestLoss = &latestLoss;
    rdFittingParams.improvementSteps = &improvementSteps;
    rdFittingParams.startSample = &startSample;
    rdFittingParams.fractionalThreshold = &fractionalThreshold;
    rdFittingParams.absoluteThreshold = &absoluteThreshold;
    rdFittingParams.numberOfPoints = &numberOfPoints;
    rdFittingParams.maxEFoldings = &maxEFoldings;

    for (j=0; j<5000; j++) {
        a = 1000.0 + 15384.0*randu();
        b = 1000.0*randu();
        tau = (1.0+38.0*randu())*1.0e-6;
        f = exp(-tSamp/tau);
        loss = 1000000.0/(LIGHT_SPEED*tau*100.0);

        temp = 1.0;
        for (i = 0; i<nSamp; i++) {
            data[i] = b + a*temp + 0.5;
            temp *= f;
        }
        rdFittingDoFit(data,tSamp,nSamp,0.0,&uncorrectedLoss,&correctedLoss);
        
        CuAssertDblEquals_Msg(tc,"Incorrect value for uncorrected loss",uncorrectedLoss,loss,0.0005*uncorrectedLoss);
        CuAssertDblEquals_Msg(tc,"Incorrect value for corrected loss",correctedLoss,loss,0.001*uncorrectedLoss);
    }
}

void TestRdFittingProcessRingdown(CuTest *tc) {
    int data[4096];
    float tSamp;
    static float tSampList[] = {  40.0e-9, 80.0e-9, 160.0e-9, 320.0e-9,
                                  640.0e-9, 1.28e-6, 2.56e-6, 5.12e-6
                               };
    int i, j, nSamp=4096;
    float tau, temp;
    float ae, be, fe;
    float a, b, f;
    float loss, uncorrectedLoss, correctedLoss;
    
    float minLoss = 0.05, maxLoss = 50.0, latestLoss, fractionalThreshold = 0.85, absoluteThreshold = 9000.0;
    float maxEFoldings = 8.0;
    unsigned int improvementSteps = 1, startSample = 10, numberOfPoints = 3000;
    RdFittingDebug rdFittingDebug;
 
    rdFittingParams.minLoss = &minLoss;
    rdFittingParams.maxLoss = &maxLoss;
    rdFittingParams.latestLoss = &latestLoss;
    rdFittingParams.improvementSteps = &improvementSteps;
    rdFittingParams.startSample = &startSample;
    rdFittingParams.fractionalThreshold = &fractionalThreshold;
    rdFittingParams.absoluteThreshold = &absoluteThreshold;
    rdFittingParams.numberOfPoints = &numberOfPoints;
    rdFittingParams.maxEFoldings = &maxEFoldings;

    for (j=0; j<5000; j++) {
        rdFittingDebug.nSamp = 4095;
        rdFittingDebug.divisor = 1;
        tSamp = tSampList[rdFittingDebug.divisor];
        
        a = 10000.0 + 6384.0*randu();
        b = 1000.0*randu();
        tau = (1.0+38.0*randu())*1.0e-6;
        f = exp(-tSamp/tau);
        loss = 1000000.0/(LIGHT_SPEED*tau*100.0);

        temp = 1.0;
        for (i = 0; i<nSamp; i++) {
            data[i] = b + a*temp + 0.5;
            temp *= f;
        }
        rdFittingProcessRingdown(data,&uncorrectedLoss,&correctedLoss,&rdFittingDebug);
        /*
            printf("nSamp = %d, divisor = %d, nPoints = %d, peakSample = %d, firstSample = %d\n",
                    rdFittingDebug.nSamp, rdFittingDebug.divisor, rdFittingDebug.nPoints,
                    rdFittingDebug.peakSample, rdFittingDebug.firstSample);
            printf("thresh = %.2f, maxValue = %.1f, minValue = %.1f\n",
                    rdFittingDebug.thresh, rdFittingDebug.maxValue, rdFittingDebug.minValue);
        */
        CuAssertDblEquals_Msg(tc,"Incorrect value for uncorrected loss",uncorrectedLoss,loss,0.0005*uncorrectedLoss);
        CuAssertDblEquals_Msg(tc,"Incorrect value for corrected loss",correctedLoss,loss,0.001*uncorrectedLoss);
    }
}


CuSuite* RdFittingGetSuite() {
    CuSuite* suite = CuSuiteNew();
    SUITE_ADD_TEST(suite,TestDummy);
    SUITE_ADD_TEST(suite,TestRdFittingSummer1);
    SUITE_ADD_TEST(suite,TestRdFittingDoFit1);
    SUITE_ADD_TEST(suite,TestRdFittingProcessRingdown);
    return suite;
}

void RunAllTests(void) {
    CuString *output = CuStringNew();
    CuSuite *suite = CuSuiteNew();
    CuSuiteAddSuite(suite,RdFittingGetSuite());
    CuSuiteRun(suite);
    CuSuiteSummary(suite,output);
    CuSuiteDetails(suite,output);
    printf("%s\n",output->buffer);
}

int main(void) {
    RunAllTests();
    return 0;
}
