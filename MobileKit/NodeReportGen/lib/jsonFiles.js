/* jsonFiles.js allows a list of JSON objects to be written out in chunks. */
/*global exports, module, require */

(function() {
	'use strict';
    var fs = require('fs');
    var _ = require('underscore');

    function appendJson(fileName, jsonStrings, done) {
        if (_.isEmpty(jsonStrings)) done(null);
        else {
            fs.exists(fileName, function (exists) {
                if (exists) {
                    fs.appendFile(fileName, ",\n" + jsonStrings.join(",\n"), function (err) {
                        done(err);
                    });
                }
                else {
                    fs.appendFile(fileName, "[" + jsonStrings.join(",\n"), function (err) {
                        done(err);
                    });
                }
            });
        }
    }

    function closeJson(fileName, done) {
        fs.appendFile(fileName, "]", function (err) {
            done(err);
        });
    }

    function emptyJson(fileName, done) {
        fs.writeFile(fileName, "[]", function (err) {
            done(err);
        });
    }

    exports.appendJson = appendJson;
    exports.closeJson = closeJson;
    exports.emptyJson = emptyJson;
})();
