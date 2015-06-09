/*
 * FILE:
 *   timestamp.c
 *
 * DESCRIPTION:
 *   Timestamp routines. Note that the instrument timestamp is a 64-bit
 *  (long long) integer with millisecond resolution.
 *
 * SEE ALSO:
 *   Specify any related information.
 *
 * HISTORY:
 *   28-Mar-2009  sze  Adapted from Python datetime source code
 */

#include <stdio.h>
#include <assert.h>

/* ---------------------------------------------------------------------------
 * General calendrical helper functions
 */

/* For each month ordinal in 1..12, the number of days in that month,
 * and the number of days before that month in the same year.  These
 * are correct for non-leap years only.
 */
static int _days_in_month[] =
{
    0, /* unused; this vector uses 1-based indexing */
    31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
};

static int _days_before_month[] =
{
    0, /* unused; this vector uses 1-based indexing */
    0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334
};

/* year -> 1 if leap year, else 0. */
static int
is_leap(int year)
{
    /* Cast year to unsigned.  The result is the same either way, but
     * C can generate faster code for unsigned mod than for signed
     * mod (especially for % 4 -- a good compiler should just grab
     * the last 2 bits when the LHS is unsigned).
     */
    const unsigned int ayear = (unsigned int)year;
    return ayear % 4 == 0 && (ayear % 100 != 0 || ayear % 400 == 0);
}

/* year, month -> number of days in that month in that year */
static int
days_in_month(int year, int month)
{
    assert(month >= 1);
    assert(month <= 12);
    if (month == 2 && is_leap(year))
        return 29;
    else
        return _days_in_month[month];
}

/* year, month -> number of days in year preceeding first day of month */
static int
days_before_month(int year, int month)
{
    int days;

    assert(month >= 1);
    assert(month <= 12);
    days = _days_before_month[month];
    if (month > 2 && is_leap(year))
        ++days;
    return days;
}

/* year -> number of days before January 1st of year.  Remember that we
 * start with year 1, so days_before_year(1) == 0.
 */
static int
days_before_year(int year)
{
    int y = year - 1;
    /* This is incorrect if year <= 0; we really want the floor
     * here.  But so long as MINYEAR is 1, the smallest year this
     * can see is 0 (this can happen in some normalization endcases),
     * so we'll just special-case that.
     */
    assert (year >= 0);
    if (y >= 0)
        return y*365 + y/4 - y/100 + y/400;
    else
    {
        assert(y == -1);
        return -366;
    }
}

/* Number of days in 4, 100, and 400 year cycles.  That these have
 * the correct values is asserted in the module init function.
 */
#define DI4Y	1461	/* days_before_year(5); days in 4 years */
#define DI100Y	36524	/* days_before_year(101); days in 100 years */
#define DI400Y	146097	/* days_before_year(401); days in 400 years  */

/* ordinal -> year, month, day, considering 01-Jan-0001 as day 1. */
void
ord_to_ymd(int ordinal, int *year, int *month, int *day)
{
    int n, n1, n4, n100, n400, leapyear, preceding;

    /* ordinal is a 1-based index, starting at 1-Jan-1.  The pattern of
     * leap years repeats exactly every 400 years.  The basic strategy is
     * to find the closest 400-year boundary at or before ordinal, then
     * work with the offset from that boundary to ordinal.  Life is much
     * clearer if we subtract 1 from ordinal first -- then the values
     * of ordinal at 400-year boundaries are exactly those divisible
     * by DI400Y:
     *
     *    D  M   Y            n              n-1
     *    -- --- ----        ----------     ----------------
     *    31 Dec -400        -DI400Y       -DI400Y -1
     *     1 Jan -399         -DI400Y +1   -DI400Y      400-year boundary
     *    ...
     *    30 Dec  000        -1             -2
     *    31 Dec  000         0             -1
     *     1 Jan  001         1              0          400-year boundary
     *     2 Jan  001         2              1
     *     3 Jan  001         3              2
     *    ...
     *    31 Dec  400         DI400Y        DI400Y -1
     *     1 Jan  401         DI400Y +1     DI400Y      400-year boundary
     */
    assert(ordinal >= 1);
    --ordinal;
    n400 = ordinal / DI400Y;
    n = ordinal % DI400Y;
    *year = n400 * 400 + 1;

    /* Now n is the (non-negative) offset, in days, from January 1 of
     * year, to the desired date.  Now compute how many 100-year cycles
     * precede n.
     * Note that it's possible for n100 to equal 4!  In that case 4 full
     * 100-year cycles precede the desired day, which implies the
     * desired day is December 31 at the end of a 400-year cycle.
     */
    n100 = n / DI100Y;
    n = n % DI100Y;

    /* Now compute how many 4-year cycles precede it. */
    n4 = n / DI4Y;
    n = n % DI4Y;

    /* And now how many single years.  Again n1 can be 4, and again
     * meaning that the desired day is December 31 at the end of the
     * 4-year cycle.
     */
    n1 = n / 365;
    n = n % 365;

    *year += n100 * 100 + n4 * 4 + n1;
    if (n1 == 4 || n100 == 4)
    {
        assert(n == 0);
        *year -= 1;
        *month = 12;
        *day = 31;
        return;
    }

    /* Now the year is correct, and n is the offset from January 1.  We
     * find the month via an estimate that's either exact or one too
     * large.
     */
    leapyear = n1 == 3 && (n4 != 24 || n100 == 3);
    assert(leapyear == is_leap(*year));
    *month = (n + 50) >> 5;
    preceding = (_days_before_month[*month] + (*month > 2 && leapyear));
    if (preceding > n)
    {
        /* estimate is too large */
        *month -= 1;
        preceding -= days_in_month(*year, *month);
    }
    n -= preceding;
    assert(0 <= n);
    assert(n < days_in_month(*year, *month));

    *day = n + 1;
}

/* year, month, day -> ordinal, considering 01-Jan-0001 as day 1. */
int
ymd_to_ord(int year, int month, int day)
{
    return days_before_year(year) + days_before_month(year, month) + day;
}

void timestamp_to_ymdhms(long long ts, int *year, int *month, int *day, int *hour, int *minute, int *second, int *millisecond)
{
    long long ms_in_day = 86400000LL;
    int ord = ts/ms_in_day + 1;
    int t = ts % ms_in_day;
    ord_to_ymd(ord,year,month,day);
    *hour = t/3600000;
    t = t % 3600000;
    *minute = t/60000;
    t = t % 60000;
    *second = t/1000;
    *millisecond = t % 1000;
}

void ymdhms_to_timestamp(int year, int month, int day, int hour, int minute, int second, int millisecond, long long *ts)
{
    int ord = ymd_to_ord(year,month,day);
    *ts = 86400000LL*(ord-1) + (((hour*60 + minute)*60 + second)*1000 + millisecond);
}
/*
int main(int argc, char *argv[])
{
    int year, month, day, hour, minute, second, millisecond;
    long long us;
    long long ts = 63373882490796LL;
    timestamp_to_ymdhms(ts,&year,&month,&day,&hour,&minute,&second,&millisecond);
    printf("Year: %d, Month: %d, Day: %d, Hour: %d, Minute: %d, Second: %d, Millisecond: %d\n",year,month,day,hour,minute,second,millisecond);
    ymdhms_to_timestamp(year,month,day,hour,minute,second,millisecond,&us);
    printf("Original timestamp: %Ld\n",ts);
    printf("Reconstructed timestamp: %Ld\n",us);
}
*/
