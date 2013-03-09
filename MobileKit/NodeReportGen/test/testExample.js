/*global console, describe, beforeEach, it, require  */

'use strict';
require("should");
var nextPrime = require('../primes').nextPrime;
var asyncPrime = require('../primes').asyncPrime;

describe('nextPrime', function() {
	it('should return the next prime number', function(done) {
		nextPrime(7).should.equal(11);
		done();
	});

	it('should find 0 and 1 as non-prime', function(done) {
		nextPrime(0).should.equal(2);
		nextPrime(1).should.equal(2);
		done();
	});

	it('should work with asyncPrime', function(done) {
		asyncPrime(128, function (n) {
			n.should.equal(131,'Wrong number');
			done();
		});
	});
});
