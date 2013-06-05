/*global __dirname, console, describe, after, before, beforeEach, it, process, require  */
/* jshint -W030, -W024, -W097 */
/*jshint undef:true, unused:true */

/* Start and stop report server running in a subprocess */

'use strict';
var expect = require("chai").expect;
var cp = require("child_process");
var fs = require("fs");
var getRest = require("../lib/getRest");
var http = require("http");
var md5hex = require("../lib/md5hex");
var mkdirp = require('mkdirp');
var path = require("path");
var rptGenStatus = require("../public/js/common/rptGenStatus");
var sf = require("../lib/statusFiles");
var ts = require("../lib/timeStamps");
var url = require("url");
var rptSrv;

var ROOT_DIR = "/temp/testing";

function rmdir(dir) {
    // Remove all files and directories under dir
    var list = fs.readdirSync(dir);
    for(var i = 0; i < list.length; i++) {
        var filename = path.join(dir, list[i]);
        var stat = fs.statSync(filename);
        if(filename == "." || filename == "..") {
            // pass these files
        } else if(stat.isDirectory()) {
            // rmdir recursively
            rmdir(filename);
        } else {
            // rm fiilename
            fs.unlinkSync(filename);
        }
    }
    fs.rmdirSync(dir);
}

function checkIncluded(dict1, dict2) {
    // Check that each key of dict1 is in dict2 and that the corresponding
    //  values match
    for (var key in dict1) {
        if (dict1.hasOwnProperty(key)) {
            expect(dict2).to.include.keys(key);
            expect(dict2[key]).to.eql(dict1[key]);
        }
    }
}

function formatNumberLength(num, length) {
    var r = "" + num;
    while (r.length < length) {
        r = "0" + r;
    }
    return r;
}

function getJSON(qry_url, params, callback) {
    var options = url.parse(qry_url);
    options.query = params;
    options.method = 'GET';
    options.timeout = 30;
    getRest(options, function (err, statusCode, output) {
        expect(err).to.be.null;
        expect(statusCode).to.eql(200);
        callback(JSON.parse(output));
    });
}

describe('statusFileHandlers', function () {
    before( function () {
        if (fs.existsSync(ROOT_DIR)) rmdir(ROOT_DIR);
        mkdirp.sync(ROOT_DIR);
    });

    it('should retrieve a simple dictionary', function (done) {
        var fname = path.join(ROOT_DIR,"temp1.dat");
        var myObj = {a:1, b:2, c:3};
        sf.writeStatus(fname, myObj, function (err) {
            expect(err).to.be.null;
            sf.readStatus(fname, function (err, statObj) {
                expect(err).to.be.null;
                expect(statObj).to.eql(myObj);
                done(null);
            });
        });
    });

    it('should allow the dictionary to be updated', function (done) {
        var fname = path.join(ROOT_DIR,"temp1.dat");
        var myObj1 = {a:1, b:2, c:3};
        var myObj2 = {c:4, d:5, e:6};
        sf.writeStatus(fname, myObj1, function (err) {
            expect(err).to.be.null;
            sf.writeStatus(fname, myObj2, function (err) {
                expect(err).to.be.null;
                sf.readStatus(fname, function (err, statObj) {
                    expect(err).to.be.null;
                    expect(statObj).to.eql({a:1, b:2, c:4, d:5, e:6});
                    done(null);
                });
            });
        });
    });
});

