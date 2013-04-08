/* jshint undef:true, unused:true, laxcomma:true, -W014, -W069, -W083 */
/*globals console, define */
define(['jquery'],
function ($) {
    'use strict';

    var P3HOST = "dev.picarro.com";
    var P3PORT = 443;
    var P3SITE = "dev";

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

    function TimezoneP3(host, port, site) {
        this.timezone = function(qry_obj, errorCbFn, successCbFn) {
            var p3h = host ? host : P3HOST;
            var p3p = port ? port : P3PORT;
            p3p = parseInt(p3p, 10);
            var p3s = site ? site : P3SITE;
            var p3proto = (p3p === 443) ? "https://" : "http://";
            var p3port = ((p3p === 443) || (p3p === 80)) ? "" : ":" + p3p;
            var p3site = "/" + p3s;

            var url = p3proto + p3h + p3port + p3site
                        +  '/rest/Utilities/tz?' + $.param(qry_obj);
            console.log('timezone', url);
            $.getJSON(url, function success(data, textStatus) {
                successCbFn(textStatus, data);
            }).fail(function(jqXHR) {
                errorCbFn(jqXHR.status + ' ' + jqXHR.statusText + ' ' + jqXHR.responseText);
            });
        };
    }
    return {GetResource: GetResource, Timezone: Timezone, TimezoneP3: TimezoneP3};
});


