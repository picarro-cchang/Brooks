/*global console, __dirname, require */
/* jshint undef:true, unused:true */

(function () {
    var argv = require('optimist').argv;
    var cjs = require("./public/js/common/canonical_stringify");
    var express = require('express');
    var fs = require('fs');
    var mkdirp = require('mkdirp');
    var newP3ApiService = require('./lib/newP3ApiService');
    var newRptGenService = require('./lib/newRptGenService');
    var newReportGen = require('./lib/newReportGen');
    var newRptGenMonitor = require('./lib/newRptGenMonitor');
    var newRunningTasks = require('./lib/newRunningTasks');
    var newUserJobDatabase = require('./lib/newUserJobDatabase');
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

    console.log("");
    console.log("siteconfig_path: ", siteconfig_path);
    console.log("siteconfig_obj: ", siteconfig_obj);
    console.log("");

    var stringToBoolean = pv.stringToBoolean;
    var newParamsValidator = pv.newParamsValidator;

    var app = express();
    app.set('view engine', 'jade');
    app.set('view options', { layout: true });
    app.set('views', path.join(__dirname, 'views'));
    app.use(express.bodyParser());

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
        var pv, reportGen, result = {}, statusFile, user, workDir;
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

    function handleIndex(req, res) {
        res.render("index",
            {assets: SITECONFIG.assets,
             force: false,
             host: SITECONFIG.proxyhost,
             identity: SITECONFIG.identity,
             port: SITECONFIG.proxyport,
             psys: SITECONFIG.psys,
             qry: req.query,
             site: SITECONFIG.p3site,
             user: req.query.userid || 'demoUser'
        });
    }

    function handleForce(req, res) {
        res.render("index",
            {assets: SITECONFIG.assets,
             force: true,
             host: SITECONFIG.proxyhost,
             identity: SITECONFIG.identity,
             port: SITECONFIG.proxyport,
             psys: SITECONFIG.psys,
             qry: req.query,
             site: SITECONFIG.p3site,
             user: req.query.userid || 'demoUser'
        });
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
        else console.log('Directory ' + REPORTROOT + ' created.');
        rptGenMonitor = newRptGenMonitor(REPORTROOT);
        app.use("/rest/data", express.static(REPORTROOT));
        runningTasks.handleIncompleteTasksOnStartup( function () {
            var port = SITECONFIG.reportport;
            app.listen(port);
            console.log("Report Server listening on port " + port + ". Root directory " + REPORTROOT);
        });
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
