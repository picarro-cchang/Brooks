newRptGenService = require('./lib/newRptGenService');

rgApi = newRptGenService({"rptgen_url": "http://localhost:5300"});

if (rgApi instanceof Error) {
    console.log("Error getting RptGenService: " + rgApi);
}
else {
    var rsc = "1";
    var params = {};
    rgApi.get(rsc, params, function (err, result) {
        if (err) console.log(err);
        else {
            console.log("Result: " + JSON.stringify(result));
        }
    });
}
