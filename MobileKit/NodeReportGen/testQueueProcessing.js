// Get result of long running task from Pcubed
/*global console, exports, process, require */

'use strict';

var util = require('util');
var _ = require('underscore');

function myProcess(inData, func, maxLoops, done) {
    var outData = [];
    function next() {
        var nLoops = (inData.length > maxLoops) ? maxLoops : inData.length;
        for (var i=0; i<inData.length; i++) {
            outData.push(func(inData.shift()));
        }
        if (inData.length === 0) done(null, outData);
        else process.nextTick(next);
    }
    next();
}

function myFunc(x) {
    return x*x;
}

var inData = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20];
myProcess(inData, myFunc, 3, function (err,result) {
    if (err) console.log("Error: " + err);
    else console.log(JSON.stringify(result));
});
