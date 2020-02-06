'use strict';
var window, document, ARGS, $, jQuery, moment, kbn;
var base_url = window.location.hostname;

var species = []
function make_panel(result) {
    var measurement = 'autogen.crds'

    var speciesArray = result;
    
    let customTargets = []
    for(var i = 0; i < speciesArray.length; i++) {
        let temp = {}
        //create one target object for each field
        temp.alias = speciesArray[i]
        temp.measurement = measurement;
        temp.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM " + measurement + " WHERE ('" + speciesArray[i] + "' =~ /^$species$/ AND valve_pos =~ /^$ports$/ AND analyzer =~ /^$instrument$/) AND $timeFilter ORDER BY time DESC"
        temp.groupBy = [{"params": ["null"],"type": "fill"}]
        temp.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        temp.resultFormat = "time_series"
        temp.rawQuery = true;
        temp.hide = false;
        temp.orderByTime = "DESC";
        temp.policy = "autogen";

        // let temp2 = {}
        // //create one target object for each field
        // temp2.alias = "Unstable"
        // temp2.measurement = measurement;
        // temp2.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM " + measurement + " WHERE ('" + speciesArray[i] + "' =~ /^$species$/ AND valve_pos =~ /^$ports$/ AND analyzer =~ /^$instrument$/ AND valve_stable_time < $stabilization_time) AND $timeFilter GROUP BY time($__interval) fill(none)"
        // temp2.groupBy = [{"params": ["null"],"type": "fill"}]
        // temp2.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        // temp2.resultFormat = "time_series"
        // temp2.rawQuery = true;
        // temp2.hide = false;
        // temp2.orderByTime = "DESC";
        // temp2.policy = "autogen";

        // let temp3 = {}
        // //create one target object for each field
        // temp3.alias = "Unselected"
        // temp3.measurement = measurement;
        // temp3.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM " + measurement + " WHERE (valve_pos = 0 AND analyzer =~ /^$instrument$/) AND $timeFilter GROUP BY time($__interval) fill(none)"
        // temp3.groupBy = [{"params": ["null"],"type": "fill"}]
        // temp3.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        // temp3.resultFormat = "time_series"
        // temp3.rawQuery = true;
        // temp3.hide = false;
        // temp3.orderByTime = "DESC";
        // temp3.policy = "autogen";

        customTargets.push(temp)
        // customTargets.push(temp2)
        // customTargets.push(temp3)
    }


    return {
        title: 'Chart',
        height: '300px',
        panels: [
          {
            title: '$ports',
            datasource: 'PiGSS data source',
            fontSize: '120%',
            maxPerRow: 4,
            repeat: "ports",
            repeatDirection: "h",
            styles: [
              {
                alias: "Time",
                dateFormat: "YYYY-MM-DD HH:mm:ss",
                pattern: "Time",
                type: "hidden"
              },
              {
                alias: "",
                decimals: 2,
                pattern: "/.*/",
                type: "number",
                unit: "short"
              }
            ],
            transform: "timeseries_to_rows",
            type: 'table',
            span: 12,
            fill: 0,
            linewidth: 0,
            targets: customTargets,
            tooltip: {
              shared: true,
              value_type: "individual"
            }
          }
        ],
        style: "dark"
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
    dashboard.title = 'Current Values';
 
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
        temp.current = {
          "text": "H2O + CO2 + NH3 + CH4", 
          "value": [
            "H2O",
            "CO2",
            "NH3",
            "CH4"
          ]},
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

    // //get port history service variable
    let temp2 = {}
    temp2.allValue = null,
    temp2.current = {"text": "All", "value": "$__all"},
    temp2.datasource = "port history server",
    temp2.definition =  "[$__from, $__to]",
    temp2.includeAll = true, 
    temp2.label = "Ports",
    temp2.multi = true,
    temp2.name = "ports",
    temp2.query = "[$__from, $__to]",
    temp2.refresh = 1,
    temp2.regex = "",
    temp2.sort = 0,
    temp2.type = "query"

    customVariables.push(temp2)

    //get analyzers
    let temp3 = {}
    temp3.allValue = null,
    temp3.current = {"text": "All", "value": "$__all"},
    temp3.datasource = "PiGSS data source",
    temp3.definition =  "SHOW TAG VALUES from crds WITH KEY = \"analyzer\"",
    temp3.includeAll = true, 
    temp3.label = "Instrument",
    temp3.multi = true,
    temp3.name = "instrument",
    temp3.query = "SHOW TAG VALUES from crds WITH KEY = \"analyzer\"",
    temp3.refresh = 1,
    temp3.regex = "",
    temp3.sort = 0,
    temp3.type = "query"

    customVariables.push(temp3)
    

$.when(
    $.post('http://' + base_url + ':8000/species/search', function(species) {
        globalThis.species = species;
    }),
).then(function() {
    dashboard.templating = {
        list: customVariables
    }
    dashboard.links = [
      {
        asDropdown: true,
        icon: "external link",
        keepTime: true,
        tags: [
          "pigss"
        ],
        title: "Dashboards",
        type: "dashboards"
      }
    ]
    dashboard.tags = ["pigss"]

    dashboard.refresh = "5s";
    dashboard.rows.push(make_panel(globalThis.species));
    callback(dashboard);
});
    
}