/*global console, __dirname, require */
/* jshint undef:true, unused:true */

(function () {
    var argv = require('optimist').argv;
    var express = require('express');
    var fs = require('fs');
    var httpProxy = require("http-proxy");
    var md5hex = require("./lib/md5hex");
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
    if (siteconfig_obj.hasOwnProperty("reportProxy")) {
        if (siteconfig_obj.reportProxy.hasOwnProperty("host")) {
            SITECONFIG.proxyhost = siteconfig_obj.reportProxy.host;
        }
        if (siteconfig_obj.reportProxy.hasOwnProperty("port")) {
            SITECONFIG.proxyport = siteconfig_obj.reportProxy.port;
        }
    }

    console.log("");
    console.log("siteconfig_path: ", siteconfig_path);
    console.log("siteconfig_obj: ", siteconfig_obj);
    console.log("");

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
        res.send([{ANALYZER: "DEMO2000"}, {ANALYZER: "FCDS2008"},
                  {ANALYZER: "CFADS2274"}, {ANALYZER: "CFADS2276"}]);
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

    app.get(/^(\/|\/getReport\/.*|\/css.*|\/js.*|\/images.*)$/, forwardTheRequest);

    app.listen(SITECONFIG.proxyport);
    logger("Proxy server listening on port: " + SITECONFIG.proxyport);
    logger("Forwarding to port: " + SITECONFIG.reportport);
    logger("DEBUG: " + DEBUG);
})();

