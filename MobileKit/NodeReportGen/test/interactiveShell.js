/*global __dirname, console, process, require  */
/* jshint -W030, -W024, -W097 */
/*jshint undef:true, unused:true */

/* Start and stop report server running in a subprocess */

'use strict';
var cp = require("child_process");
var path = require("path");

var spawn = cp.spawn,
    shell = spawn("cmd", [], {"cwd": path.join(__dirname,"..")});

process.stdin.setRawMode(true);
process.stdin.resume();
process.stdin.setEncoding('utf8');

function listener(text) {
    shell.stdin.write(text);
    if (text === "\r") shell.stdin.write("\n");  
}

process.stdin.on('data', listener);

shell.stdout.on('data', function (data) {
    var nl;
    data = data.toString();
    while ((nl = data.indexOf("\n")) >= 0) {
        process.stdout.write(data.substr(0,nl) + "| ");
        data = data.substr(nl+1);
    }
    process.stdout.write(data);
});

shell.on('close', function (code) {
    console.log('child process exited with code ' + code);
    process.stdin.pause();
});
