/* newFovsDataFetcher.js creates an object to get path data from P3 into a
    work directory. */
/*global console, exports, module, process, require */

(function() {
	'use strict';
    var cjs = require('./canonical_stringify');
    var fs = require('fs');
    var gh = require('./geohash');
    var jf = require('./jsonfiles');
    var newN2i = require('./newNamesToIndices');
    var newP3LrtFetcher = require('./newP3LrtFetcher');
    var newRptGenLrtController = require('./newRptGenLrtController');
    var newSerializer = require('./newSerializer');
    var rptGenStatus = require('./rptGenStatus');
    var sf = require('./statusFiles');
    var sis = require('./surveyorInstStatus');
    var path = require('path');
    var pv = require('./paramsValidator');
    var ts = require('./timeStamps');
    var _ = require('underscore');

    var newParamsValidator = pv.newParamsValidator;
    var latlngValidator = pv.latlngValidator;
    var validateListUsing = pv.validateListUsing;

    function FovsDataFetcher(p3ApiService, rptGenService, instructions, workDir, statusFile, submit_key) {
        this.p3ApiService = p3ApiService;
        this.rptGenService = rptGenService;
        this.instructions = instructions;
        this.workDir = workDir;
        this.statusFile = statusFile;
        this.submit_key = submit_key;
        this.norm_instr = null;
        this.pathParams = {};
        this.surveys = newN2i();
        this.filenames = {};
        this.keyDataBySubtask = {};
        this.errorOccured = false;
        this.pending = 0;
    }

    function formatNumberLength(num, length) {
        // Zero pads a number to the specified length
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }

    function extractPathsRequest(instructions) {
        // Extracts the instructions for generating a getPeaksData request
        //  as a canonical JSON string
        var result = {};
        result["instructions_type"] = "getPathsData";
        result["swCorner"] = instructions["swCorner"];
        result["neCorner"] = instructions["neCorner"];
        result["runs"] = [];
        instructions["runs"].forEach(function (run, i) {
            var r = {};
            var ir = instructions["runs"][i];
            r["analyzer"] = ir["analyzer"];
            // TODO: Support timezones in strToEtm
            r["startEtm"] = ir["startEtm"];
            r["endEtm"] = ir["endEtm"];
            result["runs"].push(r);
        });
        return cjs(result,null,2);
    }

    function runValidator(run) {
        var rpv = newParamsValidator(run,
            [ {"name": "analyzer", "required":true, "validator": "string"},
              {"name": "startEtm", "required":true, "validator": "number" },
              {"name": "endEtm", "required":true, "validator": "number" },
              {"name": "stabClass", "required":false, "validator": /[0-9A-F*]/, "default_value":"*" }
            ]);
        return rpv.validate();
    }

    FovsDataFetcher.prototype.run = function (callback) {
        var that = this;
        // Send off getPeaksData request to find the list of alogs for the swaths
        var ipv = newParamsValidator(that.instructions,
            [{"name": "swCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "neCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "fovMinAmp", "required": false, "validator": "number", "default_value": 0.03},
             {"name": "runs", "required":true, "validator": validateListUsing(runValidator)}]);

        if (ipv.ok()) {
            that.norm_instr = ipv.validate().normValues;
            var subtasks = [{"name": "getPathsData", "extractor": extractPathsRequest}];
            that.pending = subtasks.length;
            subtasks.forEach(function (task) {
                var instr = task.extractor(that.norm_instr);
                var lrtCont = newRptGenLrtController(that.rptGenService, "RptGen", {'qry': 'submit', 'contents': instr});
                lrtCont.on('submit', onTaskSubmit(task.name));
                lrtCont.on('end', onTaskEnd(task.name));
                lrtCont.on('error', onTaskError(task.name));
                lrtCont.run();
            });
        }
        else {
            sf.writeStatus(that.statusFile,
                {"status": rptGenStatus.FAILED, "msg": ipv.errors() }, function () {
                    callback(new Error(ipv.errors()));
            });
        }

        function onTaskSubmit(name) {
            return (function (n) {
                return function (submit_key) {
                    console.log("RPT_GEN_lrt_task " + n + " scheduled: " + JSON.stringify(submit_key));
                };
            })(name);
        }

        function onTaskError(name) {
            return (function (n) {
                return function (err) {
                    if (!that.errorOccured) {
                        sf.writeStatus(that.statusFile,
                            {"status": rptGenStatus.FAILED, "msg": "Subtask " +
                                n + ": " +err.message }, function () {
                                callback(err);
                        });
                        that.errorOccured = true;
                    }
                };
            })(name);
        }

        function onTaskEnd(name) {
            return (function (n) {
                return function (submit_key, key_data) {
                    that.keyDataBySubtask[n] = key_data;
                    if (!that.errorOccured) {
                        that.pending -= 1;
                        if (that.pending === 0) {
                            var surveys;
                            console.log("getPathsData job complete for getFovsData");
                            surveys = _.values(that.keyDataBySubtask["getPathsData"]["OUTPUTS"]["SURVEYS"]);
                            processSurveys(surveys, function (err) {
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
                    }
                };
            })(name);
        }

        function processSurveys(surveys, done) {
            var indices = [];
            for (var i=0; i<surveys.length; i++) indices.push(i);
            function next() {
                if (indices.length > 0) {
                    var index = indices.shift();
                    processRuns(surveys[index], function (err) {
                        if (err) done(err);
                        else process.nextTick(next);
                    });
                }
                else {
                    // Close all open FOV files here and write key file
                    done(null);
                }
            }
            next();
        }






/*
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
                    var result = JSON.stringify({"INSTRUCTIONS_TYPE": "getPathsData",
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
                                                     "HEADINGS": {"R": "ROW",
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
                        else {
                            writeKeyFile(function (err) {
                                if (err) done(err);
                                else closePathFiles(done);
                            });
                        }
                    }
                });
            }
            next();
        }

        function processRun(done) {
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
                onRunData(data, function (err) {
                    if (err) done(err);
                    else ser.acknowledge();
                });
            });
            ser.on('end', function() {
                onRunEnd(function (err) {
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

        // We store paths keyed by run index and survey index
        //  in pathBuffers until it is time to write them out
        //  to files

        // The surveys correspond to the lognames in the database
        function initializePath() {
            that.pathParams.runIndex = 0;
            that.pathParams.pType = NORMAL;
            that.pathParams.surveyIndex = null;
            that.pathParams.pathBuffers = {};
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

        function onRunData(data, done) {
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
                        }
                        if (!_.has(that.pathParams.pathBuffers[runIndex],surveyIndex)) {
                            that.pathParams.pathBuffers[runIndex][surveyIndex] = [];
                        }
                        that.pathParams.pathBuffers[runIndex][surveyIndex].push(result);
                    }
                }
                if (data.length === 0) done(null);
                else process.nextTick(next);
            }
            next();
        }

        function onRunEnd(done) {
            // Write out all the path buffers which are not empty
            var pending = 0;
            _.keys(that.pathParams.pathBuffers).forEach(function (run) {
                var pathsInRun = that.pathParams.pathBuffers[run];
                _.keys(pathsInRun).forEach(function (survey) {
                    var p = pathsInRun[survey];
                    if (p.length>0) {
                        var fname = 'path_' + formatNumberLength(run,5) + "_" +
                                    formatNumberLength(survey,5) + '.json';
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
*/

    };

    function newFovsDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key) {
        return new FovsDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key);
    }
    module.exports = newFovsDataFetcher;

})();
