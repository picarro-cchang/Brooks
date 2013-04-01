/*global console, require */

(function () {
    var argv = require('optimist').argv;
    var cjs = require("./public/js/common/canonical_stringify");
    var events = require('events');
    var express = require('express');
    var fs = require('fs');
    var getRest = require('./lib/getRest');
    var GLOBALS = require('./lib/rptGenGlobals');
    var mkdirp = require('mkdirp');
    var newP3ApiService = require('./lib/newP3ApiService');
    var newReportGen = require('./lib/newReportGen');
    var newRunningTasks = require('./lib/newRunningTasks');
    var path = require('path');
    var pv = require('./public/js/common/paramsValidator');
    var REPORTROOT = argv.r ? argv.r : path.join(__dirname, 'ReportGen');
    var rptGenStatus = require('./public/js/common/rptGenStatus');
    var sf = require('./lib/statusFiles');
    var ts = require('./lib/timeStamps');
    var tzWorld = require('./lib/tzSupport');
    var util = require('util');
    var _ = require('underscore');

    var stringToBoolean = pv.stringToBoolean;
    var newParamsValidator = pv.newParamsValidator;

    var app = express();
    app.set('view engine', 'jade');
    app.set('view options', { layout: true });
    app.set('views', path.join(__dirname, 'views'));
    app.use(express.bodyParser());

    // GLOBALS.csp_url = "https://dev.picarro.com/dev";
    GLOBALS.csp_url = "https://localhost:8081/node";
    GLOBALS.ticket_url = GLOBALS.csp_url + "/rest/sec/dummy/1.0/Admin";
    GLOBALS.identity = "85490338d7412a6d31e99ef58bce5dPM";
    GLOBALS.psys = "SUPERADMIN";

    //GLOBALS.csp_url = "https://localhost:8081/node";
    //GLOBALS.psys = "SUPERADMIN";
    //GLOBALS.identity = "85490338d7412a6d31e99ef58bce5dPM";

    GLOBALS.ticket_url = GLOBALS.csp_url + "/rest/sec/dummy/1.0/Admin";

    GLOBALS.rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath",' +
                     '"AnzMeta:byAnz","AnzLrt:getStatus","AnzLrt:byRow","AnzLrt:firstSet",' +
                     '"AnzLrt:nextSet","AnzLog:byGeo","AnzLog:makeFov"]';

    var p3ApiService = newP3ApiService({"csp_url": GLOBALS.csp_url, "ticket_url": GLOBALS.ticket_url,
            "identity": GLOBALS.identity, "psys": GLOBALS.psys, "rprocs": GLOBALS.rprocs});

    if (p3ApiService instanceof Error) throw p3ApiService;  // Fatal error


    function RptGenMonitor() {
        var that = this;
        this.logMessages = [];
        this.active = {};
        this.logFile = path.join(__dirname, 'ReportGen.log');
        fs.appendFile(this.logFile,'/* RESTARTING */\n', function() {
            setTimeout(function() { that.saveLog(); },5000);
        });
    }

    RptGenMonitor.prototype.saveLog = function () {
        var that = this;
        if (that.logMessages.length > 0) {
            fs.appendFile(that.logFile, that.logMessages.join("\n") + "\n", function () {
                that.logMessages = [];
                setTimeout(function() { that.saveLog(); },5000);
            });
        }
        else setTimeout(function() { that.saveLog(); },5000);
    };

    RptGenMonitor.prototype.monitor = function (rptGen) {
        var that = this;
        rptGen.on('start', function (d) {
            that.logMessages.push('start: ' + JSON.stringify(d));
            that.active[d.workDir] = d.instructions_type;
        });
        rptGen.on('success', function (d) {
            that.logMessages.push('success: ' + JSON.stringify(d));
            delete that.active[d.workDir];
        });
        rptGen.on('fail', function (d) {
            that.logMessages.push('fail: ' + JSON.stringify(d));
            delete that.active[d.workDir];
        });
    };

    var rptGenMonitor = new RptGenMonitor();
    GLOBALS.runningTasks  = newRunningTasks(REPORTROOT);

    function handleTz(req, res) {
        var tz = req.query["tz"] || "GMT";
        var timeStrings = []; // "2012-03-11 09:00:00.000"];
        var posixTimes = [];
        if (req.query.timeStrings) {
            req.query.timeStrings.forEach(function (t) {
                var p;
                posixTimes.push(p = tzWorld(t.replace(/\s+/," "),tz));
                timeStrings.push(tzWorld(+p,"%F %T%z (%Z)",tz));
            });
        }
        else if (req.query.posixTimes) {
            req.query.posixTimes.forEach(function (p) {
                posixTimes.push(+p);
                timeStrings.push(tzWorld(+p,"%F %T%z (%Z)",tz));
            });
        }
        res.send({"timeStrings": timeStrings, "posixTimes": posixTimes, "tz": tz});
    }

    function handleRptGen(req, res) {
        var pv, reportGen, result = {}, statusFile, workDir;
        result = _.extend(result, req.query);
        // console.log("req.query: " + JSON.stringify(req.query));
        // Handle submission of instructions file, requests for status, and retrieval of results
        switch (req.query["qry"]) {
        case "submit":
            // Validate the parameters of the request
            pv = newParamsValidator(req.query,
                [{"name": "contents", "required": true, "validator": "string"},
                 {"name": "force", "required": false, "validator": "boolean", "default_value": false,
                  "transform": stringToBoolean }]);
            if (pv.ok()) {
                reportGen = newReportGen(REPORTROOT, p3ApiService, pv.get("contents"));
                rptGenMonitor.monitor(reportGen);
                GLOBALS.runningTasks.monitor(reportGen);
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
        default:
            res.send(_.extend(result,{"error": "RptGen: Unknown or missing qry"}));
            break;
        }
    }

    function handleGetReport(req, res) {
        var qry = req.query;
        var hash = req.params.hash;
        var ts = req.params.ts;
        res.render("getReport", {qry: qry, hash: hash, ts:ts});
    }

    function handleDownload(req, res) {
        var filename = req.param("filename");
        var content = req.param("content");
        content = cjs(JSON.parse(content),null,2);
        // content = content.replace(/(\r\n|\r|\n)/g,'\n');
        res.attachment(filename);
        res.end(content);
    }

    app.get("/", function(req, res) {
        res.render("index");
    });

    app.get("/rest/RptGen", handleRptGen);

    app.get("/rest/tz", handleTz);

    app.post("/rest/download", handleDownload);

    app.get("/getReport/:hash/:ts", handleGetReport);

    app.get("/checkPdfConvert", function(req, res) {
        res.render("checkPdfConvert");
    });

    /*
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
        app.use("/rest/data", express.static(REPORTROOT));
        GLOBALS.runningTasks.handleIncompleteTasksOnStartup( function () {
            var port = 5300;
            app.listen(port);
            console.log("Report Server listening on port " + port + ". Root directory " + REPORTROOT);
        });
    });
})();
