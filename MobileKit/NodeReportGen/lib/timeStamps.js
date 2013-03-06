/* timeStamps.js supports manipulation of timestamps for report generation */
/*global exports, require */

(function() {
	'use strict';
	var _ = require('underscore');
    function getMsUnixTime(timeString) {
        if (_.isUndefined(timeString)) {
            return new Date().getTime();
        }
        else {
            return new Date(timeString).getTime();
        }
    }

    function msUnixTimeToTimeString(msUnixTime) {
        return new Date(msUnixTime).toISOString();
    }

    function formatNumberLength(num, length) {
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }

    function timeStringAsDirName(ts) {
        return formatNumberLength(getMsUnixTime(ts),13);
    }

    function strToEtm(s) {
        // Convert GMT time string to Epoch Time (s)
        return new Date(s + 'Z').getTime()/1000;
    }

    exports.getMsUnixTime = getMsUnixTime;
    exports.msUnixTimeToTimeString = msUnixTimeToTimeString;
    exports.strToEtm = strToEtm;
    exports.timeStringAsDirName = timeStringAsDirName;

})();
