/*global console, __dirname, require */
/* jshint undef:true, unused:true */
/*
reportServer.js is the node program which:
1) Serves up HTML, CSS and JS for the web pages associated with report generation. The URLs for these are:
    a) / and /force: Produces landing page and dashboard from which jobs are prepared and submitted by the user
    b) /getReport and /getReportLocal: Produce a page with a report. /getReport is
       used by the browser which accesses the report server via the authenticating proxy server whereas /getReportLocal
       is used internally by the reportServer to produce a PDF file via a headless browser.
    
2) Provides rest calls:
    a) /rest/RptGen/submit: submit a report generation instructions file
    b) /rest/RptGen/getStatus: get the status of a report generation job
    c) /rest/RptGen/getDashboard: fetch the dashboard for the specified user
    d) /rest/RptGen/updateDashboard: update the dashboard for the specified user
    e) /rest/tz: provides timezone support
    f) /rest/download: used to download instructions files
    g) /rest/data/...: Used to fetch resources (typically JSON) from the file system

Code for reportServer is contained for the most part in MobileKit/NodeReportGen/lib, with some helpers in 
MobileKit/NodeReportGen/public/js/common.

In order to carry out the jobs, reportServer makes rest requests to PCubed as well as to itself. These are currently done
using newP3ApiService and newRptGenService. We shall later migrate these to p3nodeapi. Rest calls made to itself do not go through
the authenticating proxy server.
*/
(function () {
    var argv = require('optimist').argv;
    var cjs = require("./public/js/common/canonical_stringify");
    var et = require('elementtree');
    var express = require('express');
    var fs = require('fs');
    var md5hex = require('./lib/md5hex');
    var mkdirp = require('mkdirp');
    var newP3ApiService = require('./lib/newP3ApiService');
    var newRptGenService = require('./lib/newRptGenService');
    var newReportGen = require('./lib/newReportGen');
    var newRptGenMonitor = require('./lib/newRptGenMonitor');
    var newRunningTasks = require('./lib/newRunningTasks');
    var newUserJobDatabase = require('./lib/newUserJobDatabase');
    var p3nodeapi = require("./lib/p3nodeapi");
    var path = require('path');
    var pv = require('./public/js/common/paramsValidator');
    var REPORTROOT = argv.r ? argv.r : path.join(__dirname, 'ReportGen');
    var SITECONFIG = require('./lib/siteConfig');
    var rptGenStatus = require('./public/js/common/rptGenStatus');
    var sf = require('./lib/statusFiles');
    var ts = require('./lib/timeStamps');
    var tzWorld = require('./lib/tzSupport');
    var util = require('util');
    var _ = require('underscore');

    SITECONFIG.p3host = "dev.picarro.com";
    SITECONFIG.p3port = 443;
    SITECONFIG.p3site = "dev";
    SITECONFIG.reporthost = "localhost";
    SITECONFIG.reportport = 5300;
    SITECONFIG.proxyhost = "localhost";
    SITECONFIG.proxyport = 8300;
    SITECONFIG.psys = "APITEST2";
    SITECONFIG.identity = "dc1563a216f25ef8a20081668bb6201e";
    SITECONFIG.assets = "/dev/SurveyorRpt";
    SITECONFIG.phantomPath = "";
    SITECONFIG.pdftkPath = "";
    SITECONFIG.pdfZoom = 1.0;
    SITECONFIG.apiKey = "";
    SITECONFIG.clientKey = "";
    SITECONFIG.headerFontSize = "100%";
    SITECONFIG.footerFontSize = "70%";

    var siteconfig_path = argv.s ? argv.s : path.join(__dirname, "site_config_node");
    var siteconfig_data = fs.readFileSync(siteconfig_path, 'utf8');
    var siteconfig_obj = JSON.parse(siteconfig_data);
    // Google maps API key or client key
    if (siteconfig_obj.hasOwnProperty("apiKey")) {
        SITECONFIG.apiKey = siteconfig_obj.apiKey;
    }
    if (siteconfig_obj.hasOwnProperty("clientKey")) {
        SITECONFIG.clientKey = siteconfig_obj.clientKey;
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
    if (siteconfig_obj.hasOwnProperty("reportServer")) {
        if (siteconfig_obj.reportServer.hasOwnProperty("host")) {
            SITECONFIG.reporthost = siteconfig_obj.reportServer.host;
        }
        if (siteconfig_obj.reportServer.hasOwnProperty("port")) {
            SITECONFIG.reportport = parseInt(siteconfig_obj.reportServer.port,10);
        }
        if (siteconfig_obj.reportServer.hasOwnProperty("assets")) {
            SITECONFIG.assets = siteconfig_obj.reportServer.assets;
        }
        if (siteconfig_obj.reportServer.hasOwnProperty("phantomPath")) {
            SITECONFIG.phantomPath = siteconfig_obj.reportServer.phantomPath;
        }
        if (siteconfig_obj.reportServer.hasOwnProperty("pdftkPath")) {
            SITECONFIG.pdftkPath = siteconfig_obj.reportServer.pdftkPath;
        }
        if (siteconfig_obj.reportServer.hasOwnProperty("pdfZoom")) {
            SITECONFIG.pdfZoom = siteconfig_obj.reportServer.pdfZoom;
        }
        if (siteconfig_obj.reportServer.hasOwnProperty("headerFontSize")) {
            SITECONFIG.headerFontSize = siteconfig_obj.reportServer.headerFontSize;
        }
        if (siteconfig_obj.reportServer.hasOwnProperty("footerFontSize")) {
            SITECONFIG.footerFontSize = siteconfig_obj.reportServer.footerFontSize;
        }
    }
    if (siteconfig_obj.hasOwnProperty("reportProxy")) {
        if (siteconfig_obj.reportProxy.hasOwnProperty("host")) {
            SITECONFIG.proxyhost = siteconfig_obj.reportProxy.host;
        }
        if (siteconfig_obj.reportProxy.hasOwnProperty("port")) {
            SITECONFIG.proxyport = parseInt(siteconfig_obj.reportProxy.port,10);
        }
    }
    if (siteconfig_obj.hasOwnProperty("sys")) {
        SITECONFIG.psys = siteconfig_obj.sys;
    }
    if (siteconfig_obj.hasOwnProperty("identity")) {
        SITECONFIG.identity = siteconfig_obj.identity;
    }
    var scheme = (SITECONFIG.p3port === 443) ? "https://" : "http://";
    var p3port = (SITECONFIG.p3port === 80 || SITECONFIG.p3port === 443) ? "" : ":" + SITECONFIG.p3port;

    /*
    console.log("");
    console.log("siteconfig_path: ", siteconfig_path);
    console.log("siteconfig_obj: ", siteconfig_obj);
    console.log("");
    */

    var stringToBoolean = pv.stringToBoolean;
    var newParamsValidator = pv.newParamsValidator;

    var app = express();
    var uploadDir = path.join(REPORTROOT,"uploads");
    app.set('view engine', 'jade');
    app.set('view options', { layout: true });
    app.set('views', path.join(__dirname, 'views'));
    app.use(express.bodyParser({uploadDir: uploadDir}));

    var csp_url = scheme + SITECONFIG.p3host + p3port + '/' + SITECONFIG.p3site; //"https://dev.picarro.com/dev";
    var psys = SITECONFIG.psys;
    var identity = SITECONFIG.identity;

    //csp_url = "https://dev.picarro.com/dev";
    //psys = "APITEST2";
    //identity = "dc1563a216f25ef8a20081668bb6201e";

    //csp_url = "https://localhost:8081/node";
    //psys = "SUPERADMIN";
    //identity = "85490338d7412a6d31e99ef58bce5dPM";

    var ticket_url = csp_url + "/rest/sec/dummy/1.0/Admin";

    var rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath",' +
                     '"AnzMeta:byAnz","AnzLrt:getStatus","AnzLrt:byRow","AnzLrt:firstSet",' +
                     '"AnzLrt:nextSet","AnzLog:byGeo","AnzLog:makeFov"]';

    var p3ApiService = newP3ApiService({"csp_url": csp_url, "ticket_url": ticket_url,
            "identity": identity, "psys": psys, "rprocs": rprocs});

    if (p3ApiService instanceof Error) throw p3ApiService;  // Fatal error

    var proto = (SITECONFIG.reportport === 443) ? "https" : "http";
    var rptGenService = newRptGenService({"rptgen_url": proto + '://' + SITECONFIG.reporthost + ':' + SITECONFIG.reportport});

    var rptGenMonitor;
    var runningTasks = newRunningTasks(REPORTROOT);
    var userJobDatabase = newUserJobDatabase(REPORTROOT);

    var initArgs = {host: SITECONFIG.p3host,
                    port: SITECONFIG.p3port,
                    site: SITECONFIG.p3site,
                    identity: SITECONFIG.identity,
                    psys: SITECONFIG.psys,
                    rprocs: ["Admin:verifyTicket"],
                    svc: "sec",
                    version: "1.0",
                    resource: "Admin",
                    api_timeout: 30.0,
                    jsonp: false,
                    debug: false};
    var p3Admin = new p3nodeapi.p3NodeApi(initArgs);

    function handleTz(req, res) {
        var tz = req.query["tz"] || "GMT";
        var timeStrings = []; // "2012-03-11 09:00:00.000"];
        var posixTimes = [];
        var qTimeStrings = req.query.timeStrings;
        var qPosixTimes = req.query.posixTimes;
        // Convert bare string or time to array of one element
        if (qTimeStrings && !_.isArray(qTimeStrings)) qTimeStrings = [qTimeStrings];
        if (qPosixTimes && !_.isArray(qPosixTimes)) qPosixTimes = [qPosixTimes];
        if (qTimeStrings) {
            qTimeStrings.forEach(function (t) {
                var p;
                posixTimes.push(p = tzWorld(t.replace(/\s+/," "),tz));
                timeStrings.push(tzWorld(+p,"%F %T%z (%Z)",tz));
            });
        }
        else if (qPosixTimes) {
            qPosixTimes.forEach(function (p) {
                posixTimes.push(+p);
                timeStrings.push(tzWorld(+p,"%F %T%z (%Z)",tz));
            });
        }
        res.send({"timeStrings": timeStrings, "posixTimes": posixTimes, "tz": tz});
    }

    function handleRptGen(req, res) {
        var contents, pv, reportGen, result = {}, statusFile, user, workDir;
        result = _.extend(result, req.query);
        // console.log("req.query: " + JSON.stringify(req.query));
        // Handle submission of instructions file, requests for status, and retrieval of results
        switch (req.query["qry"]) {
        case "submit":
            // Validate the parameters of the request
            pv = newParamsValidator(req.query,
                [{"name": "contents", "required": true, "validator": "string"},
                 {"name": "force", "required": false, "validator": "boolean", "default_value": false,
                  "transform": stringToBoolean },
                 {"name": "user", "required": true, "validator": "string"}]);
            if (pv.ok()) {
                reportGen = newReportGen(REPORTROOT, p3ApiService, rptGenService,
                    pv.get("user"), pv.get("contents"), runningTasks);
                rptGenMonitor.monitor(reportGen);
                runningTasks.monitor(reportGen);
                reportGen.run({"force": pv.get("force")}, function (err, r) {
                    if (err) res.send(_.extend(result,{"error": err.message}));
                    else res.send(_.extend(result,r));
                });
            }
            else res.send(_.extend(result,{"error": pv.errors()}));
            break;
        case "getStatus":
            // Validate the parameters of the request
            pv = newParamsValidator(req.query,
                [{"name": "contents_hash", "required": true, "validator": /[0-9a-fA-F]{32}/},
                 {"name": "start_ts", "required": true, "validator": /\d{4}\-\d{2}\-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z/}]);
            if (pv.ok()) {
                // Try to get status from the working directory
                workDir = path.join(REPORTROOT, pv.get("contents_hash"),
                    ts.timeStringAsDirName(pv.get("start_ts")));
                statusFile = path.join(workDir, "status.dat");
                fs.exists(workDir, function (exists) {
                    if (exists) {
                        fs.exists(statusFile, function (exists) {
                            if (exists) {
                                sf.readStatus(statusFile, function (err, status) {
                                    if (err) res.send(_.extend(result,{"error": err.message}));
                                    else res.send(_.extend(result,status));
                                });
                            }
                            else res.send(_.extend(result,{"status": rptGenStatus.NOT_STARTED}));
                        });
                    }
                    else res.send(_.extend(result,{"status": rptGenStatus.TASK_NOT_FOUND, "msg": "getStatus called for unknown task"}));
                });
            }
            else res.send(_.extend(result,{"error": pv.errors()}));
            break;
        case "updateDashboard":
            // Validate the parameters of the request
            pv = newParamsValidator(req.query,
                [{"name": "user", "required": true, "validator": "string"},
                 {"name": "object", "required": true, "validator": "string"}]);
            if (pv.ok()) {
                user = req.query.user;
                var rec = JSON.parse(req.query.object);
                userJobDatabase.updateDatabase(user,'update',rec, function(err) {
                    res.send(_.extend(result,{error: err}));
                });
            }
            else res.send(_.extend(result,{"error": pv.errors()}));
            break;
        case "getDashboard":
            // Validate the parameters of the request
            pv = newParamsValidator(req.query,
                [{"name": "user", "required": true, "validator": "string"}]);
            if (pv.ok()) {
                user = req.query.user;
                userJobDatabase.compressDatabaseAndGetAllData(user, function(err,data) {
                    res.send(_.extend(result, {error:err, dashboard: data}));
                });
            }
            else res.send(_.extend(result,{"error": pv.errors()}));
            break;
        case "stashKml":
            // Use elementTree to parse a KML string (which is first normalized to use Unix line endings). 
            //  If it parses without error, compute the MD5 hash and save the string into a file in a 
            //  subdirectory generated from the MD5 hash
            var ElementTree = et.ElementTree;
            pv = newParamsValidator(req.query,
                [{"name": "contents", "required": true, "validator": "string"}]);
            if (pv.ok()) {
                contents = req.query.contents;
                contents = contents.replace("\r\n","\n").replace("\r","\n");
                try {
                    var start = contents.indexOf("<");
                    if (start > 10 || start < 0) {
                        throw new Error("Cannot find starting element of XML file");
                    }
                    else {
                        et.parse(contents.substr(start));
                        var hash = md5hex(contents);
                        console.log("MD5 Hash: " + hash);
                        res.send(_.extend(result, {hash:hash}));
                    }
                }
                catch (err) {
                    console.log("Error in stashKml" + err.message);
                    res.send(_.extend(result,{error: err.message}));
                }
            }
            else res.send(_.extend(result,{error: pv.errors()}));
            break;
        default:
            res.send(_.extend(result,{error: "RptGen: Unknown or missing qry"}));
            break;
        }
    }

    function handleGetReport(req, res) {
        res.render("getReport",
            {apiKey: SITECONFIG.apiKey,
             assets: SITECONFIG.assets,
             clientKey: SITECONFIG.clientKey,
             hash: req.params.hash,
             host: SITECONFIG.proxyhost,
             identity: SITECONFIG.identity,
             port: SITECONFIG.proxyport,
             psys: SITECONFIG.psys,
             qry: req.query,
             site: SITECONFIG.p3site,
             ts:req.params.ts
        });
    }

    function handleGetReportLocal(req, res) {
        res.render("getReport",
            {apiKey: SITECONFIG.apiKey,
             assets: "/",
             clientKey: SITECONFIG.clientKey,
             hash: req.params.hash,
             host: "",
             identity: "",
             port: "",
             psys: "",
             qry: req.query,
             site: "",
             ts:req.params.ts
        });
    }

    function _index(req, res, force) {
        res.render("index",
            {assets: SITECONFIG.assets,
             force: false,
             host: SITECONFIG.proxyhost,
             identity: SITECONFIG.identity,
             port: SITECONFIG.proxyport,
             psys: SITECONFIG.psys,
             qry: req.query,
             site: SITECONFIG.p3site,
             ticket: req.query.ticket,
             user: req.query.userid || 'demoUser'
        });
    }

    function handleIndex(req, res) {
        if (argv.n) _index(req,res,false);
        else {
            // Verify ticket for validity
            p3Admin.verifyTicket({tkt: req.query.ticket, uid: req.query.userid, rproc: 'gdurpt'},
            function (err) {
                res.send(500, {error: "Error in verify ticket: " + err});
            },
            function (s, result) {
                if (result === "false") res.send(403, {error: "Ticket validation failed"});
                else _index(req,res,false);
            });
        }
    }

    function handleForce(req, res) {
        if (argv.n) _index(req,res,true);
        else {
            // Verify ticket for validity
            p3Admin.verifyTicket({tkt: req.query.ticket, uid: req.query.userid, rproc: 'gdurpt'},
            function (err) {
                res.send(500, {error: "Error in verify ticket: " + err});
            },
            function (s, result) {
                if (result === "false") res.send(403, {error: "Ticket validation failed"});
                else _index(req,res,true);
            });
        }
    }

    function handleDownload(req, res) {
        var filename = req.param("filename");
        var content = req.param("content");
        content = cjs(JSON.parse(content),null,2);
        // content = content.replace(/(\r\n|\r|\n)/g,'\n');
        res.attachment(filename);
        res.end(content);
    }

    app.get("/", handleIndex);

    app.get("/force", handleForce);

    app.get("/getReport/:hash/:ts", handleGetReport);

    app.get("/getReportLocal/:hash/:ts", handleGetReportLocal);

    app.get("/rest/RptGen", handleRptGen);

    app.get("/rest/tz", handleTz);

    app.post("/rest/download", handleDownload);

    app.get("/test/:testName", function(req, res) {
        res.end(req.params.testName);
    });

    app.post("/fileUpload", function(req, res, next) {
        console.log(req.body);
        console.log(req.files);
        if (!_.isEmpty(req.files)) {
            if ("kmlUpload" in req.files) {            
                fs.readFile(req.files.kmlUpload.path,"ascii",function (err,data) {
                    if (err) res.send({name: req.body.file_info, error: err.message});
                    else {
                        fs.unlink(req.files.kmlUpload.path);
                        data = data.replace(/\r\n/g,"\n").replace(/\r/g,"\n");
                        try {
                            var start = data.indexOf("<");
                            if (start > 10 || start < 0) {
                                throw new Error("Cannot find starting element of KML file");
                            }
                            else {
                                data = data.substr(start);
                                et.parse(data);
                                var hash = md5hex(data);
                                var dirName = path.join(REPORTROOT, "kml", hash.substr(0,2), hash);
                                var fname = path.join(dirName, hash + ".kml");
                                console.log("MD5 Hash: " + hash + ", dirName: " + dirName);
                                // Check to see if the file has already been uploaded
                                fs.readFile(fname, "ascii", function (err,oldData) {
                                    if (err) {
                                        console.log("File does not exist");
                                        // Copy the file into a directory with the specified hash
                                        mkdirp(dirName, null, function (err) {
                                            if (err) res.send({name: req.body.file_info, error: err.message});
                                            else {
                                                fs.writeFile(fname, data, "ascii", function (err) {
                                                    if (err) res.send({name: req.body.file_info, error: err.message});
                                                    else {
                                                        res.send({name: req.body.file_info, hash:hash});
                                                    }
                                                });
                                            }
                                        });
                                    }
                                    else {
                                        console.log("File has been found");
                                        if (data !== oldData) throw new Error("Hash collision - should never occur");
                                        else res.send({name: req.body.file_info, hash:hash});
                                    }
                                });
                            }
                        }
                        catch (err) {
                            console.log("Error in KML file upload" + err.message);
                            res.send({name: req.body.file_info, error: err.message});
                        }
                    }
                });
            }
        }
        else res.send({name: req.body.file_info});
    });

    /*
    app.get("/checkPdfConvert", function(req, res) {
        res.render("checkPdfConvert");
    });
    
    app.get("/rest/data/:hash/:ts/report.pdf", function(req, res) {
        // Note: should use a stream here, instead of fs.readFile
        var filename = path.join(REPORTROOT,req.params.hash,req.params.ts,"report.pdf");
        fs.readFile(filename, function(err, data) {
            if(err) {
                res.send("Oops! Couldn't find that file.");
            } else {
                // set the content type based on the file
                res.contentType('application/pdf');
                res.attachment();
                res.send(data);
            }
            res.end();
        });
    });
    */

    app.use(express.compress());

    app.get("/rest/data/:hash/:ts/report.pdf", function(req, res) {
        var filename = path.join(REPORTROOT,req.params.hash,req.params.ts,"report.pdf");
        fs.exists(filename, function (exists) {
            if (exists) {
                var readStream = fs.createReadStream(filename);
                res.contentType('application/octet-stream');
                res.attachment();
                util.pump(readStream, res);
            }
            else {
                res.send("Oops! Couldn't find that file.");
            }
        });
    });

    app.use("/", express.static(__dirname + '/public'));

    mkdirp(REPORTROOT, null, function (err) {
        if (err) console.log(err);
        else {
            mkdirp(uploadDir, null, function (err) {
                if (err) console.log(err);
                else {
                    rptGenMonitor = newRptGenMonitor(REPORTROOT);
                    app.use("/rest/data", express.static(REPORTROOT));
                    runningTasks.handleIncompleteTasksOnStartup( function () {
                        var port = SITECONFIG.reportport;
                        app.listen(port);
                        console.log("Report Server listening on port " + port + ". Root directory " + REPORTROOT);
                    });
                }
            });
        }
    });
    /*
    var http = require('http');
    http.createServer(function(request, response){
        var request_options = {
            host: request.headers['host'].split(':')[0],
            port: SITECONFIG.reportport,
            path: request.url,
            method: request.method
        };
        console.log('request_options', request_options);
        var proxy_request = http.request(request_options, function(proxy_response){
            proxy_response.pipe(response);
            var responseCache = '';
            proxy_response.on('data', function (chunk) {

            });
            response.writeHead(proxy_response.statusCode, proxy_response.headers);
        });
        request.pipe(proxy_request);
    }).listen(SITECONFIG.proxyport);
    */
})();
