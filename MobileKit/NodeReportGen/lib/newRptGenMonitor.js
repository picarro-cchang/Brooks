/* newRptGenMonitor.js makes a RptGenMonitor object which monitors the report generator
and logs when tasks are started and stopped. */

/*global require, module */
/*jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var events = require('events');
    var fs = require('fs');
    var path = require(path);
    var util = require('util');

    function RptGenMonitor(rootDir) {
        events.EventEmitter.call(this); // Allow this to emit events
        this.logMessages = [];
        this.writeFlag = true;
        this.logFile = path.join(rootDir, 'ReportGen.log');
        this.saveLog('/* RESTARTING at ' + (new Date()).toISOString() + ' */\n');
    }
    util.inherits(RptGenMonitor, events.EventEmitter);

    RptGenMonitor.prototype.monitor = function (rptGen) {
        var that = this;
        rptGen.on('start', function (d) {
            that.saveLog('start: ' + JSON.stringify(d));
        });
        rptGen.on('success', function (d) {
            that.saveLog('success: ' + JSON.stringify(d));
        });
        rptGen.on('fail', function (d) {
            that.saveLog('fail: ' + JSON.stringify(d));
        });
    };

    RptGenMonitor.prototype.next = function() {
        var that = this;
        if (this.logMessages.length > 0) {
            var string = that.logMessages.join("\n") + "\n";
            this.logMessages = [];
            fs.appendFile(that.logFile, string, 'ascii', function (err) {
                if (err) throw(new Error('Cannot write to log file'));
                else if (that.logMessages.length > 0) that.next();
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

    RptGenMonitor.prototype.saveLog = function (msg) {
        this.logMessages.push(msg);
        if (this.writeFlag) {
            this.writeFlag = false;
            this.next();            
        }
    };

    RptGenMonitor.prototype.waitEmpty = function(done) {
        if (!this.writeFlag) {
            this.once('queueEmpty', done);
        }
        else done();
    };

    module.exports = function (rootDir) { return new RptGenMonitor(rootDir); };
});
