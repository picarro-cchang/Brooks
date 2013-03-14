/* bisect.js implements bisection algorithms. From the Python 2.7 library. */
/*global exports, module, require */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    function bisect_right(a,x,lo,hi) {

    /* Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.splice(i,0,x) will
    insert just after the rightmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched. */
        if (lo === undefined) lo = 0;
        if (hi === undefined) hi = a.length;
        if (lo < 0) throw new Error('lo must be non-negative');
        while (lo < hi) {
            var mid = (lo + hi)>>1;
            if (x < a[mid]) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    }

    function insort_right(a, x, lo, hi) {
    /* Insert item x in list a, and keep it sorted assuming a is sorted.

    If x is already in a, insert it to the right of the rightmost x.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched. */

        a.splice(bisect_right(a, x, lo, hi), 0, x);
    }

    function bisect_left(a,x,lo,hi) {

    /* Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.splice(i,0,x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched. */
        if (lo === undefined) lo = 0;
        if (hi === undefined) hi = a.length;
        if (lo < 0) throw new Error('lo must be non-negative');
        while (lo < hi) {
            var mid = (lo + hi)>>1;
            if (a[mid] < x) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    function insort_left(a, x, lo, hi) {

    /* Insert item x in list a, and keep it sorted assuming a is sorted.

    If x is already in a, insert it to the left of the leftmost x.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched. */

        a.splice(bisect_left(a, x, lo, hi), 0, x);
    }

    exports.bisect_left = bisect_left;
    exports.bisect_right = bisect_right;
    exports.insort_left = insort_left;
    exports.insort_right = insort_right;
});
