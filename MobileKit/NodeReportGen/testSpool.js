// Get result of long running task from Pcubed
/*global console, exports, require */

'use strict';
var fs = require('fs');
var events = require('events');
var newSerializer = require('./lib/newSerializer');
var util = require('util');
var _ = require('underscore');

var eventEmitter = new events.EventEmitter();
var resultFile = "mytest1.txt";

var ser = newSerializer(eventEmitter);

ser.on("data", function (data) {
    fs.appendFile(resultFile,JSON.stringify(data) + "\n", function (err) {
        if (err) console.log('Error appending to file: ' + err);
        else ser.acknowledge();
    });
});

ser.on("end", function () {
    console.log("Done");
});

fs.writeFile(resultFile,'',function (err) {
    if (err) console.log('Error creating file: ' + err);
    else {
        for (var i=0; i<5000; i++) {
            eventEmitter.emit("data",[i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i]);
        }
        eventEmitter.emit("end");
    }
});
