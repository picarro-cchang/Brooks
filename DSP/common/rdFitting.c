/* rdFitting.c */

/* Copyright 2009 Picarro, Inc. */

/*
 * DESCRIPTION:
 *   Code for fitting exponential ringdowns
 *
 * INCLUDE FILES:
 *   Specify the header files that caller needs to include.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   22-Feb-2008  sze  Added iterative improvement of ringdown parameters using Newton's method.
 *   13-Jul-2009  sze  Ported to new platform
 *   22-Jul-2009  sze  Use only LSW of data by ANDing with 0xFFFF to accomodate transferring both
 *                      ringdown data and metadata as the LSW and MSW of 32-bit quantities
 *
 */
#include <std.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sem.h>
#include "fastrts67x.h"
#include "dspData.h"
#include "fpga.h"
#include "interface.h"
#include "rdFitting.h"
#include "rdHandlers.h"
#include "registers.h"
#include "dspMaincfg.h"
#include "spectrumCntrl.h"

RdFittingParamsType rdFittingParams;

#define TAU_APPROX 30.0e-6
#define LIGHT_SPEED 299792458.0
#define PI 3.1415926535897932384626

//-----------------------------------------------------------------------------
// rdFittingSummer
//-----------------------------------------------------------------------------
//
// Performs summer algorithm for ringdown fitting
//
void rdFittingSummer(uint32 *data,float tSamp,int nSamp,float *a, float *b, float *f)
{
    float y = 0.0, x;
    float sy = 0.0, sty = 0.0;
    float sx = 0.0, stx = 0.0;
    float syy = 0.0, syx = 0.0;
    float A, B, C, D, E, F, G, H, I, s;
    float det;
    int i;

    while ((nSamp % 4) != 0) nSamp--;
#pragma MUST_ITERATE(8,,4)
    for (i=0; i<nSamp; i++)
    {
        x = (float)(0xFFFF & data[i]);
        y += x;
        sx += x;
        stx += i*x;
        sy += y;
        sty += i*y;
        syx += y*x;
        syy += y*y;
    }
    A = nSamp;
    B = 0.5*(nSamp-1)*nSamp;
    C = sy;
    D = (nSamp/6.0)*(nSamp-1)*(2*nSamp-1);
    E = sty;
    F = syy;

    G = sx;
    H = stx;
    I = syx;
    det = A*D*F+2*B*E*C-A*E*E-B*B*F-C*C*D;
    s = (A*D*I+B*H*C+G*B*E-A*H*E-B*B*I-G*D*C)/det;
    *b = (A*H*F+G*E*C+C*B*I-A*E*I-G*B*F-C*H*C)/det;
    *a = (G*D*F+B*E*I+C*H*E-G*E*E-B*H*F-C*D*I)/det;
    *b = -*b/s;
    *a = *a/(1-s)-*b;
    *f = 1/(1-s);
}

//-----------------------------------------------------------------------------
// rdFittingImprove
//-----------------------------------------------------------------------------
//
// Polishes fit using iterations of Newton's algorithm with the normal equations.
//

