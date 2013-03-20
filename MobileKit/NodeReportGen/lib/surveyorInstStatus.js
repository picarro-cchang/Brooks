/* surveyorInstStatus.js defines status codes for the surveyor instrument manager */
/*global exports, module, require */
if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
	'use strict';
    module.exports = {
        // status register bit definitions
        "INSTMGR_STATUS_READY": 0x0001,
        "INSTMGR_STATUS_MEAS_ACTIVE": 0x0002,
        "INSTMGR_STATUS_ERROR_IN_BUFFER": 0x0004,
        "INSTMGR_STATUS_GAS_FLOWING": 0x0040,
        "INSTMGR_STATUS_PRESSURE_LOCKED": 0x0080,
        "INSTMGR_STATUS_CAVITY_TEMP_LOCKED": 0x0100,
        "INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED": 0x0200,
        "INSTMGR_STATUS_WARMING_UP": 0x2000,
        "INSTMGR_STATUS_SYSTEM_ERROR": 0x4000,
        "INSTMGR_STATUS_MASK": 0xFFFF,
        "INSTMGR_AUX_STATUS_SHIFT": 16,
        "INSTMGR_AUX_STATUS_WEATHER_MASK": 0x1F,
        // Good status
        "INSTMGR_STATUS_GOOD": 0x03c3, // OR of bit masks for good status

        // Codes for weather information. The entry in the auxiliary status is
        //  ONE PLUS the bitwise OR of the codes below. This allows us to detect
        //  a file which has no weather data in it.
        "WEATHER_DAY": 0,
        "WEATHER_NIGHT": 1,
        "WEATHER_SUNLIGHT_OVERCAST": 0 * 2,
        "WEATHER_SUNLIGHT_MODERATE": 1 * 2,
        "WEATHER_SUNLIGHT_STRONG": 2 * 2,
        "WEATHER_CLOUD_LESS50": 0 * 2,
        "WEATHER_CLOUD_MORE50": 1 * 2,
        "WEATHER_WIND_CALM": 0 * 8,
        "WEATHER_WIND_LIGHT": 1 * 8,
        "WEATHER_WIND_STRONG": 2 * 8,

        // Dictionary of Pasquill stability classes by weather
        "classByWeather":{ 0: "D",  8: "D", 16: "D", // Daytime, Overcast
                           2: "B", 10: "C", 18: "D", // Daytime, moderate sun
                           4: "A", 12: "B", 20: "C", // Daytime, strong sun
                           1: "F",  9: "E", 17: "D", // Nighttime, <50% cloud
                           3: "E", 11: "D", 19: "D"  // Nighttime, >50% cloud
        }
    };
});
