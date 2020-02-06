'use strict';
var window, document, ARGS, $, jQuery, moment, kbn;
var base_url = window.location.hostname;

var species = []
function make_panel(result) {
    result = result.toString()

    return {
        title: 'Chart',
        height: '300px',
        panels: [
          {
            title: 'Events',
            type: 'text',
            span: 12,
            fill: 0,
            content: result,
            tooltip: {
              shared: true
            }
          }
        ],
      }
}
 
return function(callback) {
    // Setup some variables
    var dashboard;
 
    // Initialize a skeleton with nothing but a rows array and service object
    dashboard = {
        rows : [],
        services : {}
    };
 
    // Set a title
    dashboard.title = 'Scripted dash';
 
    // Set default time
    dashboard.time = {
        from: "now-15m",
        to: "now"
    };
 
    var rows = 1;
    var seriesName = 'argName';
 
    if(!_.isUndefined(ARGS.rows)) {
        rows = parseInt(ARGS.rows, 10);
    }
 
    if(!_.isUndefined(ARGS.name)) {
        seriesName = ARGS.name;
    }

    var query_url = 'http://' + base_url + ':8000/port_history/search'

    $.ajax({
        method: 'POST',
        url: query_url,
        data: '{}'
    }).done(function(result) {
        dashboard.refresh = "5s";

        dashboard.rows.push(make_panel(result));

    callback(dashboard);
 
    });
}