/* rptGenStatus.js defines status codes for report generation */
/*global exports, module, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    module.exports = {
        "OTHER_ERROR": -128,
        "FAILED": -4,
        "BAD_PARAMETERS": -2,
        "TASK_NOT_FOUND": -1,
        "NOT_STARTED": 0,
        "IN_PROGRESS": 1,
        "DUPLICATE": 2,
        "DONE": 16,
        "DONE_NO_PDF": 16,
        "DONE_WITH_PDF": 17
    };
});
