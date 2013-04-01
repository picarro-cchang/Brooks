/* Use phantom.js to render a simple page with a delay */

var page = require('webpage').create();

page.paperSize = {format: "Letter", orientation: 'portrait', margin: '1cm' };

page.open('http://localhost:5300/checkPdfConvert', function (status) {
    if (status !== 'success') {
        console.log('Unable to load the address!');
        phantom.exit();
    } else {
        var next = function () {
            var getStatus = page.evaluate(function () {
                //return document.getElementById('completion').innerText.indexOf('After') >= 0;
                return window.status;
            });
            console.log('Status:', getStatus);
            if (getStatus != 'done') window.setTimeout(next,200);
            else {
                page.render('sample.pdf');
                phantom.exit();
            }            
        };
        next();
    }
});