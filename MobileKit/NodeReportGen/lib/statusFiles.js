/* statusFiles.js supports storage of status information for instruction processing in files */
/*global exports, require */

// Status information is stored as a JavaScript object which is made up
//  by merging dictionaries stored on successive lines in a status file in
//  compact JSON notation (no newlines for a stringified object)
if (typeof define !== 'function') { var define = require('amdefine')(module); }

var writeFlags = {};
var saveQueues = {};

define(function(require, exports, module) {
	'use strict';
	var fs = require('fs');
	var _ = require('underscore');

    function readStatus(filename, callback) {
        var maxLoops = 20;
        var waitForFlag = function () {
            if ((!writeFlags.hasOwnProperty(filename)) || writeFlags[filename]) {
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
            else {
                maxLoops -= 1;
                if (maxLoops >= 0) setTimeout(waitForFlag, 100);
                else callback(new Error("Waited too long for readStatus to complete: " + filename));
            }
        };
        waitForFlag();
    }

    // Write status (in object) to the specified filename by enqueueing a 
    //  request to write onto a saveQueue and returning without waiting 
    //  for the append to disc  to finish. A writeFlag is associated with
    //  each file. This flag is true when the arrival of new data requires
    //  a write to disc to take place by calling "next". It is false while 
    //  the recursive function "next" has been called and is busy clearing
    //  out the saveQueue by writing the entries to disc via asynchronous 
    //  calls to appendFile.

    function writeStatus(filename, object) {
        if (!writeFlags.hasOwnProperty(filename)) {
            writeFlags[filename] = true;
            saveQueues[filename] = [];
        }
        saveQueues[filename].push(JSON.stringify(object) + "\n");
        if (writeFlags[filename]) {
            writeFlags[filename] = false;
            next(filename);
        }
    }

    function next(filename) {
        if (saveQueues[filename].length > 0) {
            var r = saveQueues[filename].shift();
            fs.appendFile(filename, r, function(err) {
                if (err) {
                    console.log('Error writing to status file ' + filename);
                }
                else if (saveQueues[filename].length > 0) next(filename);
                else {
                    writeFlags[filename] = true;
                }
            });
        }
        else {
            writeFlag[filename] = true;
        }
    }

    exports.readStatus = readStatus;
    exports.writeStatus = writeStatus;
});
