// my test rest cluster server
var cluster = require('cluster');
var numCPUs = require('os').cpus().length;
var nodemailer = require('nodemailer');

var svcpath = null;
var transport = nodemailer.createTransport("SMTP", {
    service: 'Gmail'
    , auth: {
        user: "palert@picarro.com"
        , pass: "palert123"
    }
});

process.stdout.write('restcluster args: ' + process.argv + '\n');
if (process.argv.length > 2) {
    svcpath = process.argv[2];
}

csp_frag = "N/A"
if (process.argv.length > 4) {
    csp_frag = process.argv[4];
}


// The Worker
var restsvc = require(svcpath);

if (cluster.isMaster) {
    var i;
    console.log("versions", process.versions);
    
    // Fork workers.
    var wkr = []
    for ( i = 0; i < numCPUs; i++) {
        wkr[i] = cluster.fork();
        console.log("worker pid is: " + wkr[i].pid);
    }

    cluster.on('death', function(worker) {
        var msg = "";
        var now_ts = new Date();
        msg += csp_frag + ' worker ' + worker.pid + ' died - ' + now_ts;
        i += 1;
        wkr[i] = cluster.fork();
        msg += '\n' + "restarted as worker pid: " + wkr[i].pid;
        console.log(msg);
        var message = {
            from: 'P3 Alert <palert@picarro.com>'
            //, to: ['sdavis@picarro.com']
            , to: ['jmontross@picarro.com']
            , subject: 'P-Cubed Node.JS alert!'
            , headers: {'X-Laziness-level': 1000}
            , text: msg
        };
        transport.sendMail(message, function(error) {
            if (error) {
                console.log("error in sending email");
                console.log("   msg: ", msg);
                return;
            }
        })
    });
} else {
    console.log('This process is pid ' + process.pid);
    restsvc.run();
}
