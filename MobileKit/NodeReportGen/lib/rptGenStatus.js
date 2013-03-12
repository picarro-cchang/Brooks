/* rptGenStatus.js defines status codes for report generation */
/*global exports, module, require */

(function() {
	'use strict';
    module.exports = {
        "FAILED": -4,
        "BAD_PARAMETERS": -2,
        "TASK_NOT_FOUND": -1,
        "NOT_STARTED": 0,
        "IN_PROGRESS": 1,
        "DUPLICATE": 2,
        "LINKS_AVAILABLE": 12,
        "DONE": 16
    };
})();
