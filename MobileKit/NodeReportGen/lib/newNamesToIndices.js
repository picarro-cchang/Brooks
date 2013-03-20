/* newNamesToIndices.js makes an object which translates names to indices */
/*global exports, module, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    var _ = require('underscore');

    /****************************************************************************/
    /*  Store forward and reverse mapping between names and indices             */
    /****************************************************************************/
    function NamesToIndices() {
        this.indexByName = {};
        this.nameByIndex = [];
    }

    NamesToIndices.prototype.getName = function(index) {
        return this.nameByIndex[index];
    };

    NamesToIndices.prototype.getIndex = function(name) {
        if (!_.has(this.indexByName, name)) {
            this.indexByName[name] = this.nameByIndex.length;
            this.nameByIndex.push(name);
        }
        return this.indexByName[name];
    };

    NamesToIndices.prototype.getAllNames = function() {
        var result = {};
        this.nameByIndex.forEach(function (n, i) {
            result[i] = n;
        });
        return result;
    };

    function newNamesToIndices() {
        return new NamesToIndices();
    }

    module.exports = newNamesToIndices;

});
