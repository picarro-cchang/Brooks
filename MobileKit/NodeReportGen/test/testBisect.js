/*global console, describe, beforeEach, it, require  */

'use strict';
var should = require("chai").should();
var bs = require("../lib/bisect");
var bisect_right = bs.bisect_right;
var bisect_left = bs.bisect_left;
var insort_right = bs.insort_right;
var insort_left = bs.insort_left;

describe('bisect', function() {
    describe('#bisect_right precomputed', function () {
        it('should return expected results', function() {
            bisect_right([],1).should.equal(0);
            bisect_right([1], 0).should.equal(0);
            bisect_right([1], 1).should.equal(1);
            bisect_right([1], 2).should.equal(1);
            bisect_right([1, 1], 0).should.equal(0);
            bisect_right([1, 1], 1).should.equal(2);
            bisect_right([1, 1], 2).should.equal(2);
            bisect_right([1, 1, 1], 0).should.equal(0);
            bisect_right([1, 1, 1], 1).should.equal(3);
            bisect_right([1, 1, 1], 2).should.equal(3);
            bisect_right([1, 1, 1, 1], 0).should.equal(0);
            bisect_right([1, 1, 1, 1], 1).should.equal(4);
            bisect_right([1, 1, 1, 1], 2).should.equal(4);
            bisect_right([1, 2], 0).should.equal(0);
            bisect_right([1, 2], 1).should.equal(1);
            bisect_right([1, 2], 1.5).should.equal(1);
            bisect_right([1, 2], 2).should.equal(2);
            bisect_right([1, 2], 3).should.equal(2);
            bisect_right([1, 1, 2, 2], 0).should.equal(0);
            bisect_right([1, 1, 2, 2], 1).should.equal(2);
            bisect_right([1, 1, 2, 2], 1.5).should.equal(2);
            bisect_right([1, 1, 2, 2], 2).should.equal(4);
            bisect_right([1, 1, 2, 2], 3).should.equal(4);
            bisect_right([1, 2, 3], 0).should.equal(0);
            bisect_right([1, 2, 3], 1).should.equal(1);
            bisect_right([1, 2, 3], 1.5).should.equal(1);
            bisect_right([1, 2, 3], 2).should.equal(2);
            bisect_right([1, 2, 3], 2.5).should.equal(2);
            bisect_right([1, 2, 3], 3).should.equal(3);
            bisect_right([1, 2, 3], 4).should.equal(3);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 0).should.equal(0);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 1).should.equal(1);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 1.5).should.equal(1);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 2).should.equal(3);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 2.5).should.equal(3);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 3).should.equal(6);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 3.5).should.equal(6);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 4).should.equal(10);
            bisect_right([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 5).should.equal(10);
        });
    });
    describe('#bisect_left precomputed', function () {
        it('should return expected results', function() {
            bisect_left([], 1).should.equal(0);
            bisect_left([1], 0).should.equal(0);
            bisect_left([1], 1).should.equal(0);
            bisect_left([1], 2).should.equal(1);
            bisect_left([1, 1], 0).should.equal(0);
            bisect_left([1, 1], 1).should.equal(0);
            bisect_left([1, 1], 2).should.equal(2);
            bisect_left([1, 1, 1], 0).should.equal(0);
            bisect_left([1, 1, 1], 1).should.equal(0);
            bisect_left([1, 1, 1], 2).should.equal(3);
            bisect_left([1, 1, 1, 1], 0).should.equal(0);
            bisect_left([1, 1, 1, 1], 1).should.equal(0);
            bisect_left([1, 1, 1, 1], 2).should.equal(4);
            bisect_left([1, 2], 0).should.equal(0);
            bisect_left([1, 2], 1).should.equal(0);
            bisect_left([1, 2], 1.5).should.equal(1);
            bisect_left([1, 2], 2).should.equal(1);
            bisect_left([1, 2], 3).should.equal(2);
            bisect_left([1, 1, 2, 2], 0).should.equal(0);
            bisect_left([1, 1, 2, 2], 1).should.equal(0);
            bisect_left([1, 1, 2, 2], 1.5).should.equal(2);
            bisect_left([1, 1, 2, 2], 2).should.equal(2);
            bisect_left([1, 1, 2, 2], 3).should.equal(4);
            bisect_left([1, 2, 3], 0).should.equal(0);
            bisect_left([1, 2, 3], 1).should.equal(0);
            bisect_left([1, 2, 3], 1.5).should.equal(1);
            bisect_left([1, 2, 3], 2).should.equal(1);
            bisect_left([1, 2, 3], 2.5).should.equal(2);
            bisect_left([1, 2, 3], 3).should.equal(2);
            bisect_left([1, 2, 3], 4).should.equal(3);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 0).should.equal(0);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 1).should.equal(0);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 1.5).should.equal(1);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 2).should.equal(1);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 2.5).should.equal(3);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 3).should.equal(3);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 3.5).should.equal(6);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 4).should.equal(6);
            bisect_left([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], 5).should.equal(10);
        });
    });
    describe('#test_negative_io', function () {
        it('should throw expected exceptions', function() {
            should.Throw(bisect_left,[1, 2, 3], 5, -1, 3);
            should.Throw(bisect_right,[1, 2, 3], 5, -1, 3);
            should.Throw(insort_left,[1, 2, 3], 5, -1, 3);
            should.Throw(insort_right,[1, 2, 3], 5, -1, 3);
        });
    });
});
