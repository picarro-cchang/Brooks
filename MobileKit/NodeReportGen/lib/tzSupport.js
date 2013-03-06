/* tzSupport.js provides timezone support */
/*global exports, module, require */

(function() {
	'use strict';
    var tz = require('timezone');
    var world = tz(require("timezone/Africa"), require("timezone/America"), require("timezone/Antarctica"),
                   require("timezone/Asia"), require("timezone/Atlantic"), require("timezone/Australia"),
                   require("timezone/Europe"), require("timezone/Indian"), require("timezone/Pacific"));
    module.exports = world;
})();
