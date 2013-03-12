/* newReportMaker.js creates an object to make reports. */
/*global console, exports, module, process, require */

(function() {
    'use strict';
    var cp = require('child_process');
    var fs = require('fs');
    var jf = require('./jsonFiles');
    var newN2i = require('./newNamesToIndices');
    var newRptGenLrtController = require('./newRptGenLrtController');
    var path = require('path');
    var pv = require('./paramsValidator');
    var rptGenStatus = require('./rptGenStatus');
    var sf = require('./statusFiles');
    var sis = require('./surveyorInstStatus');
    var url = require('url');
    var _ = require('underscore');

    var newParamsValidator = pv.newParamsValidator;
    var latlngValidator = pv.latlngValidator;
    var validateListUsing = pv.validateListUsing;


    var cjs = require("./canonical_stringify");
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
            r["startEtm"] = ts.strToEtm(ir["startEtm"], instructions["timezone"]);
            r["endEtm"] = ts.strToEtm(ir["endEtm"], instructions["timezone"]);
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
        result["runs"] = [];
        instructions["runs"].forEach(function (run, i) {
            var r = {};
            var ir = instructions["runs"][i];
            r["analyzer"] = ir["analyzer"];
            r["startEtm"] = ts.strToEtm(ir["startEtm"], instructions["timezone"]);
            r["endEtm"] = ts.strToEtm(ir["endEtm"], instructions["timezone"]);
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
            r["startEtm"] = ts.strToEtm(ir["startEtm"], instructions["timezone"]);
            r["endEtm"] = ts.strToEtm(ir["endEtm"], instructions["timezone"]);
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
            r["startEtm"] = ts.strToEtm(ir["startEtm"], instructions["timezone"]);
            r["endEtm"] = ts.strToEtm(ir["endEtm"], instructions["timezone"]);
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

    function runValidator(run) {
        var rpv = newParamsValidator(run,
            [{"name": "analyzer", "required":true, "validator": "string"},
             {"name": "startEtm", "required":true,
              "validator": /\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}/ },
             {"name": "endEtm", "required":true,
              "validator": /\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}/ },
             {"name": "stabClass", "required":false,"validator": /[a-fA-F*]/, "default_value":"*"},
             {"name": "peaks", "required":false, "validator": /#[0-9a-fA-F]{6}/, "default_value":"#FFFF00"},
             {"name": "wedges", "required":false, "validator": /#[0-9a-fA-F]{6}/, "default_value":"#0000FF"},
             {"name": "fovs", "required":false, "validator": /#[0-9a-fA-F]{6}/, "default_value":"#00FF00"}
            ]);
        return rpv.validate();
    }

    function componentsValidator (components) {
        var rpv = newParamsValidator(components,
            [{"name": "baseType", "required":false, "validator": /satellite|map/, "default_value": "map"},
             {"name": "paths", "required":false, "validator": "boolean", "default_value": false},
             {"name": "peaks", "required":false, "validator": "boolean", "default_value": false},
             {"name": "wedges", "required":false, "validator": "boolean", "default_value": false},
             {"name": "fovs", "required":false, "validator": "boolean", "default_value": false},
             {"name": "submapGrid", "required":false, "validator": "boolean", "default_value": false},
             {"name": "peaksTable", "required":false, "validator": "boolean", "default_value": false},
             {"name": "surveysTable", "required":false, "validator": "boolean", "default_value": false},
             {"name": "runsTable", "required":false, "validator": "boolean", "default_value": false}
            ]);
        return rpv.validate();
    }

    function templateValidator (template) {
        var rpv = newParamsValidator(template,
            [{"name": "summary", "required":false, "validator": validateListUsing(componentsValidator), "default_value": []},
             {"name": "submaps", "required":false, "validator": validateListUsing(componentsValidator), "default_value": []}
            ]);
        return rpv.validate();
    }

    function submapsValidator (submaps) {
        var rpv = newParamsValidator(submaps,
            [{"name": "nx", "required":false, "validator": "number", "default_value": 1},
             {"name": "ny", "required":false, "validator": "number", "default_value": 1}
            ]);
        return rpv.validate();
    }

    ReportMaker.prototype.run = function (callback) {
        var that = this;

        var ipv = newParamsValidator(that.instructions,
            [{"name": "swCorner", "required": true, "validator": latlngValidator},
             {"name": "neCorner", "required": true, "validator": latlngValidator},
             {"name": "submaps", "required": false, "validator": submapsValidator, "default_value": {"nx": 1, "ny": 1}},
             {"name": "exclRadius", "required": false, "validator": "number", "default_value": 0},
             {"name": "fovMinAmp", "required": false, "validator": "number", "default_value": 0.03},
             {"name": "fovMinLeak", "required": false, "validator": "number", "default_value": 1.0},
             {"name": "fovNWindow", "required": false, "validator": "number", "default_value": 10},
             {"name": "peaksMinAmp", "required": false, "validator": "number", "default_value": 0.03},
             {"name": "runs", "required": true, "validator": validateListUsing(runValidator)},
             {"name": "timezone", "required":false, "validator": "string", "default_value": "GMT"},
             {"name": "template", "required": true, "validator": templateValidator}]);

        if (ipv.ok()) {
            that.norm_instr = ipv.validate().normValues;
            var subtasks = [{"name": "getPeaksData", "extractor": extractPeaksRequest},
                            {"name": "getAnalysesData", "extractor": extractAnalysesRequest},
                            // {"name": "getPathsData", "extractor": extractPathsRequest}//,
                            {"name": "getFovsData", "extractor": extractFovsRequest}
                           ];
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
                    sf.writeStatus(that.statusFile, {"status": rptGenStatus.LINKS_AVAILABLE}, function(err) {
                        if (err) callback(err);
                        else {
                            makePdfReports(that.norm_instr);
                        }
                    });
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
            submaps.push({"url": baseUrl, "name": "summary.pdf"});

            for (var my=0; my<suby; my++) {
                minLat = maxLat - dy;
                minLng = rptMinLng;
                for (var mx=0; mx<subx; mx++) {
                    maxLng = minLng + dx;
                    swCorner = gh.encodeGeoHash(minLat, minLng);
                    neCorner = gh.encodeGeoHash(maxLat, maxLng);
                    name = String.fromCharCode(65+my) + (mx + 1);
                    submaps.push({"url": url.format({"pathname": baseUrl, "query": {"neCorner":neCorner, "swCorner":swCorner}}), "name": (name + ".pdf")});
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
                            sf.writeStatus(that.statusFile, {"status": rptGenStatus.DONE}, function(err) {
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
            var cmd = '"C:\\Program Files (x86)\\wkhtmltopdf\\wkhtmltopdf.exe" --javascript-delay 10000 "' + url + '" "' + outFile + '"';
            var convert = cp.exec(cmd, function (err, stdout, stderr) {
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

})();
