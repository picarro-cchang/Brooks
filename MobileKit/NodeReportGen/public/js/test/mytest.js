define(['chai'],
function() {
    describe('mySuite', function () {
        it('should succeed', function () {
            expect(5).to.equal(3);
        });
        it('should also succeed', function () {
            expect(1).to.equal(1);
        });
    });
});