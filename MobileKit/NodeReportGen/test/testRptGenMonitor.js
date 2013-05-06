/*global describe, afterEach, beforeEach, it, require  */
/* jshint -W030, -W024, -W097 */
/*jshint undef:true, unused:true */
'use strict';
var expect = require("chai").expect;
var fs = require("fs");
var mkdirp = require("mkdirp");
var nRM = require("../lib/newRptGenMonitor");
var path = require("path");
var rmTreeSync = require("../lib/rmTree").rmTreeSync;
var rootDir = "/temp/RptGenMonTest";

describe('Report Generation Logger', function() {
    var rt;

    beforeEach(function () {
        mkdirp.sync(rootDir);
        expect(fs.existsSync(rootDir));
        rt = nRT(rootDir);
    });
    afterEach(function (done) {
        // Make sure all file operations complete
        rt.waitEmpty(done);
    });
    it('should initialize correctly', function() {
        expect(rt.running).to.be.empty;
        expect(rt.saveQueue).to.be.empty;
    });
    it('should allow a task to be started', function(done) {
        var taskKey1 = '12345_67890';
        var running = rt.startTask(taskKey1);
        expect(running).to.have.ownProperty(taskKey1);
        expect(running).to.not.have.ownProperty('dummy');
        expect(running[taskKey1]).to.be.closeTo((new Date()).valueOf(),10);
        expect(rt.isRunning(taskKey1)).to.be.true;
        // The update of the tasksFile takes place asynchronously
        rt.waitEmpty(function () {
            expect(JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'))).to.eql(running);
            done();
        });
        // 
    });
