'use strict';
var window, document, ARGS, $, jQuery, moment, kbn;
var base_url = window.location.hostname;

var species = []
function make_panel(result) {
    get_keys();
    var measurement = 'autogen.crds'

    var speciesArray = result;
    
    let customTargets = []
    for(var i = 0; i < speciesArray.length; i++) {
        let temp = {}
        //create one target object for each field
        temp.alias = speciesArray[i]
        temp.measurement = measurement;
        temp.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM " + measurement + " WHERE ('" + speciesArray[i] + "' =~ /^$species$/) AND $timeFilter GROUP BY time($__interval) fill(none)"
        temp.groupBy = [{"params": ["null"],"type": "fill"}]
        temp.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        temp.resultFormat = "time_series"
        temp.rawQuery = true;
        temp.hide = false;
        temp.orderByTime = "DESC";
        temp.policy = "autogen";

        customTargets.push(temp)
    }


    return {
        title: 'Chart',
        height: '300px',
        panels: [
          {
            title: 'Events',
            datasource: 'PiGSS data source',
            type: 'graph',
            span: 12,
            fill: 0,
            linewidth: 1,
            pointradius: 2,
            points: true,
            targets: customTargets,
            tooltip: {
              shared: true
            }
          }
        ],
        style: "dark"
      }
}

function get_keys() {
    var query_url = 'http://' + base_url + ':8000/species/search'
    $.ajax({
        method: 'POST',
        url: query_url
    }).done(function(result) {
    });
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

    var variableArray = ['species']
    let customVariables = []
    for (var i = 0; i < variableArray.length; i++) {
        let temp = {}
        temp.allValue = null,
        temp.current = {"text": "All", "value": "$__all"},
        temp.datasource = "species type service",
        temp.includeAll = true, 
        temp.label = "Species",
        temp.multi = true,
        temp.name = variableArray[i],
        temp.query = "",
        temp.refresh = 1,
        temp.regex = "",
        temp.sort = 0,
        temp.type = "query"

        customVariables.push(temp)
    }

    var query_url = 'http://' + base_url + ':8000/species/search'

    $.ajax({
        method: 'POST',
        url: query_url
    }).done(function(result) {
        dashboard.templating = {
            list: customVariables
        }
        dashboard.refresh = "5s";

        dashboard.rows.push(make_panel(result));

    callback(dashboard);
 
    });
}