/* newAnalysesDataFetcher.js creates an object to get analyses data from P3 into a
    work directory. */
/*global console, exports, module, process, require */

(function() {
	'use strict';
    var fs = require('fs');
    var gh = require('./geohash');
    var jf = require('./jsonFiles');
    var newN2i = require('./newNamesToIndices');
    var newP3LrtFetcher = require('./newP3LrtFetcher');
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

    var DTR = Math.PI/180.0, RTD = 180.0/Math.PI;
    
    function AnalysesDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key) {
        this.p3ApiService = p3ApiService;
        this.instructions = instructions;
        this.workDir = workDir;
        this.statusFile = statusFile;
        this.submit_key = submit_key;
        this.norm_instr = null;
        this.analyses = {};
        this.dataKeys = ['CONC', 'DELTA', 'UNCERTAINTY', 'EPOCH_TIME'];
        this.extraKeys = ['POSITION', 'RUN', 'SURVEY'];
        this.runIndex = 0;
        this.surveys = newN2i();
        this.filenames = {};
    }

    function formatNumberLength(num, length) {
        // Zero pads a number to the specified length
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }

    function n2nan(x) {
        return (x === null) ? NaN : x;
    }

    function runValidator(run) {
        var rpv = newParamsValidator(run,
            [{"name": "analyzer", "required":true, "validator": "string"},
             {"name": "startEtm", "required":true, "validator": "number" },
             {"name": "endEtm", "required":true, "validator": "number" }
            ]);
        return rpv.validate();
    }

    AnalysesDataFetcher.prototype.run = function (callback) {
        var that = this;

        var ipv = newParamsValidator(that.instructions,
            [{"name": "swCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "neCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
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
                    var s = surveys[index.shift()].replace('.analysis','.dat');
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
                    var result = JSON.stringify({"INSTRUCTIONS_TYPE": "getAnalysesData",
                                                 "SUBMIT_KEY": that.submit_key,
                                                 "INSTRUCTIONS": that.norm_instr,
                                                 "OUTPUTS": {
                                                     "SURVEYS": surveys,
                                                     "RUNS": runs,
                                                     "META": meta,
                                                     "FILES": names,
                                                     "FILE_RECORDS": records,
                                                     "HEADINGS": {"D": "DELTA",
                                                                  "C": "CONC",
                                                                  "T": "EPOCH_TIME",
                                                                  "P": "POSITION",
                                                                  "R": "RUN",
                                                                  "S": "SURVEY",
                                                                  "U": "UNCERTAINTY"}
                                                 }},null,2);
                    fs.writeFile(path.join(that.workDir,"key.json"),result,function (err) {
                        if (err) done(err);
                        else done(null);
                    });
                }
            });
        }

        function processRuns(done) {
            initializeAnalyses();
            // Serially process runs using processRun on each
            var params = that.norm_instr;
            function next() {
                processRun(function (err) {
                    if (err) done(err);
                    else {
                        that.runIndex += 1;
                        if (that.runIndex<params.runs.length) process.nextTick(next);
                        else {
                            postProcessAnalyses(function (err) {
                                if (err) done(err);
                                else writeKeyFile(function (err) {
                                    if (err) done(err);
                                    else done(null);
                                });
                            });
                        }
                    }
                });
            }
            next();
        }

        function processRun(done) {
            // Process the run specified by that.runIndex
            var params = that.norm_instr;
            var runIndex = that.runIndex;
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
                             'resolveLogname':true, 'doclist': false,
                             'limit':'all', 'logtype': 'analysis', 'rtnFmt':'lrt'};
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

        function initializeAnalyses() {
            // We store analyses data as arrays to allow for sorting and coalescing
            that.dataKeys.forEach(function (k) {
                that.analyses[k] = [];
            });
            that.extraKeys.forEach(function (k) {
                that.analyses[k] = [];
            });
        }

        function onRunData(data, done) {
            var maxLoops = 100;
            function next() {
                var nLoops = (data.length > maxLoops) ? maxLoops : data.length;
                for (var i=0; i<nLoops; i++) {
                    var m = data.shift().document;
                    var surveyName = _.isUndefined(m.LOGNAME) ? "" : m.LOGNAME;
                    var surveyIndex = that.surveys.getIndex(surveyName);
                    var runIndex = that.runIndex;
                    for (var j=0; j<that.dataKeys.length; j++) {
                        var key = that.dataKeys[j];
                        that.analyses[key].push(n2nan(m[key]));
                    }
                    that.analyses['POSITION'].push(gh.encodeGeoHash(m.GPS_ABS_LAT, m.GPS_ABS_LONG));
                    that.analyses['SURVEY'].push(surveyIndex);
                    that.analyses['RUN'].push(runIndex);
                }
                if (data.length === 0) done(null);
                else process.nextTick(next);
            }
            next();
        }

        function onRunEnd(done) {
            // Write out all the path buffers which are not empty
            done(null);
        }

        function onRunError(err, done) {
            done(err);
        }

        function postProcessAnalyses(done) {
            var result = [];
            var fname = 'analyses.json';

            // Use a permutation array to write out analyses
            var perm = [];
            for (var i=0; i<that.analyses['DELTA'].length; i++) perm[i] = i;

            var maxLoops = 500;
            var empty = true;
            function next() {
                var nLoops = (perm.length > maxLoops) ? maxLoops : perm.length;
                for (var i=0; i<nLoops; i++) {
                    var p = perm.shift();
                    var delta = +(that.analyses['DELTA'][p].toFixed(2));
                    var conc = +(that.analyses['CONC'][p].toFixed(2));
                    var uncertainty = +(that.analyses['UNCERTAINTY'][p].toFixed(2));
                    var epochTime = +(that.analyses['EPOCH_TIME'][p].toFixed(0));
                    var pos = that.analyses['POSITION'][p];
                    var survey = that.analyses['SURVEY'][p];
                    var run = that.analyses['RUN'][p];
                    var row = JSON.stringify({"D": delta,"C": conc,"T": epochTime,"P": pos,
                        "R": run,"S": survey, "U": uncertainty});
                    result.push(row);
                }
                if (!_.isEmpty(result)) {
                    if (fname in that.filenames) {
                        that.filenames[fname] += result.length;
                    }
                    else {
                        that.filenames[fname] = result.length;
                    }
                    jf.appendJson(path.join(that.workDir,fname), result, function (err) {
                        empty = false;
                        result = [];
                        if (err) done(err);
                        else {
                            if (perm.length === 0) {
                                jf.closeJson(path.join(that.workDir,fname), done);
                            }
                            else process.nextTick(next);
                        }
                    });
                }
                else {
                    if (perm.length === 0) {
                        if (!(fname in that.filenames)) that.filenames[fname] = 0;
                        if (empty) jf.emptyJson(path.join(that.workDir,fname), done);
                        else jf.closeJson(path.join(that.workDir,fname), done);
                    }
                }
            }
            next();
        }
    };

    function newAnalysesDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key) {
        return new AnalysesDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key);
    }
    module.exports = newAnalysesDataFetcher;

})();
