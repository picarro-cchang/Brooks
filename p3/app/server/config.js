module.exports = function(){
    switch(process.env.NODE_ENV){
        case 'development':
        console.log('app started in development mode');
            return {
              "mongo":{"dbport":27017,
              "replSet":false
            }
          };

        case 'local':
            return {
                "mongo":{"dbport":27017}
               ,"p3node" : {
                     "csp_url":  "https://localhost:8081/node" //"https://dev.picarro.com/node"
                   , "ticket_url":  "https://localhost:8081/node/rest/sec/dummy/1.0/Admin/" //"https://dev.picarro.com/node/rest/sec/dummy/1.0/Admin/"
                   , "identity":  "85490338d7412a6d31e99ef58bce5dPM"
                   , "psys":  "SUPERADMIN"
                   , "rprocs":  '["AnzMeta:byAnz", "AnzLogMeta:byEpoch", "AnzLog:byEpoch"]'
                 }
             };

        case 'production':
            console.log('app started in production mode');
            return {
              "mongo":{
                "dbport":[37017,38018,37019],
                "replSet":true
              }
          };

        default:
            console.log('app started in production mode');
            return {
              "mongo":{
                "dbport":[37017,38018,37019],
                "replSet":true
              }
          };
    }
};