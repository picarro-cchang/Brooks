#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const double PI = 3.1415926535897932385;
/* 
    Lower tail quantile for standard normal distribution function.

    This function returns an approximation of the inverse cumulative
    standard normal distribution function.  I.e., given P, it returns
    an approximation to the X satisfying P = Pr{Z <= X} where Z is a
    random variable from the standard normal distribution.

    The algorithm uses a minimax approximation by rational functions
    and the result has a relative error whose absolute value is less
    than 1.15e-9.
*/
double ltqnorm(double p) {
    double a[] = { -3.969683028665376e+01,  
                    2.209460984245205e+02,
                   -2.759285104469687e+02,  
                    1.383577518672690e+02,
                   -3.066479806614716e+01,
                    2.506628277459239e+00 };
    double b[] = { -5.447609879822406e+01,  
                    1.615858368580409e+02,
                   -1.556989798598866e+02,  
                    6.680131188771972e+01,
                   -1.328068155288572e+01 };
    double c[] = { -7.784894002430293e-03, 
                   -3.223964580411365e-01,
                   -2.400758277161838e+00,
                   -2.549732539343734e+00,
                    4.374664141464968e+00,
                    2.938163982698783e+00 };
    double d[] = {  7.784695709041462e-03,  
                    3.224671290700398e-01,
                    2.445134137142996e+00,
                    3.754408661907416e+00 };
    double plow = 0.02425, phigh = 1.0 - plow, q;

    if (p <= 0 || p >= 1) {
        printf("Argument to ltqnorm %f must be in the open interval (0,1)", p);
        exit(1);
    }
    if (p < plow) {
        // Use rational approximation for lower region
        q = sqrt(-2.0 * log(p));
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0);
    }
    else if (phigh < p) {
        q = sqrt(-2.0 * log(1.0 - p));
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0);
    }
    else {
        q = p - 0.5;
        double r = q*q;
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0);
    }
}

/*
    Calculate probability that a normal random variable will be
    less than the mean + z standard deviations
*/
double cnorm(double z) {
    return 0.5 * erf(z/sqrt(2.0));
}

struct coeffs {
    double power;
    double scale;
} PG_coeffs[] = {
    { 1.92607854134, 7.06164265123 },
    { 1.85109993492, 9.23174186112 },
    { 1.83709437442, 14.0085461312 },
    { 1.79141020506, 21.8533325178 },
    { 1.74832538645, 29.2243762172 },
    { 1.72286808749, 46.0503577192 }
};

/* 
  Calculate the concentration in ppm under stability class stabClass (0=A,...,5=F)
   due to a point source of Q cu ft/hr at distance x m downwind when 
   the wind speed is u m/s 
*/

double getConc(int stabClass, double Q, double u, double x) {
    struct coeffs c = PG_coeffs[stabClass];
    return (Q / u) * pow(x / c.scale, -c.power);  
}

/*
  Get the maximum distance at which a source of rate Q cu ft/hr can
   be located if it is to be found with an instrument capable of measuring
   concentration "conc" above ambient, when the wind speed is u m/s.

  Since this would normally diverge at small u, a regularization is applied
   so that the maximum distance is made to vary as u**a for u<u0. The
   sharpness of the transition at u0 is controlled by 1<q<infinity
*/

double getMaxDist(int stabClass, double Q, double u, double conc, double u0, double a, double q) {
    struct coeffs c = PG_coeffs[stabClass];
    double d = c.scale * pow( u * conc /Q, -1.0 / c.power);
    if (u0 > 0.0) {
        double v = u / u0;
        d *= pow(v, a) / pow(pow(v, a*q) + pow(v, -(double) q / c.power), 1.0/q);

    }
    return d;
}

