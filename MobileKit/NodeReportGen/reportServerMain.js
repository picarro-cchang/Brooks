/*global console, __dirname, require */
var requirejs = require('requirejs');

requirejs.config({
    nodeRequire: require,
    basePath: __dirname
});

requirejs(['reportServer1'],
function(reportServer) {
    reportServer();
});
