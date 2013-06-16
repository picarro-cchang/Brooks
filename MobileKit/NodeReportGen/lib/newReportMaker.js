/* newReportMaker.js creates an object to make reports. */
/*global console, exports, module, process, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var cp = require('child_process');
    var fs = require('fs');
    var jf = require('./jsonFiles');
    var newN2i = require('./newNamesToIndices');
    var newRptGenLrtController = require('./newRptGenLrtController');
    var path = require('path');
    var pv = require('../public/js/common/paramsValidator');
    var rptGenStatus = require('../public/js/common/rptGenStatus');
    var sf = require('./statusFiles');
    var sis = require('./surveyorInstStatus');
    var SITECONFIG = require('./siteConfig');
    var url = require('url');
    var _ = require('underscore');
    var instrValidator = require('../public/js/common/instructionsValidator').instrValidator;

    var newParamsValidator = pv.newParamsValidator;
    var latlngValidator = pv.latlngValidator;
    var validateListUsing = pv.validateListUsing;


    var cjs = require("../public/js/common/canonical_stringify");
    var gh = require("./geohash");
    var ts = require("./timeStamps");

    function extractAnalysesRequest(instructions) {
        // Extracts the instructions for generating a getAnalysesData request
        //  as a canonical JSON string
        var result = {};
        result["instructions_type"] = "getAnalysesData";
        result["swCorner"] = gh.encodeGeoHash.apply(null, instructions["swCorner"]);
        result["neCorner"] = gh.encodeGeoHash.apply(null, instructions["neCorner"]);
        result["runs"] = [];
        instructions["runs"].forEach(function (run, i) {
            var r = {};
            var ir = instructions["runs"][i];
            r["analyzer"] = ir["analyzer"];
            r["startEtm"] = ir["startEtm"];
            r["endEtm"] = ir["endEtm"];
            result["runs"].push(r);
        });
        return cjs(result,null,2);
    }

    function extractPeaksRequest(instructions) {
        // Extracts the instructions for generating a getPeaksData request
        //  as a canonical JSON string
        var result = {};
        result["instructions_type"] = "getPeaksData";
        result["swCorner"] = gh.encodeGeoHash.apply(null, instructions["swCorner"]);
        result["neCorner"] = gh.encodeGeoHash.apply(null, instructions["neCorner"]);
        result["exclRadius"] = instructions["exclRadius"];
        result["runs"] = [];
        instructions["runs"].forEach(function (run, i) {
            var r = {};
            var ir = instructions["runs"][i];
            r["analyzer"] = ir["analyzer"];
            r["startEtm"] = ir["startEtm"];
            r["endEtm"] = ir["endEtm"];
            result["runs"].push(r);
        });
        return cjs(result,null,2);
    }

    function extractPathsRequest(instructions) {
        // Extracts the instructions for generating a getPeaksData request
        //  as a canonical JSON string
        var result = {};
        result["instructions_type"] = "getPathsData";
        result["swCorner"] = gh.encodeGeoHash.apply(null, instructions["swCorner"]);
        result["neCorner"] = gh.encodeGeoHash.apply(null, instructions["neCorner"]);
        result["runs"] = [];
        instructions["runs"].forEach(function (run, i) {
            var r = {};
            var ir = instructions["runs"][i];
            r["analyzer"] = ir["analyzer"];
            r["startEtm"] = ir["startEtm"];
            r["endEtm"] = ir["endEtm"];
            result["runs"].push(r);
        });
        return cjs(result,null,2);
    }

    function extractFovsRequest(instructions) {
        // Extracts the instructions for generating a getFovsData request
        //  as a canonical JSON string
        var result = {};
        result["instructions_type"] = "getFovsData";
        result["swCorner"] = gh.encodeGeoHash.apply(null, instructions["swCorner"]);
        result["neCorner"] = gh.encodeGeoHash.apply(null, instructions["neCorner"]);
        result["fovMinAmp"] = instructions["fovMinAmp"];
        result["fovMinLeak"] = instructions["fovMinLeak"];
        result["fovNWindow"] = instructions["fovNWindow"];
        result["runs"] = [];
        instructions["runs"].forEach(function (run, i) {
            var r = {};
            var ir = instructions["runs"][i];
            r["analyzer"] = ir["analyzer"];
            r["startEtm"] = ir["startEtm"];
            r["endEtm"] = ir["endEtm"];
            r["stabClass"] = ir["stabClass"].toUpperCase();
            result["runs"].push(r);
        });
        return cjs(result,null,2);
    }

    function extractFacilitiesRequest(instructions) {
        // Extracts the instructions for generating a getFacilitiesData request
        //  as a canonical JSON string
        var result = {};
        result["instructions_type"] = "getFacilitiesData";
        result["swCorner"] = gh.encodeGeoHash.apply(null, instructions["swCorner"]);
        result["neCorner"] = gh.encodeGeoHash.apply(null, instructions["neCorner"]);
        result["facilities"] = instructions["facilities"].slice(0);
        return cjs(result,null,2);
    }

    function extractMarkersRequest(instructions) {
        // Extracts the instructions for generating a getMarkersData request
        //  as a canonical JSON string
        var result = {};
        result["instructions_type"] = "getMarkersData";
        result["swCorner"] = gh.encodeGeoHash.apply(null, instructions["swCorner"]);
        result["neCorner"] = gh.encodeGeoHash.apply(null, instructions["neCorner"]);
        result["markersFiles"] = instructions["markersFiles"].slice(0);
        return cjs(result,null,2);
    }

    function ReportMaker(rptGenService, instructions, workDir, statusFile, submit_key, forceFlag) {
        this.rptGenService = rptGenService;
        this.instructions = instructions;
        this.workDir = workDir;
        this.statusFile = statusFile;
        this.submit_key = submit_key;
        this.forceFlag = forceFlag;
        this.norm_instr = null;
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

    function n2nan(x) {
        return (x === null) ? NaN : x;
    }

    ReportMaker.prototype.run = function (callback) {
        var i, that = this;
        console.log(JSON.stringify(that.instructions));
        var v = instrValidator(that.instructions);
        console.log(v.valid);
        if (v.valid) {
            that.norm_instr = v.normValues;
            var subtasks = [{"name": "getPeaksData", "extractor": extractPeaksRequest},
                            {"name": "getAnalysesData", "extractor": extractAnalysesRequest}];
            // Determine if path or field of view is required by looking through the template
            var template = that.norm_instr.template;
            var summaryFigs = template.summary.figures, submapFigs = template.submaps.figures;
            var needFov = false;
            for (i=0; i<summaryFigs.length; i++) needFov = needFov || summaryFigs[i].paths || summaryFigs[i].fovs;
            for (i=0; i<submapFigs.length; i++) needFov = needFov || submapFigs[i].paths || submapFigs[i].fovs;
            if (needFov) subtasks.push({"name": "getFovsData", "extractor": extractFovsRequest});
            // Determine if there are any markers files and if any markers are in the template
            var needMarkers = false;
            if (!_.isEmpty(that.norm_instr.markersFiles)) {
                for (i=0; i<summaryFigs.length; i++) needMarkers = needMarkers || summaryFigs[i].markers;
                for (i=0; i<submapFigs.length; i++) needMarkers = needMarkers || submapFigs[i].markers;
                if (needMarkers) subtasks.push({"name": "getMarkersData", "extractor": extractMarkersRequest});
            }
            // Determine if there are any facilities files and if any facilities are in the template
            var needFacilities = false;
            if (!_.isEmpty(that.norm_instr.facilities)) {
                for (i=0; i<summaryFigs.length; i++) needFacilities = needFacilities || summaryFigs[i].facilities;
                for (i=0; i<submapFigs.length; i++) needFacilities = needFacilities || submapFigs[i].facilities;
                if (needFacilities) subtasks.push({"name": "getFacilitiesData", "extractor": extractFacilitiesRequest});
            }

            that.pending = subtasks.length;
            subtasks.forEach(function (task) {
                var instr = task.extractor(that.norm_instr);
                var user = that.submit_key.user;
                var lrtCont = newRptGenLrtController(that.rptGenService, "RptGen", {'qry': 'submit', 'contents': instr,
                    'user': user, 'force': that.forceFlag});
                lrtCont.on('submit', onTaskSubmit(task.name));
                lrtCont.on('end', onTaskEnd(task.name));
                lrtCont.on('error', onTaskError(task.name));
                lrtCont.run();
            });
        }
        else {
            sf.writeStatus(that.statusFile,
                {"status": rptGenStatus.FAILED, "msg": v.errorList.join("\n") }, function () {
                    callback(new Error(v.errorList.join("\n")));
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
                            writeKeyFile();
                        }
                    }
                };
            })(name);
        }

        function writeKeyFile() {
            var result = JSON.stringify({"INSTRUCTIONS_TYPE": "makeReport",
                                         "SUBMIT_KEY": that.submit_key,
                                         "INSTRUCTIONS": that.norm_instr,
                                         "SUBTASKS": that.keyDataBySubtask},null,2);
            fs.writeFile(path.join(that.workDir,"key.json"),result,function (err) {
                if (err) {
                    sf.writeStatus(that.statusFile,
                        {"status": rptGenStatus.FAILED, "msg": err.message }, function () {
                            callback(err);
                    });
                }
                else {
                    if (that.norm_instr.makePdf) {
                        makePdfReports(that.norm_instr);
                    }
                    else {
                        sf.writeStatus(that.statusFile, {"status": rptGenStatus.DONE_NO_PDF}, function(err) {
                            if (err) callback(err);
                            else callback(null);
                        });
                    }
                }
            });
        }

        function makePdfReports(instructions) {
            var subx = instructions.submaps.nx;
            var suby = instructions.submaps.ny;
            var rptMaxLat = instructions.neCorner[0];
            var rptMaxLng = instructions.neCorner[1];
            var rptMinLat = instructions.swCorner[0];
            var rptMinLng = instructions.swCorner[1];
            var dx = (rptMaxLng - rptMinLng) / subx;
            var dy = (rptMaxLat - rptMinLat) / suby;

            var minLat, maxLat = rptMaxLat, minLng, maxLng;
            var name, neCorner, submaps = [], swCorner;
            var proto = (SITECONFIG.reportport === 443) ? "https" : "http";
            var prefix = proto + '://' + SITECONFIG.reporthost + ':' + SITECONFIG.reportport;
            var baseUrl = prefix + '/getReportLocal/' + that.submit_key.hash + '/' + that.submit_key.dir_name;

            /* Determine if the summary map has any elements enabled. If it has, add it to the list to be rendered */
            var tables = instructions.template.summary.tables;
            if (!_.isEmpty(instructions.template.summary.figures) ||
                tables.analysesTable || tables.peaksTable || tables.surveysTable || tables.runsTable) {
                submaps.push({"url": url.format({"pathname": baseUrl, "query": {"name":"Summary"}}), "name": "summary.pdf"});
            }

            tables = instructions.template.submaps.tables;
            if (!_.isEmpty(instructions.template.submaps.figures) ||
                tables.analysesTable || tables.peaksTable || tables.surveysTable || tables.runsTable) {
                for (var my=0; my<suby; my++) {
                    minLat = maxLat - dy;
                    minLng = rptMinLng;
                    for (var mx=0; mx<subx; mx++) {
                        maxLng = minLng + dx;
                        swCorner = gh.encodeGeoHash(minLat, minLng);
                        neCorner = gh.encodeGeoHash(maxLat, maxLng);
                        name = String.fromCharCode(65 + my) + (mx + 1);
                        submaps.push({"url": url.format({"pathname": baseUrl,
                            "query": {"neCorner":neCorner, "swCorner":swCorner, "name":name}}),
                            "name": (name + ".pdf")});
                        minLng = maxLng;
                    }
                    maxLat = minLat;
                }
            }

            var ss = submaps.slice(0);
            function next() {
                var submap;
                if (ss.length > 0) {
                    submap = ss.shift();
                    convertToPdf(submap.url, submap.name, function (err) {
                        if (err) callback(err);
                        else {
                            process.nextTick(next);
                        }
                    });
                }
                else {
                    concatenatePdf(submaps.slice(0), function (err) {
                        if (err) callback(err);
                        else {
                            sf.writeStatus(that.statusFile, {"status": rptGenStatus.DONE_WITH_PDF}, function(err) {
                                if (err) callback(err);
                                else callback(null);
                            });
                        }
                    });
                }
            }
            next();
        }

        function concatenatePdf(submapList, done) {
            var pdfFiles = [];
            submapList.forEach(function (submap) {
                pdfFiles.push(submap.name);
            });
            var cmd = '"' + SITECONFIG.pdftkPath + '" ' + pdfFiles.join(" ") + " cat output report.pdf";
            console.log(cmd);
            var concat = cp.exec(cmd, {"cwd": that.workDir}, function (err, stdout, stderr) {
                if (err) {
                    console.log(err.stack);
                    console.log('Error code: ' + err.code);
                    console.log('Signal received: ' + err.signal);
                }
                console.log('Child Process STDOUT: ' + stdout);
                console.log('Child Process STDERR: ' + stderr);
            });
            concat.on('exit', function (code) {
                console.log('Child process exited with code ' + code);
                if (code === 0) {
                    // Delete the component PDF files, do not wait for completion
                    pdfFiles.forEach(function (fname) {
                        fs.unlink(path.join(that.workDir, fname));
                    });
                    done(null);
                }
                else done(new Error("Concatenate Pdf: error code " + code));
            });
        }

        function convertToPdf(url, pdfFile, done) {
            var outFile = path.join(that.workDir, pdfFile);
            var cmd = '"' + SITECONFIG.phantomPath + '" screenDump.js "' +
                        url + '" "' + outFile + '" "Letter" "' + SITECONFIG.pdfZoom +
                        '" "' + SITECONFIG.headerFontSize + '" "' +
                        SITECONFIG.footerFontSize + '"';
            console.log(cmd);
            var convert = cp.exec(cmd, {"cwd": __dirname}, function (err, stdout, stderr) {
                if (err) {
                    console.log(err.stack);
                    console.log('Error code: ' + err.code);
                    console.log('Signal received: ' + err.signal);
                }
                console.log('Child Process STDOUT: ' + stdout);
                console.log('Child Process STDERR: ' + stderr);
            });
            convert.on('exit', function (code) {
                console.log('Child process exited with code ' + code);
                if (code === 0) {
                    done(null);
                }
                else done(new Error("Convert to Pdf: error code " + code));
            });
        }
    };

    function newReportMaker(rptGenService, instructions, workDir, statusFile, submit_key, forceFlag) {
        return new ReportMaker(rptGenService, instructions, workDir, statusFile, submit_key, forceFlag);
    }
    module.exports = newReportMaker;

});
