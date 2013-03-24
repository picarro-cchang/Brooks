// newReportGen.js
/*global console, exports, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var events = require('events');
    var fs = require('fs');
    var getSubDirs = require('./dirUtils').getSubDirs;
    var getTicket = require('./md5hex');
    var GLOBALS = require('./rptGenGlobals');
    var mkdirp = require('mkdirp');
    var newAnalysesDataFetcher = require('./newAnalysesDataFetcher');
    var newFovsDataFetcher = require('./newFovsDataFetcher');
    var newPathsDataFetcher = require('./newPathsDataFetcher');
    var newPeaksDataFetcher = require('./newPeaksDataFetcher');
    var newRptGenService = require('./newRptGenService');
    var newReportMaker = require('./newReportMaker');
    var path = require('path');
    var rptGenStatus = require('../public/js/common/rptGenStatus');
    var sf = require('./statusFiles');
    var ts = require('./timeStamps');
    var util = require('util');
    var _ = require('underscore');

    var rptGenService = newRptGenService({"rptgen_url": "http://localhost:5300"});

    /****************************************************************************/
    /*  Report Generation                                                       */
    /****************************************************************************/

    function ReportGen(reportDir, p3ApiService, contents) {
        events.EventEmitter.call(this); // Call the constructor of the superclass
        this.reportDir = reportDir;
        this.contents = contents;
        this.instructions = null;
        this.p3ApiService = p3ApiService;
        this.ticket = null;
        this.request_ts = null;
        this.submit_key = {};
    }

    util.inherits(ReportGen, events.EventEmitter);

    ReportGen.prototype.run = function(params, callback) {
        // Parse the contents into an object to verify it is syntactically valid JSON
        var instrDir, instrFname;
        var that = this;
        try {
            this.instructions = JSON.parse(this.contents);
        }
        catch (err) {
            callback(new Error("Instructions are not in valid JSON notation"));
            return;
        }
        this.ticket = getTicket(this.contents);
        this.request_ts = ts.msUnixTimeToTimeString(ts.getMsUnixTime());
        instrDir = path.join(this.reportDir,this.ticket);
        instrFname = path.join(instrDir, "instructions.json");

        function handleInstructions(instrDir, instrFname, contents) {
            // We have a directory for each instructions file, whose name is gven by the MD5 hash
            //  of the instructions (called the "ticket"). This creates the directory, if needed.
            // The function "startNewRun" is called only if we have to do the instructions.

            fs.exists(instrDir, function (exists) {
                if (exists) {
                    // If the ticket directory already exists, the instructions file there
                    //  must match the contents. Otherwise an unrecoverable hash collision
                    //  has taken place
                    fs.readFile(instrFname, "ascii", function (err, data) {
                        if (err) callback(err);
                        else if (data !== contents) callback(new Error("MD5 hash collision in instructions"));
                        else {
                            if (params["force"]) startNewRun();
                            else checkForPreviousRuns();
                        }
                    });
                }
                else {
                    // Create the ticket directory and the instructions file
                    mkdirp(instrDir, null, function (err) {
                        if (err) callback(err);
                        else {
                            fs.writeFile(instrFname, contents, "ascii", function (err) {
                                if (err) callback(err);
                                else startNewRun();
                            });
                        }
                    });
                }
            });
        }

        function checkForPreviousRuns() {
            getSubDirs(instrDir, function (err, subdirs) {
                if (err) callback(err);
                if (subdirs.length > 0) {
                    var lastSubdir = subdirs[subdirs.length - 1];
                    var start_ts = ts.msUnixTimeToTimeString(parseInt(lastSubdir,10));
                    var statusFile = path.join(instrDir, lastSubdir, "status.dat");
                    // Fetch the status from the subdirectory
                    sf.readStatus (statusFile, function (err, result) {
                        if (err) callback(err);
                        else {
                            if (_.isEmpty(result)) {
                                result = {"status": rptGenStatus.NOT_STARTED,
                                          "rpt_contents_hash": that.ticket,
                                          "rpt_start_ts": start_ts};
                            }
                            result.request_ts = that.request_ts;
                            // if not done and not currently running, mark old run as bad and start a new run
                            var bad = result.status < 0;
                            var done = result.status >= rptGenStatus.DONE;
                            var taskKey = that.ticket + '_' + lastSubdir;
                            var running = GLOBALS.runningTasks.isRunning(taskKey);
                            if (!done && !running) {
                                if (bad) startNewRun();
                                else {
                                    sf.writeStatus(statusFile,
                                    {status: rptGenStatus.FAILED, msg:'Server failed during job'}, function (err) {
                                        if (err) callback(err);
                                        else startNewRun();
                                    });
                                }
                            }
                            else callback(null, result);
                        }
                    });
                }
                else startNewRun();
            });
        }

        function startNewRun() {
            var dirName = ts.timeStringAsDirName(that.request_ts);
            var workDir = path.join(instrDir, dirName);
            var taskKey = that.ticket + '_' + dirName;
            var statusFile = path.join(workDir, "status.dat");
            var status;
            // The work directory is specified by a ms time stamp under the instructions
            //  directory
            that.submit_key.hash = that.ticket;
            that.submit_key.time_stamp = that.request_ts;
            that.submit_key.dir_name = dirName;

            mkdirp(workDir, null, function (err) {
                if (err) callback(err);
                else {
                    // Start work here
                    status = {"status": rptGenStatus.IN_PROGRESS,
                              "rpt_contents_hash": that.ticket,
                              "rpt_start_ts": that.request_ts,
                              "request_ts": that.request_ts};
                    sf.writeStatus(statusFile, status, function (err) {
                        if (err) callback(err);
                        else {
                            sf.readStatus(statusFile, function (err, result) {
                                if (err) callback(err);
                                else {
                                    // Indicate that run has started
                                    callback(null, result);
                                    obeyInstructions(taskKey, workDir, statusFile);
                                }
                            });
                        }
                    });
                }
            });
        }
        handleInstructions(instrDir, instrFname, this.contents);


        function obeyInstructions(taskKey, workDir, statusFile) {
            var instructions = that.instructions;
            var p3ApiService = that.p3ApiService;
            var type = instructions["instructions_type"];

            function logCompletion(err) {
                var now = ts.getMsUnixTime();
                var now_ts = ts.msUnixTimeToTimeString(now);
                var duration = 0.001*(now - ts.getMsUnixTime(that.request_ts));
                if (err) that.emit('fail', {"taskKey": taskKey, "workDir": workDir, "instructions_type": type, "stop_ts": now_ts, "duration": duration, "error": err.message});
                else that.emit('success', {"taskKey": taskKey, "workDir": workDir, "instructions_type": type, "stop_ts": now_ts, "duration": duration});
            }

            that.emit('start', {"taskKey": taskKey, "workDir": workDir, "instructions_type": type, "start_ts": that.request_ts});
            console.log("Starting execution of instructions here");
            switch (type) {
                case "ignore":
                    sf.writeStatus(statusFile, {"status": rptGenStatus.DONE}, logCompletion);
                    break;
                case "getAnalysesData":
                    newAnalysesDataFetcher(p3ApiService, instructions, workDir, statusFile, that.submit_key).run(logCompletion);
                    break;
                case "getPathsData":
                    newPathsDataFetcher(p3ApiService, instructions, workDir, statusFile, that.submit_key).run(logCompletion);
                    break;
                case "getFovsData":
                    newFovsDataFetcher(p3ApiService, instructions, workDir, statusFile, that.submit_key).run(logCompletion);
                    break;
                case "getPeaksData":
                    newPeaksDataFetcher(p3ApiService, instructions, workDir, statusFile, that.submit_key).run(logCompletion);
                    break;
                case "makeReport":
                    newReportMaker(rptGenService, instructions, workDir, statusFile, that.submit_key).run(logCompletion);
                    break;
                default:
                    sf.writeStatus(statusFile,{"status": rptGenStatus.FAILED, "msg": "Bad instructions_type"},function (err){
                        logCompletion(new Error("Bad instructions_type"));
                    });
                    break;
            }
        }
    };

    function newReportGen(reportDir, p3ApiService, contents) {
        return new ReportGen(reportDir, p3ApiService, contents);
    }

    module.exports = newReportGen;
});