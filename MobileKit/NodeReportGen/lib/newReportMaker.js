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

    function ReportMaker(rptGenService, instructions, workDir, statusFile, submit_key) {
        this.rptGenService = rptGenService;
        this.instructions = instructions;
        this.workDir = workDir;
        this.statusFile = statusFile;
        this.submit_key = submit_key;
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
        var that = this;
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
            for (var i=0; i<summaryFigs.length; i++) needFov = needFov || summaryFigs[i].paths || summaryFigs[i].fovs;
            for (i=0; i<submapFigs.length; i++) needFov = needFov || submapFigs[i].paths || submapFigs[i].fovs;
            if (needFov) subtasks.push({"name": "getFovsData", "extractor": extractFovsRequest});

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
            var baseUrl = 'http://localhost:5300/getReport/' + that.submit_key.hash + '/' + that.submit_key.dir_name;
            submaps.push({"url": url.format({"pathname": baseUrl, "query": {"name":"Summary"}}), "name": "summary.pdf"});

            for (var my=0; my<suby; my++) {
                minLat = maxLat - dy;
                minLng = rptMinLng;
                for (var mx=0; mx<subx; mx++) {
                    maxLng = minLng + dx;
                    swCorner = gh.encodeGeoHash(minLat, minLng);
                    neCorner = gh.encodeGeoHash(maxLat, maxLng);
                    name = String.fromCharCode(65+my) + (mx + 1);
                    submaps.push({"url": url.format({"pathname": baseUrl,
                        "query": {"neCorner":neCorner, "swCorner":swCorner, "name":name}}),
                        "name": (name + ".pdf")});
                    minLng = maxLng;
                }
                maxLat = minLat;
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
            var cmd = 'C:\\Program Files (x86)\\PDF Labs\\PDFtk Server\\bin\\pdftk.exe';
            var pdfFiles = [];
            submapList.forEach(function (submap) {
                pdfFiles.push(submap.name);
            });
            cmd = '"' + cmd + '" ' + pdfFiles.join(" ") + " cat output report.pdf";
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
                done(null);
            });
        }

        function convertToPdf(url, pdfFile, done) {
            var outFile = path.join(that.workDir, pdfFile);
            var cmd = '"C:\\Program Files (x86)\\phantomjs-1.9.0-windows\\phantomjs.exe" screenDump.js "' +
                        url + '" "' + outFile + '" Letter';
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
                done(null);
            });
        }
    };

    function newReportMaker(rptGenService, instructions, workDir, statusFile, submit_key) {
        return new ReportMaker(rptGenService, instructions, workDir, statusFile, submit_key);
    }
    module.exports = newReportMaker;

});
