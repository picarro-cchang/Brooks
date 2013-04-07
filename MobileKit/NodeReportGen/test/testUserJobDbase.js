/*global console, describe, afterEach, beforeEach, it, require  */
/* jshint -W030, -W024, -W097 */
/*jshint undef:true, unused:true */
'use strict';
var expect = require("chai").expect;
var fs = require("fs");
var mkdirp = require("mkdirp");
var newUJD = require("../lib/newUserJobDatabase");
var path = require("path");
var rmTreeSync = require("../lib/rmTree").rmTreeSync;
var rootDir = "/temp/UserJobs";


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

describe('User Job Database', function() {
    var ujd;
    describe('Adding, Updating and Deleting', function () {
        beforeEach(function (done) {
            rmTreeSync(rootDir);
            mkdirp.sync(rootDir);
            expect(fs.existsSync(rootDir));
            ujd = newUJD(rootDir);
            done();
        });

        afterEach(function (done) {
            ujd.closeAll(done);
        });

        it('should initially return an empty database', function(done) {
            var user = 'myUser';
            sequence([process(ujd,'getAllData',[user], check)], done);

            function check(data, next) {
                expect(ujd.activeUsers).to.have.ownProperty(user);
                expect(fs.existsSync(path.join(rootDir,'users',user)));
                expect(data).to.be.empty;
                next();
            }
        });

        it('should allow addition of one entry', function(done) {
            var user = 'myUser';
            sequence([
                process(ujd,'updateDatabase',[user,'add',{hash:"123456",directory:"789012",name:"Job1",value:1}]),
                process(ujd,'getAllData',[user],check)], done);

            function check(data, next) {
                expect(ujd.activeUsers).to.have.ownProperty(user);
                expect(data).not.to.be.empty;
                expect(data.length).to.equal(1);
                expect(data[0].name).to.equal("Job1");
                next();
            }
        });

        it('should allow addition of several entries', function(done) {
            sequence([
                process(ujd,'getAllData',['user1'], dump),
                process(ujd,'updateDatabase',['user1','add',{hash: "123456", directory: "789012", name: "Job1", value: 26}]),
                process(ujd,'updateDatabase',['user1','add', {hash: "983743", directory: "734235", name: "Job2", value: 40}]),
                process(ujd,'updateDatabase',['user1','add', {hash: "123892", directory: "213123", name: "Job3", value: 39}]),
                process(ujd,'getAllData',['user1'], checkEntries)], done);

            function dump(data,next) {
                expect(data).to.be.empty;
                next();
            }

            function checkEntries(data, next) {
                expect(data.length).to.equal(3);
                expect(data[0].name).to.equal("Job1");
                expect(data[1].name).to.equal("Job2");
                expect(data[2].name).to.equal("Job3");
                next();
            }
        });

        it('should allow an entry to be updated', function(done) {
            var dbase;
            sequence([
                process(ujd,'getDatabase',['user1'], function(db, next) { dbase = db; next(); } ),
                process(ujd,'updateDatabase',['user1','add',{hash: "123456", directory: "789012", name: "Job1", value: 26}]),
                process(ujd,'updateDatabase',['user1','add', {hash: "983743", directory: "734235", name: "Job2", value: 40}]),
                process(ujd,'updateDatabase',['user1','update', {hash: "123456", directory: "789012", name: "Job3", value: 39}]),
                process(ujd,'getAllData',['user1'], checkEntries)], done);

            function checkEntries(data, next) {
                expect(data.length).to.equal(2);
                expect(dbase.get("123456_789012").value).to.equal(39);
                expect(dbase.get("983743_734235").value).to.equal(40);
                next();
            }
        });

        it('should allow an entry to be deleted', function(done) {
            var dbase;
            sequence([
                process(ujd,'getDatabase',['user1'], function(db, next) { dbase = db; next(); } ),
                process(ujd,'updateDatabase',['user1','add',{hash: "123456", directory: "789012", name: "Job1", value: 26}]),
                process(ujd,'updateDatabase',['user1','add', {hash: "983743", directory: "734235", name: "Job2", value: 40}]),
                process(ujd,'updateDatabase',['user1','delete', {hash: "123456", directory: "789012"}]),
                process(ujd,'getAllData',['user1'], checkEntries),
                process(ujd,'compressDatabaseAndGetAllData',['user1']),
                process(ujd,'getDatabase',['user1'], function(db, next) { dbase = db; next(); } ),
                process(ujd,'getAllData',['user1'], checkEntries)], done);

            function checkEntries(data, next) {
                console.log(dbase.path);
                expect(data.length).to.equal(1);
                expect(dbase.get("123456_789012")).to.be.an("undefined");
                expect(dbase.get("983743_734235")).to.eql({hash: "983743", directory: "734235", name: "Job2", value: 40});
                next();
            }
        });


    });
});
