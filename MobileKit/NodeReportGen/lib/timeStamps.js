/* timeStamps.js supports manipulation of timestamps for report generation */
/*global exports, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
	var _ = require('underscore');
    var tzWorld = require('./tzSupport');

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

    function strToEtm(s,timezone) {
        // Convert GMT time string to Epoch Time (s)
        s = s.replace(/\s+/," ");
        if (timezone === undefined) timezone = "GMT";
        return tzWorld(s,timezone)/1000.0;
    }

    function etmToStr(etm,timezone) {
        if (timezone === undefined) timezone = "GMT";
        return tzWorld((+etm)*1000,"%F %T%z (%Z)",timezone);
    }

    exports.etmToStr = etmToStr;
    exports.getMsUnixTime = getMsUnixTime;
    exports.msUnixTimeToTimeString = msUnixTimeToTimeString;
    exports.strToEtm = strToEtm;
    exports.timeStringAsDirName = timeStringAsDirName;

});
