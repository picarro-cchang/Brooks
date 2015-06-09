# These are various static string representations
# Do not change these without complete regression testing all postprocess apps

UNIX_PICARRO_HOME = "/usr/local/picarro"
WIN_PICARRO_HOME = "C:/Picarro"

PROCESS_TYPE = "Process"
SAMPLE_TYPE = "Sample"
DETAIL_TYPE = "Detail"
COMMENTS_TYPE = "COMMENTS"
DISPLAY_SUMMARY_TYPE = "DISPLAY SUMMARY"
DISPLAY_DETAIL_TYPE = "DISPLAY DETAIL"
PLOT_TYPE = "PLOT"
DEFINITIONS_TYPE = "DEFINITIONS"
PROCESS_VARIABLES_TYPE = "PROCESS VARIABLES"
SAMPLE_VARIABLES_TYPE = "SAMPLE VARIABLES"
DETAIL_VARIABLES_TYPE = "DETAIL VARIABLES"
FUNCTION_DEFINITION_TYPE = "FUNCTION DEFINITION"

SOURCE_PARM = "source1"
SOURCE_PARM2 = "source2"
SOURCE_PARM3 = "source3"
SOURCE_PARM4 = "source4"
SOURCE_PARM5 = "source5"
INSTRUCTION_PARM = "instFile"
STANDARDS_PARM = "standardsFile"
IGNOREINST_PARM = "ignoreRow"
EXPORT_DATA_WITH_GRAPH_PARM = "expData"
POINTS_PARM = "points"

LAST_START_DIR_PARM = "startDir"
LAST_NAME_PARM= "searchName" 
LAST_FROM_TS_PARM = "searchFromTS"
LAST_TO_TS_PARM = "searchToTS" 
LAST_COPY_DIR_PARM = "copyDir" 
LAST_CONCAT_NAME_PARM = "concatName" 

IDENTIFIER = "identifier"
INJECTION = "injection"
LINE = "line"
TIMECODE = "timecode"
OUTPUTBASE = "OutputBase"
STANDARDSFILE = "StandardsFile"
SAMPLE = "sample"
JOB = "job"
VALUE = "value"
FLOAT = "float"
INT = "int"
IGNORE = "ignore"
OK = "ok"
STATUS = "status"

RED = "red"
YELLOW = "yellow"
GREEN = "green"
CYAN = "cyan"
BLUE = "blue"
MAGENTA = "magenta"
BLACK = "black"
WHITE = "white"
GREY = "grey"

VARRAY = "varray"
NAME = "name"

COMBO = "combo"
PLOT = "plot"
PLOT0 = "plot0"
PLOT1 = "plot1"
PLOT2 = "plot2"
PLOT3 = "plot3"
PLOT_NEXT = "plot_next"
MOD = "mod"
MOD0 = "mod0"
MOD1 = "mod1"
MOD2 = "mod2"
MOD3 = "mod3"
EXPORT_SHEET = "export_sheet"
HTML = "html"
PARAMETER = "parameter"
HTML_PANE = "html_pane"
PLOT_PANE = "plot_pane"
INST = "inst"
FILESAVE = "filesave"
OUTFILE = "outfile"
OUTFILE2 = "outfile2"
WILDCARD = "wildcard"
WILDCARD2 = "wildcard2"
GOOD_MSG = "good_msg"
GOOD_MSG2 = "good_msg2"
OPEN_MSG = "open_msg"
OPEN_MSG2 = "open_msg2"
RTN_OUTFILE = "rtn_outfile"
RTN_OUTFILE2 = "rtn_outfile2"
INFO_MSG = "info_msg"
INFO_MSG2 = "info_msg2"
SOURCE = "source"
START_TIMER = "start_timer"
STOP_TIMER = "stop_tmer"
FILEOPEN = "fileopen"
SKIPOUT_2 = "skip out2"
STEP = "step"
TEXT_CNTL = "text_cntl"
TEXT_CNTL_DSP = "text_cntl_display"
SPACER_CNTL = "spacer_cntl"
SPACER_CNTL_SM = "spacer_cntl_sm"
SPACER_CNTL_SKIP = "spacer_cntl_skip"
CHOICE_CNTL = "choice_cntl"
RADIO_CNTL = "radio_cntl"
NOTE_CNTL = "note_cntl"
PASSWD_CNTL = "passwd_cntl"
DIROPEN = "diropen"
START_PATH = "start_path"
MODAL_WIN = "modal_win"
POST_BTN_MSG = "post_btn_msg"
POST_BTN_ERROR_MSG = "post_btn_error_msg"
BUTTON = "button"
PROCESS = "process"