void rdFittingImprove(uint32 *data,float tSamp,int nSamp,
                      float *a, float *b, float *f, int niter)
{
    double A, B, C, D, E, F, G, H, I;
    double num1, num2, num3, den;
    int i, k;
    float x, r, f1, f2;

    // Make nSamp a multiple of 4
    nSamp -= (nSamp & 0x3);

    for (k=0; k<niter; k++)
    {
        x = 1.0f;
        G=0;
        H=0;
        I=0;
        f1 = 1.0f/(1.0f-(*f));
        f2 = 1.0f/(1.0f-(*f)*(*f));

#pragma MUST_ITERATE(64,,4)
        for (i=0; i<nSamp; i++)
        {
            r = (0xFFFF & data[i])-((*a)*x+(*b));
            G += r;
            H += x*r;
            I += i*x*r;
            x *= (*f);
        }
        // Explicit sums of coefficients of normal equations
        A = nSamp;
        B = (1.0f - x)*f1;
        C = ((*f) - (nSamp-(nSamp-1)*(*f))*x)*f1*f1;
        D = (1.0f - x*x)*f2;
        E = ((*f)*(*f) - (nSamp-(nSamp-1)*(*f)*(*f))*x*x)*f2*f2;
        F = ( (*f)*(*f)*(1+(*f)*(*f)) -
              (nSamp*nSamp - (2*nSamp*nSamp-2*nSamp-1)*(*f)*(*f) +
               (nSamp-1)*(nSamp-1)*(*f)*(*f)*(*f)*(*f))*x*x)*f2*f2*f2;

        num1 = G*D*F+B*E*I+C*H*E-G*E*E-B*H*F-C*D*I;
        num2 = A*H*F+G*E*C+C*B*I-A*E*I-G*B*F-C*H*C;
        num3 = A*D*I+B*H*C+G*B*E-A*H*E-B*B*I-G*D*C;
        den  = A*D*F+2*B*E*C-A*E*E-B*B*F-C*C*D;

        *f *= (1.0 + (num3/den)/(*a));
        *b += num1/den;
        *a += num2/den;
    }
}

//-----------------------------------------------------------------------------
// rdFittingCorrector
//-----------------------------------------------------------------------------
//
// Performs RD backscatter correction algorithm.
//
float rdFittingCorrector(uint32 *data,float tSamp,int nSamp,float tau,
                         float a, float b, float f, float delay)
{
    // Calculate quantities for backscatter correction

    float A, B, C, D, E, F, G, H, I;
    float J=0, K=0, L=0, M=0;
    float num, den;
    int i;
    float t, dt = tSamp/tau, x, r, xr, txr;
    float t0 = delay/tau;
    int p = 1;
    int N;
    float u,u2,u3,u4,v,v2,v3,v4,d,d2,d3,d4,e,h,fN,f2N;

    // Make nSamp a multiple of 4
    nSamp -= (nSamp & 0x3);
    N = nSamp;

    // Calculate sums from zero to infinity

    u = t0;
    u2 = u*u;
    u3 = u2*u;
    u4 = u2*u2;
    d = dt;
    d2 = d*d;
    d3 = d2*d;
    d4 = d2*d2;
    e = 1/(1-f);
    h = 1/(1-f*f);

    B = e;
    C = (u+d*e-d)*e;
    D = (2*u2-d2-2*d*u+((-u2-d2+2*d2*h)/h+2*u/h*d)*e)*e*e;
    E = h;
    F = u*h+(h-1)*h*d;
    G = (u2+d2+(-3*d2+2*d2*h)*h)*h+(-2*u+2*u*h)*h*d;
    H = (3*d2*u+(-9*d2*u+6*d2*u*h)*h)*h+(-1+(7+(-12+6*h)*h)*h)*h*d3+(-3*u2+3*u2*h)*h*d+h*u3;
    I = (6*d2*u2+(-18*d2*u2+12*d2*u2*h)*h)*h+h*u4+(1+(-15+(50+(-60+24*h)*h)*h)*h)*h*d4+
        (-4*u+(28*u+(-48*u+24*u*h)*h)*h)*h*d3+(-4+4*h)*h*d*u3;

    // Subtract sums from N to infinity

    while (p<N) p=2*p;
    fN = 1.0;
    while (p>0)
    {
        fN = fN*fN;
        if (p & N) fN *= f;
        p = p >> 1;
    }
    f2N = fN*fN;

    v = t0+N*d;
    v2 = v*v;
    v3 = v2*v;
    v4 = v2*v2;

    B -= fN*e;
    C -= fN*(v+d*e-d)*e;
    D -= fN*(2*v2-d2-2*d*v+((-v2-d2+2*d2*h)/h+2*v/h*d)*e)*e*e;
    E -= f2N*h;
    F -= f2N*(v*h+(h-1)*h*d);
    G -= f2N*((v2+d2+(-3*d2+2*d2*h)*h)*h+(-2*v+2*v*h)*h*d);
    H -= f2N*((3*d2*v+(-9*d2*v+6*d2*v*h)*h)*h+(-1+(7+(-12+6*h)*h)*h)*h*d3+(-3*v2+3*v2*h)*h*d+h*v3);
    I -= f2N*((6*d2*v2+(-18*d2*v2+12*d2*v2*h)*h)*h+h*v4+(1+(-15+(50+(-60+24*h)*h)*h)*h)*h*d4+
              (-4*v+(28*v+(-48*v+24*v*h)*h)*h)*h*d3+(-4+4*h)*h*d*v3);

    // Calculate remaining sums which are data dependent

    A = nSamp;
    x = 1.0;
#pragma MUST_ITERATE(64,,4)
    for (i=0; i<nSamp; i++)
    {
        t = i*dt+t0;
        r = (float)(0xFFFF & data[i])-(a*x+b);
        J += r;
        K += (xr = x*r);
        L += (txr = t*xr);
        M += t*txr;
        x *= f;
    }
    num = -A*E*H*M+A*E*L*I-A*L*G*G+A*G*H*K+A*G*F*M-A*F*K*I-
          E*L*D*D+E*H*D*J-E*C*J*I+E*C*D*M+C*J*G*G-G*C*D*K-
          G*H*B*J-G*C*B*M+2.0f*G*L*B*D-G*F*D*J+F*B*J*I-
          H*D*B*K+C*B*K*I+B*B*H*M+F*K*D*D-F*B*D*M-L*B*B*I;
    den = 2.0f*G*G*B*D-A*G*G*G+F*F*D*D+B*B*H*H+2.0f*F*B*C*I+C*C*G*G-
          E*G*D*D-E*C*C*I-A*E*H*H-A*F*F*I-2.0f*F*G*C*D+A*E*G*I-
          2.0f*H*C*B*G+2.0f*E*H*C*D-G*B*B*I-2.0f*H*F*B*D+2.0f*A*H*F*G;
    return (num/den)*(tau/a);
}

