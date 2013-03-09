/* dirUtils.js provides functions for finding subdirectories */
/*global exports, module, require */

(function() {
	'use strict';
    var fs = require('fs');
    var path = require('path');

    function getSubDirs(dname, done) {
        // Get top level subdirectories of dname
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
    }

    function getAllSubDirs(dname, done) {
        // Recursively get all subdirectories of dname
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
    }

    exports.getSubDirs = getSubDirs;
    exports.getAllSubDirs = getAllSubDirs;

})();
