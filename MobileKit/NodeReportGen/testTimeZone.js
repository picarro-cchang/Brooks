// Get result of long running task from Pcubed
/*global console, __dirname, exports, require */

'use strict';
var fs = require('fs');
var timezoneJS = require('./public/js/lib/date');

timezoneJS.timezone.zoneFileBasePath = './public/tz';
timezoneJS.timezone.transport = function (opts) {
    // No success handler, what's the point?
    if (opts.async) {
        if (typeof opts.success !== 'function') return;
        opts.error = opts.error || console.error;
        return fs.readFile(opts.url, 'utf8', function (err, data) {
            return err ? opts.error(err) : opts.success(data);
        });
    }
    return fs.readFileSync(opts.url, 'utf8');
};

timezoneJS.timezone.init({async: false});

// Pre-DST-leap
var dt = new timezoneJS.Date(2006, 9, 29, 1, 59, 'America/Los_Angeles');
console.log(dt.getTimezoneOffset());
// Post-DST-leap
dt = new timezoneJS.Date(2006, 9, 29, 2, 0, 'America/Los_Angeles');
console.log(dt.getTimezoneOffset());

dt = new timezoneJS.Date('2012-06-10  06:13', 'America/Los_Angeles');
console.log(dt.toUTCString());

dt = new timezoneJS.Date('2012-06-10  06:13', 'America/New_York');
console.log(dt.toUTCString());

dt = new timezoneJS.Date(2012,5,10, 'America/New_York');
console.log(dt.valueOf());
console.log(dt.toUTCString());

dt = new timezoneJS.Date(2012,5,10,13,13, 'Etc/GMT');
console.log(dt.valueOf());
console.log(dt.toUTCString());

dt.setTimezone('America/Los_Angeles');
console.log(dt);
console.log(dt.valueOf());
console.log(dt.toString());
/*
for (var i=0; i<24; i++) {
    dt = new Date(2012,2,11,i,0,0);
    console.log(dt.toISOString());
    console.log(dt.getTimezoneOffset());
}
*/
dt = new timezoneJS.Date("2012-03-11T09:00:00.000Z");
console.log(dt.toISOString());

/*
for (var i=0; i<24; i++) {
    dt = new timezoneJS.Date(2012,2,10,i,0,0, "Asia/Shanghai");
    console.log(dt.toUTCString());
    console.log(dt.getTimezoneOffset());
}
for (var i=0; i<24; i++) {
    dt = new timezoneJS.Date(2012,2,11,i,0,0, "Asia/Shanghai");
    console.log(dt.toUTCString());
    console.log(dt.getTimezoneOffset());
}
for (var i=0; i<24; i++) {
    dt = new timezoneJS.Date(2012,2,12,i,0,0, "Asia/Shanghai");
    console.log(dt.toUTCString());
    console.log(dt.getTimezoneOffset());
}
*/