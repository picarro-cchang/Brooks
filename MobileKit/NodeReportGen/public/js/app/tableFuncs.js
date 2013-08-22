/* Simple table-based forms for jQuery and bootstrap
 * 
 * This file provides the object tableFuncs which contains functions to support:
 * 1) Generating a table whose rows may be entered and edited via a form on a modal page
 * 2) Loading and saving the table to an array ("tableData") whose elements are objects describing the rows
 * 3) The relationship between the data in the table and what is displayed in its HTML representation 
 *     may be defined using translation functions. Similarly, the form used to edit the table contents
 *     may be customized.
 *
 * An example of the "tableData" array for a table with three rows is
 *
 * tableData = [
 *                {"H1":"Row1_1","H2":true, "H3":"#00FF00","H4":1.0,"C":"Row1_Comments and more"},
 *                {"H1":"Row2_1","H2":false,"H3":"#FF0000","H4":4.0,"C":"Row2_Comments and more"},
 *                {"H1":"Row3_1","H2":false,"H3":"#0000FF","H4":9.0,"C":"Row3_Comments and more"}
 *            ];
 *
 * Each row consists of key/value pairs. The keys represent the columns in the table which are to be saved,
 *  but their names are not necessarily the same as the heading names. A separate template object is used 
 *  to define how the table is laid out and how it appears on the web page.
 * 
 *  An example template is
 *  
 *  template = {id:"test-table",
 *                layout:[
 *                    {key:"H1",width:"15%",th:"Heading 1",tf:String,eid:"id_H1",cf:String},
 *                    {key:"H2",width:"15%",th:"Heading 2",tf:boolToIcon,eid:"id_H2",
 *                        ef:function(s,b){$(s).val(String(b));},cf:function(s){ return s==="true"; }},
 *                    {key:"H3",width:"15%",th:"Heading 3",tf:makeColorPatch,eid:"id_H3",cf:String},
 *                    {key:"H4",width:"15%",th:"Heading 4",tf:parseFloat,eid:"id_H4",cf:String},
 *                    {key:"C", width:"15%",th:"Comments", tf:processComments,tfParams:{fieldWidth:12},
 *                        eid:"id_C",cf:String},
 *                    {width:"5%",th:tableFuncs.newRowButton(),tf:tableFuncs.editButton},
 *                    {width:"5%",th:tableFuncs.clearButton(),tf:tableFuncs.deleteButton},
 *                    {key:"S",width:"15%",th:"Status",omit:true},
 *                vf:validate,
 *                cb:function(type,data,row) { console.log("Done"); } 
 *                ]};
 *
 * id: This is the id of the table in the DOM
 * layout: This is an array specifying the layout of the table. There is one element per column in the table.
 *      "key" is the column key, which matches the key in the tableData
 *      "width" is the width of the column
 *      "th" is the column heading
 *      "tf" (optional) is the translation function which generates the HTML of the table <tr> element from the data 
 *            in the tableData for the specified key. "tf" takes the value for the table cell (from tableData) as 
 *            its first argument. 
 *            Additional parameters for the translation function may be specified using "tfParams".
 *            If "tf" is not specified, undefined values are translated to an empty string and other values are
 *            passed through String to generate the HTML
 *        "tfParams" (optional) is an object which is passed as the second argument to the HTML translation function
 *      "eid" (optional) is the id of the form element via which the user enters or edits the value of the table cell
 *      "ef" (optional) is a function used to fill a form element with the data in a cell so that it may be edited. The
 *            signature is ef(element,cellValue). If not present, the form element is filled using element.val(cellValue)
 *      "cf" (optional) is a function used to translate the value in a form element into the data to be placed in the cell.
 *            If not specified, the value() method of the form element is used.
 *      "omit" (optional). If this is present and truthy, the column key is not written into tableData.
 * vf: This is the name of a validation function with signature validate(rowData,eidByKey,row,container). It
 *      is called when a row is edited or inserted. It should return true to indicate that the row is valid.
 *      "rowData" is a row which is proposed for introduction into the tableData array
 *      "eidByKey" is a dictionary which gives the id of the edit control corresponding to the column key
 *      "container" is a jQuery representation of the modal div containing the editing form for the table
 * cb: Callback on completion of a table operation. The first parameter is a string indicating the event type, the second
 *      is a reference to the data of the table, the third is the data of the row involved and the fourth is the row itself
 *      to allow this to be modified.
 */

