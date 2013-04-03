define(['chai', 'mocha'],
function(chai) {
    return function () {
        var expect;
        expect = (typeof chai !== "undefined" && chai !== null ? chai.expect : void 0) || require('chai').expect;

        describe('Slow tests', function() {
            it('display test start events', function(done) {
                setTimeout((function() {
                    return done();
                }), 1862);
                return expect(true).to.be["true"];
            });
            it('and are correctly overwritten', function(done) {
                setTimeout((function() {
                    return done();
                }), 1538);
                return expect(true).to.be["true"];
            });
            return it('with pass or fail output', function(done) {
                setTimeout((function() {
                    return done();
                }), 1239);
                return expect(true).to.be["true"];
            });
        });
    };
});
