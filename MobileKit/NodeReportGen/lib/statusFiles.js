/* statusFiles.js supports storage of status information for instruction processing in files */
/*global exports, require */

// Status information is stored as a JavaScript object which is made up
//  by merging dictionaries stored on successive lines in a status file in
//  compact JSON notation (no newlines for a stringified object)

(function() {
	'use strict';
	var fs = require('fs');
	var _ = require('underscore');

    function readStatus(filename, callback) {
        var result = {};
        fs.readFile(filename, "ascii", function (err, data) {
            if (err) callback(err);
            else {
                data.split("\n").forEach(function (line) {
                    try {
                        result = _.extend(result, JSON.parse(line));
                    }
                    catch (e) {}  // Ignore JSON parse errors
                });
                callback(null, result);
            }
        });

    }

    function writeStatus(filename, object, callback) {
        fs.appendFile(filename, JSON.stringify(object) + "\n", callback);
    }

    exports.readStatus = readStatus;
    exports.writeStatus = writeStatus;
})();