//-----------------------------------------------------------------------------
// rdFittingInit
//-----------------------------------------------------------------------------
//
// Initialize data structure for accessing ringdown fit parameters
//
void rdFittingInit()
{
    rdFittingParams.minLoss = registerAddr(RDFITTER_MINLOSS_REGISTER);
    rdFittingParams.maxLoss = registerAddr(RDFITTER_MAXLOSS_REGISTER);
    rdFittingParams.latestLoss = registerAddr(RDFITTER_LATEST_LOSS_REGISTER);
    rdFittingParams.improvementSteps = registerAddr(RDFITTER_IMPROVEMENT_STEPS_REGISTER);
    rdFittingParams.startSample = registerAddr(RDFITTER_START_SAMPLE_REGISTER);
    rdFittingParams.fractionalThreshold = registerAddr(RDFITTER_FRACTIONAL_THRESHOLD_REGISTER);
    rdFittingParams.absoluteThreshold = registerAddr(RDFITTER_ABSOLUTE_THRESHOLD_REGISTER);
    rdFittingParams.numberOfPoints = registerAddr(RDFITTER_NUMBER_OF_POINTS_REGISTER);
    rdFittingParams.maxEFoldings = registerAddr(RDFITTER_MAX_E_FOLDINGS_REGISTER);
}

#define IDLE 0
#define CROSSED_UPPER 1

//-----------------------------------------------------------------------------
// rdFittingDoFit
//-----------------------------------------------------------------------------
// Perform an exponential fit on the nSamp points starting at data.
//  The time between samples is tSamp seconds, and the measured
//  losses (in ppm/cm) are placed in *uncorrectedLoss and
//  *correctedLoss.

