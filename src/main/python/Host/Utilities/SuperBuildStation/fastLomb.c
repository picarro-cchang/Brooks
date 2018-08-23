/*
 * fastlomb.c
 *
 *  Created on: Oct 11, 2010
 *      Author: stan
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define SQR(x) ((x)*(x))
#define SIGN(a,b) ((b>0)?((a)>0?(a):-(a)) : ((a)>0?-(a):(a)))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)>(b)?(a):(b))
#define SWAP(a,b) { double t=(a); (a)=(b); (b)=t; }

void four1(double data[], int n, int isign)
/* Replaces data[0..2*n-1] by its discrete Fourier transform, if isign is input as 1; or replaces
 data[0..2*n-1] by n times its inverse discrete Fourier transform, if isign is input as 1. data
 is a complex array of length n stored as a real array of length 2*n. n must be an integer power
 of 2. */
{
	int nn, mmax, m, j, istep, i;
	double wtemp, wr, wpr, wpi, wi, theta, tempr, tempi;
	if (n < 2 || n & (n - 1)) {
		printf("n must be power of 2 in four1\n");
		exit(1);
	}
	nn = n << 1;
	j = 1;
	for (i = 1; i < nn; i += 2) {
		if (j > i) {
			SWAP(data[j - 1], data[i - 1]);
			SWAP(data[j], data[i]);
		}
		m = n;
		while (m >= 2 && j > m) {
			j -= m;
			m >>= 1;
		}
		j += m;
	}
	mmax = 2;
	while (nn > mmax) {
		istep = mmax << 1;
		theta = isign * (6.28318530717959 / mmax);
		wtemp = sin(0.5 * theta);
		wpr = -2.0 * wtemp * wtemp;
		wpi = sin(theta);
		wr = 1.0;
		wi = 0.0;
		for (m = 1; m < mmax; m += 2) {
			for (i = m; i <= nn; i += istep) {
				j = i + mmax;
				tempr = wr * data[j - 1] - wi * data[j];
				tempi = wr * data[j] + wi * data[j - 1];
				data[j - 1] = data[i - 1] - tempr;
				data[j] = data[i] - tempi;
				data[i - 1] += tempr;
				data[i] += tempi;
			}
			wr = (wtemp = wr) * wpr - wi * wpi + wr;
			wi = wi * wpr + wtemp * wpi + wi;
		}
		mmax = istep;
	}
}

void realft(double data[], int n, int isign)
/* Calculates the Fourier transform of a set of n real-valued data points. Replaces these data
 (which are stored in array data[0..n-1]) by the positive frequency half of their complex Fourier
 transform. The real-valued first and last components of the complex transform are returned
 as elements data[0] and data[1], respectively. n must be a power of 2. This routine also
 calculates the inverse transform of a complex data array if it is the transform of real data.
 (Result in this case must be multiplied by 2/n.) */
{
	int i, i1, i2, i3, i4;
	double c1 = 0.5, c2, h1r, h1i, h2r, h2i, wr, wi, wpr, wpi, wtemp;
	double theta = 3.141592653589793238 / (double) (n >> 1);
	if (isign == 1) {
		c2 = -0.5;
		four1(data, n / 2, 1);
	} else {
		c2 = 0.5;
		theta = -theta;
	}
	wtemp = sin(0.5 * theta);
	wpr = -2.0 * wtemp * wtemp;
	wpi = sin(theta);
	wr = 1.0 + wpr;
	wi = wpi;
	for (i = 1; i < (n >> 2); i++) {
		i2 = 1 + (i1 = i + i);
		i4 = 1 + (i3 = n - i1);
		h1r = c1 * (data[i1] + data[i3]);
		h1i = c1 * (data[i2] - data[i4]);
		h2r = -c2 * (data[i2] + data[i4]);
		h2i = c2 * (data[i1] - data[i3]);
		data[i1] = h1r + wr * h2r - wi * h2i;
		data[i2] = h1i + wr * h2i + wi * h2r;
		data[i3] = h1r - wr * h2r + wi * h2i;
		data[i4] = -h1i + wr * h2i + wi * h2r;
		wr = (wtemp = wr) * wpr - wi * wpi + wr;
		wi = wi * wpr + wtemp * wpi + wi;
	}
	if (isign == 1) {
		data[0] = (h1r = data[0]) + data[1];
		data[1] = h1r - data[1];
	} else {
		data[0] = c1 * ((h1r = data[0]) + data[1]);
		data[1] = c1 * (h1r - data[1]);
		four1(data, n / 2, -1);
	}
}

void spread(double y, double yy[], int n, double x, int m)

