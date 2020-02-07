/* global _ */

'use strict' ;

var window, document, ARGS, $, jQuery, moment, kbn;

var dashboard

var ARGS

console.log(ARGS);

dashboard = {
  rows: []
};

dashboard.title = 'Dynamic Home Dashboard'

dashboard.time = {
  from : "now-6h",
  to : "now"
};

var rows = 1
var filedKeys = []

var fieldArray = ['HCl'] // array with one element only by default
var variableArray = ['species']

if(!_.isUndefined(ARGS.field)) {
  fieldArray = ARGS.field.split(';') //creates a array of field values to be displayed
}

var measurement = 'crds'

if(!_.isUndefined(ARGS.measurement)) {
  measurement = ARGS.measurement
}

let customVariables = []
for (var i = 0; i < variableArray.length; i++) {
    let temp = {}
    temp.allValue = null,
    temp.current = {"text": "All", "value": "$__all"},
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

let customTargets = []
for(var i = 0; i < fieldArray.length; i++) {
  let temp = {}
  //create one target object for each field
  temp.alias = measurement + "." + fieldArray[i]
  temp.measurement = measurement;
  temp.query = "SELECT last("+ fieldArray[i] + ") FROM " + measurement + " WHERE $timeFilter GROUP BY fill(null) ORDER BY time DESC LIMIT 1"
  temp.groupBy = [{"params": ["null"],"type": "fill"}]
  temp.select = [[{"params" : [fieldArray[i]], "type" : "field"}, {"params": [],"type": "last"}]]
  temp.resultFormat = "time_series"
  temp.rawQuery = true;
  temp.hide = false;
  temp.orderByTime = "DESC";
  temp.policy = "autogen";

  customTargets.push(temp)
}

for (var i = 0; i < rows; i++) {
  dashboard.rows.push({
    title: 'Chart',
    height: '300px',
    panels: [
      {
        title: 'Events',
        type: 'table',
        span: 12,
        fill: 1,
        linewidth: 2,
        targets: customTargets,
        tooltip: {
          shared: true
        }
      }
    ],
    refresh: "5s",
    style: "dark",
    // templating: {
    //     list: customVariables
    // }
  });
}


console.log(dashboard);


return dashboard
