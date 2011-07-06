'''
TravellerDataPush.py
Push data from formatted input file(s) into selected Cavity Traveller Document
If no traveller document is given, show a selection screen to allow entry 
(selection) of the traveller document. 

This generates a log file showing the result of the operation.

USAGE:
    TravellerDataPush.py [-h] [--help ] 
                         [-l <log-file> ] [--log-file=<log-file> ] 
                         [-c <ctl-file> ] [--ctl-file=<ctl-file> ] 
                         [-d <data-file> ] [--data-file=<data-file> ] 
                         [-i <image-file> ] [--image-file=<image-file> ] 
                         [-p <plot-file> ] [--plot-file=<plot-file> ] 
                         [-t <travelle-identifierr> ] 
                         [--traveller-identifier=<traveller-identifier> ]
                         [-n <travelle-name> ] 
                         [--mfg-url=<mfg-url> ]
                         [--traveller-name=<traveller-name> ]
                         ctl-file

OPTIONS
    -h,              --help                     Display Help/Usage.
    
    -l <log-file>,   --log-file=<log-file>      The path for the log file. The 
                                                user must have write access to 
                                                the path.
                                                
                                                The log is opened "w" so any 
                                                prior data in the file will be
                                                overwritten.
                                                
     NOTE: If the log-file is not specified the log file will named:
           TravellerDataPush_YYYYMMDDHHMMSS.log in the execution path.
                                                
    -c <ctl-file>,   --ctl-file=<ctl-file>      The optional Control File. If 
                                                the control file is given, it 
                                                will override all other entries.
                                                
    -d <data-file>,  --data-file=<data-file>    Data File. This file contains
                                                the data to be pushed into the
                                                traveller document.
                                                
    -i <image-file>, --image-file=<image-file>  Image File. This file contains
                                                the image to be pushed into the
                                                traveller document as a note
                                                attachment.
                                                
    -p <plot-file>,  --plot-file=<plot-file>    Plot File. This file is an H5 or
                                                CSV file containing the XY plot
                                                data. This will be pushed into
                                                the traveller document as a note
                                                attachment.
                                                
    -t <traveller-identifier>,  --traveller-identifier=<traveller-identifier>    
                                                The document identifier for the
                                                traveller to receive the data.
                                                
                                                Note: Either traveller-name OR
                                                traveller-identifier, but not
                                                both.
                                                
    -n <traveller-name>,  --traveller-name=<traveller-name>    
                                                The document name for the
                                                traveller to receive the data.
                                                
                                                Note: Either traveller-name OR
                                                traveller-identifier, but not
                                                both.
                                                
    -u <mfg-url>,  --mfg-url=<mfg-url>          The url for the xmlrpc call to
                                                the manufacturing database.
                                                
            defaults to http://user:password@mfg.picarro.com/xmlrpc/
            where user:password is default user/password for xmlrpc calls

ARGUMENTS
    ctl-file    The only optional argument is the optional control file. If the
                control file is give, it will override any other entry.
                
FILES
    ctl-file    The control file is a formatted text file containing the paths
                to the various data files and optionally the traveller document
                identifier.
                
                format (one file path per line):
                    data-file: <path-to-file>
                    image-file: <path-to-file>
                    plot-file: <path-to-file>
                    traveller-identifier: <document-identifier>
                    traveller-name: <document-name>
                    
                    Note: Either traveller-identifier or traveller-name, but not
                    both.
                        
                    Note: the control file can optionally contain the data to be
                    pushed into the traveller document instead of the data-file
                    argument. If there is a data-file argument, it will override
                    all of the attribute-name arguments

                    format (one data value per line):
                        attribute-name: <data-value>
                        
                        Note: one colon, and one space, then data value
                            EXAMPLE:
                                stepid: step_7
                                user: bsimpson
                                rdmdoc_wavelength: 1375
                                rdmdoc_rd_time: 44.81886
                                rdmdoc_s2s_pct: 3.66209

                        Note: stepid is always required. user is always required
                            and must be a valid and active userid in the 
                            manufacturing database.
                            
                        Note: all data-value's should be string representation.
                            Datetime in format: YYYY-MM-DD HH:MM:SS
                            Numbers with optional signs, and NO comma's: 
                            -99999.999
                    
    data-file   The data file is a formatted text file containing the data to
                be pushed into the traveller document.
                
                format (one data value per line):
                    attribute-name: <data-value>
                    
                    Note: one colon, and one space, then data value
                        EXAMPLE:
                            stepid: step_7
                            user: bsimpson
                            rdmdoc_wavelength: 1375
                            rdmdoc_rd_time: 44.81886
                            rdmdoc_s2s_pct: 3.66209
                    
                    Note: stepid is always required. user is always required and
                        must be a valid and active userid in the manufacturing 
                        database.
                        
                    Note: all data-value's should be string representation.
                        Datetime in format: YYYY-MM-DD HH:MM:SS
                        Numbers with optional signs, and NO comma's: -99999.999
                    
    image-file  The image file is a png or jpeg image file. This file will be
                pushed into the traveller document as a note attachment.
                
    plot-file   The plot-file is an H5 or CSV format data file of XY plot data. 
                This file will be pushed into the traveller document as a note
                attachment.

EXAMPLES
    TravellerDataPush.py --ctl-file=/path/to/some/control.file
        This would push any data and/or datafiles identified in control.file 
        into the traveller identified within the control.file.

    TravellerDataPush.py --data-file /path/to/some/data.file 
      --image-file=/path/to/some/image.file 
      --plot-file=/path/to/some/plot.file
      --traveller-identifier=CADOC_20110524120121
          This would push data from data.file, the image from image.file, and
          the plot from plot.file into the traveller with identifier value
          CADOC_20110524120121.
    
    TravellerDataPush.py --data-file /path/to/some/data.file 
      --image-file=/path/to/some/image.file 
      --plot-file=/path/to/some/plot.file
          This would show a selection screen allowing the user to select a
          traveller document. Once selected, This would push data from 
          data.file, the image from image.file, and the plot from plot.file into
          the selected traveller document.

Note:
    Data (from either data-file or ctl-file) has specific requirements that
    must be met based on the specific step of the travaller document. 
        
'''
import os
import sys
import getopt
import shutil
import datetime
import xmlrpclib
import cStringIO

