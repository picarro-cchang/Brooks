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
var path = require("path");
var url = require("url");
var rptSrv;

var ROOT_DIR = "/temp/testing";

var rmdir = function(dir) {
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
};

describe('reportServer', function() {
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
                    expect(result).to.equal("testUrl");
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
                    expect(result).to.equal(testContents);
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
                    expect(result).to.equal(buff.toString("ascii"));
                    done(null);
                });

            }).end();
        });
    });

    function getJSON(qry_url, params, callback) {
        var options = url.parse(qry_url);
        options.query = params;
        options.method = 'GET';
        getRest(options, function (err, statusCode, output) {
            expect(err).to.be.null;
            expect(statusCode).to.equal(200);
            callback(JSON.parse(output));
        });
    }

    describe('timezone conversion', function() {
        it('should convert POSIX time to GMT', function (done) {
            getJSON('http://localhost:5300/rest/tz', {tz:"GMT", posixTimes:[0,1367883839000]}, function(output) {
                expect(output["timeStrings"][0]).to.equal("1970-01-01 00:00:00+0000 (UTC)");
                expect(output["timeStrings"][1]).to.equal("2013-05-06 23:43:59+0000 (UTC)");
                done(null);
            });
        });

        it('should convert POSIX time to local time', function (done) {
            getJSON('http://localhost:5300/rest/tz', {tz:"America/Los_Angeles", posixTimes:[0,1367883839000]}, function(output) {
                expect(output["timeStrings"][0]).to.equal("1969-12-31 16:00:00-0800 (PST)");
                expect(output["timeStrings"][1]).to.equal("2013-05-06 16:43:59-0700 (PDT)");
                done(null);
            });
        });

        it('should convert local time to POSIX time', function (done) {
            getJSON('http://localhost:5300/rest/tz', {tz:"America/Los_Angeles",
                timeStrings:["1969-12-31 16:00:00","2013-05-06 16:43:59"]}, function(output) {
                expect(output["timeStrings"][0]).to.equal("1969-12-31 16:00:00-0800 (PST)");
                expect(output["timeStrings"][1]).to.equal("2013-05-06 16:43:59-0700 (PDT)");
                expect(output["posixTimes"][0]).to.equal(0);
                expect(output["posixTimes"][1]).to.equal(1367883839000);
                done(null);
            });
        });

        it('should handle a single element (not an array)', function (done) {
            getJSON('http://localhost:5300/rest/tz', {tz:"GMT", timeStrings:["1970-01-01 00:00:00"]}, function(output) {
                expect(output["timeStrings"][0]).to.equal("1970-01-01 00:00:00+0000 (UTC)");
                expect(output["posixTimes"][0]).to.equal(0);
                done(null);
            });
        });
    });

    describe('RptGen rest calls', function () {
        it('should object to a missing command', function (done) {
            getJSON('http://localhost:5300/rest/RptGen', {}, function(output) {
                expect(output).to.include.keys('error');
                expect(output.error).to.include('Unknown or missing qry');
                done(null);
            });
        });

        it('should object to an invalid command', function (done) {
            getJSON('http://localhost:5300/rest/RptGen', {qry:"invalid"}, function(output) {
                expect(output).to.include.keys('error');
                expect(output.error).to.include('Unknown or missing qry');
                done(null);
            });
        });

        describe('getting status information', function () {
            it('should complain if the parameters of getStatus are missing', function (done) {
                getJSON('http://localhost:5300/rest/RptGen', {qry:"getStatus"}, function(output) {
                    expect(output).to.include.keys('error');
                    expect(output.error).to.include('contents_hash missing');
                    expect(output.error).to.include('start_ts missing');
                    done(null);
                });
            });

            it('should complain if the contents_hash is not valid', function (done) {
                getJSON('http://localhost:5300/rest/RptGen', {qry:"getStatus", contents_hash:"BAD"}, function(output) {
                    expect(output).to.include.keys('error');
                    expect(output.error).to.include('contents_hash fails regex');
                    expect(output.error).to.include('start_ts missing');
                    done(null);
                });
            });

            it('should complain if the start_ts is not valid', function (done) {
                getJSON('http://localhost:5300/rest/RptGen', {qry:"getStatus", start_ts:"BAD"}, function(output) {
                    expect(output).to.include.keys('error');
                    expect(output.error).to.include('contents_hash missing');
                    expect(output.error).to.include('start_ts fails regex');
                    done(null);
                });
            });

        });
    });
});
