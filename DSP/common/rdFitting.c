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
#include <stdlib.h>
#include <math.h>
#include "interface.h"
#include "rdFitting.h"
#include "fpga.h"
#include "registers.h"

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
void rdFittingSummer(int *data,float tSamp,int nSamp,float *a, float *b, float *f)
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

void rdFittingImprove(int *data,float tSamp,int nSamp,
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
float rdFittingCorrector(int *data,float tSamp,int nSamp,float tau,
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
    rdFittingParams.minLoss = registerAddr(RD_MINLOSS_REGISTER);
    rdFittingParams.maxLoss = registerAddr(RD_MAXLOSS_REGISTER);
    rdFittingParams.latestLoss = registerAddr(RD_LATEST_LOSS_REGISTER);
    rdFittingParams.improvementSteps = registerAddr(RD_IMPROVEMENT_STEPS_REGISTER);
    rdFittingParams.startSample = registerAddr(RD_START_SAMPLE_REGISTER);
    rdFittingParams.fractionalThreshold = registerAddr(RD_FRACTIONAL_THRESHOLD_REGISTER);
    rdFittingParams.absoluteThreshold = registerAddr(RD_ABSOLUTE_THRESHOLD_REGISTER);
    rdFittingParams.numberOfPoints = registerAddr(RD_NUMBER_OF_POINTS_REGISTER);
    rdFittingParams.maxEFoldings = registerAddr(RD_MAX_E_FOLDINGS_REGISTER);
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

int rdFittingDoFit(int *data, float tSamp, unsigned int nPoints, float toffset,
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
int rdFittingProcessRingdown(int *buffer,
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
