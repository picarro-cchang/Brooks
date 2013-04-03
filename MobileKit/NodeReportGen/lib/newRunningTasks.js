/* newRunningTasks.js makes a RunningTask object which is used to store in volatile memory and to
    persist on the disk a collection of running tasks. These are used to handle orphan tasks left
    behind if the server is prematurely stopped */

/*global module, require */
/*jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var events = require('events');
    var fs = require('fs');
    var path = require('path');
    var rptGenStatus = require('../public/js/common/rptGenStatus');
    var sf = require('./statusFiles');
    var util = require('util');
    var _ = require('underscore');

    function RunningTasks(rootDir) {
        events.EventEmitter.call(this); // Allow this to emit events
        this.rootDir = rootDir;
        this.tasksFile = path.join(rootDir, 'RunningTasks.json');
        this.writeFlag = true;
        this.running = {};
        this.saveQueue = [];
    }
    util.inherits(RunningTasks, events.EventEmitter);
    RunningTasks.prototype.isRunning = function (taskKey) {
        return this.running.hasOwnProperty(taskKey);
    };
    RunningTasks.prototype.startTask = function (taskKey) {
        if (taskKey in this.running) throw new Error('startTask failed: task is already running');
        this.running[taskKey] = (new Date()).valueOf();
        this.saveRunning();
        return this.running;
    };
    RunningTasks.prototype.endTask = function (taskKey) {
        if (!(taskKey in this.running)) throw new Error('endTask failed: task is not running');
        delete this.running[taskKey];
        this.saveRunning();
        return this.running;
    };
    RunningTasks.prototype.saveRunning = function() {
        this.saveQueue.push(_.clone(this.running));
        if (this.writeFlag) {
            this.writeFlag = false;
            this.next();
        }
    };
    RunningTasks.prototype.next = function() {
        var that = this;
        if (this.saveQueue.length > 0) {
            var r = this.saveQueue.shift();
            fs.writeFile(this.tasksFile, JSON.stringify(r,null,2), 'ascii', function(err) {
                if (err) throw(new Error('Cannot write to tasks file'));
                else if (that.saveQueue.length > 0) that.next();
                else {
                    that.writeFlag = true;
                    that.emit('queueEmpty');
                }
            });
        }
        else {
            that.writeFlag = true;
            that.emit('queueEmpty');
        }
    };
    RunningTasks.prototype.waitEmpty = function(done) {
        if (!this.writeFlag) {
            this.once('queueEmpty', done);
        }
        else done();
    };
    RunningTasks.prototype.monitor = function (rptGen) {
        var that = this;
        rptGen.on('start', function (d) {
            that.startTask(d.taskKey);
        });
        rptGen.on('success', function (d) {
            that.endTask(d.taskKey);
        });
        rptGen.on('fail', function (d) {
            that.endTask(d.taskKey);
        });
    };
    RunningTasks.prototype.handleIncompleteTasksOnStartup = function (done) {
        /* At startup, we need to mark as bad (by changing the status) any tasks which were
            left hanging when the server last went down. This is achieved by looking at the 
            list of tasks in the tasksFile which is on disk. After marking any incomplete 
            tasks from the contents of that file, it should be updated with the current running
            tasks (empty) */
        var that = this;
        fs.readFile(that.tasksFile,'ascii', function (err, data) {
            if (!err) {
                var next;
                var incompleteJobs = _.keys(JSON.parse(data));
                // console.log(incompleteJobs);
                next = function () {
                    if (incompleteJobs.length > 0) {
                        var ij = incompleteJobs.shift();
                        var workDir = path.join(that.rootDir, ij.replace('_', '/'));
                        var statusFile = path.join(workDir,'status.dat');
                        // console.log(workDir);
                        fs.exists(workDir, function (exists) {
                            if (exists) {
                                fs.exists(statusFile, function (exists) {
                                    if (exists) {
                                        // console.log("Status file found: ", statusFile);
                                        sf.readStatus(statusFile, function (err, status) {
                                            // console.log("Status of task: " + status.status);
                                            if (err || (!status.status) || status.status >= rptGenStatus.DONE) next();
                                            else {
                                                // console.log("Marking status as bad: " + statusFile);
                                                sf.writeStatus(statusFile,
                                                {status: rptGenStatus.FAILED, msg:"Server restarted during job"}, next);
                                            }
                                        });
                                    }
                                    else next();
                                });
                            }
                            else next();
                        });
                    }
                    else refresh();
                };
                next();
            }
            else refresh(); // Ignore errors
        });
        function refresh() {
            that.saveRunning();
            that.waitEmpty(done);
        }
    };
    module.exports = function (rootDir) { return new RunningTasks(rootDir); };
});
