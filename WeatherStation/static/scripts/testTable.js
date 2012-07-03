
function boolToIcon(value) {
    var name = (value) ? ("icon-ok") : ("icon-remove");
    return (undefined !== value) ? '<i class="' + name + '"></i>' : '';
}

function makeColorPatch(value) {
    var result = '<div style="width:15px;height:15px;border:1px solid #000;margin:0 auto;';
    result += 'background-color:' + value + ';"></div>';
    return (undefined !== value) ? result : '';
}

function processComments(value, params) {
    var fieldWidth = 15;
    if (undefined !== params && undefined !== params.fieldWidth) {
        fieldWidth = params.fieldWidth;
    }
    if (value.length <= fieldWidth) {
        return value;
    }
    else {
        return value.substring(0, fieldWidth - 3) + "...";
    }
}

function validate(eidByKey, template, container, onSuccess) {
    var numRe = /^[+\-]?([0-9]+\.?[0-9]*|(\.[0-9]+))$/;
    if (!numRe.test($("#" + eidByKey.H4).val())) {
        tableFuncs.addError(eidByKey.H4, "Number required");
        tableFuncs.addTip(container, "Please try again");
    }
    else {
        onSuccess();
    }
}

var template = {id: "test-table",
                vf: validate, 
                layout: [
    {key: "H1", width: "15%", th: "Heading 1", tf: String, eid: "id_H1", cf: String},
    {key: "H2", width: "15%", th: "Heading 2", tf: boolToIcon, eid: "id_H2",
      ef: function (s, b) {
            $(s).val(String(b));
        }, cf: function (s) {   return s === "true"; 
                            }
        },
    {key: "H3", width: "15%", th: "Heading 3", tf: makeColorPatch, eid: "id_H3", cf: String},
    {key: "H4", width: "15%", th: "Heading 4", tf: parseFloat, eid: "id_H4", cf: parseFloat},
    {key: "C", width: "15%", th: "Comments", tf: processComments, tfParams: {fieldWidth: 12},
        eid: "id_C", cf: String},
    {width: "5%", th: tableFuncs.newRowButton(), tf: tableFuncs.editButton},
    {width: "5%", th: tableFuncs.clearButton(), tf: tableFuncs.deleteButton},
    {key: "S", width: "15%", th: "Status", omit: true}
]};


var tableData = [
    {"H1": "Row1_1", "H2": true, "H3": "#00FF00", "H4": 1.0, "C": "Row1_Comments and more"},
    {"H1": "Row2_1", "H2": true, "H3": "#FF0000", "H4": 4.0, "C": "Row2_Comments and more", "S": "Status"},
    {"H1": "Row3_1", "H2": false, "H3": "#0000FF", "H4": 9.0, "C": "Row3_Comments and more"}
];

// Row used to initialize form on insert
var initRow = {"H1": "First", "H2": true, "H3": "#FFFFFF", "H4": 1.0, "C": "Comments"};

function editTableChrome()
{
    var header, body, footer;
    var controlClass = "input-large";
    header = '<div class="modal-header"><h3>Data Row</h3></div>';
    body   = '<div class="modal-body">';
    body += '<form id="id_edit_form" class="form-horizontal"><fieldset>';
    body += tableFuncs.editControl("Heading 1", tableFuncs.makeInput("id_H1", {"class": controlClass, "placeholder": "Some text"}));
    body += tableFuncs.editControl("Heading 2", tableFuncs.makeSelect("id_H2", {"class": controlClass}, {"true": "Yes", "false": "No"}));
    body += tableFuncs.editControl("Heading 3", tableFuncs.makeSelect("id_H3", {"class": controlClass},
            {"#000000": "black", "#0000FF": "blue", "#00FF00": "green", "#FF0000": "red", 
             "#00FFFF": "cyan",  "#FF00FF": "magenta", "#FFFF00": "yellow", "#FFFFFF": "white" }));
    body += tableFuncs.editControl("Heading 4", tableFuncs.makeInput("id_H4", {"class": controlClass, "placeholder": "Height"}));
    body += tableFuncs.editControl("Comments", tableFuncs.makeTextArea("id_C", {"class": controlClass}));
    body += '</fieldset></form></div>';
    footer = '<div class="modal-footer">';
    footer += '<p class="validate_tips alert alert-error hide"></p>';
    footer += '<button class="btn btn-primary btn-ok">OK</button>';
    footer += '<button class="btn btn-cancel">Cancel</button>';
    footer += '</div>';
    return header + body + footer;
}

function beforeShow() {}

function initialize(winH, winW) {
    var container = $("#myModal");
    $("#id_jsTable").html(tableFuncs.makeTable(tableData, template));
    $("#id_jsTable table").addClass("table table-condensed table-striped");
    $("#id_jsTable table tbody").addClass("sortable");
    $(".sortable").sortable({helper: tableFuncs.sortableHelper});
    $("#id_jsTable tbody").on("click", "a.table-delete-row", function (e) {
        $(e.currentTarget).closest("tr").remove();
    });
    $("#id_jsTable table").on("click", "a.table-clear", function (e) {
        $(e.currentTarget).closest("table").find("tbody").empty();
    });
    $("#id_jsTable tbody").on("click", "a.table-edit-row", function (e) {
        tableFuncs.editRow($(e.currentTarget).closest("tr"), template, container, editTableChrome, beforeShow);
    });
    $("#id_jsTable table").on("click", "a.table-new-row", function (e) {
        tableFuncs.insertRow(e, template, container, editTableChrome, beforeShow, initRow);
    });
}
