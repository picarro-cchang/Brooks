/* md5hex.js calculates the MD5 hash of its argument and returns a hex string. */
/*global exports, module, require */

(function() {
	'use strict';
    /****************************************************************************/
    /*  Calculation of MD5 hash                                                 */
    /****************************************************************************/
    var crypto = require('crypto');

    function md5Hex(contents) {
        var hash = crypto.createHash("md5").update(contents).digest("hex");
        return hash;
    }

    module.exports = md5Hex;

})();
