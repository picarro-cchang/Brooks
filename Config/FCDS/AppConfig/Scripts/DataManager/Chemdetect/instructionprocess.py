'''
instructionprocess.py -- the instructionprocess module contains the
InstructionProcess class
This class will process source data using a defined procedural instruction set.
'''
from scipy import *
from numpy import *
import time
import csv

class InstructionProcess(object):
    '''
    Evaluate and process instructions from a procedural instruction set
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        # error log
        self._error_log = {}

        # container of current values for all computed instruction variables
        self.current_var_values = {}

        # instruction set. Each row is a tuple of fn_id, result_var_name, function_string
        # where the instruction_string is in form of:  func(parm)
        # func must be a member of the instruction_dict.
        # If parm contains additional func, then they must also be
        # members of the instruction_dict

        self.instruction_set_list = []

        # control variables (set from instruction load process)
        self.cntl_vars = {}
        self.cntl_vars['debug_mode'] = None # True to display debug statements
        self.cntl_vars['max_run'] = 0 # max elements in a running array (for std_running, mean_running...)

        self._named_py_vars = [
                               'True',
                               'False',
                               'None',
                               ]
        # some defaults
        self.current_var_values['true'] = True
        self.current_var_values['True'] = True
        self.current_var_values['TRUE'] = True
        self.current_var_values['false'] = False
        self.current_var_values['False'] = False
        self.current_var_values['FALSE'] = False

        # current_running container
        # This container holds the list of values (up to max-points)
        # This allows mean/std and other array calculations
        # value is a tuple (max_points, []) where list is mas size of len(max_points)
        self._current_running_values = {}

        # container of all instructions
        self.instruction_dict = {}
        self.instruction_dict['truth_evaluation'] = ('_do_truth_evaluation','simple')
        self.instruction_dict['evaluation'] = ('_do_evaluation','simple')
        self.instruction_dict['abs'] = ('_do_abs','simple')
        self.instruction_dict['bool_and'] = ('_do_bool_and','simple')
        self.instruction_dict['bool_or'] = ('_do_bool_or','simple')
        self.instruction_dict['bool_xor'] = ('_do_bool_xor','simple')

        self.instruction_dict['sum'] = ('_do_sum','array')
        self.instruction_dict['mean'] = ('_do_mean','array')
        self.instruction_dict['std'] = ('_do_std','array')
        self.instruction_dict['slope'] = ('_do_slope','array')

        self.instruction_dict['mean_running'] = ('_do_mean_running','simple')
        self.instruction_dict['std_running'] = ('_do_std_running','simple')

        self.instruction_dict['cond'] = ('_do_cond','simple')



        self._sorted_instruction_names = []
        self._sorted_var_names = []
        self._array_instruction_list = []


    def _process_initialization(self):
        '''
        sort instructions by length of instruction name.
        This will help to prevent false matches when parsing instructions that
        that have names partially matching other instructions....
        such as.... bool vs bool_xor.
        '''
        self._sorted_instruction_names = sorted(self.instruction_dict.keys(), key=len, reverse=True)
        self._sorted_var_names = sorted(self.current_var_values.keys(), key=len, reverse=True)
        self._resolved_fn_dict = {}
        self._varint = 0

        if self.cntl_vars['debug_mode']: print 'self._sorted_instruction_names: ', self._sorted_instruction_names
        if self.cntl_vars['debug_mode']: print
        if self.cntl_vars['debug_mode']: print 'self._sorted_var_names: ', self._sorted_var_names
        if self.cntl_vars['debug_mode']: print

    def _build_array_instruction_list(self):
        for inst in self.instruction_dict.keys():
            if self.cntl_vars['debug_mode']: print inst, self.instruction_dict[inst][0], self.instruction_dict[inst][1]
            if self.instruction_dict[inst][1] == 'array':
                self._array_instruction_list.append(inst)

    def _do_truth_evaluation(self, factor_str):
        try:
            rtn_val = eval('%s' % factor_str)
        except:
            return (16, "ERROR: truth_evaluation error. %s" % factor_str)

        return (0, rtn_val)

    def _do_evaluation(self, factor_str):
        try:
            factor_str = factor_str.replace('None', '0.0')
            factor_str = factor_str.replace('NONE', '0.0')
            factor_str = factor_str.replace('none', '0.0')
            rtn_val = eval('%s' % factor_str)
        except:
            return (16, "ERROR: evaluation error. %s" % factor_str)

        return (0, rtn_val)

    def _bool_eval(self, lval, oper, rval):
        try:
            if lval in ('True', 'TRUE', 'true'):
                lval = True
            if rval in ('True', 'TRUE', 'true'):
                rval = True
            if lval in ('False', 'FALSE', 'false'):
                lval = False
            if rval in ('False', 'FALSE', 'false'):
                rval = False

            if oper == "and":
                return (0, (lval and rval))
            elif oper == "or":
                return (0, (lval or rval))
            elif oper == "xor":
                return (0, (bool(lval) ^ bool(rval)))
        except:
            return (16, "ERROR: bool error.")

    def _do_bool_and(self, factor_str):
        lval, cma, rval = factor_str.partition(',')
        return self._bool_eval(lval, 'and', rval)

    def _do_bool_or(self, factor_str):
        lval, cma, rval = factor_str.partition(',')
        return self._bool_eval(lval, 'or', rval)

    def _do_bool_xor(self, factor_str):
        lval, cma, rval = factor_str.partition(',')
        return self._bool_eval(lval, 'xor', rval)

    def _do_abs(self, factor_str):
        factor = eval(factor_str)

        rtn_val = 0.0

        try:
            n_factor = float(factor)
        except:
            try:
                n_factor = int(factor)
            except:
                return (16, "ERROR: abs error. Numeric factor required.")

        try:
            rtn_val = abs(n_factor)
            return (0, rtn_val)
        except:
            return (16, "ERROR: abs error.")


    def _do_sum(self, factor_str):
        factor_ary = eval(factor_str)
        try:
            a = array(factor_ary)
            return (0, a.sum())
        except:
            return (16, "ERROR: sum error. is the factor an array?. %s" %(factor_ary))

    def _do_mean(self, factor_str):
        factor_ary = eval(factor_str)
        try:
            a = array(factor_ary)
            return (0, a.mean())
        except:
            return (16, "ERROR: sum error. is the factor an array?. %s" %(factor_ary))


    def _do_std(self, factor_str):
        factor_ary = eval(factor_str)
        try:
            a = array(factor_ary)
            return (0, a.std())
        except:
            return (16, "ERROR: sum error. is the factor an array?. %s" %(factor_ary))


    def _do_slope(self, factor_str):
        factor_aryx, factor_aryy = eval(factor_str)
        try:
            ax = array(factor_aryx)
            ay = array(factor_aryy)

            slope, intercept, r_value, p_value, std_err = stats.linregress(ax,ay)

            return (0, slope)
        except:
            return (16, "ERROR: sum error. is the factor an array?. %s" %(factor_ary))


    def _append_running_array(self, factor_str):
        if not 'self.current_var_values[' in factor_str:
            return (16, "ERROR: running array append error. Invalid factor_str: %s" % factor_str)

        try:
            lv, sep, temp = factor_str.partition('[')
            vname_str, sep, rv = temp.partition(']')

            vname = eval('%s' % vname_str)
            value = eval('%s' % factor_str)

            if not vname in self._current_running_values:
                self._current_running_values[vname] = (int(self.cntl_vars['max_run']), [])

            tsize = len(self._current_running_values[vname][1])
            if tsize >= self._current_running_values[vname][0]:
                ovsize = 1 + tsize - self._current_running_values[vname][0]
                for i in range(ovsize):
                    del self._current_running_values[vname][1][0]

            self._current_running_values[vname][1].append(value)

            return (0, vname)

        except:
            return (16, "ERROR: running array append error. Append error. factor_str: %s" % factor_str)


    def _do_mean_running(self, factor_str):
        rtn, vname = self._append_running_array(factor_str)

        if not rtn == 0:
            return (rtn, vname)

        try:
            a = array(self._current_running_values[vname][1])
            return (0, a.mean())
        except:
            return (16, "ERROR: mean_running error. array error. factor_str: %s" % factor_str)


    def _do_std_running(self, factor_str):
        rtn, vname = self._append_running_array(factor_str)

        if not rtn == 0:
            return (rtn, vname)

        try:
            a = array(self._current_running_values[vname][1])
            return (0, a.std())
        except:
            return (16, "ERROR: mean_running error. array error. factor_str: %s" % factor_str)


    def _do_cond(self, factor_str):
        cond_str, cma, rtnvals_str = factor_str.partition(',')
        tval_str, cma, fval_str = rtnvals_str.partition(',')

        try:
            cond = eval('%s' % cond_str)
        except:
            return (16, "ERROR: cond error. condition error. factor_str: %s" % factor_str)

        if cond:
            try:
                rtnval = eval('%s' % tval_str)
            except:
                return (16, "ERROR: cond error. true return error. factor_str: %s" % factor_str)
        else:
            try:
                rtnval = eval('%s' % fval_str)
            except:
                return (16, "ERROR: cond error. false return error. factor_str: %s" % factor_str)

        return (0, rtnval)


    def resolve_function(self, fn_id, fn_string):
        '''
        How to resolve function
        1) search for named variables (these are variables from the list of
                replace named variable with simple value that exists for that variable
                Note: simple value is a dictionary containing the current value of the variable

            Example:
                start: "evaluation(evaluation(ABCD+EFGH+evaluation(HHH/YYY))>3)"
                var000 = 'ABCD'
                after 1.1: "evaluation(evaluation(val[var000]+EFGH+evaluation(HHH/YYY))>3)"

                var001 = 'EFGH'
                after 1.2: "evaluation(evaluation(val[var000]+val[var001]+evaluation(HHH/YYY))>3)"

                var002 = 'HHH'
                after 1.3: "evaluation(evaluation(val[var000]+val[var001]+evaluation(val[var002]/YYY))>3)"

                var003 = 'YYY'
                after 1.4: "evaluation(evaluation(val[var000]+val[var001]+evaluation(val[var002]/val[var003]))>3)"



        2) search for named functions
            replace with function evaluation

            Example:
                where val dictionary contains:
                val[var000] = 19.0
                val[var001] = 23.0
                val[var002] = 45.0
                val[var003] = 9.0

                start: "evaluation(evaluation(val[var000]+val[var001]+evaluation(val[var002]/val[var003]))>3)"
                evaluation(val[var002]/val[var003]) = 9

                after 2.1: "evaluation(evaluation(val[var000]+val[var001]+9)>3)"
                evaluation(val[var000]+val[var001]+9) = 51

                after 2.2: "evaluation(51>3)"
                evaluation(51>3) = True

                after 2.3: "True"

        '''
        def myval(iparm):
            return iparm[5]

        def myval2(iparm):
            return resolution_dict[iparm][0]

        if not self._sorted_instruction_names:
            self._process_initialization()

        if not self._array_instruction_list:
            self._build_array_instruction_list()

        # 1) resolve variable names into values
        # preserve the resolved values and instruction order for the specified
        # function ID so it does not need to be recalculated.
        if fn_id in self._resolved_fn_dict:
            resolved_fn_string, instruction_order = self._resolved_fn_dict[fn_id]
            if self.cntl_vars['debug_mode']: print 'resolving variable names - resolved_fn_string: %s' % resolved_fn_string
        else:
            resolved_fn_string = fn_string
            if self.cntl_vars['debug_mode']: print 'resolving variable names - resolved_fn_string: %s' % resolved_fn_string

            # replace the string variable name key with an internal self variable
            # This helps with the resolution of the current_var_values as it is
            # possible for the string variable name to itself be something that
            # might get replaced inappropriately.
            # Example: self.current_var_values['SOME_NAME'] will become
            #          self._var1 = 'SOME_NAME'
            #          self.current_var_values[self._var1]
            for named_var in self._sorted_var_names:
                if named_var in resolved_fn_string:
                    if not named_var in self._named_py_vars:
                        named_found = True
                        vname = '_var%s' % self._varint
                        self._varint += 1
                        setattr(self, '%s' % vname, named_var)
                        resolved_fn_string = resolved_fn_string.replace(named_var, 'self.current_var_values[self.%s]' % vname)
                        if self.cntl_vars['debug_mode']: print named_var, 'self.current_var_values[self.%s]' % vname
                        if self.cntl_vars['debug_mode']: print resolved_fn_string
                        if self.cntl_vars['debug_mode']: print
                        #time.sleep(2)


            if not resolved_fn_string.count('(') == resolved_fn_string.count(')'):
                raise RuntimeError, 'Error Parsing function: %s  paren count miss-match' % (fn_string)

            if self.cntl_vars['debug_mode']: print

            # Locate all instructions
            if self.cntl_vars['debug_mode']: print 'locating instruction positions'
            instr_loc = []
            iloc_idx = 0
            insttemp_fn_string = resolved_fn_string
            for named_inst in self._sorted_instruction_names:
                stri = 0
                search_again = True
                while search_again:
                    search_again = False
                    if named_inst in insttemp_fn_string[stri:]:
                        iloc = insttemp_fn_string[stri:].find(named_inst)
                        iloc += stri
                        open_paren_idx = iloc+len(named_inst)
                        close_paren_idx = 0

                        search_str = insttemp_fn_string[open_paren_idx + 1:]

                        opncnt = 1
                        maxcnt = 1
                        for idx in range(len(search_str)):
                            if ')' == '%s' %(search_str[idx:idx+1]):
                                opncnt -= 1
                            elif '(' == '%s' %(search_str[idx:idx+1]):
                                opncnt += 1
                                maxcnt += 1

                            if opncnt == 0:
                                close_paren_idx = open_paren_idx + idx
                                break

                        #(instruction, instr_location, start_parm_idx, end_parm_idx)
                        instr_loc.append((iloc_idx,
                                          named_inst,
                                          iloc,
                                          open_paren_idx+1,
                                          close_paren_idx+1,
                                          maxcnt,
                                          resolved_fn_string[open_paren_idx+1:close_paren_idx+1],
                                          resolved_fn_string[iloc:close_paren_idx+2],
                                          ))
                        iloc_idx += 1

                        stri = iloc+1
                        search_again = True
                        rplval = '_' * len(named_inst)
                        insttemp_fn_string = insttemp_fn_string.replace(named_inst, rplval, 1)

            if self.cntl_vars['debug_mode']:
                for i in instr_loc:
                    print 'instr_loc: ', i
            if self.cntl_vars['debug_mode']: print

            # set order of instruction resolution
            if self.cntl_vars['debug_mode']: print 'setting resolution order'
            instruction_order = []
            instruction_order = sorted(instr_loc, key=myval)

            if self.cntl_vars['debug_mode']:
                print
                print
                for i in instruction_order:
                    print i
                    print
                print
                print

            # Store the resolved function and instruction order so that we do not
            # need to re-process for this instruction again.
            self._resolved_fn_dict[fn_id] = (resolved_fn_string, instruction_order)


        # 2) resolving instructions
        resolution_dict = {}
        rorder = 0

        if self.cntl_vars['debug_mode']: print 'resolving instructions'
        idx = 0
        for instr_tuple in instruction_order:
            ilocidx, inst, iloc, startp, endp, maxcnt, parm, fparm = instr_tuple

            # resolve previously resolved values in the parm
            if self.cntl_vars['debug_mode']: print idx, inst, fparm
            for rsl_parm in sorted(resolution_dict.keys(), key=myval2):
                if rsl_parm in parm:
                    parm = parm.replace(rsl_parm, '%s' % resolution_dict[rsl_parm][1])
                    if self.cntl_vars['debug_mode']: print 'parm: ', idx, parm
                    fparm = fparm.replace(rsl_parm, '%s' % resolution_dict[rsl_parm][1])
                    if self.cntl_vars['debug_mode']: print 'fparm: ', idx, fparm


            # This is the method and parameters for the instruction
            mthd = 'self.%s("%s")' % (self.instruction_dict[inst][0], parm)
            if self.cntl_vars['debug_mode']: print mthd

            rtn, resolution = eval(mthd)
            if rtn == 0:
                if self.cntl_vars['debug_mode']: print 'result: ', resolution
                resolution_dict[fparm] = (rorder, resolution)
                rorder += 1
            else:
                raise RuntimeError, 'Error Parsing function: %s  error in: %s' % (fn_string, fparm)

            if self.cntl_vars['debug_mode']: print

            idx += 1

        return resolution

    def load_set_from_csv(self, instruction_path):
        '''
        load instruction set from CSV file
        '''
        if not instruction_path:
            raise RuntimeError, 'No valid instruction set path to process'


        #self.ip = InstructionProcess()
        #self.cntl_vars['debug_mode'] = True
        self.cntl_vars['max_run'] = 500

        try:
            csv_data_file = open(instruction_path,'rb')
            data_reader = csv.reader(csv_data_file, dialect='excel',)
        except:
            raise RuntimeError, 'error with path to instruction set'


        initialize_section = None
        process_section = None

        fn_id = 0
        for r in data_reader:
            if len(r) >= 1:
                if r[0][0:1] == '#':
                    if self.cntl_vars['debug_mode']: print r[0]
                    continue

            if len(r) > 1:
                try:
                    p0 = eval(r[0].strip())
                except:
                    p0 = r[0].strip()

                try:
                    p1 = eval(r[1].strip())
                except:
                    p1 = r[1].strip()

                if p0 == 'INITIALIZE':
                    initialize_section = True
                    process_section = None
                    if self.cntl_vars['debug_mode']: print 'loading INITIALIZE values'
                elif p0 == 'PROCESS':
                    initialize_section = None
                    process_section = True
                    if self.cntl_vars['debug_mode']: print 'loading PROCESS statements'
                else:
                    if p0:
                        if initialize_section:
                            if len(r) >= 2:
                                try:
                                    val = float(p1)
                                except:
                                    val = p1

                                if p0 in self.cntl_vars:     #currently 'debug_mode' and 'max_run' are cntl_vars
                                    self.cntl_vars[p0] = val
                                else:                        #the rest of the vars in the INITIALIZE section
                                    self.current_var_values[p0] = val

                                if self.cntl_vars['debug_mode']: print p0, val

                        elif process_section:
                            if len(r) >= 2:
                                if self.cntl_vars['debug_mode']: print '%4d' %fn_id, p0, p1
                                self.instruction_set_list.append(('%s' %fn_id, p0, p1))
                                fn_id += 1


        for instruction in self.instruction_set_list:
            fn_id, result_var, function_str = instruction
            if self.cntl_vars['debug_mode']: print fn_id, result_var, function_str
            if not result_var in self.current_var_values:
                self.current_var_values[result_var] = None


    def process_set(self):
        '''
        process instruction set
        '''
        for instruction in self.instruction_set_list:
            fid, result_var, function_str = instruction
            if not result_var in self.current_var_values:
                self.current_var_values[result_var] = None
            self.current_var_values[result_var] = self.resolve_function(fid, function_str)


if __name__ == '__main__':
    raise RuntimeError, "%s %s" % ("instructionprocess.py", "This closs cannot run as a stand-alone process")
