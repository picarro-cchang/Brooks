/* newUserJobDatabase.js maintains a simple file-based database to save list of jobs that a user has initiated */

/*global require, module */
/*jshint undef:true, unused:true */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    var dirty = require('dirty');
    var fs = require('fs');
    var mkdirp = require('mkdirp');
    var path = require('path');
    var _ = require('underscore');

    function UserJobDatabase(rootDir) {
        this.rootDir = rootDir;
        this.usersDir = path.join(rootDir,'users');
        this.activeUsers = {};
    }

    UserJobDatabase.prototype.getDatabase = function(user, done) {
        // Get the database corresponding to this user, adding it to activeUsers if necessary
        var that = this;
        var dirName = path.join(that.usersDir, user);
        var db;
        if (!that.activeUsers.hasOwnProperty(user)) {
            // Find existing database or make a new one. In either case, only call done once the
            //  database has loaded
            mkdirp(dirName, null, function (err) {
                if (err) done(err);
                else {
                    // Find the file with the lexically largest name in the directory
                    fs.readdir(dirName, function (err, files) {
                        if (err) done(err);
                        else {
                            if (_.isEmpty(files)) {
                                var fname = path.join(dirName,(new Date()).valueOf() + '.db');
                                db = that.activeUsers[user] = dirty(fname);
                            }
                            else {
                                files.sort();
                                var lastFile = path.join(dirName,files[files.length-1]);
                                db = that.activeUsers[user] = dirty(lastFile);
                            }
                            db.on('load', function() { done(null, db); });
                        }
                    });
                }
            });
        }
        else {
            // User is already active, return database from cache
            db = that.activeUsers[user];
            done(null, db);
        }
    };

    UserJobDatabase.prototype.getAllData = function(user, done) {
        this.getDatabase(user, function (err, db) {
            if (err) done(err);
            else {
                var documents = [];
                db.forEach(function (key, document) {
                    documents.push(document);
                });
                done(null, documents);
            }
        });
    };

    UserJobDatabase.prototype.compressDatabaseAndGetAllData = function(user, done) {
        var that = this;
        that.getDatabase(user, function (err, db) {
            if (err) done(err);
            else {
                // Make a new database which is derived from the old
                var oldPath = db.path;
                var newPath = oldPath.replace(/[0-9]+\.db/,(new Date()).valueOf() + '.db');
                var dbCompressed = dirty(newPath);
                var documents = [];
                db.forEach(function (key, document) {
                    dbCompressed.set(key, document);
                    documents.push(document);
                });
                that.closeDatabase(user, function () {
                    that.activeUsers[user] = dbCompressed;
                    fs.unlink(oldPath, function (err) {
                        if (err) done(err);
                        else done(null, documents);
                    });
                });
            }
        });
    };

    UserJobDatabase.prototype.updateDatabase = function(user, action, document, done) {
        var key = document.hash + '_' + document.directory;
        this.getDatabase(user, function (err, db) {
            if (action === 'add' || action === 'update') {
                db.set(key, document, done);
            }
            else if (action === 'delete') {
                db.rm(key, done);
            }
        });
    };

    UserJobDatabase.prototype.closeDatabase = function(user, done) {
        // This is needed to close the file that stores the database for a user
        var that = this;
        if (that.activeUsers.hasOwnProperty(user)) {
            var db = that.activeUsers[user];
            delete that.activeUsers[user];
            db._writeStream.end();
            db._writeStream.on('close',done);
        }
        else done();
    };

    UserJobDatabase.prototype.closeAll = function(done) {
        // Close all the files that store the databases
        var that = this;
        if (_.isEmpty(that.activeUsers)) done();
        else {
            var user = _.keys(that.activeUsers)[0];
            that.closeDatabase(user, function () { that.closeAll(done); });
        }
    };

    module.exports = function (rootDir) { return new UserJobDatabase(rootDir); };
});
