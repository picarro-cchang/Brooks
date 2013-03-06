// checkPdfConvertMain.js
/*global console, requirejs, TEMPLATE_PARAMS */

// See http://backbonetutorials.com/organizing-backbone-using-modules/
// wkhtmltopdf.exe" --javascript-delay 5000 http://localhost:5300/getReport/789b6c577369b4976f90e15eb9a5cc57/1361469440096 test2.pdf
requirejs.config({
    //By default load any module IDs from js/lib
    baseUrl: '/js/lib',
    //except, if the module ID starts with "app",
    //load it from the js/app directory. paths
    //config is relative to the baseUrl, and
    //never includes a ".js" extension since
    //the paths config could be for a directory.
    paths: {
        'app': '/js/app',
        'jquery-migrate': '/js/lib/jquery-migrate-1.1.1.min',
        'underscore': '/js/lib/underscore-min'
    },
    shim: {
        'jquery-migrate': {
            deps: ['jquery']
        },
        'underscore' : {
            exports: '_'
        }
    }
});

requirejs(['app/checkPdfConvert'],
function (checkPdfConvert) {
    'use strict';
    checkPdfConvert.initialize();
});
