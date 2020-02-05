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
 
return function(callback) {
    // Setup some variables
    var dashboard;
 
    // Initialize a skeleton with nothing but a rows array and service object
    dashboard = {
        rows : [],
        services : {}
    };
 
    // Set a title
    dashboard.title = 'Scripted Async Dash Test';
 
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

    // //get port history service
    let temp2 = {}
    temp2.allValue = null,
    temp2.current = {"text": "All", "value": "$__all"},
    temp2.datasource = "port history service",
    temp2.definition =  "[$__from, $__to]",
    temp2.includeAll = true, 
    temp2.label = "Ports",
    temp2.multi = false,
    temp2.name = "ports",
    temp2.query = "[$__from, $__to]",
    temp2.refresh = 1,
    temp2.regex = "",
    temp2.sort = 0,
    temp2.type = "query"

    customVariables.push(temp2)

    

$.when(
    // $.post('http://' + base_url + ':8000/port_history/search', function(ports) {
    // }),

    $.post('http://' + base_url + ':8000/species/search', function(species) {
        dashboard.rows.push(make_panel(species));
    }),

    

).then(function() {
    dashboard.templating = {
        list: customVariables
    }
    dashboard.refresh = "5s";

    callback(dashboard);
});
    
}