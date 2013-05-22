
            var gi = "test";
            google.load("earth", "1");

            function init() {
              google.earth.createInstance('ge_container', initCB, failureCB);
            }

            function initCB(instance) {
                ge = instance;
                gi = ge;
                ge.getWindow().setVisibility(true);
                // var link = ge.createLink('');
                // var href = 'http://localhost:5000/static/test3.kml'
                // link.setHref(href);

                // var networkLink = ge.createNetworkLink('');
                // networkLink.set(link, true, true); // Sets the link, refreshVisibility, and flyToView

                // ge.getFeatures().appendChild(networkLink);
                // GoogleEarth.setView(48.761, -121.794);
                GoogleEarth.init();

                // setTimeout(function(){
                //     GoogleEarth.renderSample();
                // }, 1000)

            }

            function failureCB(errorCode) {
            }

            google.setOnLoadCallback(init);