'use strict';
var window, document, ARGS, $, jQuery, moment, kbn;
var base_url = window.location.hostname;

var species = []
var currentPortPanel = {}

function random_color(species_amount) {
  let colorArray = []
  for (var step = 0; step < species_amount; step++) {
    var r, g, b;
    var h = step / species_amount;
    var i = ~~(h * 6);
    var f = h * 6 - i;
    var q = 1 - f;
    switch(i % 6){
        case 0: r = 1; g = f; b = 0; break;
        case 1: r = q; g = 1; b = 0; break;
        case 2: r = 0; g = 1; b = f; break;
        case 3: r = 0; g = q; b = 1; break;
        case 4: r = f; g = 0; b = 1; break;
        case 5: r = 1; g = 0; b = q; break;
    }
    var c = "#" + ("00" + (~ ~(r * 255)).toString(16)).slice(-2) + ("00" + (~ ~(g * 255)).toString(16)).slice(-2) + ("00" + (~ ~(b * 255)).toString(16)).slice(-2);
    colorArray.push(c)
  }
  return colorArray
}

function make_panel(result) {
    var measurement = 'autogen.crds'

    var speciesArray = result;
    var colors = random_color(speciesArray.length);
    
    let customSeriesOverride = [
      {
        alias: "Unstable",
        color: "rgb(66, 66, 66)",
        legend: false,
      },
      {
        alias: "Unselected",
        color: "rgb(102, 84, 84)",
        legend: false
      },
      {
        alias: "Port",
        points: false
      }
    ]
    let customTargets = []
    for(var i = 0; i < speciesArray.length; i++) {
        //Species
        let temp = {}
        let tempColor = {}
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
        tempColor.alias = speciesArray[i];
        tempColor.color = colors[i];
        customSeriesOverride.push(tempColor);

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
        temp3.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM " + measurement + " WHERE ('" + speciesArray[i] + "' =~ /^$species$/ AND valve_pos = '0' AND analyzer =~ /^$instrument$/) AND $timeFilter GROUP BY time($__interval) fill(none)"
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

    let port = {}
    port.alias = "Port"
    port.measurement = measurement;
    port.query = "SELECT last(port) AS Port FROM " + measurement + " WHERE $timeFilter GROUP BY time($__interval) fill(none)"
    port.groupBy = [{"params": ["null"],"type": "fill"}]
    port.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
    port.resultFormat = "time_series"
    port.rawQuery = true;
    port.hide = false;
    port.orderByTime = "DESC";
    port.policy = "autogen";

    customTargets.push(port)

    //current ports
    let tempPort = {}

    tempPort = {
      groupBy: [
        {
          "params": [
            "$__interval"
          ],
          "type": "time"
        }
      ],
      limit: "",
      measurement: "crds",
      orderByTime: "DESC",
      policy: "default",
      query: "SELECT * FROM "+ measurement +" WHERE $timeFilter ORDER BY time DESC LIMIT 1",
      rawQuery: true,
      refId: "A",
      resultFormat: "table",
      select: [
        [
          {
            "params": [
              "*"
            ],
            "type": "field"
          }
        ]
      ],
      tags: []
    }

    return {
          title: 'Chart',
          panels: [
            {
              datasource: "PiGSS data source",
              gridPos: {
                "h": 12,
                "w": 24,
                "x": 0,
                "y": 0
              },
              mappingTypes: [
                {
                  "name": "value to text",
                  "value": 1
                },
                {
                  "name": "range to text",
                  "value": 2
                }
              ],
              nullPointMode: "connected",
              postfix: "",
              postfixFontSize: "50%",
              prefix: "Current Port:",
              prefixFontSize: "65%",
              rangeMaps: [
                {
                  "from": "null",
                  "text": "N/A",
                  "to": "null"
                }
              ],
              tableColumn: "valve_pos",
              targets: [
                tempPort
              ],
              title: "",
              transparent: true,
              type: "singlestat",
              valueFontSize: "65%",
              valueMaps: [
                {
                  "op": "=",
                  "text": "N/A",
                  "value": "null"
                }
              ],
              valueName: "current"
          },
            {
              title: '$species',
              maxPerRow: 2,
              renderer: "flot",
              datasource: 'PiGSS data source',
              transparent: true,
              fontSize: '120%',
              repeat: "species",
              repeatDirection: "h",
              legend: false,
              type: 'graph',
              span: 12,
              fill: 0,
              linewidth: 0,
              pointradius: 2,
              points: true,
              seriesOverrides: customSeriesOverride,
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
    dashboard.title = 'Analyzer Outputs';
 
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
    // dashboard.rows.push(currentPortPanel)
    dashboard.rows.push(make_panel(globalThis.species));

    callback(dashboard);
});
    
}