from Tkinter import *

CWD = os.getcwd()

ipvusr="ipvadmin"
ipvpass="p3c1rr4p3c1rr4"
ipvup = "%s:%s@" % (ipvusr, ipvpass)
#RPCURI_DFT = "http://%slocalhost/xmlrpc/" % (ipvup)
RPCURI_DFT = "http://plucky/xmlrpc/"
#RPCURI_DFT = "http://ubuntuhost64:8000/xmlrpc/"

XMLRPC_USER = 'xml_user'
XMLRPC_PW = 'skCyrcFHVZecfD'

PNL_TITLE = 'Push To Traveller'
BTN_WIDTH = 35
MSG_WIDTH = 300

PNL_LBLS = {
            'doc_choice': 'Document',
            'rdmdoc_wavelength': 'Wavelength',
            'rdmdoc_rd_time': 'RDT',
            'rdmdoc_s2s_pct': 'S-S Noise',
            'rdmdoc_vert': 'Vertical',
            'rdmdoc_horiz': 'Horizontal',
            'rdmdoc_vpzt': 'Vpzt',
            'new_set': 'Continue step?',
            'userid': 'User',
            }

MEASURE_STEP = {
             'step_3': 'cadoc_front_rd_measure',
             'step_6': 'cadoc_pzt_rd_measure',
             'step_9': 'cadoc_post_glue_rd_measure',
             'step_12': 'cadoc_post_heat_rd_measure',
             'step_17': 'cadoc_initial_rd_measure',
             'step_20': 'cadoc_final_rd_measure',
                }

#import wx


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class _Logger(object):
    def __init__(self, **kwargs):
        run_ts = datetime.datetime.now()
        log_file_name = 'TravellerDataPush_%s.log' % (run_ts.strftime("%Y%m%d%H%M%S"))
        self.path = os.path.join(CWD, log_file_name)

        if kwargs:
            if 'path' in kwargs:
                self.path = kwargs['path']
                del kwargs['path']
        
        self.logf = open(self.path, 'w')

    def write(self, msg="", ts=None):
        if not ts:
            ts = datetime.datetime.now()
        
        try:    
            self.logf.write('%s.%s: %s\n' % (
                                             ts.strftime("%Y%m%d%H%M%S"), 
                                             ts.microsecond,
                                             msg)
                            )
        except:
            return False
        
        return True
        
    def close(self):
        try:
            self.logf.close()
        except:
            return False
        
        return True

