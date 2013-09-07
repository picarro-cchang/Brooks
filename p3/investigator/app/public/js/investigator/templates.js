
// // Fixed HTML pane
// function modalNetWarning() {
//     var hdr, body, footer, c1array, c2array;

//     body = '<p><h3>' + TXT.conn_warning_txt + '</h3></p>';

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c1array.push('<h3>' + TXT.conn_warning_hdr + '</h3>');
//     c2array.push(HBTN.warningCloseBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
//     footer = "";

//     return setModalChrome(
//         hdr,
//         body,
//         footer
//         );
// }


// var statusPane = function () {
//     var pane = '<table style="width: 100%;">';
//     pane += '<tr>';
//     pane += '<td style="width:25%; padding:5px 0px 10px 10px;">';
//     pane += '<img class="stream-ok" src="' + CNSNT.spacer_gif + '" onclick="showStream();" name="stream_stat" id="id_stream_stat" />';
//     pane += '</td>';
//     pane += '<td style="width:25%; padding:5px 0px 10px 10px;">';
//     pane += '<img class="analyzer-ok" src="' + CNSNT.spacer_gif + '" onclick="showAnalyzer();" name="analyzer_stat" id="id_analyzer_stat" />';
//     pane += '</td>';
//     pane += '<td style="width:25%; padding:5px 0px 10px 10px;">'
//     pane += '<img class="gps-uninstalled" src="' + CNSNT.spacer_gif + '" onclick="showGps();" name="gps_stat" id="id_gps_stat" />';
//     pane += '</td>';
//     pane += '<td style="width:25%; padding:5px 0px 10px 10px;">'
//     pane += '<img class="ws-uninstalled" src="' + CNSNT.spacer_gif + '" onclick="showWs();" name="ws_stat" id="id_ws_stat" />';
//     pane += '</td>';
//     pane += '</tr>';
//     pane += '</table>';
//     return pane;
// };

// var followPane = function () {
//     var pane = '<table style="width: 100%;">'
//         + '<tr>'
//         + '<td style="width:33.33%;">'
//         + '<img class="follow" src="' + CNSNT.spacer_gif + '" data-checked="true" onclick="changeFollow();" name="follow" id="id_follow" />'
//         + '</td>'
//         + '<td style="width:33.33%;">'
//         + '<img class="overlay" src="' + CNSNT.spacer_gif + '" data-checked="true" name="overlay" id="id_overlay" />'
//         + '</td>'
//         + '<td style="width:33.33%; padding-left:5px;">'
//         + '<img class="wifi" src="' + CNSNT.spacer_gif + '" name="data_alert" id="id_data_alert" />'
//         + '</td>'
//         + '</tr>'
//         + '</table>';

//     return pane;
// };

// var modePane = function() {
//     var pane = '';

//     if (CNSNT.prime_view) {
//         pane = '<div style="margin-left:20px;">'
//             + '<h2 id="mode">Survey Mode</h2>'
//             + '</div>';
//     }

//     return pane;
// }

// // tableChrome NOTE: first element (index 0) in each cNarray is the "style" tag for the td div
// function tableChrome(tblStyle, trStyle, c1array, c2array, c3array, c4array) {
//     var tbl, i, len, body, c1sty, c2sty, c3sty, c4sty;
//     tbl = '';
//     body = '';

//     c1sty = '';
//     c2sty = '';
//     c3sty = '';
//     c4sty = '';

//     // all passed arrays must be of same length
//     if (c2array !== undefined) {
//         if (c1array.length !== c2array.length) {
//             return tbl;
//         }
//     }
//     if (c3array !== undefined) {
//         if (c1array.length !== c3array.length) {
//             return tbl;
//         }
//     }
//     if (c4array !== undefined) {
//         if (c1array.length !== c4array.length) {
//             return tbl;
//         }
//     }

