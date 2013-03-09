/*global console, describe, beforeEach, it, require  */

'use strict';
var should = require("should");
var newn2i = require("../lib/newNamesToIndices");

describe('newNamesToIndices', function() {
	describe('#addingSomeNames', function () {
		it('should return undefined when empty', function() {
			var n2i = newn2i();
			should.equal(n2i.getName(0), undefined);
		});
		it('should be able to store names', function() {
			var n2i = newn2i();
			n2i.getIndex("a").should.equal(0);
			n2i.getIndex("b").should.equal(1);
			n2i.getName(0).should.equal("a");
			n2i.getName(1).should.equal("b");
			should.equal(n2i.getName(2), undefined);
		});
		it('should be able to remove duplicate names', function() {
			var n2i = newn2i();
			n2i.getIndex("a").should.equal(0);
			n2i.getIndex("b").should.equal(1);
			n2i.getIndex("c").should.equal(2);
			n2i.getIndex("b").should.equal(1);
			n2i.getName(0).should.equal("a");
			n2i.getName(1).should.equal("b");
			n2i.getName(2).should.equal("c");
		});
		it('should be able to return all names', function() {
			var n2i = newn2i();
			n2i.getIndex("a").should.equal(0);
			n2i.getIndex("b").should.equal(1);
			n2i.getIndex("c").should.equal(2);
			n2i.getIndex("b").should.equal(1);
			n2i.getAllNames().should.eql({0: "a", 1: "b", 2:"c"});
		});
	});
});
