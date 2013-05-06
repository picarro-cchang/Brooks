/*global __dirname, console, describe, after, before, beforeEach, it, process, require  */
/* jshint -W030, -W024, -W097 */
/*jshint undef:true, unused:true */

/* Start and stop report server running in a subprocess */

'use strict';
var expect = require("chai").expect;
var cp = require("child_process");
var fs = require("fs");
var http = require("http");
var path = require("path");
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
                expect(result).to.equal(fs.readFileSync(fname,{encoding:'ascii'}));
                done(null);
            });

        }).end();
    });

});
