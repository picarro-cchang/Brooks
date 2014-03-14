'''
instproc.py -- the instproc module contains the InstructionProcess class
This class will process a source CSV file (from coordinator) using a defined 
procedural instruction set (also a CSV file). The instruction set defines the 
process and defines the resulting information
'''
import os
import csv
import re
import datetime
import time
import string

from postprocessdefn import *

from scipy import stats
from numpy import *

CCVER = '1.2.0'

class InstructionProcess(object):
    '''
    Evaluate and process instructions from a ChemCorrect (tm) procedural
    instruction set
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if "ctl_file" in kwargs:
            self._ctl_file = kwargs["ctl_file"]
            del kwargs["ctl_file"]
        else:
            self._ctl_file = None
            
        # About Info
        self.about_name = "InstructionProcess"

        if not 'ccver' in kwargs:
            self.about_version = CCVER
        else:
            self.about_version = kwargs['ccver']
            del kwargs['ccver']

        self.about_copyright = "(c) 2011 Picarro Inc."
        self.about_description = "Post process the analyzer output using \
        ChemCorrect(tm) procedural instruction set."
        self.about_website = "http://www.picarro.com"

        self._unix_picarro_home = "/usr/local/picarro"
        self._win_picarro_home = "C:/Picarro"
        self._chemcorrect_dir = "ChemCorrect"
        self._archive_dir = "Archive/Spectra"
        self._archive2_dir = "Archive/Spectra10"
        self._outdir = ""

        if os.name == "nt":
            self._picarro_home = self._win_picarro_home
        else:
            self._picarro_home = self._unix_picarro_home
            
        # error log
        self._error_log = {}
        
        self._valid_instruction_types = [
                         DEFINITIONS_TYPE,
                         PROCESS_VARIABLES_TYPE,
                         SAMPLE_VARIABLES_TYPE,
                         DETAIL_VARIABLES_TYPE,
                         DISPLAY_SUMMARY_TYPE,
                         DISPLAY_DETAIL_TYPE,
                         PLOT_TYPE,
                         COMMENTS_TYPE,
                         FUNCTION_DEFINITION_TYPE,
                         ]
        
        self._instructions_catalog = {
                                    "float": ["",True,True,True],
                                    "is_standard_sample": ["",False,True,True],
                                    "col": ["",False,True,True],
                                    "mean_all": ["",True,True,True],
                                    "mean_standards": ["",True,True,True],
                                    "std_all": ["",True,True,True],
                                    "std_standards": ["",True,True,True],
                                    "evaluation": ["_do_evaluation",True,True,True],
                                    "truth_evaluation": ["_do_truth_evaluation",True,True,True],
                                    "math_evaluation": ["_do_math_evaluation",True,True,True],
                                    "abs": ["_do_abs",True,True,True],
                                    "current_standards_mean": ["_do_current_standards_mean",False,True,True],
                                    "current_standards_diff": ["_do_current_standards_diff",False,True,True],
                                    "current_standards_endval": ["_do_current_standards_endval",False,True,True],
                                    "known_standard": ["_do_known_standard",False,True,True],
                                    "prior_standards_mean": ["_do_prior_standards_mean",False,True,True],
                                    "prior_standards_endval": ["_do_prior_standards_endval",False,True,True],
                                    "bool_xor": ["_do_bool_xor",True,True,True],
                                    "bool_or": ["_do_bool_or",True,True,True],
                                    "bool_and": ["_do_bool_and",True,True,True],
                                    "fit_type1": ["_do_fit_type1",True,True,True]
                                    }

        # evaluation reg ex
        self._re_float = re.compile("(float)\(([0-9]*[.][0-9]*)\)")
        self._re_eval = re.compile("(evaluation)\(([A-Z,0-9,\_]*[\*\+\-\\\=\!\<\>][=]?[A-Z,0-9,\_]*)\)")
        self._re_factors = re.compile(r'(?P<lfactor>[A-Z,0-9,\.,\_]*)(?P<operand>[\*\+\-\\\=\!\<\>][=]?)(?P<rfactor>[A-Z,0-9,\.,\_]*)')
        self._re_bool_and = re.compile("(bool_and)\(([A-Z,0-9,\_]*[\,][A-Z,0-9,\_]*)\)")
        self._re_bool_or = re.compile("(bool_or)\(([A-Z,0-9,\_]*[\,][A-Z,0-9,\_]*)\)")
        self._re_bool_xor = re.compile("(bool_xor)\(([A-Z,0-9,\_]*[\,\ ][A-Z,0-9,\_]*)\)")
        self._re_bool_factors = re.compile(r'(?P<lfactor>[A-Z,0-9,\_]*)(?P<operand>[\,])(?P<rfactor>[A-Z,0-9,\_]*)')
        self._re_number = re.compile("[\-\+]?[0-9]*[\.\,]?[0-9]+$")
        self._re_integer = re.compile("[\-\+]?[0-9]+$")

        self._column_label_dict = {}
        self._source_dict = {}
        self._samples_detail_dict = {} #sample/col -> value
        self._samples_summary_dict = {} # sample/col -> value -  ignore rows filtered
        self._samples_name_dict = {} # name -> stds boolean
        self._instruction_samples_name_dict = {} # name -> stds boolean
        self._variables_dict = {} # variable/usage -> value

        self._details_detail_dict = {} #sample/col -> value
        self._details_summary_dict = {} # sample/col -> value -  ignore rows filtered
        self._details_name_dict = {} # name -> stds boolean
        self._instruction_detail_name_dict = {} # name -> stds boolean

        self._dt=datetime.datetime.now()


    def get_instruction_from_ctl(self, ctl_file = None):
        '''
        initialize ctl files
        '''
        if ctl_file:
            self._ctl_file = ctl_file
            
            
        if not self._ctl_file:
            return None
        
        instruction_file = {}
        
        f_data = None
        last_source = None
        last_inst = None
        last_inj_ignore = None

        try:
            f = open(self._ctl_file, "rw")
            if f:
                f_data = f.readline()
                while f_data:
                    if "LAST SOURCE: " in f_data:
                        last_source = f_data[13:].strip()
                    if "LAST INST: " in f_data: 
                        last_inst = f_data[11:].strip()
                    if "LAST INJ IGNORE: " in f_data: 
                        last_inj_ignore = f_data[17:].strip()
                    
                    f_data = f.readline()
            
        except:
            pass

        if last_source:
            instruction_file[SOURCE_PARM] = last_source
        
        if last_inst:
            instruction_file[INSTRUCTION_PARM] = last_inst

        if last_inj_ignore:
            instruction_file[IGNOREINST_PARM] = last_inj_ignore
        
        return instruction_file


    def _load_standards(self, def_parms):
        self._stdsfile = def_parms[STANDARDS_PARM]

        self._stateStdsDone = None
        self._stdsdata = {}
        self._stdsdata_current = {}
        self._stdsdata_all = {}
        self._standards_col_names = {}

        # set up the csv reader 
        dataCsv = file(self._stdsfile,"rb")
        dataReader = csv.reader(dataCsv, )

        # Process the data from the csv
        row = 0
        lastWsRow = 0
        firstData = True
        for r in dataReader:
            if row == 0:
                #print r[0].strip(), r[1].strip(), r[2].strip()
                c1n = r[1].strip()
                c2n = r[2].strip()
            if row >= 1:
                self._stdsdata[r[0].strip()] = {}
                self._stdsdata[r[0].strip()][c1n] = r[1]
                self._stdsdata[r[0].strip()][c2n] = r[2]
            row += 1
        
        self._stateStdsDone = True    
        return True
    

        
    def _load_definition_instructions(self, def_parms):
        '''
        load definition instructions
        '''
        self._file_inst = def_parms[INSTRUCTION_PARM]
        
        instCsv = file(self._file_inst, "rb")
        instReader = csv.reader(instCsv,)
        
        instType = None
        for r in instReader:
            if not r:
                continue 
            
            for i in range(len(r)):
                orig = r[i].strip()
                fixed = ""
                for c in orig:
                    if c in string.printable:
                        if not c == string.whitespace:
                            ##print "c: ", c 
                            fixed += c 
                        elif c == ' ':
                            fixed += c
                        
                r[i] = fixed
            
            if r[0].strip() in self._valid_instruction_types:
                instType = r[0].strip()
                #print "instType: %s" %(instType)
                continue
            
            # Everything after COMMENTS are "comments" so break and don't look for new instType
            if instType == COMMENTS_TYPE:
                break
            
            if r[0].strip() > "":
                if instType == DEFINITIONS_TYPE:
                    inst_var = r[0].strip()
                    
                    if inst_var == IDENTIFIER:
                        self._identifier_colname = r[1].strip()
                        #print "identifier: ", r[1].strip(), self._identifier_colname

                    if inst_var == SAMPLE:
                        self._sample_colname = r[1].strip()
                        #print SAMPLE, r[1].strip(), self._sample_colname
                    
                    if inst_var == JOB:
                        self._job_colname = r[1].strip()
                        #print JOB, r[1].strip(), self._job_colname
                    
                    if inst_var == INJECTION:
                        self._injection_colname = r[1].strip()
                        #print "injection: ", r[1].strip(), self._injection_colname
                    
                    if inst_var == OUTPUTBASE:
                        self._outfile = "%s_%s.xls" %(r[1].strip(), self._dt.strftime("%Y%m%d%H%M%S"))
                        self._outdir = "%s_%s" %(r[1].strip(), self._dt.strftime("%Y%m%d%H%M%S"))
                        #print "outfile", self._outfile
                        #print "outdir", self._outdir
                    
#                    if inst_var == STANDARDSFILE:
#                        self._stdsfile = r[1].strip()
#                        #print STANDARDSFILE, self._stdsfile
                    
                    if inst_var == LINE:
                        self._line_colname = r[1].strip()
                        #print LINE, self._line_colname
                    
                    if inst_var == TIMECODE:
                        self._timecode_colname = r[1].strip()
                        #print TIMECODE, self._timecode_colname

                
                else:
                    break
                
                

    def _load_instructions(self, load_parms):
        '''
        load procedural instruction set
        '''
        self._file_inst = load_parms[INSTRUCTION_PARM]
        self._file_injignore = load_parms[IGNOREINST_PARM]
        
        instCsv = file(self._file_inst, "rb")
        instReader = csv.reader(instCsv,)
        
        self._instruction_proc_vars = {}
        self._instruction_samp_vars = {}
        self._instruction_dtl_vars = {}
        self._instruction_stds_vars = {}
        self._sum_all_types = ["mean_all", 
                               "std_all", 
                               "current_standards_diff", 
                               "current_standards_mean",
                               "current_standards_endval",
                               "prior_standards_endval", 
                               "prior_standards_mean",
                               ]
        self._sum_standards_types = [
                                     "mean_standards", 
                                     "std_standards",
                                     ]
        self._sum_mean_types = [
                                "mean_all", 
                                "mean_standards", 
                               "current_standards_diff", 
                               "current_standards_mean",
                               "current_standards_endval",
                               "prior_standards_endval", 
                               "prior_standards_mean",
                                ]
        self._sum_std_types = ["std_all", "std_standards",]
        self._truth_types = ["is_standard_sample", "bool_and", "bool_or", "bool_xor"]

        self._sum_all_types_proc_names = []
        self._sum_standards_types_proc_cols = []
        self._sum_standards_types_proc_names = []
        self._float_types_proc_names = []
        self._evaluation_types_proc_names = []
        self._truth_types_proc_names = []
        self._truth_evaluation_proc_names = []

        self._sum_all_types_samp_names = []
        self._sum_standards_types_samp_cols = []
        self._sum_standards_types_samp_names = []
        self._evaluation_types_samp_names = []
        self._truth_types_samp_names = []
        self._truth_evaluation_samp_names = []

        self._sum_all_types_dtl_cols = []
        self._sum_all_types_dtl_names = []
        self._sum_standards_types_dtl_cols = []
        self._sum_standards_types_dtl_names = []
        self._evaluation_types_dtl_names = []
        self._truth_types_dtl_names = []
        self._truth_evaluation_dtl_names = []

        self._sum_all_types_stds_cols = []
        self._sum_all_types_stds_names = []
        self._sum_standards_types_stds_cols = []
        self._sum_standards_types_stds_names = []

        self._float_types_stds_names = []
        self._evaluation_types_stds_names = []
        
        self._process_inst_var_order = []
        self._sample_inst_var_order = []
        self._detail_inst_var_order = []
        
        self._display_order = []
        self._display_inst = {}
        
        self._detail_order = []
        self._detail_inst = {}
        
        self._plot_order = []
        self._plot_inst = {}
        
        self._inst_dict = {}
        self._inst_column_count = 9
        
        instType = None
        row = 0
        for r in instReader:
            row += 1
            self._inst_dict[row] = r
            
            if not r:
                continue
            
            if r[0].strip() in self._valid_instruction_types:
                instType = r[0].strip()
                #print "instType: %s" %(instType)
                continue
            
            # Everything after COMMENTS are "comments"
            if instType == COMMENTS_TYPE:
                break
            
            if r[0].strip() > "":
                if instType == DEFINITIONS_TYPE:
                    continue
                
                if instType == DISPLAY_SUMMARY_TYPE:
                    inst_var = r[0].strip()
                    if not inst_var in self._display_order:
                        self._display_order.append(inst_var)
                        self._display_inst[inst_var] = []
                        first = True
                        for x in r:
                            if first:
                                first = False
                            else:
                                self._display_inst[inst_var].append(x)
                        #self._display_inst[inst_var] = (r[1].strip(), r[2].strip(), r[3].strip(), r[4].strip(), r[5].strip(), r[6].strip(), r[7].strip(), r[8].strip())
                        
                if instType == DISPLAY_DETAIL_TYPE:
                    inst_var = r[0].strip()
                    if not inst_var in self._detail_order:
                        self._detail_order.append(inst_var)
                        self._detail_inst[inst_var] = []
                        first = True
                        for x in r:
                            if first:
                                first = False
                            else:
                                self._detail_inst[inst_var].append(x)
                        #self._detail_inst[inst_var] = (r[1].strip(), r[2].strip(), r[3].strip(), r[4].strip(), r[5].strip(), r[6].strip(), r[7].strip(), r[8].strip())
                
                if instType == PLOT_TYPE:
                    inst_var = r[0].strip()
                    if not inst_var in self._plot_order:
                        self._plot_order.append(inst_var)
                        self._plot_inst[inst_var] = []
                        first = True
                        for x in r:
                            if first:
                                first = False
                            else:
                                self._plot_inst[inst_var].append(x)
                        #self._plot_inst[inst_var] = (r[1].strip(), r[2].strip(), r[3].strip(), r[4].strip(), r[5].strip(), r[6].strip(), r[7].strip(), r[8].strip())
                
                if instType == PROCESS_VARIABLES_TYPE:
                    inst_var = r[0].strip()
                    if not inst_var in self._process_inst_var_order:
                        self._process_inst_var_order.append(inst_var)
                    self._instruction_proc_vars[inst_var] = {}
                    self._instruction_proc_vars[inst_var]["operation"] = r[1].strip()
                    inst, val = self._decode_function(r[1].strip())

                    if not inst in self._instructions_catalog.keys():
                        raise RuntimeError, "Instruction not in catalog. instruction: %s" %(inst_var)
                    else:
                        inst_function, is_proc, is_samp, is_dtl = self._instructions_catalog[inst]
                        if not is_proc:
                            raise RuntimeError, "Instruction is not a PROCESS VARIABLES instruction. instruction: %s" %(inst_var)

                    self._instruction_proc_vars[inst_var][INST] = inst

                    if inst in self._sum_all_types:
                        if not inst_var in self._sum_all_types_proc_names:
                            self._sum_all_types_proc_names.append(inst_var)
                        
                        self._instruction_proc_vars[inst_var]["source_col"] = val
                        self._instruction_proc_vars[inst_var][VARRAY] = []
                        self._instruction_proc_vars[inst_var]["tarray"] = []

                    if inst == "fit_type1":
                        if not inst_var in self._sum_all_types_proc_names:
                            self._sum_all_types_proc_names.append(inst_var)

                        self._instruction_proc_vars[inst_var][INST] = inst
                        self._instruction_proc_vars[inst_var]["source_col"] = val
                        self._instruction_proc_vars[inst_var][VARRAY] = []
                        self._instruction_proc_vars[inst_var]["tarray"] = []

                    if inst in self._sum_standards_types:
                        if not val in self._sum_standards_types_proc_cols:
                            self._sum_standards_types_proc_cols.append(val)
                        if not inst_var in self._sum_standards_types_proc_names:
                            self._sum_standards_types_proc_names.append(inst_var)
                        
                        self._instruction_proc_vars[inst_var]["source_col"] = val
                        self._instruction_proc_vars[inst_var][VARRAY] = []
                        self._instruction_proc_vars[inst_var]["tarray"] = []

                    if inst == FLOAT:
                        if not inst_var in self._float_types_proc_names:
                            self._float_types_proc_names.append(inst_var)
                        
                        self._instruction_proc_vars[inst_var][INST] = inst
                        self._instruction_proc_vars[inst_var][VALUE] = float(val)

                    if inst in self._truth_types:
                        if not inst_var in self._truth_types_proc_names:
                            self._truth_types_proc_names.append(inst_var)

                        self._instruction_proc_vars[inst_var][INST] = inst
                        self._instruction_proc_vars[inst_var]["factors"] = val

                    if inst in ("evaluation", "truth_evaluation", "math_evaluation"):
                        if inst == "evaluation":
                            if not inst_var in self._evaluation_types_proc_names:
                                self._evaluation_types_proc_names.append(inst_var)
                        if inst == "truth_evaluation":
                            if not inst_var in self._truth_evaluation_proc_names:
                                self._truth_evaluation_proc_names.append(inst_var)

                        self._instruction_proc_vars[inst_var][INST] = inst
                        self._instruction_proc_vars[inst_var]["factors"] = val
                        
                    if inst == "abs":
                        self._instruction_proc_vars[inst_var][INST] = inst
                        self._instruction_proc_vars[inst_var]["source_col"] = val
                        

                if instType == SAMPLE_VARIABLES_TYPE:
                    inst_var = r[0].strip()
                    if not inst_var in self._sample_inst_var_order:
                        self._sample_inst_var_order.append(inst_var)
                        
                    for smpl in self._samples_name_dict.keys():
                        if not smpl in self._instruction_samp_vars.keys():
                            self._instruction_samp_vars[smpl] = {}
                        if not inst_var in self._instruction_samp_vars[smpl].keys():
                            self._instruction_samp_vars[smpl][inst_var] = {}

                        self._instruction_samp_vars[smpl][inst_var]["operation"] = r[1].strip()
                        inst, val = self._decode_function(r[1].strip())

                        if not inst in self._instructions_catalog.keys():
                            raise RuntimeError, "Instruction not in catalog. instruction: %s" %(inst_var)
                        else:
                            inst_function, is_proc, is_samp, is_dtl = self._instructions_catalog[inst]
                            if not is_samp:
                                raise RuntimeError, "Instruction is not a %s instruction. instruction: %s" %(SAMPLE_VARIABLES_TYPE, inst_var)

                        if inst in self._sum_all_types:
                            if not inst_var in self._sum_all_types_samp_names:
                                self._sum_all_types_samp_names.append(inst_var)
                            self._instruction_samp_vars[smpl][inst_var][INST] = inst
                            self._instruction_samp_vars[smpl][inst_var]["source_col"] = val
                            self._instruction_samp_vars[smpl][inst_var][VARRAY] = []
                            self._instruction_samp_vars[smpl][inst_var]["tarray"] = []

                        if inst == "fit_type1":
                            if not inst_var in self._sum_all_types_samp_names:
                                self._sum_all_types_samp_names.append(inst_var)
                            self._instruction_samp_vars[smpl][inst_var][INST] = inst
                            self._instruction_samp_vars[smpl][inst_var]["source_col"] = val
                            self._instruction_samp_vars[smpl][inst_var][VARRAY] = []
                            self._instruction_samp_vars[smpl][inst_var]["tarray"] = []

                        if inst in self._sum_standards_types:
                            if not val in self._sum_standards_types_samp_cols:
                                self._sum_standards_types_samp_cols.append(val)
                            if not inst_var in self._sum_standards_types_samp_names:
                                self._sum_standards_types_samp_names.append(inst_var)
                            self._instruction_samp_vars[smpl][inst_var][INST] = inst
                            self._instruction_samp_vars[smpl][inst_var]["source_col"] = val
                            self._instruction_samp_vars[smpl][inst_var][VARRAY] = []
                            self._instruction_samp_vars[smpl][inst_var]["tarray"] = []

                        if inst == FLOAT:
                            self._instruction_samp_vars[smpl][inst_var][INST] = inst
                            self._instruction_samp_vars[smpl][inst_var][VALUE] = float(val)

                        if inst in self._truth_types:
                            if not inst_var in self._truth_types_samp_names:
                                self._truth_types_samp_names.append(inst_var)
                            if inst == "is_standard_sample":
                                self._instruction_samp_vars[smpl][inst_var][INST] = inst
                                self._instruction_samp_vars[smpl][inst_var][VALUE] = False
                            else:
                                self._instruction_samp_vars[smpl][inst_var][INST] = inst
                                self._instruction_samp_vars[smpl][inst_var]["factors"] = val

                        if inst in ("evaluation", "truth_evaluation", "math_evaluation"):
                            if inst == "evaluation":
                                if not inst_var in self._evaluation_types_samp_names:
                                    self._evaluation_types_samp_names.append(inst_var)
                            if inst == "truth_evaluation":
                                if not inst_var in self._truth_evaluation_samp_names:
                                    self._truth_evaluation_samp_names.append(inst_var)
                            self._instruction_samp_vars[smpl][inst_var][INST] = inst
                            self._instruction_samp_vars[smpl][inst_var]["factors"] = val
                        
                        if inst == "abs":    
                            self._instruction_samp_vars[smpl][inst_var][INST] = inst
                            self._instruction_samp_vars[smpl][inst_var]["source_col"] = val
                            
                        if inst == "known_standard":    
                            self._instruction_samp_vars[smpl][inst_var][INST] = inst
                            self._instruction_samp_vars[smpl][inst_var]["source_col"] = val
                            
                        # for last_standard_diff we need to initialize to store values for standards samples
                        if inst in (
                               "current_standards_diff", 
                               "current_standards_mean",
                               "current_standards_endval",
                               "prior_standards_endval", 
                               "prior_standards_mean",
                               "fit_type1",
                                    ):
                            
                            if not smpl in self._instruction_stds_vars.keys():
                                self._instruction_stds_vars[smpl] = {}
                            
                            if not inst_var in self._instruction_stds_vars[smpl].keys():
                                self._instruction_stds_vars[smpl][inst_var] = {}

                            if not inst_var in self._sum_all_types_stds_names:
                                self._sum_all_types_stds_names.append(inst_var)
                                
                            self._instruction_stds_vars[smpl][inst_var][INST] = inst
                            self._instruction_stds_vars[smpl][inst_var]["source_col"] = val
                            self._instruction_stds_vars[smpl][inst_var][VARRAY] = []
                            self._instruction_stds_vars[smpl][inst_var]["tarray"] = []
                        

                if instType == DETAIL_VARIABLES_TYPE:
                    inst_var = r[0].strip()
                    if not inst_var in self._detail_inst_var_order:
                        self._detail_inst_var_order.append(inst_var)
                        
                    for dtl in self._details_name_dict.keys():
                        row = int(dtl) + 1
                        data = self._source_dict[row]
                        smpl = self._sample_serial_id(data[self._sample_col][VALUE].strip(), data[self._job_col][VALUE].strip())
                        ident = data[self._identifier_col][VALUE].strip()
                        
                        if not dtl in self._instruction_dtl_vars.keys():
                            self._instruction_dtl_vars[dtl] = {}
                        if not inst_var in self._instruction_dtl_vars[dtl].keys():
                            self._instruction_dtl_vars[dtl][inst_var] = {}

                        self._instruction_dtl_vars[dtl][inst_var]["operation"] = r[1].strip()
                        inst, val = self._decode_function(r[1].strip())

                        if not inst in self._instructions_catalog.keys():
                            raise RuntimeError, "Instruction not in catalog. instruction: %s" %(inst_var)
                        else:
                            inst_function, is_proc, is_samp, is_dtl = self._instructions_catalog[inst]
                            if not is_dtl:
                                raise RuntimeError, "Instruction is not a DETAIL VARIABLES instruction. instruction: %s" %(inst_var)

                        self._instruction_dtl_vars[dtl][inst_var][INST] = inst

                        if inst in self._sum_all_types:
                            if not val in self._sum_all_types_dtl_cols:
                                self._sum_all_types_dtl_cols.append(val)
                            if not inst_var in self._sum_all_types_dtl_names:
                                self._sum_all_types_dtl_names.append(inst_var)
                            self._instruction_dtl_vars[dtl][inst_var]["source_col"] = val
                            self._instruction_dtl_vars[dtl][inst_var][VARRAY] = []
                            self._instruction_dtl_vars[dtl][inst_var]["tarray"] = []

                        if inst == "fit_type1":
                            if not inst_var in self._sum_all_types_dtl_names:
                                self._sum_all_types_dtl_names.append(inst_var)
                            self._instruction_dtl_vars[dtl][inst_var][INST] = inst
                            self._instruction_dtl_vars[dtl][inst_var]["source_col"] = val
                            self._instruction_dtl_vars[dtl][inst_var][VARRAY] = []
                            self._instruction_dtl_vars[dtl][inst_var]["tarray"] = []

                        if inst in self._sum_standards_types:
                            if not val in self._sum_standards_types_dtl_cols:
                                self._sum_standards_types_dtl_cols.append(val)
                            if not inst_var in self._sum_standards_types_dtl_names:
                                self._sum_standards_types_dtl_names.append(inst_var)
                            self._instruction_dtl_vars[dtl][inst_var]["source_col"] = val
                            self._instruction_dtl_vars[dtl][inst_var][VARRAY] = []
                            self._instruction_dtl_vars[dtl][inst_var]["tarray"] = []

                        if inst == FLOAT:
                            self._instruction_dtl_vars[dtl][inst_var][VALUE] = float(val)

                        if inst == "col":
                            rval = self._get_col_from_data(r[1].strip(), data)
                            try:
                                rval = float(rval)
                            except:
                                rval = 0.0
                                self._instruction_dtl_vars[dtl][inst_var]["except"] = True
                            self._instruction_dtl_vars[dtl][inst_var][VALUE] = rval


                        if inst in self._truth_types:
                            if not inst_var in self._truth_types_dtl_names:
                                self._truth_types_dtl_names.append(inst_var)
                            if inst == "is_standard_sample":
                                self._instruction_dtl_vars[dtl][inst_var][VALUE] = False
                            else:
                                self._instruction_dtl_vars[dtl][inst_var]["factors"] = val

                        if inst in ("evaluation", "truth_evaluation", "math_evaluation"):
                            if inst == "evaluation":
                                if not inst_var in self._evaluation_types_dtl_names:
                                    self._evaluation_types_dtl_names.append(inst_var)
                            if inst == "truth_evaluation":
                                if not inst_var in self._truth_evaluation_dtl_names:
                                    self._truth_evaluation_dtl_names.append(inst_var)
                            self._instruction_dtl_vars[dtl][inst_var]["factors"] = val
                        
                        if inst == "abs":    
                            self._instruction_dtl_vars[dtl][inst_var]["source_col"] = val
                            
                        if inst in ("known_standard", "fit_type1"):    
                            self._instruction_dtl_vars[dtl][inst_var]["source_col"] = val
                            
                        # for last_standard_diff we need to initialize to store values for standards samples
                        if inst in (
                               "current_standards_diff", 
                               "current_standards_mean",
                               "current_standards_endval",
                               "prior_standards_endval", 
                               "prior_standards_mean",
                               "fit_type1",
                                    ):
                            if not smpl in self._instruction_stds_vars.keys():
                                self._instruction_stds_vars[smpl] = {}
                            if not inst_var in self._instruction_stds_vars[smpl].keys():
                                self._instruction_stds_vars[smpl][inst_var] = {}

                            if not val in self._sum_all_types_stds_cols:
                                self._sum_all_types_dtl_cols.append(val)
                            if not inst_var in self._sum_all_types_stds_names:
                                self._sum_all_types_stds_names.append(inst_var)
                            self._instruction_stds_vars[smpl][inst_var][INST] = inst
                            self._instruction_stds_vars[smpl][inst_var]["source_col"] = val
                            self._instruction_stds_vars[smpl][inst_var][VARRAY] = []
                            self._instruction_stds_vars[smpl][inst_var]["tarray"] = []


            
        return       

    def _decode_function(self, loc):
        test_inst, sep, pre_val = loc.partition("(")
        if test_inst in ("truth_evaluation", "math_evaluation", "col"):
            inst = test_inst
            val = sep + pre_val
            return inst, val
        
        if test_inst in (
                        "abs", 
                        "mean_all", 
                        "mean_standards", 
                        "std_all", 
                        "std_standards", 
                        "current_standards_diff", 
                        "current_standards_mean",
                        "current_standards_endval",
                        "prior_standards_mean", 
                        "prior_standards_endval",
                        "source_col",
                        "evaluation",
                        "known_standard",
                        "fit_type1",
                         ):
            inst = test_inst
            val, sep, right = pre_val.rpartition(")")
            return inst, val
         
        if loc == "is_standard_sample()":
            return "is_standard_sample", None
        
        m = self._re_float.match(loc)
        if m:
            inst = m.group(1)
            val = m.group(2)
            return inst, val
        
        m = self._re_eval.match(loc)
        if m:
            inst = m.group(1)
            val = m.group(2)
            lfactor, operand, rfactor = self._decode_evalfactors(val)
            return inst, (lfactor, operand, rfactor)
                
        m = self._re_bool_and.match(loc)
        if m:
            inst = m.group(1)
            val = m.group(2)
            lfactor, operand, rfactor = self._decode_evalfactors(val, True)
            return inst, (lfactor, operand, rfactor)
                
        m = self._re_bool_or.match(loc)
        if m:
            inst = m.group(1)
            val = m.group(2)
            lfactor, operand, rfactor = self._decode_evalfactors(val, True)
            return inst, (lfactor, operand, rfactor)
                
        m = self._re_bool_xor.match(loc)
        if m:
            inst = m.group(1)
            val = m.group(2)
            lfactor, operand, rfactor = self._decode_evalfactors(val, True)
            return inst, (lfactor, operand, rfactor)
                
        return None, None
    

    def _load_source(self, source_parms):
        self._first_tm = 0
        self._label_column_dict = {} # label -> col - from the original input row 1
        self._column_label_dict = {} # col -> label - from the original input row 1
        self._sample_sequence_dict = {}
        self._sample_sequence_dict_reverse = {}
        self._sample_seq = 0
        self._sample_set_dict = {}

        self._spectra_location = []
        self._spectra_smpl = []
        self._spectra_copies = []


        # populate variable dictionary column numbers (from entered parameters)
        self._vari_cols = [] # list of column numbers which are variable
        self._summary_cols = [] # list of column numbers which are reportable summary/mean 

        temp_summary_dict = {}
        
        self._file_source = source_parms[SOURCE_PARM]
        dataCsv = file(self._file_source,"rb")
        dataReader = csv.reader(dataCsv, )

        # load main input csv file
        row = 0
        lastWsRow = 0
        firstData = True
        for r in dataReader:
            row += 1
            
            # This is the header row - it contains the column names
            if row == 1:
                self._source_column_count = len(r)
                for c in range(0,self._source_column_count):
                    self._label_column_dict[r[c].strip()] = c
                    self._column_label_dict[c] = r[c].strip()

                self._sample_col = self._label_column_dict[self._sample_colname]
                self._job_col = self._label_column_dict[self._job_colname]
                self._injection_col = self._label_column_dict[self._injection_colname]
                self._identifier_col = self._label_column_dict[self._identifier_colname]   
                self._line_col = self._label_column_dict[self._line_colname]
                self._timecode_col = self._label_column_dict[self._timecode_colname]
            
            # These are data rows        
            if row > 1:
                
                if self._first_tm == 0:
                    tc = self._label_column_dict[self._timecode_colname]
                    tm = time.mktime(time.strptime( r[tc].strip(), "%Y/%m/%d %H:%M:%S"))
                    self._first_tm = tm - 1
                    
                # initialize samples dict for each new sample
                if not r[self._sample_col] in self._samples_summary_dict:
                    current_sample_nbr = self._sample_serial_id(r[self._sample_col], r[self._job_col])
                    self._samples_detail_dict[current_sample_nbr] = {}
                    self._samples_summary_dict[current_sample_nbr] = {}
                    self._samples_name_dict[current_sample_nbr] = {}
                    self._samples_name_dict[current_sample_nbr][NAME] = r[self._identifier_col].strip()
            
                # initialize detail dictionary (for each detail row)
                #print "self._line_col:", self._line_col
                if not r[self._line_col] in self._details_summary_dict:
                    current_line_nbr = int(r[self._line_col])
                    self._details_detail_dict[current_line_nbr] = {}
                    self._details_summary_dict[current_line_nbr] = {}
                    self._details_name_dict[current_line_nbr] = {}
                    dtl_name = "%s - %s" %(r[self._sample_col].strip(), r[self._injection_col].strip())
                    self._details_name_dict[current_line_nbr][NAME] = dtl_name
                    
            
            # write the source dictionary
            if row > 1:
                current_line_nbr = int(r[self._line_col]) + 1
            else:
                current_line_nbr = row
            
#            self._source_dict[row] = {}
#            for c in range(0,self._source_column_count):
#                self._source_dict[row][c] = {}
#                self._source_dict[row][c][VALUE] = r[c].strip()

            self._source_dict[current_line_nbr] = {}
            for c in range(0,self._source_column_count):
                self._source_dict[current_line_nbr][c] = {}
                self._source_dict[current_line_nbr][c][VALUE] = r[c].strip()


        return True
       
    def _sample_serial_id(self, sample, job = None):
        sample_int = int(sample)
        job_int = int(job)
        
        sj = "%s - %s" %(sample_int, job_int) 

        if not sj in self._sample_sequence_dict.keys():
            self._sample_seq += 1
            self._sample_sequence_dict[sj] = self._sample_seq
            self._sample_sequence_dict_reverse[self._sample_seq] = sj
            #print self._sample_seq, sj
        
        return self._sample_sequence_dict[sj]
    
    def _evaluate_instruction_variables(self, instruction_parms):
        try:
            self._ignore_row = int(instruction_parms[IGNOREINST_PARM])
        except:
            self._ignore_row = 0
            instruction_parms[IGNOREINST_PARM] = 0
            
        curr_samp = None
        self._row_in_sample = 0
        sd = self._sample_col
        jd = self._job_col
        
        # read all rows from source and populate varray for all instructions needing arrays
        for row_num, row in self._source_dict.iteritems():
            if not row_num == 1:
                smpl = self._sample_serial_id(row[sd][VALUE], row[jd][VALUE])
                if not curr_samp == smpl:
                    curr_samp = smpl
                    self._row_in_sample = 0
                    
                self._row_in_sample += 1

                if self._row_in_sample > self._ignore_row:
                    if IDENTIFIER not in self._instruction_samp_vars[smpl]:
                            self._instruction_samp_vars[smpl][IDENTIFIER] = row[self._identifier_col][VALUE].strip()
                    
                    # get the values array for requested columns (for full set summary)
                    for inst_var in self._sum_all_types_proc_names:
                        c = self._label_column_dict[self._instruction_proc_vars[inst_var]["source_col"]]
                        #c = self._col_nbrs[cid]
                        #print row[c][VALUE]
                        try:
                            val = float(row[c][VALUE])
                        except:
                            val = 0.0
                            self._instruction_proc_vars[inst_var]["except"] = True
                        
                        tc = self._label_column_dict[self._timecode_colname]
                        tm = time.mktime(time.strptime(row[tc][VALUE], "%Y/%m/%d %H:%M:%S"))
                        tm = tm - self._first_tm
                        self._instruction_proc_vars[inst_var]["tarray"].append(tm)
                        self._instruction_proc_vars[inst_var][VARRAY].append(val)

                    # get the values array for requested columns 
                    # but only for standards samples
                    smplstd = self._sample_serial_id(row[self._sample_col][VALUE], row[self._job_col][VALUE])
                    if self._samples_name_dict[smplstd][NAME] in self._stdsdata.keys():
                        #print "we have a standards sample ", self._samples_name_dict[int(row[self._sample_col][VALUE])][NAME]
                        for inst_var in self._sum_standards_types_proc_names:
                            c = self._label_column_dict[self._instruction_proc_vars[inst_var]["source_col"]]
                            
                            #c = self._col_nbrs[cid]
                            #print row[c][VALUE]
                            try:
                                val = float(row[c][VALUE])
                            except:
                                val = 0.0
                                self._instruction_proc_vars[inst_var]["except"] = True
                            
                            tc = self._label_column_dict[self._timecode_colname]
                            tm = time.mktime(time.strptime(row[tc][VALUE], "%Y/%m/%d %H:%M:%S"))
                            tm = tm - self._first_tm
                            self._instruction_proc_vars[inst_var]["tarray"].append(tm)
                            self._instruction_proc_vars[inst_var][VARRAY].append(val)

                    # get values array for requested samples columns (for sample by sample summary)
                    for inst_var in self._sum_all_types_samp_names:
                        c = self._label_column_dict[self._instruction_samp_vars[smpl][inst_var]["source_col"]]
                        #c = self._col_nbrs[cid]
                        try:
                            val = float(row[c][VALUE])
                        except:
                            val = 0.0
                            self._instruction_samp_vars[smpl][inst_var]["except"] = True
                        
                        tc = self._label_column_dict[self._timecode_colname]
                        tm = time.mktime(time.strptime(row[tc][VALUE], "%Y/%m/%d %H:%M:%S"))
                        tm = tm - self._first_tm
                        self._instruction_samp_vars[smpl][inst_var]["tarray"].append(tm)
                        self._instruction_samp_vars[smpl][inst_var][VARRAY].append(val)

                    # get values array for requested samples columns (for sample by sample summary)
                    for inst_var in self._sum_standards_types_samp_names:
                        c = self._label_column_dict[self._instruction_samp_vars[smpl][inst_var]["source_col"]]
                        #c = self._col_nbrs[cid]
                        try:
                            val = float(row[c][VALUE])
                        except:
                            val = 0.0
                            self._instruction_samp_vars[smpl][inst_var]["except"] = True
                        
                        tc = self._label_column_dict[self._timecode_colname]
                        tm = time.mktime(time.strptime(row[tc][VALUE], "%Y/%m/%d %H:%M:%S"))
                        tm = tm - self._first_tm
                        self._instruction_samp_vars[smpl][inst_var]["tarray"].append(tm)
                        self._instruction_samp_vars[smpl][inst_var][VARRAY].append(val)

                    # get values array for standards samples
                    for inst_var in self._sum_all_types_stds_names:
                        c = self._label_column_dict[self._instruction_stds_vars[smpl][inst_var]["source_col"]]
                        try:
                            val = float(row[c][VALUE])
                        except:
                            val = 0.0
                            self._instruction_stds_vars[smpl][inst_var]["except"] = True
                        
                        tc = self._label_column_dict[self._timecode_colname]
                        tm = time.mktime(time.strptime(row[tc][VALUE], "%Y/%m/%d %H:%M:%S"))
                        tm = tm - self._first_tm
                        self._instruction_stds_vars[smpl][inst_var]["tarray"].append(tm)
                        self._instruction_stds_vars[smpl][inst_var][VARRAY].append(val)

        # in name order, resolve all process variable instructions
        for inst_var in self._process_inst_var_order:
            self._instruction_proc_vars = self._do_instructions(inst_var, self._instruction_proc_vars)

        for smpl in self._samples_name_dict.keys():
            # in variable name order, resolve all sample variable instructions
            for inst_var in self._sample_inst_var_order:
                self._instruction_samp_vars[smpl] = self._do_instructions(inst_var, self._instruction_proc_vars, smpl, self._instruction_samp_vars[smpl])

        for dtl in self._details_name_dict.keys():
            row = int(dtl) + 1
            data = self._source_dict[row]
            smpl = self._sample_serial_id(data[self._sample_col][VALUE].strip(), data[self._job_col][VALUE].strip())
            ident = data[self._identifier_col][VALUE].strip()

            for inst_var in self._detail_inst_var_order:
                self._instruction_dtl_vars[dtl] = self._do_instructions(inst_var, self._instruction_proc_vars, smpl, self._instruction_samp_vars[smpl], dtl, self._instruction_dtl_vars[dtl])

        return
    
    def _do_instructions(self, inst_var, proc_variables, smpl=None, samp_variables=None, dtl=None, dtl_variables=None):
        if inst_var in proc_variables.keys():
            inst = proc_variables[inst_var][INST]
            vars = proc_variables
            type = PROCESS_TYPE
        elif inst_var in samp_variables.keys():
            inst = samp_variables[inst_var][INST]
            vars = samp_variables
            type = SAMPLE_TYPE
            #print "sample inst_var: ", inst_var, inst
        elif inst_var in dtl_variables.keys():
            inst = dtl_variables[inst_var][INST]
            vars = dtl_variables
            type = DETAIL_TYPE
            
        if smpl:
            if inst_var in self._sum_all_types_stds_names:
                a = array(self._instruction_stds_vars[smpl][inst_var][VARRAY])
                self._instruction_stds_vars[smpl][inst_var][VALUE] = a.mean()
            
            if inst == "is_standard_sample":
                #print "is_standard_sample smpl: ", smpl
                if self._samples_name_dict[smpl][NAME] in self._stdsdata.keys():
                    #print "standard"
                    vars[inst_var][VALUE] = True
                else:
                    #print "not standard"
                    vars[inst_var][VALUE] = False
        
        if inst in self._instructions_catalog.keys():
            if self._instructions_catalog[inst][0]:
                method_to_call = getattr(self, self._instructions_catalog[inst][0])
                vars[inst_var][VALUE] = method_to_call(type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables)
            else:
                if inst == "mean_all":
                    vars[inst_var][VALUE] = 0
                    a = array(vars[inst_var][VARRAY])
                    vars[inst_var][VALUE] = a.mean()
                elif inst == "mean_standards":
                    vars[inst_var][VALUE] = 0
                    a = array(vars[inst_var][VARRAY])
                    vars[inst_var][VALUE] = a.mean()
                elif inst == "std_all":
                    vars[inst_var][VALUE] = 0
                    a = array(vars[inst_var][VARRAY])
                    vars[inst_var][VALUE] = a.std(ddof=1)
                elif inst == "std_standards":
                    vars[inst_var][VALUE] = 0
                    a = array(vars[inst_var][VARRAY])
                    vars[inst_var][VALUE] = a.std(ddof=1)

        return vars
    
    def _do_truth_evaluation(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        return self._do_evaluation(type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables)
    
    def _do_math_evaluation(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        return self._do_evaluation(type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables)
    
    def _do_evaluation(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            eval = "(%s)" %(proc_variables[inst_var]["factors"])
        elif type == SAMPLE_TYPE:
            eval = "(%s)" %(samp_variables[inst_var]["factors"])
        else:
            eval = "(%s)" %(dtl_variables[inst_var]["factors"])
        
        return self._python_eval(eval, proc_variables, samp_variables, dtl_variables)
    
    def _python_eval(self, exp, proc_variables, samp_variables=None, dtl_variables=None):
        rtn_val = None
        safe_list = [
                     'math','acos', 'asin', 'atan', 'atan2', 
                     'ceil', 'cos', 'cosh', 'degrees', 'e', 
                     'exp', 'fabs', 'floor', 'fmod', 'frexp', 
                     'hypot', 'ldexp', 'log', 'log10', 'modf', 
                     'pi', 'pow', 'radians', 'sin', 'sinh', 
                     'sqrt', 'tan', 'tanh']
        
        variables = dict([ (k, locals().get(k, None)) for k in safe_list ])
        variables['abs'] = abs 
         
        # add all resolved proc variables to the list of available variables for the eval      
        for factor in proc_variables.keys():
            if VALUE in proc_variables[factor]:
                variables[factor] = proc_variables[factor][VALUE]

        # add all resolved sample variables to the list of available variables for the eval
        if samp_variables:
            for factor in samp_variables.keys():
                if VALUE in samp_variables[factor]:
                    variables[factor] = samp_variables[factor][VALUE]
        
        # add all resolved detail variables to the list of available variables for the eval
        if dtl_variables:
            for factor in dtl_variables.keys():
                if VALUE in dtl_variables[factor]:
                    variables[factor] = dtl_variables[factor][VALUE]
        
        #print "exp: ", exp
        try:
            rtn_val = eval(exp, {"__builtins__":None}, variables)
        except ZeroDivisionError:
            rtn_val = 0
            
        #rtn_val = eval(exp, {"__builtins__":None}, variables)
        return rtn_val

    def _do_bool_and(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            lfactor, operand, rfactor = proc_variables[inst_var]["factors"]
        elif type == SAMPLE_TYPE:
            lfactor, operand, rfactor = samp_variables[inst_var]["factors"]
        else:
            lfactor, operand, rfactor = dtl_variables[inst_var]["factors"]
            
        return self._bool_eval(inst_var, lfactor, "and", rfactor, proc_variables, samp_variables, dtl_variables)

    
    def _do_bool_or(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            lfactor, operand, rfactor = proc_variables[inst_var]["factors"]
        elif type == SAMPLE_TYPE:
            lfactor, operand, rfactor = samp_variables[inst_var]["factors"]
        else:
            lfactor, operand, rfactor = dtl_variables[inst_var]["factors"]
            
        return self._bool_eval(inst_var, lfactor, "or", rfactor, proc_variables, samp_variables, dtl_variables)

    
    def _do_bool_xor(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            lfactor, operand, rfactor = proc_variables[inst_var]["factors"]
        elif type == SAMPLE_TYPE:
            lfactor, operand, rfactor = samp_variables[inst_var]["factors"]
        else:
            lfactor, operand, rfactor = dtl_variables[inst_var]["factors"]
            
        return self._bool_eval(inst_var, lfactor, "xor", rfactor, proc_variables, samp_variables, dtl_variables)

    
    def _bool_eval(self, inst_var, lfactor, operand, rfactor, proc_variables, samp_variables, dtl_variables=None):
        rtn_val = True

        lval = self._resolve_factor(lfactor, proc_variables, samp_variables, dtl_variables)
        rval = self._resolve_factor(rfactor, proc_variables, samp_variables, dtl_variables)
        
        if lval == "False":
            lval = False
        elif lval == "True":
            lval = True
        
        if rval == "False":
            rval = False
        elif rval == "True":
            rval = True
        
        if operand == "and":
            rtn_val = (lval and rval)
        elif operand == "or":
            rtn_val = (lval or rval)
        elif operand == "xor":
            rtn_val = bool(lval) ^ bool(rval)
        else:
            raise RuntimeError, "Invalid VARIABLES bool operand is bad: %s %s %s %s" %(inst_var, lfactor, operand, rfactor)
        
        return rtn_val
    

    #def _do_abs(self, inst_var, lfactor, proc_variables, samp_variables, dtl_variables=None):
    def _do_abs(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            lfactor = proc_variables[inst_var]["source_col"]
        elif type == SAMPLE_TYPE:
            lfactor = samp_variables[inst_var]["source_col"]
        else:
            lfactor = dtl_variables[inst_var]["source_col"]
            
        rtn_val = 0.0
        
        lval = self._resolve_factor(lfactor, proc_variables, samp_variables, dtl_variables)
        
        if lval:
            rtn_val = abs(lval)
         
        #print inst_var, "lval: ", lval, "abs: ", rtn_val   
        return rtn_val   
        
    def _do_current_standards_mean(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            sample = 1
        else:
            sample = smpl

        max_k = 0
        k_name = ""
        for smpl,v in self._samples_name_dict.iteritems():
            if v[NAME] in self._stdsdata.keys():
                if smpl <= sample:
                    if max_k <= smpl:
                        max_k = smpl
                        k_name = v[NAME]
        
        if max_k > 0:
            sample_mean = self._instruction_stds_vars[max_k][inst_var][VALUE]
        else:
            sample_mean = 0
        
        return sample_mean
    
    def _do_current_standards_endval(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            sample = 1
        else:
            sample = smpl

        max_k = -1
        k_name = ""
        for smpl,v in self._samples_name_dict.iteritems():
            if v[NAME] in self._stdsdata.keys():
                if smpl <= sample:
                    if max_k <= smpl:
                        max_k = smpl
                        k_name = v[NAME]
        
        if max_k > -1:
            l = len(self._instruction_stds_vars[max_k][inst_var][VARRAY])
            sample_mean = self._instruction_stds_vars[max_k][inst_var][VARRAY][l - 1]
        else:
            sample_mean = 0
        
        return sample_mean
    

    def _do_prior_standards_mean(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            return 0
        else:
            sample = smpl

        max_k = 0
        prior_k = 0
        k_name = ""
        for smpl,v in self._samples_name_dict.iteritems():
            if v[NAME] in self._stdsdata.keys():
                if smpl <= sample:
                    if max_k <= smpl:
                        prior_k = max_k
                        max_k = smpl
                        k_name = v[NAME]
        
        if prior_k > 0:
            if VALUE in self._instruction_stds_vars[prior_k][inst_var].keys():
                sample_mean = self._instruction_stds_vars[prior_k][inst_var][VALUE]
            else:
                sample_mean = 0
        else:
            sample_mean = 0
        
        return sample_mean
    
    def _do_prior_standards_endval(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            return 0
        else:
            sample = smpl
        
        max_k = 0
        prior_k = 0
        k_name = ""
        for smpl,v in self._samples_name_dict.iteritems():
            if v[NAME] in self._stdsdata.keys():
                if smpl <= sample:
                    if max_k <= smpl:
                        prior_k = max_k
                        max_k = d
                        k_name = v[NAME]
        
        if prior_k > 0:
            l = len(self._instruction_stds_vars[prior_k][inst_var][VARRAY])
            sample_mean = self._instruction_stds_vars[prior_k][inst_var][VARRAY][l-1]
        else:
            sample_mean = 0
        
        return sample_mean
    
    def _do_current_standards_diff(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            sample = 1
        else:
            sample = smpl

        diff = 0
        max_k = 0
        k_name = ""
        for smpl,v in self._samples_name_dict.iteritems():
            if v[NAME] in self._stdsdata.keys():
                if smpl <= sample:
                    if max_k <= smpl:
                        max_k = smpl
                        k_name = v[NAME]
        
        if max_k > 0:
            sample_mean = self._instruction_stds_vars[max_k][inst_var][VALUE]
            std_col = self._instruction_samp_vars[sample][inst_var]["source_col"]
            mean1 = self._stdsdata[k_name][std_col]
            stdmean = float(mean1)
            diff = stdmean - sample_mean
        
        return diff
    
    def _do_fit_type1(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        if type == PROCESS_TYPE:
            sample = 1
            src_col_id = self._instruction_proc_vars[inst_var]["source_col"]
            sample_array = array(proc_variables[inst_var][VARRAY])
        elif type == SAMPLE_TYPE:
            sample = smpl
            src_col_id = self._instruction_samp_vars[sample][inst_var]["source_col"]
            sample_array = array(samp_variables[inst_var][VARRAY])

        else:
            row = int(dtl) + 1
            data = self._source_dict[row]
            sample = int(data[self._sample_col][VALUE].strip()) 
            src_col_id = self._instruction_dtl_vars[dtl][inst_var]["source_col"]
            source_col_id = self._instruction_dtl_vars[dtl][inst_var]["source_col"]
            source_col = self._label_column_dict[source_col_id]
            val = data[source_col][VALUE].strip()
            if not val:
                val = 0.0
            sample_array = array( float(val) )

        # build the standards set
        self._derive_standard_sample_sets()
        
 
        #get the appropriate standard sample group.
        std_group = 0
        for k in self._standard_set_dict.keys():
            if self._standard_set_dict[k]["min_smpl"] <= sample:
                std_group = k

        x_col = {}
        y_col = {}
        
        if not std_group in self._standard_set_dict.keys():
            return 0.0
        
        for ident in self._standard_set_dict[std_group]:
            if not ident == "min_smpl":
                for std_col_id in self._standard_set_dict[std_group][ident]["mean"].keys():
                    if not std_col_id in x_col.keys():
                        x_col[std_col_id] = []
                        y_col[std_col_id] = []
                    val = float(self._standard_set_dict[std_group][ident]["mean"][std_col_id])
                    actual_value = float(self._stdsdata[ident][std_col_id])
                    x_col[std_col_id].append(actual_value)
                    y_col[std_col_id].append(val)
                    #print std_group, ident, std_col_id, val, actual_value
        
        #src_col_id = self._instruction_samp_vars[sample][inst_var]["source_col"]
        cs = sample_array
        a = array(cs)
        meana = a.mean()
        
        aaa = array(x_col[src_col_id])
        ama = array(y_col[src_col_id])
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(aaa,ama)
    
        if type == PROCESS_TYPE:
            self._instruction_proc_vars[inst_var]["fit_slope"] = slope
            self._instruction_proc_vars[inst_var]["fit_intercept"] = intercept
            self._instruction_proc_vars[inst_var]["fit_rsq"] = (r_value ** 2)
            self._instruction_proc_vars[inst_var]["measure_array"] = ama
            self._instruction_proc_vars[inst_var]["actual_array"] = aaa
            self._instruction_proc_vars[inst_var]["actual_mean"] = meana
        elif type == SAMPLE_TYPE:
            self._instruction_samp_vars[sample][inst_var]["fit_slope"] = slope
            self._instruction_samp_vars[sample][inst_var]["fit_intercept"] = intercept
            self._instruction_samp_vars[sample][inst_var]["fit_rsq"] = (r_value ** 2)
            self._instruction_samp_vars[sample][inst_var]["measure_array"] = ama
            self._instruction_samp_vars[sample][inst_var]["actual_array"] = aaa
            self._instruction_samp_vars[sample][inst_var]["actual_mean"] = meana
        else:
            self._instruction_dtl_vars[dtl][inst_var]["fit_slope"] = slope
            self._instruction_dtl_vars[dtl][inst_var]["fit_intercept"] = intercept
            self._instruction_dtl_vars[dtl][inst_var]["fit_rsq"] = (r_value ** 2)
            self._instruction_dtl_vars[dtl][inst_var]["measure_array"] = ama
            self._instruction_dtl_vars[dtl][inst_var]["actual_array"] = aaa
            self._instruction_dtl_vars[dtl][inst_var]["actual_mean"] = meana
        
        #sample_mean = self._instruction_stds_vars[sample][inst_var][VALUE]
        
        # make sure slope is not nan
        if slope != slope:
            fit_value = meana
        else:
            #print mean(aaa), mean(ama), slope, intercept, "%3.5f" %(r_value), p_value
            fit_value = ((meana - intercept)/slope)
            #print "calcs for sample: ", sample, fit_value

        #print
        #print

        
        return fit_value
    
    def _derive_standard_sample_sets(self):
        if not self._sample_set_dict:
            self._standard_set_dict = {}
            curr_samp = None
            curr_std = None
            standard_flag = False
            standard_count = 0
            set_count = 0
            tmp_sample_set = {}
            row_in_sample = 0
            for dtl in self._details_name_dict.keys():
                row = int(dtl) + 1
    
                data = self._source_dict[row]
                smpl = self._sample_serial_id(data[self._sample_col][VALUE].strip(), data[self._job_col][VALUE].strip())
                ident = data[self._identifier_col][VALUE].strip()
                
                #print "smpl: %s ident: %s" %(smpl, ident)
                
                if curr_samp == None:
                    if ident in self._stdsdata.keys(): # current_standard_name:
                        standard_flag = True
                        standard_count += 1
                        tmp_sample_set[standard_count] = []
                        
                        #print "new sample is a standard", ident, smpl, standard_count
                    curr_samp = smpl
                
                #print "sample check: ", curr_samp, smpl
                if curr_samp != smpl:
                    row_in_sample = 0
                    #print "ident: %s  self._stdsdata.keys()" %(ident), self._stdsdata.keys()
                    if ident in self._stdsdata.keys(): # current_standard_name:
                        standard_flag = True
                        standard_count += 1
                        tmp_sample_set[standard_count] = []
                        
                        #print "new sample is a standard", ident, smpl, standard_count
                    else:
                        if standard_count > 1:
                            #print "we have a new set ", set_count, len(tmp_sample_set)
                            self._sample_set_dict[set_count] = tmp_sample_set
                            tmp_sample_set = {}
                            #print
                            set_count += 1
                        standard_flag = False
                        standard_count = 0
            
                    curr_samp = smpl

                row_in_sample += 1
                if row_in_sample > self._ignore_row:
                    if standard_flag:
                        #print "adding standard for ", smpl, standard_count, set_count, row
                        
                        vals = {}
                        exceptions_in_sample_data = None
                        for col_id in self._stdsdata[ident].keys():
                            col_nbr = self._label_column_dict[col_id]
                            
                            try:
                                vals[col_id] = float(data[int(col_nbr)][VALUE].strip())
                            except:
                                vals[col_id] = 0.0
                        #print smpl, vals
                        tmp_sample_set[standard_count].append((ident, smpl, vals))
                    
            # now generate the mean for these standard sets
            for std_group in self._sample_set_dict.keys():
                #print std_group
                tmp_sample_set = self._sample_set_dict[std_group]
                min_smpl = 0
                for k in tmp_sample_set.keys():
                    tmp_array = {}
                    for ident,smpl,vals in tmp_sample_set[k]:
                        # min_smpl contains the lowest sample number for this std_group
                        # this is used to determine the appropriate std_group  when 
                        # looking for a group by sample
                        if min_smpl == 0:
                            min_smpl = smpl
                            
                        if smpl < min_smpl:
                            min_smpl = smpl
                            
                        for std_col_id in vals.keys():
                            if not ident in tmp_array.keys():
                                tmp_array[ident] = {}
                            if not std_col_id in tmp_array[ident].keys():
                                tmp_array[ident][std_col_id] = []
                                
                            tmp_array[ident][std_col_id].append(vals[std_col_id])
                        #print tmp_sample_set[kk][k1]
                        #print ident, smpl, vals
                        #print 

                    #print
                    #print tmp_array
                    
                    for ident in tmp_array.keys():
                        for std_col_id in tmp_array[ident].keys():
                            aa = array(tmp_array[ident][std_col_id])
                            mean_aa = aa.mean()
                            if not std_group in self._standard_set_dict.keys():
                                self._standard_set_dict[std_group] = {}
                                self._standard_set_dict[std_group]["min_smpl"] = min_smpl
                            if not ident in self._standard_set_dict[std_group].keys():
                                self._standard_set_dict[std_group][ident] = {}
                            if not "mean" in self._standard_set_dict[std_group][ident].keys():
                                self._standard_set_dict[std_group][ident]["mean"] = {}
                            
                            self._standard_set_dict[std_group][ident]["mean"][std_col_id] = mean_aa
                    
                    #print
                #print
        #print self._standard_set_dict
            
        return True
        
    def _do_known_standard(self, type, inst_var, proc_variables, smpl, samp_variables, dtl, dtl_variables):
        mean1 = 0.0
        k_name = self._samples_name_dict[smpl][NAME]
        std_col = self._instruction_samp_vars[smpl][inst_var]["source_col"]
        if k_name in self._stdsdata.keys():
            mean1 = self._stdsdata[k_name][std_col]
        
        return float(mean1)


    def _resolve_factor(self, lfactor, proc_variables, samp_variables, dtl_variables=None):
        if lfactor == "True":
            return True
        elif lfactor == "False":
            return False
        
        if lfactor in proc_variables.keys():
            #print "lfactor: ", lfactor
            lval = proc_variables[lfactor][VALUE]
        elif (samp_variables and lfactor in samp_variables.keys()):
            #print "smpl lfactor: ", lfactor
            #print samp_variables[lfactor]
            lval = samp_variables[lfactor][VALUE]
        elif (dtl_variables and lfactor in dtl_variables.keys()):
            #print "dtl lfactor: ", lfactor
            lval = dtl_variables[lfactor][VALUE]
        else:
            try:
                lval = float(lfactor)
            except:
                #print "lfactor: ", lfactor
                #print "dtl_variables: ", dtl_variables
                raise RuntimeError, "Invalid VARIABLES eval lfactor is bad: %s" %(lfactor)

        if lval == "True":
            lval = True
        elif lval == "False":
            lval = False
            
        return lval

    
    def _decode_evalfactors(self, val, bool=None):
        if bool:
            m = self._re_bool_factors.match(val)
        else:
            m = self._re_factors.match(val)
        if m:
            lfactor = m.group('lfactor')
            operand = m.group('operand')
            rfactor = m.group('rfactor')
            return lfactor, operand, rfactor
            
        return None, None, None
      

    def _get_col_from_data(self, source, data):
        val = ""
        inst, sep, pre_value = source.partition("(")
        col_id, sep, right = pre_value.rpartition(")")
        col_nbr = self._label_column_dict[col_id]

        align_frag = ""
        is_a_float = None
        is_a_int = None

        m = self._re_number.match(data[col_nbr][VALUE].strip())
        if m:
            is_a_float = True
        else:
            m = self._re_integer.match(data[col_nbr][VALUE].strip())
            if m:
                is_a_int = True
                
        if is_a_float:
            val = float(data[col_nbr][VALUE].strip())
        elif is_a_int:
            val = int(data[col_nbr][VALUE].strip())
        else:
            val = data[col_nbr][VALUE].strip()
        
        return val
                        

    def _sample_serial_id(self, sample, job = None):
        sample_int = int(sample)
        job_int = int(job)
        
        sj = "%s - %s" %(sample_int, job_int) 

        if not sj in self._sample_sequence_dict.keys():
            self._sample_seq += 1
            self._sample_sequence_dict[sj] = self._sample_seq
            self._sample_sequence_dict_reverse[self._sample_seq] = sj
            #print self._sample_seq, sj
        
        return self._sample_sequence_dict[sj]
    
    def _sample_display_id(self, sample_serial_id):
        rtval = ""
        if sample_serial_id in self._sample_sequence_dict_reverse.keys():
            rtval = self._sample_sequence_dict_reverse[sample_serial_id]
            rtval, sep, right = rtval.rpartition(" -")
        
        return rtval
    
    

                        
    def _preserve_spectra(self, smpl):
        new_chemcorrect_dir = "%s/%s/%s" %(self._picarro_home, 
                                                self._chemcorrect_dir, 
                                                self._outdir
                                                )
        
        #print "new_chemcorrect_dir", new_chemcorrect_dir
        
        if smpl not in self._spectra_smpl:
            self._spectra_smpl.append(smpl)
            
            if not os.path.isdir(new_chemcorrect_dir) == True:
                os.makedirs(new_chemcorrect_dir) 
                
            #print "preserving spectra for sample: ", smpl

        return
    
    def _find_spectra_timecodes(self):
        for dtl in self._details_name_dict.keys():
            row = int(dtl) + 1

            data = self._source_dict[row]
            smpl = self._sample_serial_id(data[self._sample_col][VALUE].strip(),data[self._job_col][VALUE].strip())
            tc = self._label_column_dict[self._timecode_colname]
            time_code = data[tc][VALUE].strip()
            if smpl in self._spectra_smpl:
                tm = time.strptime(time_code, "%Y/%m/%d %H:%M:%S")
                ymd = time.strftime('%Y%m%d', tm)
                if not time_code in self._spectra_location: 
                    self._spectra_location.append(time_code)
                    YYYY = time.strftime('%Y', tm)
                    MM = time.strftime('%m', tm)
                    DD = time.strftime('%d', tm)
                    HH = time.strftime('%H', tm)

                    hms = time.strftime('%H%M%S', tm)

                    spectra_file = "Spectra_%s_%s.zip" %(ymd, hms)
                    spectra10_file = "Spectra10_%s_%s.zip" %(ymd, hms)
            
                    spectra_dir = "%s/%s/%s/%s/%s/%s" %(self._picarro_home, 
                                            self._archive_dir,
                                            YYYY,
                                            MM,
                                            DD,
                                            HH
                                            ) 
                    
                    spectra10_dir = "%s/%s/%s/%s/%s" %(self._picarro_home, 
                                            self._archive2_dir,
                                            YYYY,
                                            MM,
                                            DD
                                            ) 

                    fileFound = None
                    if os.path.isdir(spectra_dir) == True:
                        if not spectra_file in self._spectra_copies:
                            self._spectra_copies.append(spectra_file)
                            sort_helper = {}
                            for x in os.listdir(spectra_dir):
                                left, sep, right = x.partition("_")
                                sort_dt, sep, right = right.partition(".")
                                sort_helper[sort_dt] = x
                                if x == spectra_file:
                                    src = "%s/%s" %(spectra_dir, x)
                                    dst = "%s/%s/%s/%s" %(self._picarro_home, 
                                                    self._chemcorrect_dir, 
                                                    self._outdir,
                                                    x
                                                    )
    
                                    
                                    shutil.copy2(src, dst)
                                    fileFound = True
                                    
                            # if we don't have an exact match from Spectra, find closest match
                            # where closes is the first file greater than the one we are looking for
                            if not fileFound:
                                for x in sort(sort_helper.keys()):
                                    if not fileFound:
                                        if sort_helper[x] >= spectra10_file:
                                            src = "%s/%s" %(spectra_dir, sort_helper[x])
                                            dst = "%s/%s/%s/%s" %(self._picarro_home, 
                                                            self._chemcorrect_dir, 
                                                            self._outdir,
                                                            sort_helper[x]
                                                            )
                                            
                                            shutil.copy2(src, dst)
                                            fileFound = True
                                    
                    # If we don't have a match in the current spectra, look through the Spectra10 dir
                    if not fileFound:
                        if os.path.isdir(spectra10_dir) == True:
                            sort_helper = {}
                            for x in os.listdir(spectra10_dir):
                                #left, sep, right = x.r 
                                left, sep, right = x.partition("_")
                                sort_dt, sep, right = right.partition(".")
                                sort_helper[sort_dt] = x
                                
                                if x == spectra10_file:
                                    src = "%s/%s" %(spectra10_dir, x)
                                    dst = "%s/%s/%s/%s" %(self._picarro_home, 
                                                    self._chemcorrect_dir, 
                                                    self._outdir,
                                                    x
                                                    )
    
                                    
                                    shutil.copy2(src, dst)
                                    fileFound = True
    
                                # if we don't have an exact match from Spectra10, find closest match
                                # where closes is the first file greater than the one we are looking for
                                if not fileFound:
                                    for x in sort(sort_helper.keys()):
                                        if not fileFound:
                                            if sort_helper[x] >= spectra10_file:
                                                src = "%s/%s" %(spectra10_dir, sort_helper[x])
                                                dst = "%s/%s/%s/%s" %(self._picarro_home, 
                                                                self._chemcorrect_dir, 
                                                                self._outdir,
                                                                sort_helper[x]
                                                                )
                                                
                                                shutil.copy2(src, dst)
                                                fileFound = True
                                                
                                    
                            print "file in spectra dir: ", x
            
        return


if __name__ == '__main__':
    raise RuntimeError, "%s %s" % ("instproc.py", STANDALONE_ERROR)

#c = InstructionProcess(ctl_file="chemcorrect.ctl")
#instruction_parms = c.get_instruction_from_ctl()
#c._load_definition_instructions(instruction_parms)
#c._load_standards()
#c._load_source(instruction_parms)
#c._load_instructions(instruction_parms)
#c._evaluate_instruction_variables(instruction_parms)
#c._find_spectra_timecodes()
#c._preserve_spectra(1)

