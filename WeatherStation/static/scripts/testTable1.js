var CNSNT = {};

var tableDat = [
	{"H1":"Row1_1","H2":true, "H3":"#00FF00","H4":1.0,"C":"Row1_Comments and more"},
	{"H1":"Row2_1","H2":false,"H3":"#FF0000","H4":4.0,"C":"Row2_Comments and more"},
	{"H1":"Row3_1","H2":false,"H3":"#0000FF","H4":9.0,"C":"Row3_Comments and more"}
];

var tableFuncs = {
	boolToIcon:function(value) {
		var name = (value) ? ("icon-ok") : ("icon-remove");
		return '<i class="' + name + '"></i>';
	},
	makeColorPatch:function(value) {
		var result = '<div style="width:15px;height:15px;border:1px solid #000;margin:0 auto;';
		result += 'background-color:' + value +';"></div>';
		return result;
	},
	processComments:function(value,params) {
		var fieldWidth = 15;
		if (undefined !== params && undefined !== params["fieldWidth"]) {
			fieldWidth = params["fieldWidth"];
		}
		if (value.length <= fieldWidth) {
			return value;
		}
		else {
			return value.substring(0,fieldWidth-3) + "...";
		}
	},
	newRowButton:function() {
		return '<a class="btn btn-success btn-mini table-new-row"><i class="icon-plus icon-white"></i></a>';
	},
	clearButton:function() {
		return '<a class="btn btn-danger btn-mini table-clear"><i class="icon-remove icon-white"></i></a>';
	},
	editButton:function() {
		return '<a class="btn btn-warning btn-mini table-edit-row"><i class="icon-pencil icon-white"></i></a>';
	},
	deleteButton:function() {
		return '<a class="btn btn-danger btn-mini" onclick="deleteTableRow(this)"><i class="icon-trash icon-white"></i></a>';
	},
	editControl:function(label,control) {
	    var result = [];
		result.push('<div class="control-group">');
		result.push('<label class="control-label" for="' + $(control).attr("id") + '">' + label + '</label>');
		result.push('<div class="controls">');
	    result.push(control);
	    result.push('</div>');
	    result.push('</div>');
	    return result.join('\n');
	},
	onEditRow:function(obj) {
		console.log(obj);
		alert(obj);
	}
};

var template = {id:"test-table",
				layout:[
					{key:"H1",width:"18%",th:"Heading 1",tf:String},
	                {key:"H2",width:"18%",th:"Heading 2",tf:tableFuncs.boolToIcon},
	                {key:"H3",width:"18%",th:"Heading 3",tf:tableFuncs.makeColorPatch},
	                {key:"H4",width:"18%",th:"Heading 4",tf:parseFloat},
	                {key:"C", width:"18%",th:"Comments", tf:tableFuncs.processComments,tfParams:{fieldWidth:12}},
	                {width:"5%",th:tableFuncs.newRowButton(),tf:tableFuncs.editButton},
	                {width:"5%",th:tableFuncs.clearButton(),tf:tableFuncs.deleteButton}
	            ]};

function editTableChrome(okButton)
{
    var header, body, footer;
    
    header = '<div class="modal-header"><h3>Data Row</h3></div>';
    body   = '<div class="modal-body">';
    body += '<form id="id_edit_form" class="form-horizontal"><fieldset>';
    body += tableFuncs.editControl("Heading 1", '<input type="text" id="id_H1" class="input-xlarge"/>');
    body += tableFuncs.editControl("Heading 2", '<input type="text" id="id_H2" class="input-xlarge"/>');
    body += tableFuncs.editControl("Heading 3", '<input type="text" id="id_H3" class="input-xlarge"/>');
    body += tableFuncs.editControl("Heading 4", '<input type="text" id="id_H4" class="input-xlarge"/>');
    body += tableFuncs.editControl("Comments",  '<input type="text" id="id_C"  class="input-xlarge"/>');
    body += '</fieldset></form></div>';
    footer = '<div class="modal-footer">';
    footer += '<p class="validate_tips alert alert-error"></p>';
    footer += '<button class="btn btn-primary btn-ok">OK</button>';
    footer += '<button class="btn btn-cancel">Cancel</button>';
    footer += '</div>';
    return header + body + footer;
}

