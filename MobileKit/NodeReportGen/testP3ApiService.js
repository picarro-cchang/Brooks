newP3ApiService = require('./lib/newP3ApiService');
newRptGenService = require('./lib/newRptGenService');

csp_url = "https://dev.picarro.com/dev";
ticket_url = csp_url + "/rest/sec/dummy/1.0/Admin";
identity = "dc1563a216f25ef8a20081668bb6201e";
psys = "APITEST2";
rprocs = '["AnzLogMeta:byEpoch","AnzLog:byPos","AnzLog:byEpoch","AnzLog:makeSwath","AnzMeta:byAnz","AnzLrt:getStatus",' +
         '"AnzLrt:byRow","AnzLrt:firstSet","AnzLrt:nextSet","AnzLog:byGeo"]';
p3Api = newP3ApiService({"csp_url": csp_url, "ticket_url": ticket_url, "identity": identity, "psys": psys, "rprocs": rprocs});

if (p3Api instanceof Error) {
    console.log("Error getting P3ApiService: " + p3Api);
}
else {
    var svc = "gdu";
    var ver = "1.0";
    var rsc = "AnzLog";
    var params = {'alog':'CFADS2274-20130107-170017Z-DataLog_User_Minimal.dat', 'logtype':'dat', 'varList':'["CH4"]',
                          'limit':10, 'qry':'byPos', 'startPos':0, 'doclist':false};
    p3Api.get(svc, ver, rsc, params, function (err, result) {
        if (err) console.log(err);
        else {
            console.log("Result: " + JSON.stringify(result));
        }
    });
}
/*
rgApi = newRptGenService({"rptgen_url": "http://localhost:5300"});

if (rgApi instanceof Error) {
    console.log("Error getting RptGenService: " + rgApi);
}
else {
    var rsc = "1";
    var params = {};
    rgApi.get(svc, ver, rsc, params, function (err, result) {
        if (err) console.log(err);
        else {
            console.log("Result: " + JSON.stringify(result));
        }
    });
}
*/