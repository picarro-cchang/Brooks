/* newFovsDataFetcher.js creates an object to get path data from P3 into a
    work directory. */
/*global console, exports, module, process, require */

(function() {
	'use strict';
    var events = require('events');
    var fs = require('fs');
    var gh = require('./geohash');
    var jf = require('./jsonfiles');
    var newN2i = require('./newNamesToIndices');
    var newP3LrtFetcher = require('./newP3LrtFetcher');
    var newSerializer = require('./newSerializer');
    var rptGenStatus = require('./rptGenStatus');
    var sf = require('./statusFiles');
    var sis = require('./surveyorInstStatus');
    var path = require('path');
    var pv = require('./paramsValidator');
    var ts = require('./timeStamps');
    var util = require('util');
    var _ = require('underscore');

    var newParamsValidator = pv.newParamsValidator;
    var latlngValidator = pv.latlngValidator;
    var validateListUsing = pv.validateListUsing;

    function FovsDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key) {
        events.EventEmitter.call(this); // Call the constructor of the superclass
        this.p3ApiService = p3ApiService;
        this.instructions = instructions;
        this.workDir = workDir;
        this.statusFile = statusFile;
        this.submit_key = submit_key;
        this.norm_instr = null;
        this.pathParams = {};
        this.surveys = newN2i();
        this.filenames = {};
        this.fovError = null;
        this.fovPending = 0;
    }

    util.inherits(FovsDataFetcher, events.EventEmitter);

    function formatNumberLength(num, length) {
        // Zero pads a number to the specified length
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }

    function runValidator(run) {
        var rpv = newParamsValidator(run,
            [{"name": "analyzer", "required":true, "validator": "string"},
              {"name": "startEtm", "required":true, "validator": "number" },
              {"name": "endEtm", "required":true, "validator": "number" },
              {"name": "stabClass", "required":false, "validator": /[0-9A-F*]/, "default_value":"*" }
            ]);
        return rpv.validate();
    }

    FovsDataFetcher.prototype.run = function (callback) {
        var that = this;
        // Path segment types
        var NORMAL = 0, ANALYZING = 1,  INACTIVE = 2, BADSTATUS = 3;
        var INSTMGR_STATUS_MASK = 0xFFFF, INSTMGR_STATUS_GOOD = 0x3C3;

        var ipv = newParamsValidator(that.instructions,
            [{"name": "swCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "neCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "fovMinAmp", "required": false, "validator": "number", "default_value": 0.03},
             {"name": "fovMinLeak", "required": false, "validator": "number", "default_value": 1.0},
             {"name": "fovNWindow", "required": false, "validator": "number", "default_value": 10},
             {"name": "runs", "required":true, "validator": validateListUsing(runValidator)}]);

        if (ipv.ok()) {
            that.norm_instr = ipv.validate().normValues;
            processRuns(function (err) {
                if (err) {
                    sf.writeStatus(that.statusFile,
                        {"status": rptGenStatus.FAILED,"msg": err.message },
                        function () { callback(err); });
                }
                else {
                    sf.writeStatus(that.statusFile, {"status": rptGenStatus.DONE}, function(err) {
                        if (err) callback(err);
                        else callback(null);
                    });
                }
            });
        }
        else {
            sf.writeStatus(that.statusFile, {"status": rptGenStatus.BAD_PARAMETERS,
                "msg": ipv.errors() }, function (err) {
                callback(new Error(ipv.errors()));
            });
        }

        function getMetadata(surveys,done) {
            // Sequentially fetch metadata for all surveys
            var meta = [];
            var index = [];
            for (var i=0; i<_.keys(surveys).length; i++) index.push(i);

            function next() {
                if (index.length > 0) {
                    var s = surveys[index.shift()];
                    console.log('Fetching metadata for ' + s);
                    var p3Params = {'alog': s, 'logtype': 'dat', 'qry': 'byEpoch', 'limit':1};
                    that.p3ApiService.get("gdu", "1.0", "AnzLogMeta", p3Params, function (err, result) {
                        if (err) done(err);
                        else {
                            meta.push(_.omit(result[0],'docmap'));
                            process.nextTick(next);
                        }
                    });
                }
                else done(null, meta);
            }
            next();
        }

        function writeKeyFile(done) {
            var surveys = that.surveys.getAllNames();
            getMetadata(surveys, function (err, meta) {
                if (err) done(err);
                else {
                    var runs = {};
                    that.norm_instr.runs.forEach(function (r, i) {
                        runs[i] = r;
                    });
                    var records = [];
                    var names = _.keys(that.filenames);
                    names.sort();
                    names.forEach(function (file) {
                        records.push(that.filenames[file]);
                    });
                    var result = JSON.stringify({"INSTRUCTIONS_TYPE": "getFovsData",
                                                 "SUBMIT_KEY": that.submit_key,
                                                 "INSTRUCTIONS": that.norm_instr,
                                                 "OUTPUTS": {
                                                     "SURVEYS": surveys,
                                                     "RUNS": runs,
                                                     "FILES": names,
                                                     "FILE_RECORDS": records,
                                                     "META": meta,
                                                     "TYPES": {"NORMAL": NORMAL,
                                                               "ANALYZING": ANALYZING,
                                                               "INACTIVE": INACTIVE,
                                                               "BADSTATUS": BADSTATUS},
                                                     "HEADINGS": {"E": "EDGE",
                                                                  "R": "ROW",
                                                                  "P": "PATH",
                                                                  "T":"TYPE"}
                                                 }},null,2);
                    fs.writeFile(path.join(that.workDir,"key.json"),result,function (err) {
                        if (err) done(err);
                        else done(null);
                    });
                }
            });
        }

        function closePathFiles(done) {
            var pending = 0;
            _.keys(that.filenames).forEach(function (fname) {
                pending += 1;
                jf.closeJson(path.join(that.workDir,fname), function (err) {
                    if (err) done(err);
                    else {
                        pending -= 1;
                        if (pending === 0) done(null);
                    }
                });
            });
        }

        function processRuns(done) {
            // Serially process runs using processRun on each
            var params = that.norm_instr;
            initializePath();
            function next() {
                processRun(function (err) {
                    if (err) done(err);
                    else {
                        that.pathParams.runIndex += 1;
                        if (that.pathParams.runIndex<params.runs.length) process.nextTick(next);
                        else postProcess(done);
                    }
                });
            }
            next();
        }

        function processRun(done) {
            if (that.fovError) done(that.fovError);
            else {
                // Process the run specified by that.pathParams.runIndex
                var params = that.norm_instr;
                var runIndex = that.pathParams.runIndex;
                var run = params.runs[runIndex];
                var analyzer = run.analyzer;
                var startEtm = run.startEtm;
                var endEtm = run.endEtm;
                var swCorner = gh.decodeToLatLng(params.swCorner);
                var neCorner = gh.decodeToLatLng(params.neCorner);
                // Do the LRT
                console.log("Processing run: " + runIndex);
                var lrtParams = {'anz':analyzer, 'startEtm':startEtm, 'endEtm':endEtm,
                                 'minLng':swCorner[1], 'minLat':swCorner[0],
                                 'maxLng':neCorner[1], 'maxLat':neCorner[0],
                                 'qry': 'byEpoch', 'forceLrt':false,
                                 'resolveLogname':true, 'doclist':false,
                                 'limit':'all', 'rtnFmt':'lrt'};
                var p3LrtFetcher = newP3LrtFetcher(that.p3ApiService, "gdu", "1.0", "AnzLog", lrtParams);
                var ser = newSerializer(p3LrtFetcher);
                ser.on('data', function (data) {
                    onRunData(runIndex, data, function (err) {
                        if (err) done(err);
                        else ser.acknowledge();
                    });
                });
                ser.on('end', function() {
                    onRunEnd(runIndex, function (err) {
                        if (err) done(err);
                        else done(null);
                    });
                });
                ser.on('error', function (err) {
                    onRunError(err, function (e) {
                        done(e);
                    });
                });
                p3LrtFetcher.run();
            }
        }

        function postProcess(done) {
            // Poll for completion of fov processing then write out key file
            function next() {
                if (that.fovError) done(that.fovError);
                else {
                    if (that.fovPending > 0) setTimeout(next,1000);
                    else {
                        writeKeyFile(function (err) {
                            if (err) done(err);
                            else closePathFiles(done);
                        });
                    }
                }
            }
            next();
        }

        // We store paths keyed by run index and survey index
        //  in pathBuffers until it is time to write them out
        //  to files

        // The surveys correspond to the lognames in the database
        function initializePath() {
            that.pathParams.runIndex = 0;
            that.pathParams.pType = NORMAL;
            that.pathParams.surveyIndex = null;
            that.pathParams.pathBuffers = {};
            that.pathParams.fovProcessors = {};
        }

        function updatePathType(mask, instStatus) {
            // Determine type of path from valve mask and instrument status
            var pType = that.pathParams.pType;
            var imask = Math.round(mask);
            if ((instStatus & sis.INSTMGR_STATUS_MASK) != sis.INSTMGR_STATUS_GOOD) {
                pType = BADSTATUS;
            }
            else if (Math.abs(mask - imask) < 1.0e-4) {
                if (imask & 1) pType = ANALYZING;
                else if (imask & 16) pType = INACTIVE;
                else pType = NORMAL;
            }
            that.pathParams.pType = pType;
            return pType;
        }

        function onRunData(runIndex, data, done) {
            var params = that.norm_instr;
            var maxLoops = 100;
            function next() {
                var nLoops = (data.length > maxLoops) ? maxLoops : data.length;
                for (var i=0; i<nLoops; i++) {
                    var m = data.shift().document;
                    var fit  = _.isUndefined(m.GPS_FIT)   ? 1 : m.GPS_FIT;
                    var mask = _.isUndefined(m.ValveMask) ? 0 : m.ValveMask;
                    var row  = m.row;
                    var instStatus = m.INST_STATUS;
                    var surveyName = _.isUndefined(m.LOGNAME) ? "" : m.LOGNAME;

                    var surveyIndex = that.surveys.getIndex(surveyName);
                    var pathType = updatePathType(mask, instStatus);
                    var runIndex = that.pathParams.runIndex;
                    if (fit >= 1) {
                        var pos = gh.encodeGeoHash(m.GPS_ABS_LAT, m.GPS_ABS_LONG);
                        var result = JSON.stringify({"R": row, "P": pos, "T": pathType});
                        if (!_.has(that.pathParams.pathBuffers, runIndex)) {
                            that.pathParams.pathBuffers[runIndex] = {};
                            that.pathParams.fovProcessors[runIndex] = {};
                        }
                        if (!_.has(that.pathParams.pathBuffers[runIndex],surveyIndex)) {
                            that.pathParams.pathBuffers[runIndex][surveyIndex] = [];
                            var p = that.pathParams.fovProcessors[runIndex][surveyIndex] =
                                { "processor": new FovProcessor(that.p3ApiService,surveyName,surveyIndex,
                                    runIndex,params,params.runs[runIndex].stabClass,that.workDir),
                                  "rows":[] };
                            p.processor.on('error', onFovError);
                            p.processor.on('end', onFovEnd);
                            p.processor.start();
                        }
                        that.pathParams.pathBuffers[runIndex][surveyIndex].push(result);
                        that.pathParams.fovProcessors[runIndex][surveyIndex].rows.push(row);
                    }
                }
                if (data.length === 0) done(null);
                else process.nextTick(next);
            }
            next();
        }

        function onRunEnd(runIndex, done) {
            // Write out all the path buffers which are not empty
            var pending = 0;
            _.keys(that.pathParams.fovProcessors[runIndex]).forEach(function (survey) {
                var p = that.pathParams.fovProcessors[runIndex][survey];
                that.fovPending += 1;
                p.processor.writeoutFov(p.rows);
                console.log("RUN END: " + runIndex + " Survey: " + survey + " Rows: " + p.rows.length);
            });
            _.keys(that.pathParams.pathBuffers).forEach(function (run) {
                var pathsInRun = that.pathParams.pathBuffers[run];
                _.keys(pathsInRun).forEach(function (survey) {
                    var p = pathsInRun[survey];
                    if (p.length>0) {
                        var fname = 'path_' + formatNumberLength(survey,5) + "_" +
                                    formatNumberLength(run,5) + '.json';
                        if (fname in that.filenames) {
                            that.filenames[fname] += p.length;
                        }
                        else {
                            that.filenames[fname] = p.length;
                        }
                        pending += 1;
                        jf.appendJson(path.join(that.workDir,fname), p, function (err) {
                            if (err) done(err);
                            else {
                                pending -= 1;
                                if (pending === 0) {
                                    that.pathParams.pathBuffers = [];
                                    done(null);
                                }
                            }
                        });
                    }
                });
            });
        }

        function onRunError(err, done) {
            done(err);
        }

        function onFovError(err) {
            that.fovError = err;
        }

        function onFovEnd(fname, records) {
            if (fname) {
                that.filenames[fname] = records;
            }
            that.fovPending -= 1;
        }
    };

    /* When an FovProcessor is made, start the makeFov long running task. Subsequently,
    once we know the set of points at which the field of view is required, wait until 
    the long running task is complete and then fetch the points by row. The results are
    written into fov_survey_run.json files. */

    function FovProcessor(p3Service,surveyName,surveyIndex,runIndex,params,stabClass,workDir) {
        events.EventEmitter.call(this); // Call the constructor of the superclass
        this.p3Service = p3Service;
        this.surveyName = surveyName;
        this.surveyIndex = surveyIndex;
        this.runIndex = runIndex;
        this.stabClass = stabClass;
        this.fovMinAmp = params.fovMinAmp;
        this.fovMinLeak = params.fovMinLeak;
        this.fovNWindow = params.fovNWindow;
        this.lrt_parms_hash = null;
        this.lrt_start_ts = null;
        this.lrt_status = null;
        this.lrt_count = null;
        this.noFov = true;
        this.workDir = workDir;
    }

    util.inherits(FovProcessor, events.EventEmitter);

    FovProcessor.prototype.start = function () {
        var self = this;
        if (self.surveyName.indexOf("DataLog_User_Minimal") >= 0) {
            var lrtParams = {'alog':self.surveyName, 'stabClass':self.stabClass, 'qry':'makeFov',
                             'minAmp':self.fovMinAmp, 'minLeak': self.fovMinLeak,
                             'nWindow':self.fovNWindow};
            self.noFov = false;
            self.p3Service.get("gdu", "1.0", "AnzLog", lrtParams, function (err, result) {
                if (err) self.emit("error", err);
                else {
                    if (result["lrt_start_ts"] === result["request_ts"]) {
                        console.log("This is a new request, made at " + result["request_ts"]);
                    }
                    else {
                        console.log("This is a duplicate of a request made at " + result["lrt_start_ts"]);
                    }
                    self.lrt_status = result["status"];
                    self.lrt_parms_hash = result["lrt_parms_hash"];
                    self.lrt_start_ts = result["lrt_start_ts"];
                    console.log("MAKEFOV P3Lrt Status: " + self.lrt_status + self.lrt_parms_hash + '/' + self.lrt_start_ts);
                }
            });
            console.log("NEW FOVPROCESSOR: " + self.surveyName + " " + self.surveyIndex + " " + self.runIndex +
                " " + self.fovMinAmp + " " + self.stabClass);
        }
    };

    FovProcessor.prototype.writeoutFov = function (rows) {
        rows = rows.slice(0);
        var self = this;
        if (self.noFov) self.emit("end");
        else pollUntilDone();

        // Poll for completion of fov processing task, then fetch the specified rows, taking
        //  into account the nWindow parameter
        function pollUntilDone() {
            if (!self.lrt_parms_hash) setTimeout(pollUntilDone,5000);
            else {
                // Always make at least one call to getStatus so we know the number of rows in the result
                var params = {'prmsHash': self.lrt_parms_hash, 'startTs':self.lrt_start_ts, 'qry': 'getStatus'};
                self.p3Service.get("gdu", "1.0", "AnzLrt", params, function (err, result) {
                    if (err) self.emit("error", err);
                    else {
                        self.lrt_status = result["status"];
                        self.lrt_count = result["count"];
                        console.log("P3Lrt Status: " + self.lrt_status);
                        if (self.lrt_status === rptGenStatus.DONE) fetchData();
                        else if (self.lrt_status < 0 || self.lrt_status > rptGenStatus.DONE) self.emit("error", new Error("Failure status" + self.lrt_status));
                        else setTimeout(pollUntilDone,5000);
                    }
                });
            }
        }

        // Get data corresponding to values in rows, offset by nWindow. For efficiency, we get a 
        //  minimum number of records from P3 each time
        function fetchData() {
            var batchSize = 1000;
            var results = [];
            rows.sort(function(x,y) { return x-y; });
            function next() {
                if (rows.length > 0) {
                    var startRow = rows[0] - self.fovNWindow;
                    if (startRow <= 0) startRow = 1;
                    var params = {'prmsHash': self.lrt_parms_hash, 'startTs':self.lrt_start_ts,
                                  'limit': batchSize, 'qry': 'byRow', 'startRow': startRow,
                                  'lrttype': 'lrtfov'};
                    self.p3Service.get("gdu", "1.0", "AnzLrt", params, function (err, result) {
                        if (err) {
                            if (err.message.indexOf("404") >= 0 && err.message.indexOf("9999") >= 0) {
                                while (rows.length > 0 && rows[0] - self.fovNWindow - startRow < batchSize) {
                                    rows.shift();
                                }
                                process.nextTick(next);
                            }
                            else self.emit("error", err);
                        }
                        else {
                            while (rows.length > 0 && rows[0] - self.fovNWindow - startRow < batchSize) {
                                var row = rows.shift();
                                var fovRow = row - self.fovNWindow;
                                var resultRow = fovRow - startRow;
                                if (0 <= resultRow && resultRow < result.length) {
                                    // console.log("Fetching element: " + resultRow + " of " + result.length);
                                    var m = result[resultRow].document;
                                    // console.log("Desired row: " + fovRow + ". Got " + JSON.stringify(m));
                                    var pos = gh.encodeGeoHash(m.GPS_ABS_LAT, m.GPS_ABS_LONG);
                                    var edge = gh.encodeGeoHash(m.GPS_ABS_LAT+m.DELTA_LAT, m.GPS_ABS_LONG+m.DELTA_LONG);
                                    results.push(JSON.stringify({"R": row, "P": pos, "E": edge}));
                                }
                            }
                            console.log("SWATH: " + JSON.stringify(results[results.length-1]));
                            process.nextTick(next);
                        }
                    });
                }
                else {
                    // Data are in results. Write out a fov file and emit "end"
                    console.log("Number of SWATH rows: " + results.length);
                    var fname = 'fov_' + formatNumberLength(self.surveyIndex,5) + "_" +
                                         formatNumberLength(self.runIndex,5) + '.json';
                    jf.appendJson(path.join(self.workDir,fname), results, function (err) {
                        if (err) self.emit("error",err);
                        else self.emit("end", fname, results.length);
                    });
                }
            }
            next();
        }

    };

    function newFovsDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key) {
        return new FovsDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key);
    }
    module.exports = newFovsDataFetcher;

})();