var makeTable = null, sortableHelper = null;
/* Comment out next line to make internal functions visible */
(function() {
	function makeRowHtml(rowData,template) {
		// Constructs the HTML of a row in a table from the row data object and the table template
		var args, col, colattr, html, key, result=["<tr>"], temp;
		for (col=0;col<template.layout.length;col++) {
			temp = template.layout[col];
			key  = temp["key"];
			args = [rowData[key]];
			args.push(temp["tfParams"]);
			html = temp["tf"].apply(this,args);
			colattr = [];
			if (undefined !== key) {
				colattr.push('data-key="' + key + '"');
				colattr.push('data-value="' + escape(JSON.stringify(rowData[key]))+'"');			
			}
			result.push('<td ' + colattr.join(" ") + '>' + html + '</td>');
		}
		result.push("</tr>");
		return result.join("\n");
	}
	
	function makeBodyHtml(tableDat,template) {
		var row, rowData, result=["<tbody>"];
		for (row=0;row<tableDat.length;row++) {
			rowData = tableDat[row];
			result.push(makeRowHtml(rowData,template));
		}
		result.push("</tbody>");
		return result.join("\n");
	}
	
	function makeHeadHtml(template) {
		var col, colattr, html, key, result=["<thead><tr>"], temp, width;
		for (col=0;col<template.layout.length;col++) {
			temp = template.layout[col];
			html = temp["th"];
			key  = temp["key"];
			width = temp["width"];
			colattr = [];
			if (undefined !== key) {
				colattr.push('data-key="' + key + '"');			
			}
			if (undefined !== width) {
				colattr.push('style="width:'+ width +'"');			
			}
			result.push('<th ' + colattr.join(" ") + '>' + html + '</th>');
		}
		result.push("</tr></thead>");
		return result.join("\n");
	}
		
	/******************************************************************************************************/
    /* Externally Visible Functions                                                                       */
	/******************************************************************************************************/	
	makeTable = function(tableDat,template) {
		var result = ['<table id="' + template.id +'">'];
		result.push(makeHeadHtml(template));
		result.push(makeBodyHtml(tableDat,template));
		result.push("</table>");
		return result.join("\n");
	};
	
	sortableHelper = function(e,tr) {
	    var $originals = tr.children();
	    var $helper = tr.clone();
	    $helper.children().each(function(index)
	        {
	          // Set helper cell sizes to match the original sizes
	          $(this).width($originals.eq(index).width());
	        });
	    return $helper;
	};
	
	getTableDat = function(template) {
		var key, value, tableDat = [];
		// Get the data object from a table in the DOM. This may be serialized and 
		//  subsequently used to reconstruct the table.
		$("#"+template.id+" tbody tr").each(function(i,x){
			var rowDict = {};
			$(x).children("td").each(function(j,y){
				key = $(y).attr("data-key");
				if (undefined !== key) {
					value = JSON.parse(unescape($(y).attr("data-value")));
					rowDict[key] = value;
				}
			});
			tableDat.push(rowDict);
		});
		return tableDat;
	};
	
	deleteTableRow = function(delButton) {
		$(delButton).closest("tr").remove();
	};

	editTableRow = function(editButton) {
		$(editButton).closest("tr");
	};
	
/* Comment out next line to make internal functions visible */
})();

function initialize(winH,winW) {
	$("#id_jsTable").html(makeTable(tableDat,template));
	$("#id_jsTable table").addClass("table table-condensed table-striped");
	$("#id_jsTable table tbody").addClass("sortable");
	$(".sortable").sortable({helper:sortableHelper});
	$("#id_jsTable tbody a.table-edit-row").click(function(e) {
		$(e.currentTarget).closest("tr").remove();
	});
};
