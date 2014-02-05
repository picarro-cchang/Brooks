/* utils.js provides utilities for rendering reports */
/*global alert, console, module, require, TEMPLATE_PARAMS */
/* jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';

    // Example: hex2RGB("#FF804F") => [255, 128, 79]
    function hex2RGB(h) {
        var r, g, b;
        if (h.charAt(0)=="#") {
            r = parseInt(h.substring(1,3),16);
            g = parseInt(h.substring(3,5),16);
            b = parseInt(h.substring(5,7),16);
            return [r,g,b];
        }
        else return false;
    }

    // Example: dec2hex(4093,4) => "0FFD"
    function dec2hex(i,nibbles) {
        // Convert unsigned integer to hexadecimal of specified length with zero padding
        return (i+Math.pow(2,4*nibbles)).toString(16).substr(-nibbles).toUpperCase();
    }

    // Example: colorTuple2Hex([127, 93, 150] => "7F5D96")
    function colorTuple2Hex(colors) {
        var hexStr = [];
        for (var i=0; i<colors.length; i++) {
            hexStr.push(dec2hex(colors[i],2));
        }
        return hexStr.join("");
    }

    // Example: getDateTime(new Date()) returns a time string of the form 20130604T161700
    //  where the month, date, hours, minutes and seconds are each zero padded to two digits.
    function getDateTime(d){
        // padding function
        var s = function(a,b) { return(1e15+a+"").slice(-b); };
        return d.getUTCFullYear() +
            s(d.getUTCMonth()+1,2) +
            s(d.getUTCDate(),2) + 'T' +
            s(d.getUTCHours(),2) +
            s(d.getUTCMinutes(),2) +
            s(d.getUTCSeconds(),2);
    }

    // The following is used to buffer requests to a timezone handling service, so 
    //    that not too many requests are made at once
    //
    // Example:
    //   If DASHBOARD.Utilities.timezone is a service for converting between timezones
    //    we can get a list of time strings for a list of posix times by calling
    //
    //   params = {"tz": "America/Los_Angeles", "posixTimes": [1000, 2000, 4000]}
    //   bufferedTimezone(DASHBOARD.Utilities.timezone, params, 
    //   function (err) { console.log("Error callback: " + err);},
    //   function (status, result) { console.log("Success, status: " + status + 
    //                               " result: " + JSON.stringify(result)); }
    // The underlying service is called with at most "chunkSize" times to convert
    // If the conversions fail, we retry after a delay, up to a total of maxRetries 
    //  times over the entire request.

    function bufferedTimezone(service, qry_obj, errorCbFn, successCbFn) {
        var chunk, subqry, input, output1, output2;
        var chunkSize = 100;
        var maxRetries = 5;
        var retryDelay_ms = 1000;
        var retry = 0;
        if ("posixTimes" in qry_obj && qry_obj.posixTimes.length>0) {
            input = qry_obj.posixTimes.slice(0);
            output1 = [];
            output2 = [];
            var next1 = function() {
                if (input.length === 0) {
                    successCbFn(200, {"tz": qry_obj.tz, "posixTimes": output1, "timeStrings": output2});
                }
                else {
                    chunk = input.splice(0,chunkSize);
                    subqry = {"tz": qry_obj.tz, "posixTimes": chunk};
                    service(subqry,
                    function (err) {
                        retry += 1;
                        if (retry <= maxRetries) {
                            input = chunk.concat(input);
                            setTimeout(next1, retryDelay_ms);
                        }
                        else {
                            errorCbFn(err);
                        }
                    },
                    function (s, result) {
                        output1.push.apply(output1, result.posixTimes);
                        output2.push.apply(output2, result.timeStrings);
                        next1();
                    });
                }
            };
            next1();
        }
        else if ("timeStrings" in qry_obj && qry_obj.timeStrings.length>0) {
            input = qry_obj.timeStrings.slice(0);
            output1 = [];
            output2 = [];
            var next2 = function() {
                if (input.length === 0) {
                    successCbFn(200, {"tz": qry_obj.tz, "posixTimes": output1, "timeStrings": output2});
                }
                else {
                    chunk = input.splice(0,chunkSize);
                    subqry = {"tz": qry_obj.tz, "timeStrings": chunk};
                    service(subqry,
                    function (err) {
                        retry += 1;
                        if (retry <= maxRetries) {
                            input = chunk.concat(input);
                            setTimeout(next2, retryDelay_ms);
                        }
                        else {
                            errorCbFn(err);
                        }
                    },
                    function (s, result) {
                        output1.push.apply(output1, result.posixTimes);
                        output2.push.apply(output2, result.timeStrings);
                        next2();
                    });
                }
            };
            next2();
        }
        else {
            successCbFn(200, {"tz": qry_obj.tz, "posixTimes": [], "timeStrings": []});
        }
    }

    // Get the leading part of the resource URL associated with the MD5 hash of the instructions
    // Example: When we want to divide the report generation files in subdirectories according to the
    //  first byte of the hash to not overfill the top-level directory: 
    //
    //  instrResource("0123456789ABCDEF0123456789ABCDEF") => "/01/0123456789ABCDEF0123456789ABCDEF"

    function instrResource(hash) {
        return "/" + hash.substr(0,2) + "/" + hash;
    }

    // Submap grid string is alphabetic row string followed by numeric column string
    // Row labels are A-Z, AA-AZ, BA-BZ, etc. Column labels are numbers
    function submapGridString(row, col) {
        var rowString;
        if (row < 26) rowString = String.fromCharCode(65+row);
        else rowString = String.fromCharCode(64+Math.floor(row/26)) + String.fromCharCode(65+Math.floor(row % 26));
        return rowString + (col + 1);
    }

    module.exports.hex2RGB = hex2RGB;
    module.exports.dec2hex = dec2hex;
    module.exports.colorTuple2Hex = colorTuple2Hex;
    module.exports.getDateTime = getDateTime;
    module.exports.bufferedTimezone = bufferedTimezone;
    module.exports.instrResource = instrResource;
    module.exports.submapGridString = submapGridString;
});