//     len = c1array.length
//     for (i = 0; i < len; i += 1) {
//         if (i === 0) {
//             c1sty = c1array[i];
//             if (c2array !== undefined) {
//                 c2sty = c2array[i];
//             }
//             if (c3array !== undefined) {
//                 c3sty = c3array[i];
//             }
//             if (c4array !== undefined) {
//                 c4sty = c4array[i];
//             }
//         } else {
//             body += '<tr ' + trStyle + '>';

//             body += '<td ' + c1sty + '>' + c1array[i] + '</td>';
//             if (c2array !== undefined) {
//                 body += '<td ' + c2sty + '>' + c2array[i] + '</td>';
//             }
//             if (c3array !== undefined) {
//                 body += '<td ' + c3sty + '>' + c3array[i] + '</td>';
//             }
//             if (c4array !== undefined) {
//                 body += '<td ' + c4sty + '>' + c4array[i] + '</td>';
//             }

//             body += '</tr>';
//         }
//     }

//     tbl += '<table ' + tblStyle + '>';
//     tbl += body;
//     tbl += '</table>';

//     return tbl;
// }



// function setModalChrome(hdr, msg, click) {
//     var modalChrome = "";

//     modalChrome = '<div class="modal" style="position: relative; top: auto; left: auto; margin: 0 auto; z-index: 1">';

//     modalChrome += '<div class="modal-header">';
//     modalChrome += hdr;
//     modalChrome += '</div>';
//     modalChrome += '<div class="modal-body">';
//     modalChrome += msg;
//     modalChrome += '</div>';
//     modalChrome += '<div class="modal-footer">';
//     modalChrome += click;
//     modalChrome += '</div>';


//     modalChrome += '</div>';

//     return modalChrome;
// }

// function modalPanePrimeControls() {
//     var capOrCan, i, modalChrome, hdr, body, footer, c1array, c2array;

//     c1array = [];
//     c2array = [];

//     c1array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 50%;"');

//     c1array.push(HBTN.restartBtn);
//     c2array.push(HBTN.calibrateBtn);

//     c1array.push(HBTN.completeSurveyBtn);
//     c2array.push('');

//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c1array.push('<h3>' + TXT.anz_cntls + '</h3>');
//     c2array.push(HBTN.modChangeCloseBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);


//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c1array.push(HBTN.shutdownBtn);
//     c2array.push('');
//     footer = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
//     $("#id_restartBtn").focus();
// }

// function modalPaneExportControls() {
//     var modalChrome, exportBtns, hdr, body, footer, c1array, c2array;

//     c1array = [];
//     c2array = [];

//     c1array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 50%;"');
//     c1array.push(exportClassCntl('style="width: 100%;"'));
//     c2array.push(HBTN.exptLogBtn);
//     c1array.push('');
//     c2array.push(HBTN.exptPeakBtn);
//     c1array.push('');
//     c2array.push(HBTN.exptAnalysisBtn);
//     c1array.push('');
//     c2array.push(HBTN.exptNoteBtn);
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-aligh: left;"');
//     c2array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c1array.push('<h3>' + TXT.download_files + '</h3>');
//     c2array.push(HBTN.modChangeCloseBtn);
//     hdr = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
//     $("#id_restartBtn").focus();
// }

// function modalPaneCopyClipboard(string) {
//     var modalChrome, hdr, body, footer, c1array, c2array;
//     var textinput;

//     textinput = '<div><input type="text" id="id_copystr" style="width:90%; height:25px; font-size:20px; text-align:center;" value="' + string + '"/></div>';

//     c1array = [];
//     c2array = [];
//     c1array.push('style="border-style: none; width: 50%; text-align: right;"');
//     c2array.push('style="border-style: none; width: 50%;"');
//     c1array.push(textinput);
//     c2array.push(HBTN.copyClipboardOkBtn);
//     body = tableChrome('style="width: 100%; border-spacing: 0px;"', '', c1array, c2array);
//     hdr = '<h3>' + TXT.copyClipboard + '</h3>';

//     footer = '';

//     modalChrome = setModalChrome(
//         hdr,
//         body,
//         footer
//         );

//     $("#id_mod_change").html(modalChrome);
//     $("#id_copystr").select();
//     $("#id_copystr").focus();
// }
