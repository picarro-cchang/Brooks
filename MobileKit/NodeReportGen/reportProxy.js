/*global console, __dirname, require */
/* jshint undef:true, unused:true */
/*
The client browser accesses a URL on the proxy server to load its HTML and scripts. 

The proxy server provides an authentication layer to protect access to the services of reportServer. In particular, rest 
calls made to the proxy server must be accompanied with a valid ticket. This ticket may be issued by the proxy server in
response to an Admin:issueTicket request. If the ticket is valid, the proxy server passes the request through to the report
server. The proxy server also passes the AnzLogMeta call for finding the list of analyzers to PCubed.
*/
(function () {
    var argv = require('optimist').argv;
    var express = require('express');
    var fs = require('fs');
    var httpProxy = require("http-proxy");
    var md5hex = require("./lib/md5hex");
    var p3nodeapi = require("./lib/p3nodeapi");
    var path = require("path");
    var querystring = require("querystring");

    var DEBUG = false;
    var DBG = argv.d ? argv.d : '';
    if (DBG === "") {
        DEBUG = false;
    } else {
        DEBUG = true;
    }

    var SITECONFIG = {};
    SITECONFIG.reporthost = "localhost";
    SITECONFIG.reportport = 5300;
    SITECONFIG.proxyhost = "localhost";
    SITECONFIG.proxyport = 8300;
    SITECONFIG.p3host = "dev.picarro.com";
    SITECONFIG.p3port = 443;
    SITECONFIG.p3site = "dev";

    var siteconfig_path = argv.s ? argv.s : path.join(__dirname, "site_config_node");
    var siteconfig_data = fs.readFileSync(siteconfig_path, 'utf8');
    var siteconfig_obj = JSON.parse(siteconfig_data);
    if (siteconfig_obj.hasOwnProperty("reportServer")) {
        if (siteconfig_obj.reportServer.hasOwnProperty("host")) {
            SITECONFIG.reporthost = siteconfig_obj.reportServer.host;
        }
        if (siteconfig_obj.reportServer.hasOwnProperty("port")) {
            SITECONFIG.reportport = siteconfig_obj.reportServer.port;
        }
    }
    if (siteconfig_obj.hasOwnProperty("host")) {
        SITECONFIG.p3host = siteconfig_obj.host;
    }
    if (siteconfig_obj.hasOwnProperty("port")) {
        SITECONFIG.p3port = parseInt(siteconfig_obj.port,10);
    }
    if (siteconfig_obj.hasOwnProperty("site")) {
        SITECONFIG.p3site = siteconfig_obj.site;
    }
    if (siteconfig_obj.hasOwnProperty("reportProxy")) {
        if (siteconfig_obj.reportProxy.hasOwnProperty("host")) {
            SITECONFIG.proxyhost = siteconfig_obj.reportProxy.host;
        }
        if (siteconfig_obj.reportProxy.hasOwnProperty("port")) {
            SITECONFIG.proxyport = siteconfig_obj.reportProxy.port;
        }
    }
    if (siteconfig_obj.hasOwnProperty("sys")) {
        SITECONFIG.psys = siteconfig_obj.sys;
    }
    if (siteconfig_obj.hasOwnProperty("identity")) {
        SITECONFIG.identity = siteconfig_obj.identity;
    }

    /*
    console.log("");
    console.log("siteconfig_path: ", siteconfig_path);
    console.log("siteconfig_obj: ", siteconfig_obj);
    console.log("");
    */

    var initArgs = {host: SITECONFIG.p3host,
                    port: SITECONFIG.p3port,
                    site: SITECONFIG.p3site,
                    identity: SITECONFIG.identity,
                    psys: SITECONFIG.psys,
                    rprocs: ["AnzMeta:resource"],
                    svc: "gdu",
                    version: "1.0",
                    resource: "AnzMeta",
                    api_timeout: 30.0,
                    jsonp: false,
                    debug: false};
    var p3AnzMeta = new p3nodeapi.p3NodeApi(initArgs);

    var proxy = new httpProxy.RoutingProxy();
    var app = express();

    var logger = function() {
        var i, len, printMe;
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
            var tm = new Date();
            for(i = 0; i < len; i += 1) {
                if (arguments[i] !== "debug") {
                    console.log(tm.toTimeString() + " pCubedForwardSim.js " + tm.getMilliseconds(), "::: ", arguments[i]);
                }
            }
        }
    };

    var forwardTheRequest = function(req, res) {
        logger("forwardTheRequest", "debug");
        logger("forwardTheRequest req.url", req.url, "debug");

        proxy.proxyRequest(req, res, {
            port: SITECONFIG.reportport,
            host: SITECONFIG.reporthost
        });
    }; // forwardTheRequest

    var currentTicket = '';
    var expires = 0;
    var duration = 120000;    // Tickets last for this long (ms)
    function admin(req, res) {
        var query = req.query;
        if (query.qry === 'issueTicket') {
            if (query.sys && query.identity && query.rprocs) {
                var now = (new Date()).valueOf();
                if (now > expires) {
                    currentTicket = md5hex('' + Math.random());
                    console.log("ISSUE NEW TICKET: " + currentTicket);
                }
                else {
                    console.log("Reissuing ticket: " + currentTicket);
                }
                expires = now + duration;
                res.contentType("application/json");
                res.send(200,{'ticket': currentTicket});
            }
            else {
                res.send(401,'resource error. ' + (new Date()).toUTCString() + ' 9999 ERROR: invalid identity');
            }
        }
    } // testTicket

    function queryGet(req, res, next) {
        logger("queryGet", "debug");
        logger("queryGet req.query", req.query, "debug");
        var new_path;
        var ticket = req.params.ticket;
        if (ticket == currentTicket) {
            if (req.params.resource === "SurveyorRpt") {
                new_path = "/rest/RptGen";
                new_path += "?" + querystring.stringify(req.query);
                req.url = new_path;
                forwardTheRequest(req, res);
                logger("queryGet forward to /rest/RptGen succeeded", "debug");
            }
            else if (req.params.resource === "Utilities" && req.query.qry === "timezone") {
                new_path = "/rest/tz";
                new_path += "?" + querystring.stringify(req.query);
                req.url = new_path;
                console.log('Original', req.query, 'stringified', querystring.stringify(req.query));
                forwardTheRequest(req, res);
                logger("queryGet forward to /rest/tz succeeded", "debug");
            }
            else logger("Unknown query" + req.params.resource + ":" + querystring.stringify(req.query), "debug");
        }
        else {
            res.send(403, 'resource error. ' + (new Date()).toUTCString() + ' 9999 ERROR: invalid ticket');
            logger("queryGet invalid ticket", "debug");
        }
    } // queryGet

    function queryGetNoTicket(req, res, next) {
        logger("queryGetNoTicket", "debug");
        logger("queryGetNoTicket req.query", req.query, "debug");
        console.log("queryGetNoTicket req.query", req.params);
        var new_path;
        if (req.params.resource === "Utilities" && req.params.qry === "tz") {
            new_path = "/rest/tz";
            new_path += "?" + querystring.stringify(req.query);
            req.url = new_path;
            forwardTheRequest(req, res);
            logger("queryGetNoTicket forward to /rest/tz succeeded", "debug");
        }
        else logger("Unknown query" + req.params.resource + ":" + querystring.stringify(req.query), "debug");
    } // queryGetNoTicket


    function resourceGet(req, res, next) {
        logger("resourceGet", "debug");

        var ticket = req.params.ticket;
        if (ticket == currentTicket) {
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
            logger("resourceGet forward succeeded", "debug");
        }
        else {
            res.send(403, 'resource error. ' + (new Date()).toUTCString() + ' 9999 ERROR: invalid ticket');
            logger("resourceGet invalid ticket: " + ticket, "debug");
        }
    } // resourceGet

    function getAnalyzers(req, res) {
        var url = "/all?limit=all";
        var analyzers = [];
        p3AnzMeta.resource(url,
        function (err) {
            console.log('Error retrieving analyzer list: ' + err);
            res.send([]);
        },
        function (status, data) {
            res.send(data);
        });
    }

    app.get('/:site/rest/sec/:ticket/:ver/Admin', admin);

    app.get('/:site/rest/:svc/:ticket/:ver/AnzMeta/all', getAnalyzers);

    app.get('/:site/rest/:svc/:ticket/:ver/:resource', queryGet);

    app.get('/:site/rest/:resource/:qry', queryGetNoTicket);

    app.get('/:site/rest/:svc/:ticket/:ver/:resource/:rident/:rident2/:rident3/:rident4',
            resourceGet);

    app.get('/:site/rest/:svc/:ticket/:ver/:resource/:rident/:rident2/:rident3',
            resourceGet);

    app.get('/:site/rest/:svc/:ticket/:ver/:resource/:rident/:rident2',
            resourceGet);

    app.get('/:site/rest/:svc/:ticket/:ver/:resource/:rident',
            resourceGet);

    app.post('/rest/download', forwardTheRequest);

    app.get(/^(\/|\/force|\/getReport\/.*|\/css.*|\/js.*|\/images.*)$/, forwardTheRequest);

    app.listen(SITECONFIG.proxyport);
    logger("Proxy server listening on port: " + SITECONFIG.proxyport);
    logger("Forwarding to port: " + SITECONFIG.reportport);
    logger("DEBUG: " + DEBUG);
})();

