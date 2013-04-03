/*global console, __dirname, require */

requirejs.config({
    baseUrl: '/js/test',
    //except, if the module ID starts with "app",
    //load it from the js/app directory. paths
    //config is relative to the baseUrl, and
    //never includes a ".js" extension since
    //the paths config could be for a directory.
    paths: {
        'app': '/js/app',
        'jquery.jsonp': '/js/lib/jquery.jsonp-2.4.0.min'
    },
    shim: {
        'jquery.jsonp': {
            deps: ['jquery']
        }
    }
});

requirejs(['testP3RestApi', 'chai', 'mocha'],
function(x,chai) {
	mocha.setup({globals:['_jqjsp']});
    mocha.ui('bdd');
    mocha.reporter('html');
    expect = chai.expect;
	x();
    if (window.mochaPhantomJS) {
        mochaPhantomJS.run();
    } else {
        mocha.run();
    }
});
