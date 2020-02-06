'use strict';
var window, document, ARGS, $, jQuery, moment, kbn;
var base_url = window.location.hostname;

var species = []

function make_panel(result) {
    var measurement = 'autogen.crds'

    var speciesArray = result;
    
    let customTargets = []
    for(var i = 0; i < speciesArray.length; i++) {

        //Species
        let temp = {}
        temp.alias = speciesArray[i]
        temp.measurement = measurement;
        temp.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM " + measurement + " WHERE ('" + speciesArray[i] + "' =~ /^$species$/ AND valve_pos =~ /^$ports$/ AND analyzer =~ /^$instrument$/ AND valve_stable_time > $stabilization_time) AND $timeFilter GROUP BY time($__interval) fill(none)"
        temp.groupBy = [{"params": ["null"],"type": "fill"}]
        temp.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        temp.resultFormat = "time_series"
        temp.rawQuery = true;
        temp.hide = false;
        temp.orderByTime = "DESC";
        temp.policy = "autogen";


        //Unstable query
        let temp2 = {}
        temp2.alias = "Unstable"
        temp2.measurement = measurement;
        temp2.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM " + measurement + " WHERE ('" + speciesArray[i] + "' =~ /^$species$/ AND valve_pos =~ /^$ports$/ AND analyzer =~ /^$instrument$/ AND valve_stable_time < $stabilization_time) AND $timeFilter GROUP BY time($__interval) fill(none)"
        temp2.groupBy = [{"params": ["null"],"type": "fill"}]
        temp2.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        temp2.resultFormat = "time_series"
        temp2.rawQuery = true;
        temp2.hide = false;
        temp2.orderByTime = "DESC";
        temp2.policy = "autogen";


        //Unselected query
        let temp3 = {}
        temp3.alias = "Unselected"
        temp3.measurement = measurement;
        temp3.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM " + measurement + " WHERE (valve_pos = 0 AND analyzer =~ /^$instrument$/) AND $timeFilter GROUP BY time($__interval) fill(none)"
        temp3.groupBy = [{"params": ["null"],"type": "fill"}]
        temp3.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        temp3.resultFormat = "time_series"
        temp3.rawQuery = true;
        temp3.hide = false;
        temp3.orderByTime = "DESC";
        temp3.policy = "autogen";

        customTargets.push(temp)
        customTargets.push(temp2)
        customTargets.push(temp3)
    }


    return {
        title: 'Chart',
        height: '300px',
        panels: [
          {
            title: '$species',
            maxPerRow: 2,
            renderer: "flot",
            datasource: 'PiGSS data source',
            transparent: true,
            fontsize: '120%',
            type: 'graph',
            span: 12,
            fill: 0,
            linewidth: 0,
            pointradius: 2,
            points: true,
            seriesOverrides: [
                {
                  alias: "Unstable",
                  color: "rgb(66, 66, 66)",
                  legend: false,
                },
                {
                  alias: "Unselected",
                  color: "rgb(102, 84, 84)",
                  legend: false
                }
              ],
            targets: customTargets,
            tooltip: {
              shared: true
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
    dashboard.title = 'Anazlyer Outputs';
 
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
        temp.datasource = "species type service",
        temp.includeAll = false, 
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

     //get time stabilization
    let temp1 = {
        current: {
            selected: true,
            text: "15",
            value: "15"
          },
          hide: 2,
          label: null,
          name: "stabilization_time",
          options: [
            {
              selected: true,
              text: "15",
              value: "15"
            }
          ],
          query: "15",
          skipUrlSync: false,
          type: "textbox"
    }

    customVariables.push(temp1);

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

    dashboard.refresh = "5s";
    dashboard.rows.push(make_panel(globalThis.species));
    callback(dashboard);
});
    
}