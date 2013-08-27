/* newFacilitiesDataFetcher.js creates an object to get facilities data from P3 into a
    work directory. */
/*global console, exports, module, process, require */
/*jshint undef:true, unused:true */

// We process a list of files and compile a list of facilities which lie within the required region.
// Each facility is represented by a list of geohashed positions, a line width and line color.
// The positions are obtained by appplying XPath filters to the KML files, one per file.
// A list of positions is placed in the output JSON file if at least one of the coordinates is in the region.
// After processing all the files we write out a key file describing the JSON output.

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    var CNSNT = require('../public/js/common/cnsnt');
    var et = require('elementtree');
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

    function FacilitiesDataFetcher(p3ApiService, instructions, reportDir, workDir, statusFile, submit_key, forceFlag) {
        this.p3ApiService = p3ApiService;
        this.instructions = instructions;
        this.reportDir = reportDir;
        this.workDir = workDir;
        this.kmlFilenames = [];
        this.kmlHashes = [];
        this.statusFile = statusFile;
        this.submit_key = submit_key;
        this.forceFlag = forceFlag;
        this.norm_instr = null;
        this.facilities = {};
        this.fileIndex = 0;
        this.filenames = {};
    }

    function facilitiesFileValidator(run) {
        var rpv = newParamsValidator(run,
            [{"name": "filename", "required":true, "validator": "string"},
             {"name": "hash", "required":true, "validator": /[0-9a-f]{32}/ },
             {"name": "linecolor", "required":true, "validator": "string" },
             {"name": "linewidth", "required":true, "validator": "number" },
             {"name": "xpath", "required":true, "validator": "string"}
            ]);
        return rpv.validate();
    }

    FacilitiesDataFetcher.prototype.run = function (callback) {
        var that = this;

        var ipv = newParamsValidator(that.instructions,
            [{"name": "swCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "neCorner", "required":true, "validator": /[0-9b-hjkmnp-z]{6,12}/},
             {"name": "facilities", "required":true, "validator": validateListUsing(facilitiesFileValidator)}]);

        if (ipv.ok()) {
            that.norm_instr = ipv.validate().normValues;
            var swCorner = gh.decodeToLatLng(that.norm_instr.swCorner);
            var neCorner = gh.decodeToLatLng(that.norm_instr.neCorner);
            that.minLng = swCorner[1]; that.minLat = swCorner[0];
            that.maxLng = neCorner[1]; that.maxLat = neCorner[0];

            processFiles(function (err) {
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

        // processFile takes a KML file specified by that.norm_instr.facilities[that.fileIndex]
        //  and fills up that.facilities with objects representing the facilities 
        //  within the region rectangle (i.e. when anyInside is true). Note that the facilities
        //  lats and longs may be offset by up to CNSNT.MAX_OFFSETS degree, so we need to fetch more than
        //  just what would be in the rectangle.
        function processFile(done) {
            var facilitiesFile = that.norm_instr.facilities[that.fileIndex];
            var hash = facilitiesFile.hash;
            var filter = facilitiesFile.xpath;
            var linecolor = facilitiesFile.linecolor;
            var linewidth = facilitiesFile.linewidth;
            var filename = path.join(that.reportDir, "kml", hash.substr(0,2), hash, hash + '.kml');
            var maxLoops = 100;
            that.kmlHashes[that.fileIndex] = hash;
            that.kmlFilenames[that.fileIndex] = facilitiesFile.filename;

            fs.readFile(filename, "ascii", function (err, data) {
                if (err) done(err);
                else {
                    data = data.replace(/\r\n/g,"\n").replace(/\r/g,"\n");
                    var start = data.indexOf("<");
                    if (start > 10) {
                        done(new Error("Cannot find starting element of XML file"));
                    }
                    var tree = et.parse(data.substr(start));
                    var results = tree.findall(filter);
                    var next = function () {
                        var segment;
                        var anyInside;
                        function getSegment(p) {
                            if (p) {
                                var coords = [];
                                p.split(',').forEach(function (c) {
                                    coords.push(+c);
                                });
                                var lat = coords[1];
                                var lng = coords[0];
                                if (that.minLat-CNSNT.MAX_OFFSETS <= lat && lat <= that.maxLat+CNSNT.MAX_OFFSETS &&
                                    that.minLng-CNSNT.MAX_OFFSETS <= lng && lng <= that.maxLng+CNSNT.MAX_OFFSETS) anyInside = true;
                                segment.push(gh.encodeGeoHash(lat,lng));
                            }
                        }
                        var nLoops = (results.length > maxLoops) ? maxLoops : results.length;
                        for (var i=0; i<nLoops; i++) {
                            var e = results.shift();
                            var points = e.text.split(/\s+/);
                            segment = [];
                            anyInside = false;
                            points.forEach(getSegment);
                            if (anyInside && segment.length>1) {
                                that.facilities.push({P:segment, W:linewidth, C:linecolor, F:that.fileIndex});
                            }
                        }
                        if (results.length === 0) {
                            done(null);
                        }
                        else process.nextTick(next);
                    };
                    next();
                }
            });
        }

        // processFiles iterates through the provided facilities files, calling processFile for each.
        //  that.fileIndex indicates which file is to be processed.
        //  When all files are done it calls writeOutData and writeKeyFile
        function processFiles(done) {
            that.fileIndex = 0;
            that.facilities = [];
            var params = that.norm_instr;
            function next() {
                if (that.fileIndex == params.facilities.length) {
                    // console.log(JSON.stringify(that.facilities));
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
                            console.log("FACILITIES: ", that.facilities.length);
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
            var result = JSON.stringify({"INSTRUCTIONS_TYPE": "getFacilitiesData",
                                         "SUBMIT_KEY": that.submit_key,
                                         "INSTRUCTIONS": that.norm_instr,
                                         "OUTPUTS": {
                                             "KML_FILENAMES": that.kmlFilenames,
                                             "KML_HASHES": that.kmlHashes,
                                             "FILES": names,
                                             "FILE_RECORDS": records,
                                             "HEADINGS": {"P": "POSITIONS",
                                                          "W": "WIDTH",
                                                          "C": "COLOR",
                                                          "F": "FILE_INDEX"}
                                         }},null,2);
            fs.writeFile(path.join(that.workDir,"key.json"),result,function (err) {
                if (err) done(err);
                else done(null);
            });
        }

        function writeOutData(done) {
            var fname = 'facilities.json';
            var result = [];
            var maxLoops = 500;
            var empty = true;
            function next() {
                var nLoops = (that.facilities.length > maxLoops) ? maxLoops : that.facilities.length;
                for (var i=0; i<nLoops; i++) {
                    var p = that.facilities.shift();
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
                            if (that.facilities.length === 0) {
                                jf.closeJson(path.join(that.workDir,fname), done);
                            }
                            else process.nextTick(next);
                        }
                    });
                }
                else {
                    if (that.facilities.length === 0) {
                        if (!(fname in that.filenames)) that.filenames[fname] = 0;
                        if (empty) jf.emptyJson(path.join(that.workDir,fname), done);
                        else jf.closeJson(path.join(that.workDir,fname), done);
                    }
                }
            }
            next();
        }
    };

    function newFacilitiesDataFetcher(p3ApiService, instructions, reportDir, workDir, statusFile, submit_key, forceFlag) {
        return new FacilitiesDataFetcher(p3ApiService, instructions, reportDir, workDir, statusFile, submit_key, forceFlag);
    }
    module.exports = newFacilitiesDataFetcher;

});
