/* jshint undef:true, unused:true, laxcomma:true, -W014, -W069, -W083 */
/*globals console, define */
define(['jquery'],
function ($) {
    'use strict';
    function GetResource() {
        this.resource = function(res, errorCbFn, successCbFn) {
            var url = '/rest/data' + res;
            console.log('getResource', url);
            $.getJSON(url, function success(data, textStatus) {
                successCbFn(textStatus, data);
            }).fail(function(jqXHR) {
                errorCbFn(jqXHR.status + ' ' + jqXHR.statusText + ' ' + jqXHR.responseText);
            });
        };
    }

    function Timezone() {
        this.timezone = function(qry_obj, errorCbFn, successCbFn) {
            var url = '/rest/tz?' + $.param(qry_obj);
            console.log('timezone', url);
            $.getJSON(url, function success(data, textStatus) {
                successCbFn(textStatus, data);
            }).fail(function(jqXHR) {
                errorCbFn(jqXHR.status + ' ' + jqXHR.statusText + ' ' + jqXHR.responseText);
            });
        };
    }
    return {GetResource: GetResource, Timezone: Timezone};
});


