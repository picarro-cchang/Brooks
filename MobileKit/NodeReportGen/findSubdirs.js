// Enumerate the subdirectories of a specified path
/*globals console, require */

'use strict';
var fs = require('fs');
var path = require('path');
var dname = "c:/temp";

var getSubDirs1 = function (dname, done) {
    var subDirs = [];
    fs.readdir(dname, function(err, list) {
        var pending = list.length;
        var checkStatFor = function(fname) {
            return  function(err, stat) {
                if (err) done(err);
                else {
                    if (stat.isDirectory()) subDirs.push(fname);
                    pending -= 1;
                    if (pending === 0) done(null, subDirs.sort());
                }
            };
        };
        if (err) done(err);
        else if (list.length === 0) done(null, []);
        else {
            for (var i=0; i<list.length; i++) {
                var fname = list[i];
                fs.stat(path.join(dname,fname), checkStatFor(fname));
            }
        }
    });
};
/*
getSubDirs1(dname, function (err, dlist) {
    if (err) console.log(err);
    else console.log(dlist);
});
*/
var getSubDirs = function (dname, done) {
    var subDirs = [];
    fs.readdir(dname, function(err, list) {
        var pending = list.length;
        if (err) done(err);
        else if (pending === 0) done(null, []);
        else {
            list.forEach(function (fname) {
                fs.stat(path.join(dname,fname), function (err, stat) {
                    if (err) done(err);
                    else {
                        if (stat.isDirectory()) subDirs.push(fname);
                        pending -= 1;
                        if (pending === 0) done(null, subDirs.sort());
                    }
                });
            });
        }
    });
};

getSubDirs("c:/temp/KMLatmos/Empty", function (err, dlist) {
    if (err) console.log(err);
    else console.log(dlist);
});


// Recursive get of subdirectories
var getAllSubDirs = function (dname, done) {
    var allSubDirs = [];

    getSubDirs(dname, function (err, dlist) {
        //console.log(dlist);
        if (err) done(err);
        else {
            var pending = dlist.length;
            //console.log(pending);
            if (pending === 0) done(null, []);
            else {
                dlist.forEach( function (subDir) {
                    allSubDirs.push(subDir);
                    //console.log(allSubDirs);
                    var subPath = path.join(dname, subDir);
                    // console.log(subPath);
                    getAllSubDirs(subPath, function (err, results) {
                        //console.log(results);
                        if (err) done(err);
                        else {
                            results.forEach( function (r) {
                                allSubDirs.push(path.join(subDir, r));
                            });
                            pending -= 1;
                            if (pending === 0) done(null, allSubDirs);
                        }
                    });
                });
            }
        }    
    });
};

getAllSubDirs("c:/temp/KMLatmos", function (err, dlist) {
    if (err) console.log(err);
    else console.log(dlist.sort());
});


var walk = function(dir, done) {
  var results = [];
  fs.readdir(dir, function(err, list) {
    if (err) return done(err);
    var pending = list.length;
    if (!pending) return done(null, results);
    list.forEach(function(file) {
      file = dir + '/' + file;
      fs.stat(file, function(err, stat) {
        if (stat && stat.isDirectory()) {
          walk(file, function(err, res) {
            results = results.concat(res);
            if (!--pending) done(null, results);
          });
        } else {
          results.push(file);
          if (!--pending) done(null, results);
        }
      });
    });
  });
};


walk("c:/temp/KMLatmos", function (err, dlist) {
    if (err) console.log(err);
    else console.log(dlist);
});