CHOICE_NONE = "-- None --"

STANDALONE_ERROR = "defines a class which cannot be run \
                    as a stand-alone process."
SOURCE_REQ_ERROR = "Class requires a source file."
CSV_REQ_ERROR = "Class requires a valid csv source_file."
H5_REQ_ERROR = "Class requires a valid h5 source_file."
TEXT_REQ_ERROR = "Class requires a valid txt source_file."
INVALID_SOURCE_ERROR = "Class requires a valid source."

MARKER_COLORS_DICT = {
                    BLUE: "b",
                    GREEN: "g",
                    RED: "r",
                    CYAN: "c",
                    MAGENTA: "m",
                    YELLOW: "y",
                    BLACK: "k",
                    WHITE: "w"
                      }
        
MARKER_POINTS_DICT = {
                    "solid line": "-",
                    "dashed line": "--",
                    "dash-dot": "-",
                    "dotted line": ":",
                    "point marker": ".",
                    "pixel marker": ",",
                    "circle marker": "o",
                       }

LEGEND_LOCATION_DICT = {
                    "best": 0,
                    "upper right": 1,
                    "upper left": 2,
                    "lower left": 3,
                    "lower right": 4,
                    "right": 5,
                    "center left": 6,
                    "center right": 7,
                    "lower center": 8,
                    "upper center": 9,
                    "center": 10,                  
                        }

MARKER_POINTS_DICT_RVS = {}
for mk in MARKER_POINTS_DICT.keys():
    MARKER_POINTS_DICT_RVS[MARKER_POINTS_DICT[mk]] = mk
    
MARKER_COLORS_DICT_RVS = {}
for mk in MARKER_COLORS_DICT.keys():
    MARKER_COLORS_DICT_RVS[MARKER_COLORS_DICT[mk]] = mk

LEGEND_LOCATION_DICT_RVS = {}
for mk in LEGEND_LOCATION_DICT.keys():
    LEGEND_LOCATION_DICT_RVS[LEGEND_LOCATION_DICT[mk]] = mk
    
# colors for html panels
PNL_SHADECOLOR = GREY
PNL_GREENCOLOR = "#00FF00"
PNL_YELLOWCOLOR = YELLOW
PNL_REDCOLOR = RED
PNL_CYANCOLOR = CYAN
PNL_PLOT_DEFAULT_COLOR = BLUE
PNL_TBL_HEADINGCOLOR = "#FAEBD7"
PNL_TBL_BACKGROUNDCOLOR = "#FFFFF0"
PNL_TBL_BORDERCOLOR = "#A9A9A9"

PLOT_DEFAULT_COLOR = BLUE
PLOT_SHADE_COLOR = "light grey"


# colors for xlwt worksheets
WS_SHADECOLOR = "grey25"
WS_GREENCOLOR = GREEN
WS_YELLOWCOLOR = YELLOW
WS_REDCOLOR = RED
WS_CYANCOLOR = "cyan_ega"



MAIN_BACKGROUNDCOLOR = "#E0FFFF"
CONTROL_BACKGROUNDCOLOR = "#43C6DB"
PLOT_FACECOLOR = "#437C17"

HTML_COPYRIGHT = "&copy; 2011 Picarro Inc."