class TravellerDataPushPnl(Frame):
    def _step(self, stat):
        if stat in ('step_2', 'step_3'):
            return 'step_3'
        if stat in ('step_5', 'step_6'):
            return 'step_6'
        if stat in ('step_8', 'step_9'):
            return 'step_9'
        if stat in ('step_11', 'step_12'):
            return 'step_12'
        if stat in ('step_16', 'step_17'):
            return 'step_17'
        if stat in ('step_19', 'step_20'):
            return 'step_20'
        return None
    
    def send_new_btn_press(self):
        self.send_button_press(True)
        
    def send_cnt_btn_press(self): 
        self.send_button_press("Continue")
           
    def send_button_press(self, new_set=True):
        def _send_doc_to_mfg(data_dict):
            XMLProxy = xmlrpclib.ServerProxy(self.mfg_uri)
            rtn = XMLProxy.travx_doc_save(data_dict)
            return rtn                   

        def _send_note_to_mfg(data_dict, bin_data_string):
            XMLProxy = xmlrpclib.ServerProxy(self.mfg_uri)
            rtn = XMLProxy.travx_note_save(data_dict, bin_data_string)
            return rtn                   

        def _send_attachment(attachment, ddict, note=None):
            note_dict = {}
            try:
                plt_f = xmlrpclib.Binary(open(attachment, 'rb').read())                
                
                note_dict['userid'] = ddict['userid']        
                note_dict['trav_type'] = 'cavity'        
                note_dict['user'] = XMLRPC_USER        
                note_dict['passwd'] = XMLRPC_PW
                
                note_dict['bin_data_name'] = attachment 
                note_dict['notedocid'] = ddict['docid']
                note_dict['canote_step'] = ddict['stepid']

                if note:
                    note_dict['canote_note'] = note
                
                rslt = _send_note_to_mfg(note_dict, plt_f)
                self.my_log.write()
                self.my_log.write('NOTE ATTACHMENT DICTIONARY --')
                for ky, val in note_dict.iteritems():
                    _logme(ky, val)
                    
            except:
                self.my_log.write('file specified was not found: %s' % (attachment))

        def _dict_filter(ky, val):
            if ky in ('passwd', 'password'):
                val = '*****' 
            return '%s: %s' % (ky, val)       
        
        def _logme(nky, nval, depth=''):
            try:
                for sky, sval in nval.iteritems():
                    _logme(sky, sval, '%s: ' %(nky))
            except:
                self.my_log.write('%s%s' %(depth, _dict_filter(nky, nval)))
                
                    
        data_dict = {}
        for ky in (
                  'doc_choice',
                  ):
            if ky in self.cntls:
                data_dict[ky] = self.cntls[ky]['entry'].get()

        ky = 'userid'
        if ky in self.cntls:
            data_dict[ky] = self.cntls[ky]['variable'].get()
            self.last_userid = data_dict[ky]
        
        if new_set:
            data_dict['new_set'] = new_set
            
        for ky in self.data_items:
            data_dict[ky] = self.cntls[ky]['entry'].get()

        if self.doc_tuple:
            data_dict['docid'] = self.doc_tuple[1]
            step_id = self._step(self.doc_tuple[2])
            ms = MEASURE_STEP[step_id]
            data_dict['stepid'] = step_id
            data_dict[ms] = 'True'
        
        data_dict['trav_type'] = 'cavity'        
        data_dict['user'] = XMLRPC_USER        
        data_dict['passwd'] = XMLRPC_PW  
              
        self.my_log.write()
        self.my_log.write('DOCUMENT REQUEST DICTIONARY --')
        for ky, val in data_dict.iteritems():
            if ky == 'new_set':
                if val == 'Continue':
                    data_dict[ky] = ''
                    val = ''
                else:
                    data_dict[ky] = 'True'
                    val = 'True'
            _logme(ky, val)
            
        rslt = _send_doc_to_mfg(data_dict)
        self.my_log.write()
        self.my_log.write('DOCUMENT REQUEST RESULT --')
        try:
            for ky, val in rslt.iteritems():
                _logme(ky, val)
        except:
            self.my_log.write(rslt)

        if 'image_file' in self.parm_dict:
            _send_attachment(self.parm_dict['image_file'], data_dict, 'Screen Capture')
        if 'plot_file' in self.parm_dict:
            _send_attachment(self.parm_dict['plot_file'], data_dict, 'Plot XY Data')
            
        self.quit()

    
    def createWidgets(self):
        def _new_entry_widget_dict(label, value):
            lbl = Label(self)
            lbl['text'] = label
            vlu = Entry(self)
            vlu.insert(END, '%s' % (value))
            return {'label': lbl, 'entry': vlu}
        
        def _new_optionmenu_widget_dict(label, value, dflt=0):
            lbl = Label(self)
            lbl['text'] = label
            variable = StringVar(self)
            variable.set(value[dflt])
            vlu = OptionMenu(self, variable, *value)
            return {'label': lbl, 'entry': vlu, 'variable': variable}
        
        def _lbl(ky): 
            if ky in PNL_LBLS:
                pnllbl = PNL_LBLS[ky]
            else:
                pnllbl = ky
            return pnllbl
        
        row=0
        self.cntls = {}
        
        ky = 'userid'

        optlist = []
        for tv in self.user_list:
            optlist.append(tv[0])
        
        if self.last_userid:   
            dft = optlist.index(self.last_userid)
        else:
            dft = 0

        if optlist:
            self.cntls[ky] = _new_optionmenu_widget_dict(_lbl(ky), optlist, dft)
            self.cntls[ky]['label'].grid(row=row, column=1)
            self.cntls[ky]['entry'].grid(row=row, column=2)
            row += 1

        row += 2
        
        ky = 'doc_choice'
        val = self.doc_tuple[0]
        self.cntls[ky] = _new_entry_widget_dict(_lbl(ky), val)
        self.cntls[ky]['label'].grid(row=row, column=1)
        self.cntls[ky]['entry'].grid(row=row, column=2)
        self.cntls[ky]['entry'].config(state=DISABLED)

        row += 2
        
        for ky in (
                'rdmdoc_wavelength',
                'rdmdoc_rd_time',
                'rdmdoc_s2s_pct',
                   ):
            val = self.data_dict[ky]
            self.cntls[ky] = _new_entry_widget_dict(_lbl(ky), val)
            self.cntls[ky]['label'].grid(row=row, column=1)
            self.cntls[ky]['entry'].grid(row=row, column=2)
            self.data_items.append(ky)
            row += 1

        for ky in (
                'rdmdoc_vert',
                'rdmdoc_horiz',
                'rdmdoc_vpzt',
                   ):
            self.cntls[ky] = _new_entry_widget_dict(_lbl(ky), '')
            self.cntls[ky]['label'].grid(row=row, column=1)
            self.cntls[ky]['entry'].grid(row=row, column=2)
            self.data_items.append(ky)
            row += 1
            
        row += 2
        self.QUIT = Button(self, width=BTN_WIDTH)
        self.QUIT["text"] = "Cancel"
        self.QUIT["command"] =  self.quit
        self.QUIT.grid(row=row, column=1, columnspan=2)

        row +=3
        self.send_button = Button(self, width=BTN_WIDTH)
        self.send_button["text"] = "Send as new %s" % (self._step(self.doc_tuple[2]))
        self.send_button["command"] = self.send_new_btn_press
        self.send_button.grid(row=row, column=1, columnspan=2)
        
        row +=3
        self.send_button = Button(self, width=BTN_WIDTH)
        self.send_button["text"] = "Send as continuation of %s" % (self._step(self.doc_tuple[2]))
        self.send_button["command"] = self.send_cnt_btn_press
        self.send_button.grid(row=row, column=1, columnspan=2)

    def __init__(self, *args, **kwargs):
        self.parm_dict=kwargs['parm_dict']
        self.data_dict=kwargs['data_dict']
        self.my_log=kwargs['my_log']
        self.doc_tuple=kwargs['doc_tuple']
        self.mfg_uri=kwargs['mfg_uri']
        self.data_items = []
        master=kwargs['master']
        
        if 'userid' in self.data_dict:
            self.last_userid = self.data_dict['userid']
        else:
            self.last_userid = None
        
        self.user_list = self._get_userlist(self.mfg_uri)
        
        Frame.__init__(self, master)

        self.grid()
        self.createWidgets()

    def _get_userlist(self, full_uri):
        data_dict = {}
        data_dict["user"] = XMLRPC_USER
        data_dict["passwd"] = XMLRPC_PW
        data_dict["trav_type"] = 'cavity'

        XMLProxy = xmlrpclib.ServerProxy(full_uri)
        
        rtn_list = []
        dlist = XMLProxy.travx_getulist(data_dict)
        if dlist:
            return dlist
    
        return None

