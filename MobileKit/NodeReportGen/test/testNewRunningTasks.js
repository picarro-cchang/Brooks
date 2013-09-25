/*global describe, afterEach, beforeEach, it, require  */
/* jshint -W030, -W024, -W097 */
/*jshint undef:true, unused:true */
'use strict';
var expect = require("chai").expect;
var fs = require("fs");
var mkdirp = require("mkdirp");
var nRT = require("../lib/newRunningTasks");
var path = require("path");
var rmTreeSync = require("../lib/rmTree").rmTreeSync;
var rootDir = "/temp/RunningTaskTest";
var rptGenStatus = require('../public/js/common/rptGenStatus');
var sf = require("../lib/statusFiles");

describe('Running Task Support', function() {
    var rt;
    describe('Starting and Ending Tasks', function () {
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
        it('should allow more than one task to be started', function(done) {
            var taskKey1 = '23456_78901';
            var taskKey2 = '98765_43210';
            rt.startTask(taskKey1);
            var running = rt.startTask(taskKey2);
            expect(running).to.have.ownProperty(taskKey1);
            expect(running).to.have.ownProperty(taskKey2);
            expect(running).to.not.have.ownProperty('12345_67890');
            expect(rt.isRunning(taskKey1)).to.be.true;
            expect(rt.isRunning(taskKey2)).to.be.true;
            rt.waitEmpty(function () {
                expect(JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'))).to.eql(running);
                done();
            });
        });
        it('should throw an error when starting a previously started task', function() {
            var taskKey1 = '23456_78901';
            rt.startTask(taskKey1);
            expect(rt.startTask,taskKey1).to.throw(Error);
        });
        it('should allow tasks to be ended', function(done) {
            var taskKey1 = '23456_78901';
            var taskKey2 = '98765_43210';
            var taskKey3 = '45678_09234';
            var running = rt.startTask(taskKey1);
            running = rt.startTask(taskKey2);
            expect(running).to.have.ownProperty(taskKey1);
            expect(running).to.have.ownProperty(taskKey2);
            running = rt.endTask(taskKey1);
            expect(running).not.to.have.ownProperty(taskKey1);
            expect(running).to.have.ownProperty(taskKey2);
            running = rt.startTask(taskKey3);
            expect(running).not.to.have.ownProperty(taskKey1);
            expect(running).to.have.ownProperty(taskKey2);
            expect(running).to.have.ownProperty(taskKey3);
            rt.waitEmpty(function () {
                expect(JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'))).to.eql(running);
                done();
            });
        });
        it('should throw an error when ending a non-existent task', function() {
            var taskKey1 = '23456_78901';
            expect(rt.endTask,taskKey1).to.throw(Error);
        });
    });
    describe('Tidying up orphan tasks', function () {
        var taskKey1, taskKey2;
        beforeEach(function (done) {
            rmTreeSync(rootDir);
            mkdirp.sync(rootDir);
            expect(fs.existsSync(rootDir));
            var rt0 = nRT(rootDir);
            taskKey1 = '23456_78901';
            taskKey2 = '98765_43210';
            rt0.startTask(taskKey1);
            rt0.startTask(taskKey2);
            rt0.waitEmpty(function () {
                rt = nRT(rootDir);
                done();
            });
        });
        afterEach(function (done) {
            // Make sure all file operations complete
            rt.waitEmpty(done);
        });
        it('should start with the correct orphan tasks', function (done) {
            var orphans = JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'));
            expect(orphans).to.have.ownProperty(taskKey1);
            expect(orphans).to.have.ownProperty(taskKey2);
            done();
        });
        it('should invalidate status for the orphan tasks 1', function (done) {
            var dir1 = path.join(rt.rootDir,'23456','78901');
            var stat1 = path.join(dir1,'status.dat');
            var dir2 = path.join(rt.rootDir,'98765','43210');
            var stat2 = path.join(dir2,'status.dat');
            mkdirp.sync(dir1);
            mkdirp.sync(dir2);
            sf.writeStatus(stat1, { status:rptGenStatus.IN_PROGRESS });
            sf.writeStatus(stat2, { status:rptGenStatus.DONE });
            next();
            function next() {
                var orphans = JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'));
                expect(orphans).to.have.ownProperty(taskKey1);
                expect(orphans).to.have.ownProperty(taskKey2);
                rt.handleIncompleteTasksOnStartup(function() {
                    sf.readStatus(stat1, function(err, data) {
                        expect(err).to.be.null;
                        expect(data.status).to.equal(rptGenStatus.FAILED);
                        sf.readStatus(stat2, function(err, data) {
                            expect(err).to.be.null;
                            expect(data.status).to.equal(rptGenStatus.DONE);
                            rt.waitEmpty(function () {
                                expect(JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'))).to.eql({});
                                done();
                            });
                        });
                    });
                });
            }
        });
        it('should invalidate status for the orphan tasks 2', function (done) {
            var dir1 = path.join(rt.rootDir,'23456','78901');
            var stat1 = path.join(dir1,'status.dat');
            var dir2 = path.join(rt.rootDir,'98765','43210');
            var stat2 = path.join(dir2,'status.dat');
            mkdirp.sync(dir1);
            mkdirp.sync(dir2);
            sf.writeStatus(stat1, { status:rptGenStatus.IN_PROGRESS });
            sf.writeStatus(stat2, { status:rptGenStatus.IN_PROGRESS });
            next();
            function next() {
                var orphans = JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'));
                expect(orphans).to.have.ownProperty(taskKey1);
                expect(orphans).to.have.ownProperty(taskKey2);
                rt.handleIncompleteTasksOnStartup(function() {
                    sf.readStatus(stat1, function(err, data) {
                        expect(err).to.be.null;
                        expect(data.status).to.equal(rptGenStatus.FAILED);
                        sf.readStatus(stat2, function(err, data) {
                            expect(err).to.be.null;
                            expect(data.status).to.equal(rptGenStatus.FAILED);
                            rt.waitEmpty(function () {
                                expect(JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'))).to.eql({});
                                done();
                            });
                        });
                    });
                });
            }
        });
        it('should handle missing status files', function (done) {
            var dir1 = path.join(rt.rootDir,'23456','78901');
            var stat1 = path.join(dir1,'status.dat');
            var dir2 = path.join(rt.rootDir,'98765','43210');
            var stat2 = path.join(dir2,'status.dat');
            mkdirp.sync(dir1);
            mkdirp.sync(dir2);
            sf.writeStatus(stat2, { status:rptGenStatus.IN_PROGRESS });
            next();
            function next() {
                var orphans = JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'));
                expect(orphans).to.have.ownProperty(taskKey1);
                expect(orphans).to.have.ownProperty(taskKey2);
                rt.handleIncompleteTasksOnStartup(function() {
                    sf.readStatus(stat1, function(err, data) {
                        expect(err).not.to.be.null;
                        expect(data).to.be.undefined;
                        sf.readStatus(stat2, function(err, data) {
                            expect(err).to.be.null;
                            expect(data.status).to.equal(rptGenStatus.FAILED);
                            rt.waitEmpty(function () {
                                expect(JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'))).to.eql({});
                                done();
                            });
                        });
                    });
                });
            }
        });
        it('should handle missing status directories', function (done) {
            var dir2 = path.join(rt.rootDir,'98765','43210');
            var stat2 = path.join(dir2,'status.dat');
            mkdirp.sync(dir2);
            sf.writeStatus(stat2, { status:rptGenStatus.IN_PROGRESS });
            next();
            function next() {
                var orphans = JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'));
                expect(orphans).to.have.ownProperty(taskKey1);
                expect(orphans).to.have.ownProperty(taskKey2);
                rt.handleIncompleteTasksOnStartup(function() {
                    sf.readStatus(stat2, function(err, data) {
                        expect(err).to.be.null;
                        expect(data.status).to.equal(rptGenStatus.FAILED);
                        rt.waitEmpty(function () {
                            expect(JSON.parse(fs.readFileSync(rt.tasksFile,'ascii'))).to.eql({});
                            done();
                        });
                    });
                });
            }
        });
    });
});
