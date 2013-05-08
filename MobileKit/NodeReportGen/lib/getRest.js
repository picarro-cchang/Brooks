/* getRest.js makes a rest call via HTTP or HTTPS */
/*global console, exports, module, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    var http = require("http");
    var https = require("https");
    var url = require("url");
    var _ = require("underscore");
    /****************************************************************************/
    /* getRest:  REST get request                                               */
    /* options: http options object                                             */
    /* onResult: callback which receives the error indicator, a status          */
    /*    code and the response string                                          */
    /****************************************************************************/
    function getRest(options, onResult)
    {
        var err = null;
        var prot;
        options.agent = false;
        // Merge the query key in the options into the URL string
        // console.log("options: " + JSON.stringify(options));
        var restUrl = url.format(options);
        options = url.parse(restUrl);
        if (_.has(options,'protocol')) {
            prot = options.protocol === 'https:' ? https : http;
        }
        else prot = options.port == 443 ? https : http;
        console.log('url: ' + restUrl);
        options.rejectUnauthorized = false;
        var req = prot.request(options, function(res)
        {
            var output = '';
            console.log(options.host + ':' + res.statusCode);
            res.setEncoding('ascii');

            res.on('data', function (chunk) {
                output += chunk;
            });

            res.on('end', function() {
                onResult(null, res.statusCode, output);
            });

            res.on('error', function(e) {
                onResult(e, res.statusCode);
            });
        });

        req.on('error', function(err) {
            onResult(new Error('getRest request error: ' + err.message));
        });

        req.end();
    }
    module.exports = getRest;
});
