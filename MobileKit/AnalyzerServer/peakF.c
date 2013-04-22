#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const double PI = 3.1415926535897932385;

double test2d(double *twoD, int nrows, int ncols) {
    int i;
    double sum = 0.0;
    printf("nrows %d, ncols %d\n", nrows, ncols);
    for (i=0; i<nrows*ncols; i++) {
        printf("%f\n", twoD[i]);
        sum += twoD[i];
    }
    return sum;
} 

/*
    Checks if the specified location (level,pos) in the ssbuff array is a peak relative to its eight neighbors. Result is 
    a boolean indicating if it is a peak.
 */

#define _i(i,j) ((i)*npoints + (j))

int checkPeak(double *ssbuff, int nlevels, int npoints, int level, int pos, double minAmpl) {
    int col = pos % npoints;
    if (col < 0) col += npoints;
    double v = ssbuff[_i(level,col)];
    if (v < minAmpl) return 0;
    int colp = col + 1;
    if (colp >= npoints) colp -= npoints;
    int colm = col - 1;
    if (colm < 0) colm += npoints;
    int isPeak = (v > ssbuff[_i(level + 1, colp)]) && (v > ssbuff[_i(level + 1, col)]) && (v > ssbuff[_i(level + 1, colm)]) && \
                 (v > ssbuff[_i(level, colp)]) && (v > ssbuff[_i(level, colm)]) && \
                 (level == 0 || ((v > ssbuff[_i(level - 1, colp)]) && (v > ssbuff[_i(level - 1, col)]) && (v > ssbuff[_i(level - 1, colm)])));
    return isPeak;
}
#undef _i

#define _i(i,j) ((i) * npoints + (j))
#define _k(i,j) ((i) * maxKernel + (j))
#define _p(i,j) ((i) * (dataLen + 2) + (j))

void findPeaks(double *data, int *hList, double *scaleList, double *kernels, double *ssbuff, double *cache, double minAmpl,
               int z, int c, int concIndex, int distIndex, int etmIndex, int valveIndex, double *peaks, int *npeaks,
               int dataLen, int nlevels, int npoints, int maxKernel) {
    int i, j;
    *npeaks = 0;

    // Clear out old data
    for (i=0; i<nlevels; i++) ssbuff[_i(i,z)] = 0.0;
    for (i=0; i<dataLen; i++) cache[_i(i,c)] = data[i];
    double conc = data[concIndex];

    for (i=0; i<nlevels; i++) {
        // Add the kernel into the space-scale buffer, taking into account wrap-around
        //  into the buffer
        if (c - hList[i] < 0) {
            for (j=0; j<c + hList[i] + 1; j++) ssbuff[_i(i, j)] += conc * kernels[_k(i,hList[i] - c + j)];
            for (j=0; j<hList[i] - c; j++) ssbuff[_i(i,npoints - hList[i] + c + j)] += conc * kernels[_k(i, j)];
        }
        else if (c + hList[i] >= npoints) {
            for (j=0; j<npoints - c + hList[i]; j++) ssbuff[_i(i, c - hList[i] + j)] += conc * kernels[_k(i, j)];
            for (j=0; j<c + hList[i] + 1 - npoints; j++) ssbuff[_i(i, j)] += conc * kernels[_k(i,npoints - c + hList[i] + j)];
        }
        else {
            for (j=0; j<2 * hList[i] + 1; j++) {
                int ii, kk;
                ssbuff[ii = _i(i,c - hList[i] + j)] += conc * kernels[kk = _k(i, j)];
            }
        }
        if (i > 0) {
            // Check if we have found a peak in space-scale representation
            //  If so, add it to a list of peaks which are stored in *peaks
            int isPeak = checkPeak(ssbuff, nlevels, npoints, i - 1, c - hList[i] - 1, minAmpl);
            int col = (c - hList[i] - 1) % npoints;
            if (col < 0) col += npoints;
            if (isPeak && cache[_i(distIndex, col)] > 0.0) {
                // A peak is disqualified if the valves in an interval before the
                //  peak arrives were not in the survey state.
                int bad = 0;
                if (valveIndex >= 0) {
                    double valves;
                    int iValves;
                    // Determine if the instrument was not in survey mode at any time
                    //  during the past 10s or distance 200*dx. If so bad is set True
                    //  to disable the peak being recorded.
                    int k = col;
                    double  pkTime = cache[_i(etmIndex, col)];
                    for (j=0; j<200; j++) {
                        valves = cache[_i(valveIndex, k)];
                        iValves = round(valves);
                        if (fabs(valves - iValves) < 1.0e-4 && (iValves & 0x1F) != 0) {
                            bad = 1;
                            break;
                        }
                        if (pkTime - cache[_i(etmIndex, k)] > 10.0) break;
                        k--; if (k < 0) k += npoints;
                    }
                }
                if (!bad) {
                    double amplitude = 0.5 * ssbuff[_i(i - 1, col)]/pow(3.0,-1.5);
                    double sigma = sqrt(0.5 * scaleList[i - 1]);
                    for (j=0; j<dataLen; j++) peaks[_p(*npeaks, j)] = cache[_i(j, col)];
                    peaks[_p(*npeaks, dataLen)] = amplitude;
                    peaks[_p(*npeaks, dataLen+1)] = sigma;
                    *npeaks += 1;
                }
            }
        }
    }
}

/*
data = (dataLen,)
hList = (nlevels,)
scaleList = (nlevels,)
kernels = (nlevels, maxKernel)
ssbuff = (nlevels, npoints)
cache = (dataLen, npoints)
peaks = (nlevels, dataLen+2)
*/
