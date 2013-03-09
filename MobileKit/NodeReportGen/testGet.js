var https = require("https");
var url = require("url");

/****************************************************************************/
/* getJSON:  REST get request returning JSON object(s)                      */
/* @param options: http options object                                      */
/* @param callback: callback to pass the results JSON object(s) back        */
/****************************************************************************/

var options = url.parse("https://dev.picarro.com/dev/rest/sec/dummy/1.0/Admin?qry=issueTicket&sys=APITEST2&identity=dc1563a216f25ef8a20081668bb6201e&rprocs=%5B%22AnzLogMeta%3AbyEpoch%22%2C%22AnzLog%3AbyPos%22%2C%22AnzLog%3AbyEpoch%22%2C%22AnzLog%3AmakeSwath%22%2C%22AnzMeta%3AbyAnz%22%2C%22AnzLrt%3AgetStatus%22%2C%22AnzLrt%3AbyRow%22%2C%22AnzLrt%3AfirstSet%22%2C%22AnzLrt%3AnextSet%22%2C%22AnzLog%3AbyGeo%22%5D");
var req = https.request(options, function(res) {
    var output = '', err = null;
    console.log(options.host + ':' + res.statusCode);
    res.setEncoding('utf8');

    res.on('data', function (chunk) {
        output += chunk;
    });

    res.on('end', function() {
        var obj = {};
        try {
            obj = JSON.parse(output);
            console.log("output: " + JSON.stringify(obj));
        }
        catch (e) {
            err = new Error(e);
            console.log("error: " + err);
        }
    });    
});
req.end();

/*
    dev.picarro.com:500")

    console.log("rest::getJSON");
    var err = null;
    var prot;
    console.log(url.format(options));
    if (_.has(options,'protocol')) {
        prot = options['protocol'] === 'https:' ? https : http;
    }
    else prot = options.port == 443 ? https : http;
    var req = prot.request(options, function(res)
    {
        var output = '';
        console.log(options.host + ':' + res.statusCode);
        res.setEncoding('utf8');

        res.on('data', function (chunk) {
            output += chunk;
        });

        res.on('end', function() {
            console.log("output: " + output);
            var obj = {};
            try {
                obj = JSON.parse(output);
            }
            catch (e) {
                err = new Error(e);
            }
            onResult(err, res.statusCode, obj);
        });

        res.on('error', function(e) {
            onResult(e);
        });
    });

    req.on('error', function(err) {
        onResult(err);
    });

    req.end();
};
*/
