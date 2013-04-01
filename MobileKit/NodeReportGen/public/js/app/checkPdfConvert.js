// getReport.js
/*global console, requirejs, TEMPLATE_PARAMS */

define(['jquery', 'underscore'],

function ($, _) {
    'use strict';

    var instructionsLoaded = false;

    function init() {
        window.status = 'start';
        var url = "http://maps.googleapis.com/maps/api/staticmap?center=Brooklyn+Bridge,New+York,NY&zoom=13&size=600x300&maptype=roadmap&markers=color:blue%7Clabel:S%7C40.702147,-74.015794&markers=color:green%7Clabel:G%7C40.711614,-74.012318&markers=color:red%7Ccolor:red%7Clabel:C%7C40.718217,-73.998284&sensor=false";
        // $("#sampleImageDiv").html('<img src="http://www.w3schools.com/images/w3schools_green.jpg" alt="W3Schools.com" width="104" height="142">');
        $("#sampleImageDiv").html('<img src="' + url + '">');
        setTimeout(function () {
            $("#completion").html("After Delay");
            window.status = 'done';
        } ,3000);
    }
    return { "initialize": function() { $(document).ready(init); }};

});