/* Given an array yy[0..n-1], extirpolate (spread) a value y into m actual array elements that best
 approximate the “fictional” (i.e., possibly noninteger) array element number x. The weights used
 are coefficients of the Lagrange interpolating polynomial. */
{
	static int nfac[11] = { 0, 1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880 };
	int ihi, ilo, ix, j, nden;
	double fac;
	if (m > 10) {
		printf("factorial table too small in spread\n");
		exit(1);
	}
	ix = (int) x;
	if (x == (double) ix)
		yy[ix - 1] += y;
	else {
		ilo = MIN(MAX((int)(x-0.5*m),0),(int)(n-m));
		ihi = ilo + m;
		nden = nfac[m];
		fac = x - ilo - 1;
		for (j = ilo + 1; j < ihi; j++)
			fac *= (x - j - 1);
		yy[ihi - 1] += y * fac / (nden * (x - ihi));
		for (j = ihi - 1; j > ilo; j--) {
			nden = (nden / (j - ilo)) * (j - ihi);
			yy[j - 1] += y * fac / (nden * (x - j));
		}
	}
}

void fastLomb(double x[], double y[], int n, double ofac, double hifac,
		double px[], double py[], int np, int *nout, int *jmax, double *prob, double *datavar)
/* Given n data points with abscissas x[0..n-1] (which need not be equally spaced) and ordinates
 y[0..n-1], and given a desired oversampling factor ofac (a typical value being 4 or larger),
 this routine fills array px[0..nout-1] with an increasing sequence of frequencies (not angular
 frequencies) up to hifac times the “average” Nyquist frequency, and fills array py[0..nout-1]
 with the values of the Lomb normalized periodogram at those frequencies. The arrays x and y
 are not altered. The vectors px and py are resized to nout (eq. 13.8.9) if their initial size is less
 than this; otherwise, only their first nout components are filled. The routine also returns jmax
 such that py[jmax] is the maximum element in py, and prob, an estimate of the significance
 of that maximum against the hypothesis of random noise. A small value of prob indicates that
 a significant periodic signal is present. */
{
	int MACC = 4;
	int i, j, k, nwk, nfreq, nfreqt;
	double ave, ck, ckk, cterm, cwt, den, df, effm, expy, fac, fndim, hc2wt,
			hs2wt;
	double hypo, pmax, sterm, swt, var, xdif, xmax, xmin;
	double *wk1, *wk2;

	*nout = (int) (0.5 * ofac * hifac * n);
	nfreqt = (int) (ofac * hifac * n * MACC);
	nfreq = 64;
	while (nfreq < nfreqt)
		nfreq <<= 1;
	nwk = nfreq << 1;
	if (np < *nout) {
		printf("np should be at least %d.\n", *nout);
		exit(1);
	}
	ave = 0.0;
	var = 0.0;
	for (i = 0; i < n; i++) {
		ave += y[i];
		var += y[i] * y[i];
	}
	ave /= n;
	var = var / n - ave * ave;
	if (var == 0.0) {
		printf("Zero variance in Lomb periodogram calculation.\n");
		exit(1);
	}
	xmin = x[0];
	xmax = xmin;
	for (j = 1; j < n; j++) {
		if (x[j] < xmin)
			xmin = x[j];
		if (x[j] > xmax)
			xmax = x[j];
	}
	xdif = xmax - xmin;
	wk1 = (double *) calloc(nwk, sizeof(double));
	wk2 = (double *) calloc(nwk, sizeof(double));

	fac = nwk / (xdif * ofac);
	fndim = nwk;
	for (j = 0; j < n; j++) {
		ck = fmod((x[j] - xmin) * fac, fndim);
		ckk = 2.0 * (ck++);
		ckk = fmod(ckk, fndim);
		++ckk;
		spread(y[j] - ave, wk1, nwk, ck, MACC);
		spread(1.0, wk2, nwk, ckk, MACC);
	}

	realft(wk1, nwk, 1);
	realft(wk2, nwk, 1);
	df = 1.0 / (xdif * ofac);
	pmax = -1.0;
	for (k = 2, j = 0; j < *nout; j++, k += 2) {
		hypo = sqrt(wk2[k] * wk2[k] + wk2[k + 1] * wk2[k + 1]);
		hc2wt = 0.5 * wk2[k] / hypo;
		hs2wt = 0.5 * wk2[k + 1] / hypo;
		cwt = sqrt(0.5 + hc2wt);
		swt = SIGN(sqrt(0.5-hc2wt),hs2wt);
		den = 0.5 * n + hc2wt * wk2[k] + hs2wt * wk2[k + 1];
		cterm = SQR(cwt*wk1[k]+swt*wk1[k+1]) / den;
		sterm = SQR(cwt*wk1[k+1]-swt*wk1[k]) / (n - den);
		px[j] = (j + 1) * df;
		py[j] = (cterm + sterm) / (2.0 * var);
		if (py[j] > pmax)
			pmax = py[*jmax = j];
	}
	expy = exp(-pmax);
	effm = 2.0 * (*nout) / ofac;
	*prob = effm * expy;
	if (*prob > 0.01)
		*prob = 1.0 - pow(1.0 - expy, effm);
	*datavar = var;
	free(wk1);
	free(wk2);
}
