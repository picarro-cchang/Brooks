/* rptGenGlobals.js defines the object that stores global data for the node report generation program. */
/*global exports, module, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    module.exports = {
        csp_url: null,
        identity: null,
        psys: null,
        rprocs: null,
        ticket_url: null
    };
});
