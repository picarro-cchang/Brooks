
(function () {
    var argv = require('optimist').argv;
    var express = require('express');
    var httpProxy = require("http-proxy");
    var querystring = require("querystring");
    
    var DEBUG = false;
    var DBG = argv.d ? argv.d : '';
    if (DBG === "") {
        DEBUG = false;
    } else {
        DEBUG = true;
    }
    
    var LPORT = argv.l ? argv.l : '3000';
    LPORT = parseInt(LPORT,10);
    
    var FPORT = argv.f ? argv.f : '5300';
    FPORT = parseInt(FPORT,10);
    
    var FHOST = "localhost";
    
    var proxy = new httpProxy.RoutingProxy();
    var app = express();

    var logger = function() {
        var i, len, printMe
        len = arguments.length;
        
        printMe = true;
        
        if (len > 0) {
            if (arguments[len-1] === "debug") {
                if (DEBUG !== true) {
                    printMe = false;
                }
            }
        }
        
        if (printMe === true) {
            var tm = new Date()
            for(i = 0; i < len; i += 1) {
                if (arguments[i] !== "debug") {
                    console.log(tm.toTimeString() + " pCubedForwardSim.js " + tm.getMilliseconds(), "::: ", arguments[i]);
                }
            }
        }
    }
    
    var forwardTheRequest = function(req, res) {
        logger("forwardTheRequest", "debug");
        logger("forwardTheRequest req.url", req.url, "debug");
        
        proxy.proxyRequest(req, res, {
            port: FPORT,
            host: FHOST
        });
    }; // forwardTheRequest
    
    var queryGet = function(req, res, next) {
        logger("queryGet", "debug");
        logger("queryGet req.query", req.query, "debug");
        
        var new_path = "/rest/RptGen";
        new_path += "?" + querystring.stringify(req.query);
        req.url = new_path;
        
        forwardTheRequest(req, res);
    }; // queryGet

    var resourceGet = function(req, res, next) {
        logger("resourceGet", "debug");
        
        var new_path = "/rest/data";
        if (req.params.hasOwnProperty("rident")) {
            logger("resourceGet req.params.rident", req.params.rident, "debug");
            
            new_path += "/" + req.params.rident;
            
            if (req.params.hasOwnProperty("rident2")) {
                logger("resourceGet req.params.rident2", req.params.rident2, "debug");
                
                new_path += "/" + req.params.rident2;
                
                if (req.params.hasOwnProperty("rident3")) {
                    logger("resourceGet req.params.rident3", req.params.rident3, "debug");
                    
                    new_path += "/" + req.params.rident3;
                    
                    if (req.params.hasOwnProperty("rident4")) {
                        logger("resourceGet req.params.rident4", req.params.rident4, "debug");
                        
                        new_path += "/" + req.params.rident4;
                    }
                }
            }
        }
        req.url = new_path;
        
        forwardTheRequest(req, res);
    }; // resourceGet

    app.get('/:site/rest/:svc/:ticket/:ver/:resource', queryGet);
    
    app.get('/:site/rest/:svc/:ticket/:ver/:resource/:rident/:rident2/:rident3/:rident4'
        , resourceGet);

    app.get('/:site/rest/:svc/:ticket/:ver/:resource/:rident/:rident2/:rident3'
        , resourceGet);

    app.get('/:site/rest/:svc/:ticket/:ver/:resource/:rident/:rident2'
        , resourceGet);

    app.get('/:site/rest/:svc/:ticket/:ver/:resource/:rident'
        , resourceGet);

    app.get('/', function(req, res) {
        //throw new Error('How in the world did you get here');
        res.send('Ooooops!!', 500);
    });
    
    app.listen(LPORT);
    logger("pCubedForwardSim Server listening on port: " + LPORT); 
    logger("pCubedForwardSim Server forwarding to port: " + FPORT);
    logger("pCubedForwardSim Server DEBUG: " + DEBUG);
})();

