/* newIdTracker.js provides is for tracking objects */

define ([],
function () {
    'use strict';
    function IdTracker() {
        this.nextObjId = 1;
    }
    IdTracker.prototype.objectId = function(obj) {
        if (obj === null || obj === undefined) return null;
        if (obj.__obj_id === null || obj.__obj_id === undefined) obj.__obj_id = this.nextObjId++;
        return obj.__obj_id;
    };

    return function () {
        return new IdTracker();
    };
});
