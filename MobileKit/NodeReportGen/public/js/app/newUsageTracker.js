/* newUsageTracker.js */
/*global alert, module, require */
/* jshint undef:true, unused:true */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var _ = require('underscore');
    var newIdTracker = require('app/newIdTracker');

    // use and release are used to keep track of whether the page is ready to be printed out. Every time
    //  a redering process is initiated, use is called and whenever it ends, release is called. The noneLeft
    //  function is called if there are no entries pending this.waitForFinish milliseconds after everything
    //  has been released

    function UsageTracker() {
        this.pending = {};
        this.idTracker = newIdTracker();
        this.firstFlag = true;
        this.timer = null;
        this.waitForFinish = 200;
    }

    UsageTracker.prototype.use = function (obj, first) {
        var id = this.idTracker.objectId(obj);
        if (id === null) return;
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
        if (!this.pending.hasOwnProperty(id)) {
            this.pending[id] = 0;
        }
        this.pending[id] += 1;
        if (_.isFunction(first) && this.firstFlag) {
            this.firstFlag = false;
            first();
        }
    };

    UsageTracker.prototype.release = function(obj, noneLeft) {
        var id = this.idTracker.objectId(obj);
        if (id !== null) {
            if (!this.pending.hasOwnProperty(id)) alert("Error in usage tracking algorithm");
            else {
                this.pending[id] -= 1;
            }
            if (this.pending[id] === 0) delete this.pending[id];
        }
        if (_.isFunction(noneLeft) && _.isEmpty(this.pending)) {
            if (this.timer) clearTimeout(this.timer);
            this.timer = setTimeout(function () {
                if (_.isEmpty(this.pending)) {
                    this.firstFlag = true;
                    this.timer = null;
                    noneLeft();
                }
            }, this.waitForFinish);
        }
    };
    module.exports = function () { return new UsageTracker(); };
});
