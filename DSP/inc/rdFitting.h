/* rdFitting.h */

/* Copyright 2009 Picarro, Inc. */

/*
 * DESCRIPTION: Code for fitting exponential ringdowns
 *
 *    INCLUDE FILES:
 *       Specify the header files that caller needs to include.
 *
 *       SEE ALSO:
 *          Specify any related information.
 *
 */
#ifndef  _RDFITTING_H_
#define  _RDFITTING_H_

typedef struct
{
    float *minLoss;
    float *maxLoss;
    float *latestLoss;
    unsigned int *improvementSteps;
    unsigned int *startSample;
    float *fractionalThreshold;
    float *absoluteThreshold;
    unsigned int *numberOfPoints;
    float *maxEFoldings;
} RdFittingParamsType;

typedef struct
{
    unsigned int nSamp;
    unsigned int divisor;
    unsigned int nPoints;
    unsigned int peakSample;
    unsigned int firstSample;
    float thresh;
    float maxValue;
    float minValue;
} RdFittingDebug;

extern RdFittingParamsType rdFittingParams;

#define MAXFILT (8)

struct medFilt {
    float last5[5];
    int lastPos;
};

//-----------------------------------------------------------------------------
// rdFittingSummer
//-----------------------------------------------------------------------------
//
// Performs summer algorithm for ringdown fitting
//
void rdFittingSummer(uint32*data,float tSamp,int nSamp,float *a,
                     float *b, float *f);

//-----------------------------------------------------------------------------
// rdFittingImprove
//-----------------------------------------------------------------------------
//
// Polishes fit using iterations of Newton's algorithm with the normal equations.
//

void rdFittingImprove(uint32 *data,float tSamp,int nSamp, float *a,
                      float *b, float *f, int niter);

//-----------------------------------------------------------------------------
// rdFittingCorrector
//-----------------------------------------------------------------------------
//
// Performs RD backscatter correction algorithm.

//
float rdFittingCorrector(uint32 *data,float tSamp,int nSamp,float tau,
                         float a, float b, float f, float delay);

//-----------------------------------------------------------------------------
// rdFittingInit
//-----------------------------------------------------------------------------
//
// Initialize data structure for accessing ringdown fit parameters
//
void rdFittingInit();

//-----------------------------------------------------------------------------
// rdFittingDoFit
//-----------------------------------------------------------------------------
// Perform an exponential fit on the nSamp points starting at data.
//  The time between samples is tSamp seconds, and the measured
//  losses (in ppm/cm) are placed in *uncorrectedLoss and
//  *correctedLoss.

int rdFittingDoFit(uint32 *data, float tSamp, unsigned int nPoints,
                   float toffset, float *uncorrectedLoss,
                   float *correctedLoss, float *amplitude, float *background,
                   float *rmsResidual);

//-----------------------------------------------------------------------------
// rdFittingProcessRingdown
//-----------------------------------------------------------------------------
// Find the portion of the buffer which contains the rindown
//  waveform and send it
int rdFittingProcessRingdown(uint32 *buffer,
                             float *uncorrectedLoss, float *correctedLoss,
                             float *amplitude, float *background, float *rmsResidual,
                             RdFittingDebug *rdFittingDebug);

//-----------------------------------------------------------------------------
// rdFitting
//-----------------------------------------------------------------------------
// Task function that takes waveforms off the queue of ringdown buffers and
//  calls the fitting routine

void rdFitting(void);

//-----------------------------------------------------------------------------
// Median filter support for storing loss values in buffers
//-----------------------------------------------------------------------------
void medianFiltBank_init();
DataType medianFiltBank(int filtNum,DataType data);

#endif
