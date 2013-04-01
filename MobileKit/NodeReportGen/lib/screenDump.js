var page = require('webpage').create(),
    system = require('system'),
    address, output, size;

if (system.args.length < 3 || system.args.length > 5) {
    console.log('Usage: screenDump.js URL filename [paperwidth*paperheight|paperformat] [zoom]');
    console.log('  paper (pdf output) examples: "5in*7.5in", "10cm*20cm", "A4", "Letter"');
    phantom.exit(1);
} else {
    address = system.args[1];
    output = system.args[2];
    page.viewportSize = { width: 600, height: 600 };
    if (system.args.length > 3 && system.args[2].substr(-4) === ".pdf") {
        size = system.args[3].split('*');
        page.paperSize = size.length === 2 ? { width: size[0], height: size[1], margin: '0px' }
                                           : { format: system.args[3], orientation: 'portrait', margin: '1cm' };

        /* default header/footer for pages that don't have custom overwrites (see below)
        page.paperSize.header = {
            height: "1cm",
            contents: phantom.callback(function(pageNum, numPages) {
                if (pageNum == 1) {
                    return "";
                }
                return "<h1>Header <span style='float:right'>" + pageNum + " / " + numPages + "</span></h1>";
            })
        };
        page.paperSize.footer = {
            height: "1cm",
            contents: phantom.callback(function(pageNum, numPages) {
                if (pageNum == numPages) {
                    return "";
                }
                return "<h1>Footer <span style='float:right'>" + pageNum + " / " + numPages + "</span></h1>";
            })
        };
        */
    }
    if (system.args.length > 4) {
        page.zoomFactor = system.args[4];
    }
    page.open(address, function (status) {
        if (status !== 'success') {
            console.log('Unable to load the address!');
            phantom.exit();
        } else {
            var maxTimeOut = 30000; // milliseconds
            var start = (new Date()).getTime();
            var next = function () {
                var getStatus = page.evaluate(function () {
                    return window.status;
                });
                if (getStatus != 'done' && (new Date()).getTime()-start < maxTimeOut) window.setTimeout(next,200);
                else {
                    page.render(output);
                    phantom.exit();
                }
            };
            next();
        }
    });
}