/*
  Calculate maximum width of field of view about the point (x_N,y_N) based on a path of 2N+1 points (x_0,y_0) through (x_{2N},y_{2N})
   where the mean wind bearing is (u=WIND_E,v=WIND_N) and there is a standard deviation of the wind direction given by d_sdev.


  Consider a segment of path specified by (x[0],y[0]) through (x[2*N],y[2*N]). A line is drawn through (x[N],y[N]) in the
    direction of (u,v) and the trial source position is placed at a distance "dist" along this line. This function calculates
    the angle ranges subtended by the path segment at the trial source position, where zero angle corresponds to the line joining
    the source to (x[N],y[N]). The angle ranges are returned as amin[i],amax[i] for i=0...(*na)-1.
    Angles are in radians.

  The pointers amin and amax should point to arrays of at least 2*N+1 doubles. The returned value *na indicates the number used

*/
void angleRange(double *x, double *y, int N, double dist, double u, double v, double dmax, double *amin, double *amax, int *na)
{
    const double BAD_VALUE = -999999.0;
    double acen = 0.0, d, lastA = BAD_VALUE;
    enum {INSIDE_GROUP, OUTSIDE_GROUP} state;
    int i;
    if (isnan(u) || isnan(v) || isnan(x[N]) || isnan(y[N]) || (u == 0.0 && v == 0.0)) {
        *na = 0;
        return;
    }
    double w = sqrt(u * u + v * v);
    double uhat = u/w, vhat = v/w;
    // Calculate the trial source position
    double sx = x[N] + dist * uhat;
    double sy = y[N] + dist * vhat;

    // Calculate the angles subtended by the path segments at the trial source position and unwrap modulo 2*pi
    for (i=0; i<=2*N; i++) {
        if (isnan(x[i]) || isnan(y[i])) {
            amin[i] = BAD_VALUE;
        }
        else {
            amin[i] = atan2(sy-y[i], sx-x[i]);
            if (lastA != BAD_VALUE) amin[i] += 2.0*PI*floor((lastA - amin[i])/(2.0*PI) + 0.5);
            lastA = amin[i];
            if (i == N) acen = lastA;
            // Calculate distance from path to source and disqualify path segments out of range
            d = sqrt((sx-x[i]) * (sx-x[i]) + (sy-y[i]) * (sy-y[i]));
            if (d > dmax) amin[i] = BAD_VALUE;
        }
        // printf("%d: %f\n", i, amin[i]);
    }

    // Find min and max angles in groups of contiguous good angles. These are the angleRanges required.

    double gmin = 0, gmax = 0;
    state = OUTSIDE_GROUP;
    *na = 0;
    for (i=0; i<=2*N; i++) {
        if (amin[i] != BAD_VALUE) amin[i] -= acen;
        switch (state) {
            case INSIDE_GROUP:
                if (amin[i] == BAD_VALUE) {
                    state = OUTSIDE_GROUP;
                    amin[*na] = gmin;
                    amax[*na] = gmax;
                    *na += 1;
                }
                else {
                    gmin = (amin[i] < gmin) ? amin[i] : gmin;
                    gmax = (amin[i] > gmax) ? amin[i] : gmax;
                }
                break;
            case OUTSIDE_GROUP:
                if (amin[i] != BAD_VALUE) {
                    state = INSIDE_GROUP;
                    gmin = gmax = amin[i];
                }
                break;    
        }
        // printf("%d: %f, %f\n", i, amin[i], amax[i]);
    }
    if (state == INSIDE_GROUP) {
        amin[*na] = gmin;
        amax[*na] = gmax;
        *na += 1;        
    }
}

/*
  Find the probability that in covered by a set of angleRanges [(amin1,amax1),(amin2,amax2)...] for a normal probability
    distribution with zero mean and standard deviation sigma
    Angles are in radians.
*/
double coverProb(double *amin, double *amax, int na, double sigma) {
    double prob = 0.0;
    int i;
    for (i=0; i<na; i++) {
        prob += cnorm(amax[i]/sigma) - cnorm(amin[i]/sigma);
    }
    return prob;
}

struct swParams {
    double *x;
    double *y;
    int N;
    double u;
    double v;
    double sigma;
    double dmax;
    double thresh;
    double tol;
};

static double amin[41], amax[41];

double my_func(double d, void *params) {
    int na = 0;
    struct swParams *sp = (struct swParams *) params;
    angleRange(sp->x, sp->y, sp->N, d, sp->u, sp->v, sp->dmax, amin, amax, &na);
    return coverProb(amin, amax, na, sp->sigma) - sp->thresh;
}

/*
  Use binary search to find a zero of func lying between xmin and xmax to a tolerance tol
*/

double binSearch(double xmin, double xmax, double tol, double (*func)(double, void*), void *params) {
    int i, max_loops = 64;
    double fxmin = (*func)(xmin, params);
    double fxmax = (*func)(xmax, params);
    double c, fc;
    for (i=0; i<max_loops; i++) {
        if ((fxmin >= 0 && fxmax >= 0) || (fxmin <= 0 && fxmax <= 0)) {
            printf("Error in binSearch.\n");
            exit(1);
        }
        c = 0.5*(xmin + xmax);
        fc = (*func)(c, params);
        if (fc == 0.0 || xmax - xmin < tol) break;
        if ((fc >= 0 && fxmin <= 0) || (fc <= 0 && fxmin >= 0)) {
            xmax = c;
            fxmax = fc;
        }
        else {
            xmin = c;
            fxmin = fc;
        }
    }
    return c;
}

/*
  Find the maximum width of the swath (to a tolerance of tol) attached to the point x[N],y[N] in
    the direction of (u,v) when the standard deviation of the wind direction is sigma. The swath width
    is never greater than dmax, and the probability that the path covers the the range of wind directions
    is no less than thresh.

    Angles are in Radians.
*/

double maxDist(double *x, double *y, int N, double u, double v, double sigma, double dmax, double thresh, double tol)
{
    double dmin = 0.1;
    struct swParams swp;
    if (N > 20) {
        printf("Too many points in swath calculation");
        exit(1);
    }
    if (isnan(x[N]) || isnan(y[N])) return 0.0;
    swp.x = x; swp.y = y; swp.N = N; swp.u = u; swp.v = v; 
    swp.sigma = sigma; swp.dmax = dmax; swp.thresh = thresh; swp.tol = tol;
    if (my_func(dmax,(void *) &swp) > 0) return dmax;
    else if (my_func(dmin,(void *) &swp) < 0) return 0.0;
    else return binSearch(dmin, dmax, tol, my_func, (void *) &swp);
}