if (typeof define !== 'function') { var define = require('amdefine')(module); }

define(function(require, exports, module) {
    'use strict';
    $ = require('jquery');

    var tableFuncs;

    function closeModal(m) {
        m.modal("hide");
        m.html();
    }

    function makeRowHtml(rowData, template) {
        // Constructs the HTML of a row in a table from the row data object and the table template
        var args, col, colattr, html, key, result = ["<tr>"], temp;
        for (col = 0;col < template.layout.length;col++) {
            html = "";
            temp = template.layout[col];
            key  = temp.key;
            args = [rowData[key]];
            args.push(temp.tfParams);
            if (temp.hasOwnProperty("tf")) {
                html = temp.tf.apply(this, args);
            }
            else {
                html = (rowData[key] === undefined) ? "" : String(rowData[key]);
            }
            colattr = [];
            if (undefined !== key) {
                colattr.push('data-key="' + key + '"');
                colattr.push('data-value="' + escape(JSON.stringify(rowData[key])) + '"');
            }
            result.push('<td ' + colattr.join(" ") + '>' + html + '</td>');
        }
        result.push("</tr>");
        return result.join("\n");
    }

    function makeBodyHtml(tableData, template) {
        var row, rowData, result = ["<tbody>"];
        for (row = 0;row < tableData.length;row++) {
            rowData = tableData[row];
            result.push(makeRowHtml(rowData, template));
        }
        result.push("</tbody>");
        return result.join("\n");
    }

    function makeHeadHtml(template) {
        var col, colattr, html, key, result = ["<thead><tr>"], temp, width;
        for (col = 0;col < template.layout.length;col++) {
            temp = template.layout[col];
            html = temp.th;
            key  = temp.key;
            width = temp.width;
            colattr = [];
            if (undefined !== key) {
                colattr.push('data-key="' + key + '"');
            }
            if (undefined !== width) {
                colattr.push('style="width:' + width + '"');
            }
            result.push('<th ' + colattr.join(" ") + '>' + html + '</th>');
        }
        result.push("</tr></thead>");
        return result.join("\n");
    }

    function getRowData(row, template) {
        var key, value, rowDict = {};
        $(row).children("td").each(function (j, y) {
            var temp = template.layout[j];
            var omit = (undefined !== temp.omit) && temp.omit;
            key = $(y).attr("data-key");
            if (!omit && (undefined !== key)) {
                value = $(y).attr("data-value");
                if ("undefined" !== value) {
                    value = JSON.parse(unescape(value));
                    rowDict[key] = value;
                }
            }
        });
        return rowDict;
    }

    function appendToTable(rowData, template) {
        $("#" + template.id + " tbody").append(makeRowHtml(rowData, template));
    }

    function makeRowDataFromEditForm(eidByKey, template) {
        var cf, col, rowData = {}, temp;
        var key, layout = template.layout;

        for (col = 0;col < layout.length;col++) {
            temp = layout[col];
            key  = temp.key;
            var omit = (undefined !== temp.omit) && temp.omit;
            if (undefined !== key && !omit) {
                // Get the conversion function from the output of the .val method of the 
                //  control to the data
                if (undefined !== eidByKey[key]) {
                    cf = temp.cf;
                    if (typeof cf === "function") {
                        rowData[key] = cf($("#" + eidByKey[key]).val());
                    }
                    else {
                        rowData[key] = $("#" + eidByKey[key]).val();
                    }
                }
            }
        }
        return rowData;
    }

    function editRowOk(e) {
        var onSuccess;
        var data = e.data;
        var eidByKey = data.eidByKey, container = data.container, row = data.row, template = data.template;

        onSuccess = function () {
            var rowData = makeRowDataFromEditForm(eidByKey, template);
            // Get index of tr so we can return the new row to the callback
            var which = $("#" + template.id + " tbody tr").index(row);
            $(row).replaceWith(makeRowHtml(rowData, template));
            closeModal(container);
            if (typeof template.cb === 'function') {
                template.cb("update", tableFuncs.getTableData(template), rowData, $("#" + template.id + " tbody tr").eq(which));
            }
        };
        if (typeof template.vf === 'function') {
            template.vf(eidByKey, template, container, onSuccess);
        }
        else {
            onSuccess();
        }
    }

    function insertRowOk(e) {
        var onSuccess;
        var data = e.data;
        var eidByKey = data.eidByKey, container = data.container, template = data.template;

        onSuccess = function () {
            var rowData = makeRowDataFromEditForm(eidByKey, template);
            $("#" + template.id + " tbody").append(makeRowHtml(rowData, template));
            closeModal(container);
            if (typeof template.cb === 'function') {
                var table = tableFuncs.getTableData(template);
                template.cb("add", table, table[table.length-1],$("#" + template.id + " tbody tr").eq(-1));
            }
        };
        if (typeof template.vf === 'function') {
            template.vf(eidByKey, template, container, onSuccess);
        }
        else {
            onSuccess();
        }
    }

    function makeControl(elem, id, attrDict, contents) {
        var result = '<' + elem + ' id="' + id + '"';
        for (var a in attrDict) {
            if (attrDict.hasOwnProperty(a)) {
                result += ' ' + a + '="' + attrDict[a] + '"';
            }
        }
        result += '>' + contents + '</' + elem + '>';
        return result;
    }

    /******************************************************************************************************/
    /* Externally Visible Functions                                                                       */
    /******************************************************************************************************/

    tableFuncs = {
        newRowButton: function () {
            return '<button type="button" class="btn btn-success btn-mini table-new-row"><i class="icon-plus icon-white"></i></button>';
        },
        clearButton: function () {
            return '<button type="button" class="btn btn-danger btn-mini table-clear"><i class="icon-remove icon-white"></i></button>';
        },
        editButton: function () {
            return '<button type="button" class="btn btn-warning btn-mini table-edit-row"><i class="icon-pencil icon-white"></i></button>';
        },
        deleteButton: function () {
            return '<button type="button" class="btn btn-danger btn-mini table-delete-row"><i class="icon-trash icon-white"></i></button>';
        },
        editControl: function (label, control) {
            var result = [];
            result.push('<div class="control-group">');
            result.push('<label class="control-label" for="' + $(control).attr("id") + '">' + label + '</label>');
            result.push('<div class="controls">');
            result.push(control);
            result.push('</div>');
            result.push('</div>');
            return result.join('\n');
        },
        addError: function (field_id, message) {
            var id = "#" + field_id;
            if ($(id).next('.help-inline').length === 0) {
                $(id).after('<span class="help-inline">' + message + '</span>');
                $(id).parents("div .control-group").addClass("error");
            }
            $(id).on('focus keypress', function () {
                $(this).next('.help-inline').fadeOut("fast", function () {
                    $(this).remove();
                });
                $(this).parents('.control-group').removeClass('error');
            });
        },
        addTip: function (container, message) {
            $(container).find(".validate_tips").html(message).show();
            $(container).find("input, select, textarea").on('focus keypress', function () {
                $(".validate_tips").fadeOut("fast");
            });
        },
        makeControl: makeControl,
        makeInput: function (id, attrDict) {
            return makeControl("input", id, attrDict, "");
        },
        makeTextArea: function (id, attrDict) {
            return makeControl("textarea", id, attrDict, "");
        },
        makeSelect: function (id, attrDict, optionsDict) {
            var options = "";
            for (var o in optionsDict) {
                if (optionsDict.hasOwnProperty(o)) {
                    options += '<option value="' + o + '">' + optionsDict[o] + '</option>';
                }
            }
            return makeControl('select', id, attrDict, options);
        },
        getRowData: function(row,template) {
            return getRowData(row,template);
        },
        getTableData: function (template) {
            var tableData = [];
            // Get the data object from a table in the DOM. This may be serialized and 
            //  subsequently used to reconstruct the table.
            $("#" + template.id + " tbody tr").each(function (i, row) {
                tableData.push(getRowData(row, template));
            });
            return tableData;
        },
        makeTable: function (tableData, template) {
            var result = ['<table id="' + template.id + '">'];
            result.push(makeHeadHtml(template));
            result.push(makeBodyHtml(tableData, template));
            result.push("</table>");
            return result.join("\n");
        },
        sortableHelper: function (e, tr) {
            var $originals = tr.children();
            var $helper = tr.clone();
            $helper.children().each(function (index) {
                // Set helper cell sizes to match the original sizes
                $(this).width($originals.eq(index).width());
            });
            return $helper;
        },
        editRow: function (row, template, container, makeChrome, beforeShow)
        {
            var rowData = getRowData(row, template);
            var efByKey = {}, eidByKey = {};

            $(template.layout).each(function (i, o) {
                efByKey[o.key]  = o.ef;
                eidByKey[o.key] = o.eid;
            });
            $(container).html(makeChrome());
            for (var key in rowData) {
                if (rowData.hasOwnProperty(key)) {
                    // Populate the edit control field, translating via the ef field 
                    //  of template if this is specified 
                    if (typeof efByKey[key] === "function") {
                        efByKey[key]($(container).find("#" + eidByKey[key]), rowData[key]);
                    }
                    else {
                        $(container).find("#" + eidByKey[key]).val(rowData[key]);
                    }
                }
            }
            $(container).find("button.btn-ok").on("click", {row: row, template: template, eidByKey: eidByKey,
                container: container}, editRowOk);
            $(container).find("button.btn-cancel").on("click", function (e) {
                closeModal($(container));
            });
            if (typeof beforeShow === "function") {
                beforeShow(function () {
                    $(container).modal("show");
                });
            }
            else $(container).modal("show");
        },
        insertRow: function (e, template, container, makeChrome, beforeShow, initRowData) {
            var efByKey = {}, eidByKey = {};
            $(template.layout).each(function (i, o) {
                efByKey[o.key]  = o.ef;
                eidByKey[o.key] = o.eid;
            });
            $(container).html(makeChrome());
            if (undefined !== initRowData) {
                for (var key in initRowData) {
                    if (initRowData.hasOwnProperty(key)) {
                        // Populate the edit control field, translating via the ef field 
                        //  of template if this is specified 
                        if (typeof efByKey[key] === "function") {
                            efByKey[key]($(container).find("#" + eidByKey[key]), initRowData[key]);
                        }
                        else {
                            $(container).find("#" + eidByKey[key]).val(initRowData[key]);
                        }
                    }
                }
            }
            $(container).find("button.btn-ok").on("click", {template: template, eidByKey: eidByKey,
                container: container}, insertRowOk);
            $(container).find("button.btn-cancel").on("click", function (e) {
                closeModal($(container));
            });
            if (typeof beforeShow === "function") {
                beforeShow(function () {
                    $(container).modal("show");
                });
            }
            else $(container).modal("show");
        },
        setCell: function (row, key, value, template) {
            var args, col, html = "", temp;
            // Set the value of a particular cell in the table specified by the row and the key
            for (col = 0;col < template.layout.length;col++) {
                temp = template.layout[col];
                if (key === temp.key) {
                    args = [value];
                    args.push(temp.tfParams);
                    if (temp.hasOwnProperty("tf")) {
                        html = temp.tf.apply(this, args);
                    }
                    else {
                        html = (value === undefined) ? "" : String(value);
                    }
                    break;
                }
            }
            $(row).find('td[data-key="' + key + '"]').attr("data-value", escape(JSON.stringify(value))).html(html);
        },
        getRowByIndex: function (index, template) {
            return $("#" + template.id + " tbody tr").eq(index);
        }
    };

    module.exports = tableFuncs;
});
