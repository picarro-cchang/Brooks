define(['app/p3restapi', 'chai', 'mocha'],
function(p3restapi, chai) {
    'use strict';
    return function () {
        var expect = chai.expect;
        var IDENTITY = "dc1563a216f25ef8a20081668bb6201e";
        var PSYS = "APITEST2";
        var HOST = "dev.picarro.com";
        var PORT = 443;
        var SITE = "dev";

        describe('AnzMeta', function() {
            this.timeout(6000);
            var AnzMeta;
            it('should fetch a list of analyzers', function (done) {
                var initArgs = {host: HOST, port: PORT, site: SITE,
                                identity: IDENTITY, psys: PSYS,
                                rprocs: ["AnzMeta:byAnz"],
                                svc: "gdu", version: "1.0",
                                resource: "AnzMeta",
                                jsonp: true,
                                debug: true};
                AnzMeta = new p3restapi.p3RestApi(initArgs);
                AnzMeta.byAnz({limit: 5},
                function (err) {
                    console.log("Error in get:", err);
                    console.log("");
                    done();
                },
                function (status, rtnObj) {
                    console.log("Success in get:", status);
                    console.log(rtnObj);
                    done();
                });
            });
        });
    };
});
