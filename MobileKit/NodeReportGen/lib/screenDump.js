// screenDump.js is used by phantom.js to produce a PDF file from HTML via a screen dump from the headless browser
//  The window.status must be set to 'done' to trigger the conversion after all the page elements have been rendered
var page = require('webpage').create(),
    system = require('system'),
    address, output, size,
    paperSize = {},
    headerFontSize = "100%";
    footerFontSize = "70%";

page.onConsoleMessage = function (msg) {
    console.log(msg);
};

if (system.args.length < 3 || system.args.length > 7) {
    console.log('Usage: screenDump.js URL filename [paperwidth*paperheight|paperformat] [zoom] [headerFontSize] [footerFontSize]');
    console.log('  paper (pdf output) examples: "5in*7.5in", "10cm*20cm", "A4", "Letter"');
    phantom.exit(1);
} else {
    address = system.args[1];
    output = system.args[2];
    // page.viewportSize = { width: 600, height: 600 };
    if (system.args.length > 3 && system.args[2].substr(-4) === ".pdf") {
        size = system.args[3].split('*');
        paperSize = size.length === 2 ? { width: size[0], height: size[1], margin: '0px' }
                                      : { format: system.args[3], orientation: 'portrait', margin: '1cm' };
    }
    if (system.args.length > 4) {
        page.zoomFactor = +system.args[4];
    }
    if (system.args.length > 5) {
        headerFontSize = system.args[5];
    }
    if (system.args.length > 6) {
        footerFontSize = system.args[6];
    }
    page.open(address, function (status) {
        var pdfPages = 0;
        if (status !== 'success') {
            console.log('Unable to load the address!');
            console.log("PDF_PAGES: " + pdfPages);
            phantom.exit();
        } else {
            var maxTimeOut = 120000; // milliseconds
            var start = (new Date()).getTime();
            var next = function () {
                var getStatus = page.evaluate(function () {
                    return window.status;
                });
                if (getStatus != 'done' && (new Date()).getTime()-start < maxTimeOut) window.setTimeout(next,200);
                else {
                    var ua = page.evaluate(function() {
                        var el;
                        el = document.getElementById('leftHead');
                        var leftHead = el ? el.innerHTML:null;
                        el = document.getElementById('rightHead');
                        var rightHead = el ? el.innerHTML:null;
                        el = document.getElementById('leftFoot');
                        var leftFoot = el ? el.innerHTML:null;
                        el = document.getElementById('rightFoot');
                        var rightFoot = el ? el.innerHTML:null;
                        el = document.getElementById('startPage');
                        var startPage = +(el ? el.innerHTML:1);

                        return {leftHead:leftHead, rightHead:rightHead,
                                leftFoot:leftFoot, rightFoot:rightFoot, startPage:startPage};
                    });

                    paperSize.header = {
                        height: "2cm",
                        contents: phantom.callback(function(pageNum, numPages) {
                            var txt = ua.leftHead;
                            pdfPages = numPages;
                            return '<h4 style="font-family:Sans-serif;font-size=' + headerFontSize + '">' +
                                txt + '<span style="float:right">' +
                                ua.rightHead + ' page ' + pageNum + '  of  ' + numPages + '</span></h4>';
                        })
                    };
                    paperSize.footer = {
                        height: "1cm",
                        contents: phantom.callback(function(pageNum, numPages) {
                            pdfPages = numPages;
                            return '<p style="font-family:Sans-serif;font-size=' + footerFontSize + '"><small>' +
                                ua.leftFoot + '<span style="float:right">Page  ' +
                                (pageNum + ua.startPage - 1)  + "</span></small></p>";
                        })
                    };
                    /* N.B. Can only assign to page.paperSize. It is NOT possible to change page.paperSize by assigning to its keys */
                    paperSize.margin = {
                        left: '0.5in',
                        top: '0.25in',
                        right: '0.25in',
                        bottom: '0.25in'
                    };
                    page.paperSize = paperSize;
                    page.render(output);
                    console.log("PDF_PAGES: " + pdfPages);
                    phantom.exit();
                }
            };
            next();
        }
    });
}