int rdFittingDoFit(uint32 *data, float tSamp, unsigned int nPoints, float toffset,
                   float *uncorrectedLoss, float *correctedLoss)
{
    float a, b, f, a0, b0, f0, tau1, tau2;
    unsigned int nPoints0 = 300, nRecommended;

    // Estimate the number of points needed for ringdown calculation, based
    //  on the first nPoints0 points. This is to ensure we do not fit too
    //  many points when the ring-down becomes very short.

    if (nPoints < nPoints0) return ERROR_RD_INSUFFICIENT_DATA;
    rdFittingSummer(data,tSamp,nPoints0,&a0,&b0,&f0);
    nRecommended = (int)(-*(rdFittingParams.maxEFoldings)/log(f0));

    if (nRecommended < 50) nRecommended = 50;
    if (nPoints>nRecommended) nPoints = nRecommended;

    // Carry out the actual fit followed by iterative improvement
    rdFittingSummer(data,tSamp,nPoints,&a,&b,&f);
    rdFittingImprove(data,tSamp,nPoints,&a,&b,&f,
                     *(rdFittingParams.improvementSteps));

    tau1 = tau2 = -tSamp/log(f);
    tau2 += rdFittingCorrector(data,tSamp,nPoints,tau2,a,b,f,toffset);

    // convert to absorbance in ppm/cm
    *uncorrectedLoss = 1000000.0/(LIGHT_SPEED*tau1*100.0);
    *correctedLoss   = 1000000.0/(LIGHT_SPEED*tau2*100.0);

    if (*uncorrectedLoss < *(rdFittingParams.minLoss) ||
            *uncorrectedLoss > *(rdFittingParams.maxLoss) ||
            *correctedLoss < *(rdFittingParams.minLoss) ||
            *correctedLoss > *(rdFittingParams.maxLoss))
    {
        *uncorrectedLoss = 0.0;
        *correctedLoss = 0.0;
        return ERROR_RD_BAD_RINGDOWN;
    }
    else
        return STATUS_OK;
}

//-----------------------------------------------------------------------------
// rdFittingProcessRingdown
//-----------------------------------------------------------------------------
// Find the portion of the buffer which contains the rindown
//  waveform and send it
int rdFittingProcessRingdown(uint32 *buffer,
                             float *uncorrectedLoss, float *correctedLoss,
                             RdFittingDebug *rdFittingDebug)
{
    unsigned int startSample = *(rdFittingParams.startSample);
    unsigned int minValue, maxValue, peakSample;
    unsigned int sample, divisor, nSamp, nPoints;
    float tSamp, frac, thresh;
    static float tSampList[] = {  40.0e-9, 80.0e-9, 160.0e-9, 320.0e-9,
                                  640.0e-9, 1.28e-6, 2.56e-6, 5.12e-6
                               };

    // Get the current number of samples and sampling interval
    //  by reading the FPGA registers
    if (rdFittingDebug)
    {
        nSamp = rdFittingDebug->nSamp;
        divisor = rdFittingDebug->divisor;
    }
    else
    {
        nSamp = readFPGA(FPGA_RDMAN + RDMAN_NUM_SAMP);
        divisor = readFPGA(FPGA_RDMAN + RDMAN_DIVISOR);
    }

    if (divisor >= sizeof(tSampList)/sizeof(float)) return ERROR_BAD_VALUE;
    tSamp = tSampList[divisor];

    // Get the maximum number of points allowed in the fit window
    nPoints = *(rdFittingParams.numberOfPoints);
    // Find the amplitude of the ringdown, starting from startSample
    maxValue = minValue = 0xFFFF & buffer[startSample];
    for (sample=startSample; sample<nSamp; sample++)
    {
        unsigned int bufferValue = 0xFFFF & buffer[sample];
        if (maxValue <= bufferValue)
        {
            peakSample = sample;
            maxValue = bufferValue;
        }
        if (minValue >= bufferValue) minValue = bufferValue;
    }
    // Select the portion of the ringdown following the peak which
    //  is below frac*maxValue + (1-frac)*minValue and also below
    //  *(rdFittingParams.absoluteThreshold) where
    //  frac = *(rdFittingParams.fractionalThreshold)

    frac = *(rdFittingParams.fractionalThreshold);
    thresh = frac*maxValue + (1-frac)*minValue;
    if (thresh>*(rdFittingParams.absoluteThreshold))
        thresh=*(rdFittingParams.absoluteThreshold);

    // Find first sample which is below the threshold
    for (sample=peakSample; sample<nSamp; sample++)
        if ((float)(0xFFFF & buffer[sample]) < thresh) break;

    // Fit the next nPoints points, or to the end of the available
    //  data (whichever comes first)
    if (nPoints > nSamp-sample) nPoints = nSamp-sample;
    if (nPoints == 0) return ERROR_RD_INSUFFICIENT_DATA;

    if (rdFittingDebug)
    {
        rdFittingDebug->nPoints = nPoints;
        rdFittingDebug->peakSample = peakSample;
        rdFittingDebug->firstSample = sample;
        rdFittingDebug->thresh = thresh;
        rdFittingDebug->maxValue = maxValue;
        rdFittingDebug->minValue = minValue;
    }

    return rdFittingDoFit(&buffer[sample], tSamp, nPoints, 0.0,
                          uncorrectedLoss, correctedLoss);
}

