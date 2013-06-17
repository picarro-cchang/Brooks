/* inKml.js reads a KML file into a JSON object  */
/*global console, module, process, require */
/*jshint undef:true, unused:true */

'use strict';
var et = require('elementtree');
var fs = require('fs');
var gh = require('../lib/geohash');

var data = fs.readFileSync("PlasticMain_After1983_LN.kml","utf8");
// Search for the start of the file, which should be "<"
var start = data.indexOf("<");
if (start > 10) {
    throw new Error("Cannot find starting element of XML file");
}
var tree = et.parse(data.substr(start));
var filter = ".//LineString//coordinates";
// var filter = ".//Point//coordinates";
var results = tree.findall(filter);
var maxLoops = 10;

var start = (new Date()).valueOf();
// "results" is an array of elements which match the given filter
// We need to extract the "text" attribute of each element which consists
//  of white-space separated triples, each triple being of the form 
//  latitude,longitude,height. The triples of an element are the successive
//  coordinates of a polyline (called a segment). We want to geohash encode 
//  these coordinates and place the segments into the "segments" array.   
var segments = [];
function next() {
    var segment;
    function getSegment(p) {
        if (p) {
            var coords = [];
            p.split(',').forEach(function (c) {
                coords.push(+c);
            });
            segment.push(gh.encodeGeoHash(coords[1], coords[0]));
        }
    }
    var nLoops = (results.length > maxLoops) ? maxLoops : results.length;
    for (var i=0; i<nLoops; i++) {
        var e = results.shift();
        var points = e.text.split(/\s+/);
        segment = [];
        points.forEach(getSegment);
        segments.push({P:segment});
    }
    if (results.length === 0) {
        console.log(JSON.stringify(segments,null,2));
        console.log("Done: " + ((new Date()).valueOf() - start));
    }
    else process.nextTick(next);
}
next();
