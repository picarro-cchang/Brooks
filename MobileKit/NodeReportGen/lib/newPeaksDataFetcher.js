/* newPeaksDataFetcher.js creates an object to get peaks data from P3 into a
    work directory. */
/*global console, exports, module, process, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    var bs = require("../lib/bisect");
    var fs = require('fs');
    var gh = require('./geohash');
    var jf = require('./jsonFiles');
    var newN2i = require('./newNamesToIndices');
    var newP3LrtFetcher = require('./newP3LrtFetcher');
    var newSerializer = require('./newSerializer');
    var rptGenStatus = require('../public/js/common/rptGenStatus');
    var sf = require('./statusFiles');
    var sis = require('./surveyorInstStatus');
    var path = require('path');
    var pv = require('../public/js/common/paramsValidator');
    var ts = require('./timeStamps');
    var _ = require('underscore');

    var bisect_left = bs.bisect_left;
    var newParamsValidator = pv.newParamsValidator;
    var latlngValidator = pv.latlngValidator;
    var validateListUsing = pv.validateListUsing;

    var DTR = Math.PI/180.0, RTD = 180.0/Math.PI, rEarth = 6371000;

    function PeaksDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key, forceFlag) {
        this.p3ApiService = p3ApiService;
        this.instructions = instructions;
        this.workDir = workDir;
        this.statusFile = statusFile;
        this.submit_key = submit_key;
        this.forceFlag = forceFlag;
        this.norm_instr = null;
        this.peaks = {};
        this.dataKeys = ['CH4', 'AMPLITUDE', 'WIND_DIR_SDEV', 'EPOCH_TIME'];
        this.extraKeys = ['WIND_DIR_MEAN', 'POSITION', 'RUN', 'SURVEY', 'lat', 'lng', 'active'];
        this.runIndex = 0;
        this.surveys = newN2i();
        this.filenames = {};
    }

    function haversine(lng1, lat1, lng2, lat2) {
        /* Calculate the great circle distance between two points
        on the earth (specified in decimal degrees) */
        lng1 = DTR * lng1;
        lat1 = DTR * lat1;
        lng2 = DTR * lng2;
        lat2 = DTR * lat2;
        // haversine formula
        var dlng = lng2 - lng1;
        var dlat = lat2 - lat1;
        var dx = Math.sin(dlng/2);
        var dy = Math.sin(dlat/2);
        var a = dy * dy + Math.cos(lat1) * Math.cos(lat2) * dx * dx;
        var c = 2 * Math.asin(Math.sqrt(a));
        return rEarth * c;
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

    PeaksDataFetcher.prototype.run = function (callback) {
        var that = this;

        var ipv = newParamsValidator(that.instructions,
            [{"name": "swCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "neCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "exclRadius", "required":false, "validator": "number", "default_value": 0.0 },
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
                    var s = surveys[index.shift()].replace('.peaks','.dat');
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
                    // Get number of records in each file, which is currently the value
                    //  in that.filenames, keyed by the names
                    var names = _.keys(that.filenames);
                    names.sort();
                    names.forEach(function (file) {
                        records.push(that.filenames[file]);
                    });
                    var result = JSON.stringify({"INSTRUCTIONS_TYPE": "getPeaksData",
                                                 "SUBMIT_KEY": that.submit_key,
                                                 "INSTRUCTIONS": that.norm_instr,
                                                 "OUTPUTS": {
                                                     "SURVEYS": surveys,
                                                     "RUNS": runs,
                                                     "META": meta,
                                                     "FILES": names,
                                                     "FILE_RECORDS": records,
                                                     "HEADINGS": {"A": "AMPLITUDE",
                                                                  "C": "CH4",
                                                                  "T": "EPOCH_TIME",
                                                                  "P": "POSITION",
                                                                  "R": "RUN",
                                                                  "S": "SURVEY",
                                                                  "W": "WIND_DIR_MEAN",
                                                                  "U": "WIND_DIR_SDEV"}
                                                 }},null,2);
                    fs.writeFile(path.join(that.workDir,"key.json"),result,function (err) {
                        if (err) done(err);
                        else done(null);
                    });
                }
            });
        }

        function processRuns(done) {
            initializePeaks();
            // Serially process runs using processRun on each
            var params = that.norm_instr;
            function next() {
                if (that.runIndex == params.runs.length) {
                    postProcessPeaks(function (err) {
                        if (err) done(err);
                        else writeKeyFile(function (err) {
                            if (err) done(err);
                            else done(null);
                        });
                    });
                }
                else {
                    processRun(function (err) {
                        if (err) done(err);
                        else {
                            that.runIndex += 1;
                            process.nextTick(next);
                        }
                    });
                }
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
                             'qry': 'byEpoch', 'forceLrt':that.forceFlag,
                             'resolveLogname':true, 'doclist': false,
                             'limit':'all', 'logtype': 'peaks', 'rtnFmt':'lrt'};
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

        function initializePeaks() {
            that.peaks = [];
        }

        function onRunData(data, done) {
            var maxLoops = 100;
            function next() {
                var nLoops = (data.length > maxLoops) ? maxLoops : data.length;
                for (var i=0; i<nLoops; i++) {
                    var row = {};
                    var m = data.shift().document;
                    var surveyName = _.isUndefined(m.LOGNAME) ? "" : m.LOGNAME;
                    if (surveyName.indexOf("DataLog_User_Minimal") < 0) continue;
                    var surveyIndex = that.surveys.getIndex(surveyName);
                    var runIndex = that.runIndex;
                    row['lat'] = n2nan(m['GPS_ABS_LAT']);
                    row['lng'] = n2nan(m['GPS_ABS_LONG']);
                    row['valid'] = true;
                    if (!isNaN(row['lat']) && !isNaN(row['lng'])) {
                        for (var j=0; j<that.dataKeys.length; j++) {
                            var key = that.dataKeys[j];
                            row[key] = n2nan(m[key]);
                        }
                        row['WIND_DIR_MEAN'] = RTD*Math.atan2(n2nan(m['WIND_E']),n2nan(m['WIND_N']));
                        row['POSITION'] = gh.encodeGeoHash(row['lat'],row['lng']);
                        row['SURVEY'] = surveyIndex;
                        row['RUN'] = runIndex;
                        that.peaks.push(row);
                    }
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

        function postProcessPeaks(done) {
            var params = that.norm_instr;
            var exclRadius = params.exclRadius;
            var i;

            // First sort peaks by amplitude
            that.peaks.sort(function (j,k) { return (k.AMPLITUDE - j.AMPLITUDE); });

            // Calculate permutation arrays for sorting by latitude and longitude
            //  and the sorted arrays for exclusion radius processing
            if (exclRadius > 0.0) {
                applyExclusion(exclRadius, function () {
                    writeOutData(done);
                });
            }
            else writeOutData(done);
        }

        function applyExclusion(exclRadius, done) {
            var latPerm = [], lngPerm = [];
            var latSort = [], lngSort = [];
            var i, j;

            function neighbors(location) {
                // Returns indices in that.peaks which lie within exclRadius of location
                var closest = [];
                var inRangeLat = {}, inRangeBoth = {};
                var deltaLat = RTD * exclRadius / rEarth;
                var deltaLng = deltaLat / Math.cos(DTR * location.lat);
                var latSort = [], lngSort = [];
                var i, j;
                for (i=0; i<that.peaks.length; i++) {
                    latSort.push(that.peaks[latPerm[i]].lat);
                    lngSort.push(that.peaks[lngPerm[i]].lng);
                }
                // Get points which are close to location in both lat and lng
                i = bisect_left(latSort, location.lat - deltaLat);
                while (i<latSort.length && latSort[i] <= location.lat + deltaLat) {
                    j = latPerm[i];
                    if (that.peaks[j].valid) inRangeLat[j] = true;
                    i += 1;
                }
                i = bisect_left(lngSort, location.lng - deltaLng);
                while (i<lngSort.length && lngSort[i] <= location.lng + deltaLng) {
                    j = lngPerm[i];
                    if (inRangeLat[j]) inRangeBoth[j] = true;
                    i += 1;
                }
                for (var k in inRangeBoth) {
                    if (inRangeBoth.hasOwnProperty(k)) {
                        var dist = haversine(location.lng, location.lat,
                                             that.peaks[k].lng, that.peaks[k].lat);
                        if (dist <= exclRadius) closest.push({"index": +k, "dist": dist});
                    }
                }
                // closest.sort(function(j,k) { return j.dist - k.dist; });
                return closest;
            }

            for (i=0; i<that.peaks.length; i++) {
                latPerm.push(i);
                lngPerm.push(i);
            }
            latPerm.sort(function(j,k) { return that.peaks[j].lat - that.peaks[k].lat; });
            lngPerm.sort(function(j,k) { return that.peaks[j].lng - that.peaks[k].lng; });
            for (i=0; i<that.peaks.length; i++) {
                latSort.push(that.peaks[latPerm[i]].lat);
                lngSort.push(that.peaks[lngPerm[i]].lng);
            }

            // Starting with the peak of highest amplitude, find all other peaks within
            //  exclRadius of this peak, and set their valid flags to false

            // console.log("Before exclusion, number of peaks: " + that.peaks.length);
            var index = [];
            var maxLoops = 50;
            for (i=0; i<that.peaks.length; i++) index.push(i);

            function next() {
                var nLoops = (index.length > maxLoops) ? maxLoops : index.length;
                for (var k=0; k<nLoops; k++) {
                    i = index.shift();
                    if (that.peaks[i].valid) {
                        var nbr = neighbors(that.peaks[i]);
                        // console.log("Neighbors of " + i + JSON.stringify(nbr));
                        for (j=0; j<nbr.length; j++) {
                            if (nbr[j].index > i) that.peaks[nbr[j].index].valid = false;
                        }
                    }
                }
                if (index.length === 0) {
                    var peaksLeft = [];
                    for (i=0; i<that.peaks.length; i++) {
                        if (that.peaks[i].valid) peaksLeft.push(that.peaks[i]);
                    }
                    that.peaks = peaksLeft;
                    // console.log("After exclusion, number of peaks: " + that.peaks.length);
                    done();
                }
                else process.nextTick(next);
            }
            next();
        }


        function writeOutData(done) {
            var result = [];
            var fname = 'peaks.json';
            var maxLoops = 500;
            var empty = true;
            function next() {
                var nLoops = (that.peaks.length > maxLoops) ? maxLoops : that.peaks.length;
                for (var i=0; i<nLoops; i++) {
                    var p = that.peaks.shift();
                    var amp = +(p.AMPLITUDE.toFixed(3));
                    var conc = +(p.CH4.toFixed(2));
                    var windDirMean = +(p.WIND_DIR_MEAN.toFixed(1));
                    var windDirSdev = +(p.WIND_DIR_SDEV.toFixed(1));
                    var epochTime = +(p.EPOCH_TIME.toFixed(0));
                    var pos = p.POSITION;
                    var survey = p.SURVEY;
                    var run = p.RUN;
                    var row = JSON.stringify({"A": amp,"C": conc,"T": epochTime,"P": pos,
                        "R": run,"S": survey,"W": windDirMean, "U": windDirSdev});
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
                            if (that.peaks.length === 0) {
                                jf.closeJson(path.join(that.workDir,fname), done);
                            }
                            else process.nextTick(next);
                        }
                    });
                }
                else {
                    if (that.peaks.length === 0) {
                        if (!(fname in that.filenames)) that.filenames[fname] = 0;
                        if (empty) jf.emptyJson(path.join(that.workDir,fname), done);
                        else jf.closeJson(path.join(that.workDir,fname), done);
                    }
                }
            }
            next();
        }
    };

    function newPeaksDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key, forceFlag) {
        return new PeaksDataFetcher(p3ApiService, instructions, workDir, statusFile, submit_key, forceFlag);
    }
    module.exports = newPeaksDataFetcher;

});
