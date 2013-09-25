/* newMarkersDataFetcher.js creates an object to get markers data from P3 into a
    work directory. */
/*global console, module, process, require */
/*jshint undef:true, unused:true */

// We process a list of files and compile a list of markers which lie within the required region.
// Each marker is represented by a geohashed position, a text string and a hexadecimal color string.
// After processing all the files we write out a key file describing the JSON output.

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    var csv = require('csv');
    var fs = require('fs');
    var gh = require('./geohash');
    var jf = require('./jsonFiles');
    var rptGenStatus = require('../public/js/common/rptGenStatus');
    var sf = require('./statusFiles');
    var path = require('path');
    var pv = require('../public/js/common/paramsValidator');
    var _ = require('underscore');

    var newParamsValidator = pv.newParamsValidator;
    var validateListUsing = pv.validateListUsing;

    function MarkersDataFetcher(p3ApiService, instructions, reportDir, workDir, statusFile, submit_key, forceFlag) {
        this.p3ApiService = p3ApiService;
        this.instructions = instructions;
        this.reportDir = reportDir;
        this.workDir = workDir;
        this.statusFile = statusFile;
        this.submit_key = submit_key;
        this.forceFlag = forceFlag;
        this.norm_instr = null;
        this.markers = {};
        this.fileIndex = 0;
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

    function markersFileValidator(run) {
        var rpv = newParamsValidator(run,
            [{"name": "filename", "required":true, "validator": "string"},
             {"name": "hash", "required":true, "validator": /[0-9a-f]{32}/ }
            ]);
        return rpv.validate();
    }

    MarkersDataFetcher.prototype.run = function (callback) {
        var that = this;

        var ipv = newParamsValidator(that.instructions,
            [{"name": "swCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "neCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "markersFiles", "required":true, "validator": validateListUsing(markersFileValidator)}]);

        if (ipv.ok()) {
            that.norm_instr = ipv.validate().normValues;
            var swCorner = gh.decodeToLatLng(that.norm_instr.swCorner);
            var neCorner = gh.decodeToLatLng(that.norm_instr.neCorner);
            that.minLng = swCorner[1]; that.minLat = swCorner[0];
            that.maxLng = neCorner[1]; that.maxLat = neCorner[0];

            processFiles(function (err) {
                if (err) {
                    sf.writeStatus(that.statusFile,
                        {"status": rptGenStatus.FAILED,"msg": err.message });
                    callback(err);
                }
                else {
                    sf.writeStatus(that.statusFile, {"status": rptGenStatus.DONE});
                    callback(null);
                }
            });
        }
        else {
            sf.writeStatus(that.statusFile, {"status": rptGenStatus.BAD_PARAMETERS,
                "msg": ipv.errors() });
            callback(new Error(ipv.errors()));
        }

        // processFile takes a CSV file specified by that.norm_instr.markersFiles[that.fileIndex]
        //  and fills up that.markers with objects representing the markers within the region 
        //  rectangle
        function processFile(done) {
            var markersFile = that.norm_instr.markersFiles[that.fileIndex];
            var hash = markersFile.hash;
            var filename = path.join(that.reportDir, "csv", hash.substr(0,2), hash, hash + '.csv');
            var errorCount = 0;
            fs.readFile(filename, "ascii", function (err, data) {
                if (err) done(err);
                else {
                    data = data.replace(/\r\n/g,"\n").replace(/\r/g,"\n");
                    csv().from.string(data,{columns:['latitude','longitude','text','color']})
                    .on('error', function() {
                        this.removeAllListeners('record').removeAllListeners('end');
                        done(new Error("Bad CSV file"));
                    })
                    .on('record', function(row, index) {
                        var lat = Number(row['latitude']);
                        if (isNaN(lat) || lat<-90.0 || lat>90.0) errorCount += 1;
                        var lng = Number(row['longitude']);
                        if (isNaN(lng)  || lat<-180.0 || lat>180.0) errorCount += 1;
                        var color = parseInt(row['color'],16);
                        if (isNaN(color)) errorCount += 1;
                        var text = row['text'];
                        // console.log('#' + index + ' ' + JSON.stringify(row));
                        if (errorCount > 0) {
                            console.log("Error count", errorCount);
                            this.removeAllListeners('record').removeAllListeners('end');
                            done(new Error("Errors found in CSV file"));
                        }
                        else {
                            // console.log(lat, lng, text, color);
                            if (that.minLat <= lat && lat <= that.maxLat &&
                                that.minLng <= lng && lng <= that.maxLng) {
                                var position = gh.encodeGeoHash(lat,lng);
                                var cs = '#' + formatNumberLength(color.toString(16),6);
                                that.markers.push({P:position, T:text, C:cs});
                            }
                        }
                    })
                    .on('end', function() {
                        this.removeAllListeners('record').removeAllListeners('end');
                        if (errorCount === 0) done(null);
                        else done(new Error("Errors found in CSV file"));
                    });
                }
            });
        }

        // processFiles iterates through the provided markers files, calling processFile for each.
        //  that.fileIndex indicates which file is to be processed.
        //  When all files are done it calls writeOutData and writeKeyFile
        function processFiles(done) {
            that.fileIndex = 0;
            that.markers = [];
            var params = that.norm_instr;
            function next() {
                if (that.fileIndex == params.markersFiles.length) {
                    // console.log(JSON.stringify(that.markers));
                    writeOutData(function (err) {
                        if (err) done(err);
                        else writeKeyFile(function (err) {
                            if (err) done(err);
                            else done(null);
                        });
                    });
                }
                else {
                    processFile(function (err) {
                        if (err) done(err);
                        else {
                            that.fileIndex += 1;
                            console.log("MARKERS: ", that.markers.length);
                            process.nextTick(next);
                        }
                    });
                }
            }
            next();
        }

        function writeKeyFile(done) {
            var records = [];
            // Get number of records in each file, which is currently the value
            //  in that.filenames, keyed by the names
            var names = _.keys(that.filenames);
            names.sort();
            names.forEach(function (file) {
                records.push(that.filenames[file]);
            });
            var result = JSON.stringify({"INSTRUCTIONS_TYPE": "getMarkersData",
                                         "SUBMIT_KEY": that.submit_key,
                                         "INSTRUCTIONS": that.norm_instr,
                                         "OUTPUTS": {
                                             "FILES": names,
                                             "FILE_RECORDS": records,
                                             "HEADINGS": {"P": "POSITION",
                                                          "T": "TEXT",
                                                          "C": "COLOR"}
                                         }},null,2);
            fs.writeFile(path.join(that.workDir,"key.json"),result,function (err) {
                if (err) done(err);
                else done(null);
            });
        }

        function writeOutData(done) {
            var fname = 'markers.json';
            var result = [];
            var maxLoops = 500;
            var empty = true;
            function next() {
                var nLoops = (that.markers.length > maxLoops) ? maxLoops : that.markers.length;
                for (var i=0; i<nLoops; i++) {
                    var p = that.markers.shift();
                    var row = JSON.stringify(p);
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
                            if (that.markers.length === 0) {
                                jf.closeJson(path.join(that.workDir,fname), done);
                            }
                            else process.nextTick(next);
                        }
                    });
                }
                else {
                    if (that.markers.length === 0) {
                        if (!(fname in that.filenames)) that.filenames[fname] = 0;
                        if (empty) jf.emptyJson(path.join(that.workDir,fname), done);
                        else jf.closeJson(path.join(that.workDir,fname), done);
                    }
                }
            }
            next();
        }
    };

    function newMarkersDataFetcher(p3ApiService, instructions, reportDir, workDir, statusFile, submit_key, forceFlag) {
        return new MarkersDataFetcher(p3ApiService, instructions, reportDir, workDir, statusFile, submit_key, forceFlag);
    }
    module.exports = newMarkersDataFetcher;

});