describe('reportServer', function () {
    before( function (done) {
        if (fs.existsSync(ROOT_DIR)) rmdir(ROOT_DIR);
        rptSrv = cp.spawn("node", ["reportServer", "-r", ROOT_DIR],
                          {"cwd": path.join(__dirname,"..")});

        rptSrv.stdout.on('data', function (data) {
            data = data.toString();
            process.stdout.write(data);
        });

        rptSrv.stderr.on('data', function (data) {
            data = data.toString();
            process.stderr.write(data);
        });

        setTimeout(done, 1000);
    });

    after( function (done) {
        rptSrv.kill();
        rptSrv.on('close', function (code) {
            console.log('report server exited with code ' + code);
            done(null);
        });
    });

    describe('basicTests', function () {
        it('should create the test root directory', function(done) {
            fs.exists(ROOT_DIR, function (exists) {
                expect(exists).to.be.true;
                done(null);
            });
        });

        it('should get correct response from /test/testUrl', function(done) {
            var options = {
              host: 'localhost',
              port: 5300,
              path: '/test/testUrl'
            };
            http.request(options, function(response) {
                var result = "";
                //another chunk of data has been recieved, so append it to `result`
                response.on('data', function (chunk) {
                    result += chunk;
                });

                //the whole response has been recieved, so we just print it out here
                response.on('end', function () {
                    expect(result).to.eql("testUrl");
                    done(null);
                });

            }).end();
        });

        it('should get files via /rest/data', function(done) {
            // Create a test file under ROOT_DIR and check it can be accessed 
            //  as /rest/data/myFile.txt
            var testFile = 'myFile.txt';
            var testPath = path.join(ROOT_DIR,testFile);
            var testContents = 'This is some test data';
            fs.writeFileSync(testPath, testContents);
            var options = {
              host: 'localhost',
              port: 5300,
              // Do not use path.join here since we always want / (not \ in Windows)
              path: '/rest/data/' +  testFile
            };
            http.request(options, function(response) {
                var result = "";
                // another chunk of data has been recieved, so append it to `result`
                response.on('data', function (chunk) {
                    result += chunk;
                });
                // the whole response has been recieved, so we can check it is what we
                //   wrote into the test file
                response.on('end', function () {
                    expect(result).to.eql(testContents);
                    fs.unlinkSync(testPath);
                    done(null);
                });

            }).end();
        });

        it('should get public files e.g. for css', function(done) {
            // Try accessing /css/reportGen.css via HTTP request, 
            //  which corresponds to ../public/css/reportGen.css
            var options = {
              host: 'localhost',
              port: 5300,
              path: '/css/reportGen.css'
            };
            http.request(options, function(response) {
                var result = "";
                // another chunk of data has been recieved, so append it to `result`
                response.on('data', function (chunk) {
                    result += chunk;
                });
                // the whole response has been recieved, so we can check it is what we
                //   wrote into the test file
                response.on('end', function () {
                    var fname = path.join(__dirname,"../public",options.path);
                    var buff = fs.readFileSync(fname);
                    expect(result).to.eql(buff.toString("ascii"));
                    done(null);
                });

            }).end();
        });
    });

    describe('timezone conversion', function() {
        it('should convert POSIX time to GMT', function (done) {
            var request = {tz:"GMT", posixTimes:[0,1367883839000]};
            getJSON('http://localhost:5300/rest/tz', request, function(output) {
                checkIncluded(request, output);
                expect(output["timeStrings"][0]).to.eql("1970-01-01 00:00:00+0000 (UTC)");
                expect(output["timeStrings"][1]).to.eql("2013-05-06 23:43:59+0000 (UTC)");
                done(null);
            });
        });

        it('should convert POSIX time to local time', function (done) {
            var request = {tz:"America/Los_Angeles", posixTimes:[0,1367883839000]};
            getJSON('http://localhost:5300/rest/tz', request, function(output) {
                expect(output["timeStrings"][0]).to.eql("1969-12-31 16:00:00-0800 (PST)");
                expect(output["timeStrings"][1]).to.eql("2013-05-06 16:43:59-0700 (PDT)");
                done(null);
            });
        });

        it('should convert local time to POSIX time', function (done) {
            var request = {tz:"America/Los_Angeles",
                           timeStrings:["1969-12-31 16:00:00","2013-05-06 16:43:59"]};
            getJSON('http://localhost:5300/rest/tz', request, function(output) {
                expect(output["timeStrings"][0]).to.eql("1969-12-31 16:00:00-0800 (PST)");
                expect(output["timeStrings"][1]).to.eql("2013-05-06 16:43:59-0700 (PDT)");
                expect(output["posixTimes"][0]).to.eql(0);
                expect(output["posixTimes"][1]).to.eql(1367883839000);
                done(null);
            });
        });

        it('should handle a single element (not an array)', function (done) {
            var request = {tz:"GMT", timeStrings:["1970-01-01 00:00:00"]};
            getJSON('http://localhost:5300/rest/tz', request, function(output) {
                expect(output["timeStrings"][0]).to.eql("1970-01-01 00:00:00+0000 (UTC)");
                expect(output["posixTimes"][0]).to.eql(0);
                done(null);
            });
        });
    });

    describe('RptGen rest calls', function () {
        it('should object to a missing command', function (done) {
            var request = {};
            getJSON('http://localhost:5300/rest/RptGen', request, function(output) {
                checkIncluded(request, output);
                expect(output).to.include.keys('error');
                expect(output.error).to.include('Unknown or missing qry');
                done(null);
            });
        });

        it('should object to an invalid command', function (done) {
            var request = {qry:"invalid"};
            getJSON('http://localhost:5300/rest/RptGen', request, function(output) {
                checkIncluded(request, output);
                expect(output).to.include.keys('error');
                expect(output.error).to.include('Unknown or missing qry');
                done(null);
            });
        });

        describe('getting status information', function () {
            it('should complain if the parameters of getStatus are missing', function (done) {
                var request = {qry:"getStatus"};
                getJSON('http://localhost:5300/rest/RptGen', request, function(output) {
                    checkIncluded(request, output);
                    expect(output).to.include.keys('error');
                    expect(output.error).to.include('contents_hash missing');
                    expect(output.error).to.include('start_ts missing');
                    done(null);
                });
            });

            it('should complain if the contents_hash is not valid', function (done) {
                var request = {qry:"getStatus", contents_hash:"BAD"};
                getJSON('http://localhost:5300/rest/RptGen', request, function(output) {
                    checkIncluded(request, output);
                    expect(output).to.include.keys('error');
                    expect(output.error).to.include('contents_hash fails regex');
                    expect(output.error).to.include('start_ts missing');
                    done(null);
                });
            });

            it('should complain if the start_ts is not valid', function (done) {
                var request = {qry:"getStatus", start_ts:"BAD"};
                getJSON('http://localhost:5300/rest/RptGen', request, function(output) {
                    checkIncluded(request, output);
                    expect(output).to.include.keys('error');
                    expect(output.error).to.include('contents_hash missing');
                    expect(output.error).to.include('start_ts fails regex');
                    done(null);
                });
            });

            it('should complain if task is not present', function (done) {
                var uTime = 1234567890123;
                var start_ts = ts.msUnixTimeToTimeString(uTime);
                var hash = md5hex("sample content");
                var request = {qry:"getStatus", start_ts:start_ts, contents_hash:hash };
                getJSON('http://localhost:5300/rest/RptGen', request, function(output) {
                    checkIncluded(request, output);
                    expect(output).to.include.keys('status');
                    expect(output.status).to.eql(rptGenStatus.TASK_NOT_FOUND);
                    expect(output).to.include.keys('msg');
                    expect(output.msg).to.include('unknown task');
                    done(null);
                });
            });

            it('should retrieve status from a prescribed file', function (done) {
                var uTime = 1234567890123;
                var start_ts = ts.msUnixTimeToTimeString(uTime);
                var hash = md5hex("sample content");
                // Generate the directories for the status file. Note the directory name
                //  for the timestamp is leading zero-padded to a width of 13 characters
                this.request_ts = ts.msUnixTimeToTimeString(ts.getMsUnixTime());
                var dirName = formatNumberLength(uTime, 13);
                var instrDir = path.join(ROOT_DIR, hash, dirName);
                mkdirp.sync(instrDir, null);
                var fname = path.join(instrDir, 'status.dat');
                var statObject = {status:1234, floodle:5678};
                fs.writeFileSync(fname, JSON.stringify(statObject));
                var request = {qry:"getStatus", start_ts:start_ts, contents_hash:hash };
                getJSON('http://localhost:5300/rest/RptGen', request, function(output) {
                    checkIncluded(request, output);
                    checkIncluded(statObject, output);
                    rmdir(instrDir);
                    done(null);
                });
            });

            it('should retrieve status from a large collection of files', function (done) {
                this.timeout(5000);
                var uTime, uTimes = [];
                var hash, hashes = [];
                var status, statusList = [];
                var nRequests = 1000;
                for (var i=0; i<nRequests; i++) {
                    hash = md5hex("Picarro" + i);
                    uTime = Math.floor(Math.random() * 2000000000000);
                    status = Math.floor(Math.random() * 100000);
                    hashes.push(hash);
                    uTimes.push(uTime);
                    statusList.push(status);
                    var dirName = formatNumberLength(uTime, 13);
                    var instrDir = path.join(ROOT_DIR, hash, dirName);
                    mkdirp.sync(instrDir, null);
                    var fname = path.join(instrDir, 'status.dat');
                    var statObject = {status:status, index:i};
                    fs.writeFileSync(fname, JSON.stringify(statObject));
                }
                var nPending = nRequests;
                for (i=0; i<nRequests; i++) {
                    hash = hashes[i];
                    uTime = uTimes[i];
                    var start_ts = ts.msUnixTimeToTimeString(uTime);
                    var request = {qry:"getStatus", start_ts:start_ts, contents_hash:hash };
                    getJSON('http://localhost:5300/rest/RptGen', request, function(output) {
                        expect(output).to.include.keys(["index","status"]);
                        var index = output["index"];
                        expect(output.status).to.eql(statusList[index]);
                        expect(output.contents_hash).to.eql(hashes[index]);
                        expect(output.start_ts).to.eql(ts.msUnixTimeToTimeString(uTimes[index]));
                        nPending -= 1;
                        if (nPending === 0) done(null);
                    });
                }
            });
        });
    });
});
