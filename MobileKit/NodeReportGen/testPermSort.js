// Get result of long running task from Pcubed
/*global console, exports, process, require */

'use strict';

var _ = require('underscore');

var a = [1,5,6,2,7,3,10,15,25];
var i = [0,1,2,3,4,5,6,7,8]

i.sort(function(j,k) { return a[j]-a[k]; });
console.log(i);
