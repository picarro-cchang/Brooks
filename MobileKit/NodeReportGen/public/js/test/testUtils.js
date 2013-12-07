define(['app/utils','underscore'],
function(utils,_) {
    var hex2RGB = utils.hex2RGB;
    var dec2hex = utils.dec2hex;
    var colorTuple2Hex = utils.colorTuple2Hex;
    var instrResource = utils.instrResource;
    var submapGridString = utils.submapGridString;

    describe('Conversion Routines', function () {
        it('hex2RGB should convert color string', function () {
            expect(hex2RGB("#FF804F")).to.deep.equal([255, 128, 79]);
            expect(hex2RGB("silly")).to.be.false;
        });
        it('dec2hex should convert decimal to hex', function () {
            expect(dec2hex(4093,4)).to.equal("0FFD");
            expect(dec2hex(257,3)).to.equal("101");
        });
        it('colorTuple2Hex should convert decimal tuples to hex bytes', function () {
            expect(colorTuple2Hex([127, 93, 150])).to.equal("7F5D96");
            expect(colorTuple2Hex([255, 128, 150, 19])).to.equal("FF809613");
        });
        it('instrResource should shard MD5 strings by extracting first byte', function () {
            expect(instrResource("0123456789ABCDEF0123456789ABCDEF")).to.equal("/01/0123456789ABCDEF0123456789ABCDEF");
            expect(instrResource("BCDEF0123456789ABCDEF0123456789A")).to.equal("/BC/BCDEF0123456789ABCDEF0123456789A");
        });
        it('submapGridString assigns grid names', function () {
            expect(submapGridString(4,5)).to.equal("E6");
            expect(submapGridString(4,57)).to.equal("E58");
            expect(submapGridString(25,7)).to.equal("Z8");
            expect(submapGridString(26,19)).to.equal("AA20");
            expect(submapGridString(51,19)).to.equal("AZ20");
            expect(submapGridString(52,19)).to.equal("BA20");
            expect(submapGridString(26*26,19)).to.equal("ZA20");
            expect(submapGridString(27*26-1,19)).to.equal("ZZ20");
        });
    });

    var probError = 0.0;
    var numErrors = 0;

    function resetErrors(pError, nErrors) {
        if(typeof(pError)==='undefined') probError = 0.0;
        else probError = pError;
        if(typeof(nErrors)==='undefined') numErrors = 0;
        else numErrors = nErrors;
    }

    function randomDate(start, end) {
        return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
    }

    function mockService(query, errorCbFn, successCbFn) {
        // console.log("Query received: " + JSON.stringify(query));
        var i, posixTimes, result, timeStrings;
        if ("posixTimes" in query) {
            expect(query).to.not.contain.keys("timeStrings");
            timeStrings = [];
            posixTimes = query.posixTimes;
            for (i=0; i<posixTimes.length; i++) {
                timeStrings.push(new Date(posixTimes[i]).toISOString());
            }
            result = _.extend({timeStrings:timeStrings},query);
        }
        else if ("timeStrings" in query) {
            expect(query).to.not.contain.keys("posixTimes");
            posixTimes = [];
            timeStrings = query.timeStrings;
            for (i=0; i<timeStrings.length; i++) {
                posixTimes.push(new Date(timeStrings[i]).valueOf());
            }
            result = _.extend({posixTimes:posixTimes},query);
        }
        // console.log("Result: " + JSON.stringify(result));
        if (probError > 0.0) {
            if (Math.random() < probError) {
                numErrors += 1;
                errorCbFn(new Error("Failed"));
            }
            else successCbFn(200, result);
        }
        else {
            successCbFn(200, result);
        }
    }

    var bufferedTimezone = utils.bufferedTimezone;
    describe('bufferedTimezone Posix Times to Time Strings', function () {
        it('should convert a posix time to a time string', function ( done ) {
            resetErrors();
            var date = randomDate(new Date(1970,0,1), new Date());
            var posixTimes = [];
            posixTimes.push(date.valueOf());
            bufferedTimezone(mockService, {tz:"America/Los_Angeles", posixTimes: posixTimes},
                function (err) {
                    should.not.exist(err);
                    done();
                },
                function (code, result) {
                    // console.log("Success callback: " + code);
                    expect(result).to.contain.keys('tz', 'posixTimes', 'timeStrings');
                    expect(result.tz).to.equal("America/Los_Angeles");
                    expect(posixTimes.length).to.equal(result.timeStrings.length);
                    for (var i=0; i<posixTimes.length; i++) {
                        expect(new Date(posixTimes[i]).toISOString() === result.timeStrings[i]);
                    }
                    done();
                });
        });
        it('should convert many posix times to time strings', function ( done ) {
            resetErrors();
            var posixTimes = [];
            for (var i=0; i<346; i++) {
                var date = randomDate(new Date(1970,0,1), new Date());
                posixTimes.push(date.valueOf());
            }
            bufferedTimezone(mockService, {tz:"America/Los_Angeles", posixTimes: posixTimes},
                function (err) {
                    should.not.exist(err);
                    done();
                },
                function (code, result) {
                    // console.log("Success callback: " + code);
                    expect(result).to.contain.keys('tz', 'posixTimes', 'timeStrings');
                    expect(result.tz).to.equal("America/Los_Angeles");
                    expect(posixTimes.length).to.equal(result.timeStrings.length);
                    expect(posixTimes.length).to.equal(346);
                    for (var i=0; i<posixTimes.length; i++) {
                        expect(new Date(posixTimes[i]).toISOString() === result.timeStrings[i]);
                    }
                    done();
                });
        });
        it('should be fault tolerant', function ( done ) {
            this.timeout(10000);
            resetErrors(0.1);
            var posixTimes = [];
            errorCbFn = function (err) {
                expect(numErrors).to.be.least(5);
                done();
            };
            successCbFn = function (code, result) {
                expect(numErrors).to.be.below(5);
                expect(result).to.contain.keys('tz', 'posixTimes', 'timeStrings');
                expect(result.tz).to.equal("America/Los_Angeles");
                expect(posixTimes.length).to.equal(result.timeStrings.length);
                for (var i=0; i<posixTimes.length; i++) {
                    expect(new Date(posixTimes[i]).toISOString() === result.timeStrings[i]);
                }
                done();
            };
            for (var i=0; i<2000; i++) {
                var date = randomDate(new Date(1970,0,1), new Date());
                posixTimes.push(date.valueOf());
            }
            bufferedTimezone(mockService, {tz:"America/Los_Angeles", posixTimes: posixTimes},
                errorCbFn, successCbFn);
        });
        it('should be give up ultimately', function ( done ) {
            this.timeout(10000);
            resetErrors(0.5);
            var posixTimes = [];
            errorCbFn = function (err) {
                expect(numErrors).to.be.least(5);
                done();
            };
            successCbFn = function (code, result) {
                console.log('SuccessCb: ' + numErrors);
                expect(numErrors).to.be.below(5);
                expect(result).to.contain.keys('tz', 'posixTimes', 'timeStrings');
                expect(result.tz).to.equal("America/Los_Angeles");
                expect(posixTimes.length).to.equal(result.timeStrings.length);
                for (var i=0; i<posixTimes.length; i++) {
                    expect(new Date(posixTimes[i]).toISOString() === result.timeStrings[i]);
                }
                done();
            };
            for (var i=0; i<2000; i++) {
                var date = randomDate(new Date(1970,0,1), new Date());
                posixTimes.push(date.valueOf());
            }
            bufferedTimezone(mockService, {tz:"America/Los_Angeles", posixTimes: posixTimes},
                errorCbFn, successCbFn);
        });
    });
    describe('bufferedTimezone Time Strings to Posix Times', function () {
        it('should convert a time string to a Posix time', function ( done ) {
            resetErrors();
            var date = randomDate(new Date(1970,0,1), new Date());
            var timeStrings = [];
            timeStrings.push(date.toISOString());
            bufferedTimezone(mockService, {tz:"America/Los_Angeles", timeStrings: timeStrings},
                function (err) {
                    should.not.exist(err);
                    done();
                },
                function (code, result) {
                    // console.log("Success callback: " + code);
                    expect(result).to.contain.keys('tz', 'timeStrings', 'posixTimes');
                    expect(result.tz).to.equal("America/Los_Angeles");
                    expect(timeStrings.length).to.equal(result.posixTimes.length);
                    for (var i=0; i<timeStrings.length; i++) {
                        expect(new Date(timeStrings[i]).valueOf() === result.posixTimes[i]);
                    }
                    done();
                });
        });
        it('should convert many time strings to Posix times', function ( done ) {
            resetErrors();
            var timeStrings = [];
            for (var i=0; i<517; i++) {
                var date = randomDate(new Date(1970,0,1), new Date());
                timeStrings.push(date.toISOString());
            }
            bufferedTimezone(mockService, {tz:"America/Los_Angeles", timeStrings: timeStrings},
                function (err) {
                    should.not.exist(err);
                    done();
                },
                function (code, result) {
                    // console.log("Success callback: " + code);
                    expect(result).to.contain.keys('tz', 'timeStrings', 'posixTimes');
                    expect(result.tz).to.equal("America/Los_Angeles");
                    expect(timeStrings.length).to.equal(result.posixTimes.length);
                    expect(timeStrings.length).to.equal(517);
                    for (var i=0; i<timeStrings.length; i++) {
                        expect(new Date(timeStrings[i]).valueOf() === result.posixTimes[i]);
                    }
                    done();
                });
        });
        it('should be fault tolerant', function ( done ) {
            this.timeout(10000);
            resetErrors(0.1);
            var timeStrings = [];
            errorCbFn = function (err) {
                expect(numErrors).to.be.least(5);
                done();
            };
            successCbFn = function (code, result) {
                expect(numErrors).to.be.below(5);
                expect(result).to.contain.keys('tz', 'timeStrings', 'posixTimes');
                expect(result.tz).to.equal("America/Los_Angeles");
                expect(timeStrings.length).to.equal(result.posixTimes.length);
                for (var i=0; i<timeStrings.length; i++) {
                    expect(new Date(timeStrings[i]).toISOString() === result.posixTimes[i]);
                }
                done();
            };
            for (var i=0; i<2000; i++) {
                var date = randomDate(new Date(1970,0,1), new Date());
                timeStrings.push(date.toISOString());
            }
            bufferedTimezone(mockService, {tz:"America/Los_Angeles", timeStrings: timeStrings},
                errorCbFn, successCbFn);
        });
        it('should give up ultimately', function ( done ) {
            this.timeout(10000);
            resetErrors(0.5);
            var timeStrings = [];
            errorCbFn = function (err) {
                expect(numErrors).to.be.least(5);
                done();
            };
            successCbFn = function (code, result) {
                expect(numErrors).to.be.below(5);
                expect(result).to.contain.keys('tz', 'timeStrings', 'posixTimes');
                expect(result.tz).to.equal("America/Los_Angeles");
                expect(timeStrings.length).to.equal(result.posixTimes.length);
                for (var i=0; i<timeStrings.length; i++) {
                    expect(new Date(timeStrings[i]).toISOString() === result.posixTimes[i]);
                }
                done();
            };
            for (var i=0; i<2000; i++) {
                var date = randomDate(new Date(1970,0,1), new Date());
                timeStrings.push(date.toISOString());
            }
            bufferedTimezone(mockService, {tz:"America/Los_Angeles", timeStrings: timeStrings},
                errorCbFn, successCbFn);
        });
    });

});
