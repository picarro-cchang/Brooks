/*global console, describe, afterEach, beforeEach, it, require  */
/* jshint -W030, -W024, -W097 */
/*jshint undef:true, unused:true */
'use strict';
var expect = require("chai").expect;
var fs = require("fs");
var mkdirp = require("mkdirp");
var sf = require("../lib/statusFiles");
var path = require("path");
var rmTreeSync = require("../lib/rmTree").rmTreeSync;
var rootDir = "/temp/StatusFiles";


function process(object, methodName, args, onSuccess) {
    return {this: object, method: methodName, args: args, onSuccess: onSuccess};
}

function sequence(process_array,done) {
    if (process_array.length === 0) done();
    else {
        var work = process_array.shift();
        var that = work.this;
        var next = function(err) { if (err) done(err); else sequence(process_array, done); };
        var callback = function(err) {
            if (err) done(err);
            else if (work.onSuccess) {
                var args = Array.prototype.slice.call(arguments,1).concat(next);
                work.onSuccess.apply(that, args);
            }
            else sequence(process_array, done);
        };
        that[work.method].apply(that, work.args.concat(callback));
    }
}

describe('Status File Processor', function() {
    describe('Adding, Updating and Deleting', function () {
        beforeEach(function (done) {
            rmTreeSync(rootDir);
            mkdirp.sync(rootDir);
            expect(fs.existsSync(rootDir));
            done();
        });

        it('should allow a simple status file to be written and read', function (done) {
            var fname = path.join(rootDir,'file1');
            var stat1 = {'status': 'good', 'msg': 'Hello'};
            sf.writeStatus(fname, stat1);
            sf.readStatus(fname, function (err, result) {
                expect(err).to.equal(null);
                expect(result).to.deep.equal(stat1);
                done(null);
            });
        });

        it('should allow several status objects to be composed', function (done) {
            var fname = path.join(rootDir,'file1');
            var stat1 = {'status': 'good', 'msg': 'Hello'};
            var stat2 = {'status': 'so-so', 'why': 'There'};
            sf.writeStatus(fname, stat1);
            sf.writeStatus(fname, stat2);
            sf.readStatus(fname, function (err, result) {
                expect(err).to.equal(null);
                expect(result).to.deep.equal({'status': 'so-so', 'msg': 'Hello', 'why': 'There'});
                done(null);
            });
        });

        it('should work with several status files', function (done) {
            var fname1 = path.join(rootDir,'file1');
            var fname2 = path.join(rootDir,'file2');
            var stat1 = {'status': 'good', 'msg': 'Hello'};
            var stat2 = {'status': 'so-so', 'why': 'There'};
            sf.writeStatus(fname1, stat1);
            sf.writeStatus(fname2, stat2);
            sf.readStatus(fname2, function (err, result) {
                expect(err).to.equal(null);
                expect(result).to.deep.equal(stat2);
                sf.readStatus(fname1, function (err, result) {
                    expect(err).to.equal(null);
                    expect(result).to.deep.equal(stat1);
                    done(null);
                });
            });
        });


        it('should work with composition and several status files', function (done) {
            var fname1 = path.join(rootDir,'file1');
            var fname2 = path.join(rootDir,'file2');
            var stat1 = {'status': 'good', 'msg': 'Hello'};
            var stat2 = {'status': 'so-so', 'why': 'There'};
            var stat3 = {'status': 'bad', 'err': 'Confused'};
            sf.writeStatus(fname1, stat1);
            sf.writeStatus(fname2, stat1);
            sf.writeStatus(fname1, stat2);
            sf.writeStatus(fname2, stat3);
            sf.readStatus(fname2, function (err, result) {
                expect(err).to.equal(null);
                expect(result).to.deep.equal({'status': 'bad', 'msg': 'Hello', 'err': 'Confused'});
                sf.readStatus(fname1, function (err, result) {
                    expect(err).to.equal(null);
                    expect(result).to.deep.equal({'status': 'so-so', 'msg': 'Hello', 'why': 'There'});
                    done(null);
                });
            });
        });
    });
});