class TravellerDataPush():
    def __init__(self, *args, **kwargs):
        '''
        '''
        run_ts = datetime.datetime.now()
        parm_dict = {}
        data_dict = {}
        self.last_userid = None

        if kwargs:
            if 'parm_dict' in kwargs:
                parm_dict = kwargs['parm_dict']

            if 'data_dict' in kwargs:
                data_dict = kwargs['data_dict']

        log_file_path = None
        if 'log_file' in parm_dict:
            if parm_dict['log_file']:
                log_file_path = parm_dict['log_file']
            del parm_dict['log_file']
                
        if not log_file_path:
            log_file_name = 'TravellerDataPush_%s.log' % (run_ts.strftime("%Y%m%d%H%M%S"))
            log_file_path = os.path.join(CWD, log_file_name)
       
        mylog = _Logger(path=log_file_path) 
        mylog.write('Starting TravellerDataPush')
        
        if 'ctl_file' in parm_dict:
            if parm_dict['ctl_file']:
                ctl_dict = {}
                self._file_pull(parm_dict['ctl_file'], ctl_dict)
                
                for ctlk in (
                            'data_file', 
                            'image_file',
                            'plot_file',
                            'traveller_identifier',
                            'traveller_name',
                            'mfg_url',
                             ):
                    
                    if ctlk in ctl_dict:
                        parm_dict[ctlk] = ctl_dict[ctlk]
                        del ctl_dict[ctlk]
                    else:
                        parm_dict[ctlk] = None
                
                if ctl_dict:
                    data_dict = ctl_dict
                    
            del parm_dict['ctl_file']
            
        if 'data_file' in parm_dict:
            if parm_dict['data_file']:
                ctl_dict = {}
                self._file_pull(parm_dict['data_file'], ctl_dict)
                
                if ctl_dict:
                    data_dict = ctl_dict
        
            del parm_dict['data_file']

        for ky, val in parm_dict.iteritems():
            data_dict[ky] = val
            
        if not 'mfg_url' in parm_dict:
            parm_dict['mfg_url'] = RPCURI_DFT
        elif not parm_dict['mfg_url']:
            parm_dict['mfg_url'] = RPCURI_DFT
        
        srch_dict = {}
        if 'traveller_identifier' in parm_dict:
            if parm_dict['traveller_identifier']:
                srch_dict['identifier'] = parm_dict['traveller_identifier'].strip()

        if 'traveller_name' in parm_dict:
            if parm_dict['traveller_name']:
                srch_dict['doc_name'] = parm_dict['traveller_name'].strip()
                
        cavity_sn = None
        if 'cavity_sn' in data_dict:
            if data_dict['cavity_sn']:
                cavity_sn = data_dict['cavity_sn'].strip()
                srch_dict['cadoc_name'] = cavity_sn
                
        if 'userid' in data_dict:
            self.last_userid = data_dict['userid']
        
        doc_tuple = self._get_doclist(parm_dict['mfg_url'], srch_dict)

        if doc_tuple:
            self._show_panel(parm_dict, data_dict, mylog, doc_tuple, parm_dict['mfg_url'])
        else:
            if cavity_sn:
                msg = 'There are no Cavity Traveller Documents (in proper status) for the given Serial number: %s' % (cavity_sn)
            else:
                msg = 'There are no Cavity Traveller Documents (in proper status).'
            mylog.write(msg)
            self._show_message(msg)
    
    def _show_message(self, msg):
        root = Tk()
        root.wm_title(PNL_TITLE)

        Message(root, text=msg, width=MSG_WIDTH, background='white').pack(padx=10, pady=10, expand=True)
        
        root.QUIT = Button(root, width=BTN_WIDTH)
        root.QUIT["text"] = "Cancel"
        root.QUIT["command"] =  root.destroy
        root.QUIT.pack(padx=10, pady=10, expand=True)
        
        root.mainloop()
        
    def _show_panel(self, parm_dict, data_dict, my_log, doc_tuple, mfg_uri):
        root = Tk()
        root.wm_title(PNL_TITLE)
        app = TravellerDataPushPnl(
                          master=root, 
                          parm_dict=parm_dict, 
                          data_dict=data_dict, 
                          my_log=my_log,
                          doc_tuple=doc_tuple,
                          mfg_uri=mfg_uri
                          )
        
        app.mainloop()
        self.last_userid = app.last_userid
        root.destroy()
      
            
    def _file_pull(self, data_file, data_file_dict, psep=': '):
        try:
            ctl_f = open(data_file, "r")
            if ctl_f:
                f_data = ctl_f.readline()
                while f_data:
                    dline = f_data.strip()
    
                    ky, sep, val = dline.partition(psep)
                    ky = ky.replace('-', '_')
                    
                    data_file_dict[ky.strip()] = val.strip()
    
                    f_data = ctl_f.readline()
            
        except:
            return False
        return True
    
    def _get_doclist(self, full_uri, search_criteria=None):
        data_dict = {}
        data_dict["user"] = XMLRPC_USER
        data_dict["passwd"] = XMLRPC_PW
        data_dict['trav_type'] = 'cavity'
        
        if search_criteria:
            for val in search_criteria:
                if search_criteria[val]:
                    data_dict[val] = search_criteria[val]
        
        XMLProxy = xmlrpclib.ServerProxy(full_uri)
        
        rtn_list = []
        for sts in (
                    'step_2',
                    'step_3',
                    'step_5',
                    'step_6',
                    'step_8',
                    'step_9',
                    'step_11',
                    'step_12',
                    'step_16',
                    'step_17',
                    'step_19',
                    'step_20',
                    ):
            data_dict['cadoc_status'] = sts
            dlist = XMLProxy.travx_getlist(data_dict)
            if dlist:
                for val in dlist:
                    return (val['name'], val['identifier'], val['status'], val['id'])
    
        return None
    
