/*global console, describe, beforeEach, it, require  */

'use strict';
var should = require("chai").should();
var ts = require("../lib/timeStamps");

describe('timeStampFunctions', function() {
	describe('#getMsUnixTime()', function () {
		it('should return current unix time', function() {
			Math.abs(ts.getMsUnixTime()-(new Date().getTime())).should.be.below(100);
		});
		it('should return correct time for a known timestring', function() {
			ts.getMsUnixTime("1971-01-01T00:00:00.000Z").should.equal(365*24*3600*1000);
		});
		it('should give NaN for bad timestrings', function () {
			isNaN(ts.getMsUnixTime("Bad")).should.be.ok;
			isNaN(ts.getMsUnixTime("1971-01-01T00:00:00.000A")).should.be.ok;
		});
	});
	describe('#msUnixTimeToTimeString()', function () {
		it('should produce a timestring from a known time', function() {
			var msUnixTime = 2*365*24*3600*1000;
			ts.msUnixTimeToTimeString(msUnixTime).should.equal("1972-01-01T00:00:00.000Z");
		});
		it('should produce a timestring which can be converted back correctly', function() {
			var msUnixTime = ts.getMsUnixTime();
			var timeString = ts.msUnixTimeToTimeString(msUnixTime);
			msUnixTime.should.equal(ts.getMsUnixTime(timeString));
		});
	});
});