// This is a task function associated with TSK_rdFitting which does the ringdown fitting
void rdFitting(void)
{
    int i, j, bufferNum;
    unsigned int base;
    unsigned int virtLaserNum;
    float arctanvar1, arctanvar2, dp;
    float uncorrectedLoss, correctedLoss, thetaC;
    DataType data;
    RingdownBufferType *ringdownBuffer;
    RingdownMetadataDoubleType metaDouble;
    RingdownParamsType *rdParams;
    SpectCntrlParams *s=&spectCntrlParams;
    volatile RingdownEntryType *ringdownEntry;
    volatile VirtualLaserParamsType *vLaserParams;
    double *metaDoublePtr = (double*) &metaDouble;
    int metaSigned[8] = {0,0,0,0,0,1};
    int x, m, N;
    double s1, sx;
    // double si, si2, six;
    int wrapped;
    int *counter = (int*)(REG_BASE+4*RD_FITTING_COUNT_REGISTER);
    
    while (1)
    {
        SEM_pend(&SEM_rdFitting,SYS_FOREVER);
        (*counter)++;
        if (!get_queue(&rdBufferQueue,&bufferNum))
        {
            message_puts("rdBuffer queue empty in rdFitting");
            spectCntrlError();
        }
        if (bufferNum == MISSING_RINGDOWN)
        {
            //  Get the information from nextRdParams, since no ringdown actually took place
            rdParams = &nextRdParams;
            ringdownEntry = get_ringdown_entry_addr();
            ringdownEntry->wlmAngle = 0.0;
            ringdownEntry->uncorrectedAbsorbance = 0.0;
            ringdownEntry->correctedAbsorbance = 0.0;
            ringdownEntry->status = rdParams->status;
            ringdownEntry->count = rdParams->countAndSubschemeId >> 16;
            ringdownEntry->tunerValue = 0;
            ringdownEntry->pztValue = 0;
            ringdownEntry->lockerOffset = 0;
            ringdownEntry->laserUsed = rdParams->injectionSettings;
            ringdownEntry->ringdownThreshold = rdParams->ringdownThreshold;
            ringdownEntry->subschemeId = rdParams->countAndSubschemeId & 0xFFFF;
            ringdownEntry->schemeTable = rdParams->schemeTableAndRow >> 16;
            ringdownEntry->schemeRow   = rdParams->schemeTableAndRow & 0xFFFF;
            ringdownEntry->ratio1 = 0;
            ringdownEntry->ratio2 = 0;
            ringdownEntry->fineLaserCurrent = 0;
            ringdownEntry->coarseLaserCurrent = rdParams->coarseLaserCurrent;
            ringdownEntry->laserTemperature = rdParams->laserTemperature;
            ringdownEntry->etalonTemperature = rdParams->etalonTemperature;
            ringdownEntry->cavityPressure  = (unsigned int)(50.0 * rdParams->cavityPressure);
            ringdownEntry->ambientPressure = (unsigned int)(50.0 * rdParams->ambientPressure);
            ringdownEntry->lockerError = 0;
            ringdown_put();
            if (SPECT_CNTRL_RunningState == *(int*)registerAddr(SPECT_CNTRL_STATE_REGISTER)) SEM_postBinary(&SEM_startRdCycle);
        }
        else
        {
            ringdownBuffer = &ringdownBuffers[bufferNum];
            rdFittingProcessRingdown(ringdownBuffer->ringdownWaveform,&uncorrectedLoss,&correctedLoss,0);
            data.asFloat = uncorrectedLoss;
            writeRegister(RDFITTER_LATEST_LOSS_REGISTER,data);
            // We need to find position of metadata just before ringdown. We have a modified circular
            //  buffer which wraps back to the midpoint, and the MSB indicates if this buffer has wrapped.
            rdParams = &(ringdownBuffer->parameters);
            base = rdParams->addressAtRingdown & ~0x7;
            wrapped = base >= 32768;
            if (base == 32768 + 2048) base = 4096;
            else base = base & 0xFFF;
            // Use linear extrapolation to find the metadata values at the time of ringdown
            m = *(unsigned int *)registerAddr(RDFITTER_META_BACKOFF_REGISTER);
            N = *(unsigned int *)registerAddr(RDFITTER_META_SAMPLES_REGISTER);
            s1 = N;
            // Next two variables are used for extrapolation
            // si = (-2*m-N+1)*N/2;
            // si2 = N*(6*m*(m+N-1)+2*N*N-3*N+1)/6;
            for (j=0; j<sizeof(RingdownMetadataType)/sizeof(uint32); j++)
            {
                sx = 0;
                // six = 0;
                for (i=-m-N+1; i<=-m; i++)
                {
                    unsigned int index = base + 8*i;
                    if (index < 2048 && wrapped) index += 2048;
                    // The metadata are in the MS 16 bits of the ringdown waveform.
                    x = (ringdownBuffer->ringdownWaveform[index+j] >> 16) & 0xFFFF;
                    // Treat as signed, if necessary
                    if (metaSigned[j] && x>=0x8000) x = x - 0x10000;
                    sx += x;
                    // Following line is used for extrapolation
                    // six += i*x;
                }
                if (N > 1) {
                    // First line uses extrapolation, second is simple averaging
                    // metaDoublePtr[j] = (si2*sx - si*six)/(s1*si2 - si*si);
                    metaDoublePtr[j] = sx/s1;
                }
                else metaDoublePtr[j] = sx;
            }
            // The averaged or extrapolated metadata are in the metaDouble structure

            virtLaserNum = (rdParams->injectionSettings >> 2) & 0x7;
            // laserNum = rdParams->injectionSettings & 0x3;
            vLaserParams = &virtualLaserParams[virtLaserNum];

            // Get metadata and params, and write results to ringdown queue
            ringdownEntry = get_ringdown_entry_addr();

            // Calculate the angle in the WLM plane, corrected by the ambient pressure and etalon temperature
            arctanvar1 = vLaserParams->ratio1Scale*((metaDouble.ratio2/32768.0)-vLaserParams->ratio2Center) -
                         vLaserParams->ratio2Scale*((metaDouble.ratio1/32768.0)-vLaserParams->ratio1Center)*sinsp(vLaserParams->phase);
            arctanvar2 = vLaserParams->ratio2Scale*((metaDouble.ratio1/32768.0)-vLaserParams->ratio1Center)*cossp(vLaserParams->phase);
            dp = rdParams->ambientPressure - vLaserParams->calPressure;

            thetaC = (vLaserParams->pressureC0 + dp*(vLaserParams->pressureC1 + dp*(vLaserParams->pressureC2 + dp*vLaserParams->pressureC3))) +
                     (vLaserParams->tempSensitivity * (rdParams->etalonTemperature-vLaserParams->calTemp)) + atan2sp(arctanvar1,arctanvar2);

            ringdownEntry->wlmAngle = thetaC;
            ringdownEntry->uncorrectedAbsorbance = uncorrectedLoss;
            ringdownEntry->correctedAbsorbance = correctedLoss;
            // TODO: Modify the status as necessary if there are any fitter issues
            ringdownEntry->status = rdParams->status;
            if (bufferNum) ringdownEntry->status |= 0x8000;
            ringdownEntry->count = rdParams->countAndSubschemeId >> 16;
            ringdownEntry->tunerValue = rdParams->tunerAtRingdown;
            ringdownEntry->pztValue = metaDouble.pztValue;
            ringdownEntry->lockerOffset = metaDouble.lockerOffset;
            ringdownEntry->laserUsed = rdParams->injectionSettings;
            ringdownEntry->ringdownThreshold = rdParams->ringdownThreshold;
            ringdownEntry->subschemeId = rdParams->countAndSubschemeId & 0xFFFF;
            ringdownEntry->schemeTable = rdParams->schemeTableAndRow >> 16;
            ringdownEntry->schemeRow   = rdParams->schemeTableAndRow & 0xFFFF;
            ringdownEntry->ratio1 = metaDouble.ratio1;
            ringdownEntry->ratio2 = metaDouble.ratio2;
            ringdownEntry->fineLaserCurrent = metaDouble.fineLaserCurrent;
            ringdownEntry->coarseLaserCurrent = rdParams->coarseLaserCurrent;
            ringdownEntry->laserTemperature = rdParams->laserTemperature;
            ringdownEntry->etalonTemperature = rdParams->etalonTemperature;
            ringdownEntry->cavityPressure  = (unsigned int)(50.0 * rdParams->cavityPressure);
            ringdownEntry->ambientPressure = (unsigned int)(50.0 * rdParams->ambientPressure);
            ringdownEntry->lockerError = metaDouble.lockerError;
            // Next line is used to recenter the PZT values per virtual laser
            if (0 != (ringdownEntry->subschemeId & SUBSCHEME_ID_RecenterMask)) {
                *(s->pztOffsetByVirtualLaser_[virtLaserNum]) += *(s->pztOffsetUpdateFactor_) * (ringdownEntry->tunerValue - 32768);
                if (*(s->pztOffsetByVirtualLaser_[virtLaserNum]) > 0.6*(*(s->pztIncrPerFsr_)))  *(s->pztOffsetByVirtualLaser_[virtLaserNum])  -= *(s->pztIncrPerFsr_);
                if (*(s->pztOffsetByVirtualLaser_[virtLaserNum]) < -0.6*(*(s->pztIncrPerFsr_))) *(s->pztOffsetByVirtualLaser_[virtLaserNum])  += *(s->pztIncrPerFsr_);
            }
            // After fitting, the buffer is available again
            if (bufferNum == 0)
                SEM_postBinary(&SEM_rdBuffer0Available);
            else
                SEM_postBinary(&SEM_rdBuffer1Available);
            ringdown_put();
            // Reset bit 2 of DIAG_1 after fitting
            changeBitsFPGA(FPGA_KERNEL+KERNEL_DIAG_1, 2, 1, 0);
        }
    }
}