def main(argv=None):
    run_ts = datetime.datetime.now()

    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], 
                                       'hcdiptnlu', 
                                       [
                                        'help', 
                                        'ctl-file=',
                                        'data-file=',
                                        'image-file=',
                                        'plot-file=',
                                        'traveller-identifier=',
                                        'traveller-name=',
                                        'mfg-url=',
                                        'log-file=',
                                        ]
                                       )
        except getopt.error, msg:
             raise Usage(msg)

        for o, a in opts:
            if o in ('-h', '--help'):
                raise Usage(__doc__) 

        parm_dict = {}
        for p in (
                'log_file',
                'ctl_file',
                'data_file',
                'image_file',
                'plot_file',
                'traveller_identifier',
                'traveller_name',
                'mfg_url',
                  ):
            parm_dict[p] = None

        _get_opts_and_args(parm_dict, opts)
        _setup_and_validate_parms(parm_dict, args) 
        
        c = TravellerDataPush(parm_dict=parm_dict)
            
        # more code, unchanged
    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "for help use --help"
        return 2

def _get_opts_and_args(parm_dict, opts):
    '''
    get passed in options and arguments
    '''
    for user_opt, user_arg in opts:
        if user_opt in ("-h", "--help"):
            raise Usage(__doc__)
        
        if user_opt in ('-c', '--ctl-file'):
            parm_dict['ctl_file'] = user_arg
        if user_opt in ('-d', '--data-file'):
            parm_dict['data_file'] = user_arg
        if user_opt in ('-i', '--image-file'):
            parm_dict['image_file'] = user_arg
        if user_opt in ('-p', '--plot-file'):
            parm_dict['plot_file'] = user_arg
        if user_opt in ('-t', '--traveller-identifier'):
            parm_dict['traveller_identifier'] = user_arg
        if user_opt in ('-n', '--traveller-name'):
            parm_dict['traveller_name'] = user_arg
        if user_opt in ('-u', '--mfg-url'):
            parm_dict['mfg_url'] = user_arg
        if user_opt in ('-l', '--log-file'):
            parm_dict['log_file'] = user_arg

def _setup_and_validate_parms(parm_dict, args):
    '''
    setup parms from passed in arguments
    '''
    all_ok = True

    if 1 <= len(args):
        parm_dict["ctl_file"] = args[0]

    if not all_ok:
        raise Usage(__doc__) 


if __name__ == '__main__':
    sys.exit(main())
