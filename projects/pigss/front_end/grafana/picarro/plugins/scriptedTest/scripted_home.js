'use strict';
var window, document, ARGS, $, jQuery, moment, kbn;
var base_url = window.location.hostname;

var species = []

function make_panel(result) {
    var measurement = 'autogen.crds'

    var speciesArray = result;
    
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
      }
    ]
    let customGraphTargets = [];
    let customTable1Targets = [];
    let customTable2Targets = [];

    let queryString = ""
    for (var i = 0; i < speciesArray.length - 1; i++) {
      queryString += "last(" + speciesArray[i] + ") AS " + speciesArray[i] + ", ";
    }
    queryString += "last(" + speciesArray[speciesArray.length -1] + ") AS " + speciesArray[speciesArray.length -1]+ " "

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

        let temp4 = {}
        temp4.alias = speciesArray[i];
        temp4.measurement = measurement;
        temp4.query = "SELECT last(" + speciesArray[i] + ") AS \"Current $species\", min(" + speciesArray[i] + ") AS \"Min. $species\", max(" +speciesArray[i] + ") AS \"Max. $species\" FROM " + measurement + " WHERE ('" + speciesArray[i] + "' =~ /^$species$/ AND valve_pos =~ /^$port_value_current$/ AND analyzer =~ /^$instrument$/) AND $timeFilter fill(null)",
        temp4.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        temp4.resultFormat = "table"
        temp4.rawQuery = true;
        temp4.hide = false;
        temp4.orderByTime = "DESC";
        temp4.policy = "autogen";

        let temp5 = {}
        temp5.alias = "";
        temp5.measurement = measurement;
        temp5.query = "SELECT last(" + speciesArray[i] + ") AS " + speciesArray[i] + " FROM autogen.crds WHERE ('" + speciesArray[i] + "' =~ /^$species$/ AND analyzer =~ /^$instrument$/) AND $timeFilter GROUP BY time(5s), \"valve_pos\" fill(none) ORDER BY time DESC LIMIT 1",
        temp5.select = [[{"params" : [speciesArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
        temp5.resultFormat = "table"
        temp5.rawQuery = true;
        temp5.hide = false;
        temp5.orderByTime = "DESC";
        temp5.policy = "autogen";

        customTable2Targets.push(temp5)

        //SELECT last(H2O) AS H2O FROM autogen.crds WHERE ('H2O' =~ /^$species$/ AND analyzer =~ /^$instrument$/) AND $timeFilter GROUP BY time(5s), "valve_pos" fill(none) ORDER BY time DESC LIMIT 1

        customTable1Targets.push(temp4)
        customGraphTargets.push(temp)
        customGraphTargets.push(temp2)
        customGraphTargets.push(temp3)
    }

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
        height: '300px',
        panels: [
          {
            datasource: "PiGSS data source",
            gridPos: {
              "x": 0,
              "y": 0,
              "h": 1,
              "w": 24,
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
            title: 'Analyzer Readings',
            maxPerRow: 2,
            renderer: "flot",
            datasource: 'PiGSS data source',
            transparent: true,
            fontSize: '120%',
            legend: false,
            type: 'graph',
            span: 12,
            fill: 0,
            linewidth: 0,
            pointradius: 2,
            points: true,
            seriesOverrides: customSeriesOverride,
            targets: customGraphTargets,
            tooltip: {
              shared: true
            }
          },
          {
            title: "",
            maxPerRow: 3,
            datasource: "PiGSS data source",
            repeat: "species",
            repeatDirection: "h",
            transparent: true,
            fontSize: "110%",
            gridPos: {
              h: 3,
              w: 12,
              x: 0,
              y: 0
            },
            styles: [
              {
                alias: "Time",
                dateFormat: "YYYY-MM-DD HH:mm:ss",
                pattern: "Time",
                type: "hidden"
              },
              {
                alias: "",
                dateFormat: "YYYY-MM-DD HH:mm:ss",
                decimals: 2,
                pattern: "/.*/",
                type: "number",
                unit: "short"
              }
            ],
            targets: customTable1Targets,
            transform: "table",
            type: "table"
          },
          {
            title: "Most Recent Values by Port",
            datasource: "PiGSS data source",
            transparent: true,
            fontSize: "110%",
            gridPos: {
              h: 3,
              w: 12,
              x: 0,
              y: 0
            },
            styles: [
              {
                alias: "Time",
                dateFormat: "YYYY-MM-DD HH:mm:ss",
                pattern: "Time",
                type: "hidden"
              },
              {
                alias: "",
                dateFormat: "YYYY-MM-DD HH:mm:ss",
                decimals: 2,
                pattern: "/.*/",
                type: "number",
                unit: "short"
              }
            ],
            targets: customTable2Targets,
            transform: "table",
            type: "table"
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

    //current port
    let temp4 = {}
    temp4.allValue = null,
    temp4.datasource = "PiGSS data source",
    temp4.definition = "SELECT valve_pos, CavityPressure FROM crds ORDER BY time DESC LIMIT 1",
    temp4.includeAll = false,
    temp4.hide = 2,
    temp4.label = null,
    temp4.multi = false,
    temp4.name = "port_value_current",
    temp4.query = "SELECT valve_pos, CavityPressure FROM crds ORDER BY time DESC LIMIT 1",
    temp4.refresh = 1,
    temp4.type = "query"

    customVariables.push(temp4)

    

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