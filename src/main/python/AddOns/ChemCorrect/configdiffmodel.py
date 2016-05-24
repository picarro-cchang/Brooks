'''
configdiff.py -- The configdiff module contains the ConfigDiffModel class.
This class will display an XY plot of data from the source CSV or H5 file (from 
coordinator).

'''
import os
import datetime
import threading

import xlwt


from postprocessdefn import *
from Utilities import AppInfo

from config2h5 import ConfigToH5, DiffTwoTables


class ConfigDiffModel(object):
    '''
    ConfigDiff Model Class
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''

        # version and about info
        about = AppInfo()
        self.about_version = about.getAppVer()
        self.about_name = "ConfigDiff"  #about.getAppName()
        self.about_copyright = about.getCopyright()
        self.about_description = "List of differences between two config \
                                 locations."    # about.getDescription()
        self.about_website = about.getWebSite()

        self._title = "Configuration Difference Viewer"
        self._max_source_lines = 100
        
        self._init_process_parms()
        self._line_source1 = None
        self._line_source2 = None
        self._comp_source1 = None
        self._comp_source2 = None
        self._first_time = None
        self.working = None

        self._html_escape_table = {"&": "&amp;",
                                   '"': "&quot;",
                                   "'": "&apos;",
                                   ">": "&gt;",
                                   "<": "&lt;",
                                   }
        
    
    def _init_process_parms(self):
        '''
        initialize process_parms
        '''
        self.process_parms = {
                              "column_list": None,
                              "html_source": {},
                              "plot_fig": {},
                              "plot_data": {},
                              STATUS: None
                              }
           
    def process_source(self, source_parms=None, brief_html = None):
        '''
        process the passed source file - for XY Plot we only need to open
        the source and get the column name list
        '''
        if not source_parms:
            raise RuntimeError, INVALID_SOURCE_ERROR
        
        self._init_process_parms()
        
        self._source1 = source_parms[SOURCE_PARM]
        self._source2 = source_parms[SOURCE_PARM2]
        
        if self._source1:
            if self._source2:
                self._do_compare()
                
                self.process_parms["html_source"][0] = self._build_html(brief_html)
                self.process_parms[STATUS] = OK

    def _do_compare(self):
        '''
        use config2h5 module to do config compare
        '''

        if self._comp_source1:
            if self._comp_source1 == self._source1:
                if self._comp_source2 == self._source2:
                    return 
        
        self._diff = None

        self._comp_source1 = self._source1
        self._comp_source2 = self._source2

        c=ConfigToH5(start_dir=self._source1,
                     new_name="config1.h5")
        c.get_config_files()
        
        c2=ConfigToH5(start_dir=self._source2,
                     new_name="config2.h5")
        c2.get_config_files()
    
        c3=DiffTwoTables(file1="config1.h5", file2="config2.h5")

        self._diff = None
        self._diff = c3.compare()

        c = None
        c2 = None
        c3 = None
        
        
    def _build_html(self, brief_html = None):
        '''
        build the html source file
        '''
        show_truncation_msg = None
        
        if self._line_source1:
            if self._line_source1 == self._source1:
                if self._line_source2 == self._source2:
                    return self._line_data
        
        if brief_html:
            self._max_source_lines = 200
        
        line = "<HTML><BODY bgcolor='%s'>" % (MAIN_BACKGROUNDCOLOR)
        line += "<H2 align='center'>%s</H2>" % (self._title)
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                    '98%', 
                                                    PNL_TBL_BACKGROUNDCOLOR
                                                                )

        line += "<tr><td align='center'>"
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                        '98%', 
                                                        PNL_TBL_BORDERCOLOR
                                                                )


        line += "<tr>"
        line += "<td bgcolor='%s'>" % (PNL_TBL_BORDERCOLOR)
        
        line += "<table width='%s'>" % ("100%")

        
        line += "<tr>"
        line += "<td bgcolor='%s'>" % (PNL_TBL_BACKGROUNDCOLOR)

        line +=     "<table border=1 width='%s'>" % ("100%")
        line +=       "<tr>"
        
        line +=         "<td width='%s'>" % ("50%")
        line +=         "Path 1: <b>%s</b>" % (self._source1)
        line +=         "</td>"
        
        line +=         "<td width='%s'>" % ("50%")
        line +=         "Path 2: <b>%s</b>" % (self._source2)
        line +=         "</td>"
        
        line +=       "</tr>"
        
        line +=      "</table>" #194

        line += "</td>"
        line += "</tr>" #191

        line += "</table>" #182
        line += "</td>" #180
        line += "</tr>" #179
        
        if self._diff:

            line += "<tr>"
            line += "<td bgcolor='%s'>" % (PNL_TBL_BACKGROUNDCOLOR)

            line +=     "<table border=1 width='%s'>" % ("100%")

            
            last_pth = None
            for dkey in range(1,len(self._diff) + 1):
                path1 = self._diff[dkey]["path1"]
                path2 = self._diff[dkey]["path2"]

                if (("path1" in self._diff[dkey].keys())
                    and (self._diff[dkey]["path1"])):
                    
                    p1 = os.path.join(self._diff[dkey]["path1"], 
                                      "%s.%s" %(self._diff[dkey]["file"],
                                                self._diff[dkey]["type"])
                                      )
                else:
                    p1 = None

                if (("path2" in self._diff[dkey].keys()) 
                    and (self._diff[dkey]["path2"])):
                    
                    p2 = os.path.join(self._diff[dkey]["path2"], 
                                      "%s.%s" %(self._diff[dkey]["file"],
                                                self._diff[dkey]["type"])
                                      )
                else:
                    p2 = None
                
                if p1:
                    pth = p1
                else:
                    pth = p2

                if pth == last_pth:
                    continue
                else:
                    last_pth = pth

                    line +=       "<tr>"
                    line +=         "<td width='%s'>" % ("100%")
                    line +=         "<a href='%s%s'>%s </a>" % ("#", pth, pth) 
                    line +=         "</td>"
                    line +=       "</tr>"

            line +=      "</table>" #194

            line += "</td>"
            line += "</tr>" #191



            
            i = 0
            last_pth = None
            for dkey in range(1,len(self._diff) + 1):
                path1 = self._diff[dkey]["path1"]
                path2 = self._diff[dkey]["path2"]
                file = self._diff[dkey]["file"]
                type = self._diff[dkey]["type"]
                section = self._diff[dkey]["section"]
                keyword = self._diff[dkey]["keyword"]
                value1 = self._diff[dkey]["value1"]
                value2 = self._diff[dkey]["value2"]
                
                
                if (("path1" in self._diff[dkey].keys())
                    and (self._diff[dkey]["path1"])):
                    
                    p1 = os.path.join(self._diff[dkey]["path1"], 
                                      "%s.%s" %(self._diff[dkey]["file"],
                                                self._diff[dkey]["type"])
                                      )
                else:
                    p1 = None

                if (("path2" in self._diff[dkey].keys()) 
                    and (self._diff[dkey]["path2"])):
                    
                    p2 = os.path.join(self._diff[dkey]["path2"], 
                                      "%s.%s" %(self._diff[dkey]["file"],
                                                self._diff[dkey]["type"])
                                      )
                else:
                    p2 = None
                
                if p1:
                    pth = p1
                else:
                    pth = p2
                
                
                if (not p1) or (not p2):
                    if pth == last_pth:
                        continue
                    else:
                        i += 1
                
                
                        last_pth = pth
                        
                        p1str = ""
                        p2str = ""

                        if (section == "Error" 
                            and keyword == "Error" 
                            and value1 == "Error"):
                            
                            p1str = "<b>This file must be manually evaluated!</b>"
                            p2str = "<b>This file must be manually evaluated!</b>"

                        else:
                            if not p1:
                                p1str = "<b>Missing File</b>"
                            if not p2:
                                p2str = "<b>Missing File</b>"
                        
                        line += "<tr>"
                        line += "<td bgcolor='%s'>" % (PNL_TBL_BORDERCOLOR)
                        
                        line += "<table width='%s'>" % ("100%")
        
                        
                        line += "<tr>"
                        line += "<td bgcolor='%s'>" % (PNL_TBL_BORDERCOLOR)
                        
                        line += "<a name='%s'><b>Difference %s: %s</b>" % (pth, i, pth) 
                        line += "</td>"
                        line += "</tr>" #185
    
    
                        line += "<tr>"
                        line += "<td bgcolor='%s'>" % (PNL_TBL_BACKGROUNDCOLOR)
        
                        line +=     "<table border=1 width='%s'>" % ("100%")
                        line +=       "<tr>"
                        
                        line +=         "<td width='%s'>" % ("50%")
                        line +=         p1str
                        line +=         "</td>"
                        
                        line +=          "<td width='%s'>" % ("50%")
                        line +=          p2str
                        line +=          "</td>"
                        
                        line +=       "</tr>"
                        line +=      "</table>" #194
        
                        line += "</td>"
                        line += "</tr>" #191
    
    
                        line += "</table>" #182
                        line += "</td>" #180
                        line += "</tr>" #179
                        
                else:
                    i += 1
                
                    if pth == last_pth:
                        phline = "<b>Difference %s</b>" % (i)
                    else:
                        phline = "<a name='%s'><b>Difference %s: %s</b>" % (pth, i, pth)

                
                    last_pth = pth

                    line += "<tr>"
                    line += "<td bgcolor='%s'>" % (PNL_TBL_BORDERCOLOR)
                    
                    line += "<table width='%s'>" % ("100%")
    
                    
                    line += "<tr>"
                    line += "<td bgcolor='%s'>" % (PNL_TBL_BORDERCOLOR)
                    
                    line += phline 
                    line += "</td>"
                    line += "</tr>" #185


                    line += "<tr>"
                    line += "<td bgcolor='%s'>" % (PNL_TBL_BACKGROUNDCOLOR)
    
                    line +=     "<table border=1 width='%s'>" % ("100%")
                    line +=       "<tr>"
                    
                    line +=         "<td width='%s'>" % ("50%")
                    line +=         "[%s]" % (self._diff[dkey]["section"])
                    line +=         "</td>"
                    
                    line +=          "<td width='%s'>" % ("50%")
                    line +=          "[%s]" % (self._diff[dkey]["section"])
                    line +=          "</td>"
                    
                    line +=       "</tr>"
                    
                    line +=       "<tr>"
                    line +=           "<td width='%s'>" % ("50%")
                    vtext = self._html_escape(self._diff[dkey]["value1"])
                    
                    line +=           "%s = <b>%s</b>" % (self._diff[dkey]["keyword"], 
                                                   vtext)
                    line +=           "</td>"
    
                    line +=         "<td width='%s'>" % ("50%")
                    vtext = self._html_escape(self._diff[dkey]["value2"])
                    
                    line +=           "%s = <b>%s</b>" % (self._diff[dkey]["keyword"], 
                                                   vtext)
                    line +=         "</td>"
    
                    line +=        "</tr>"
                    line +=      "</table>" #194
    
                    line += "</td>"
                    line += "</tr>" #191


                    line += "</table>" #182
                    line += "</td>" #180
                    line += "</tr>" #179
                
                
                #if i > self._max_source_lines:
                #    show_truncation_msg = True
                #    break
                
        line += "</table>" #153
        line += "</td></tr>"

        if show_truncation_msg:
            msg = "Source file truncated after this point."
            msg += " To see the rest of the source, please different viewer."
            line += "<tr><td><h3><p>%s</h3></td><tr/>" % (msg)
            
        line += "<tr><td><p></td><tr/>"
        line += "</table>"

        line += "<table><tr><td align='right'>"
        line += "&copy; 2010 Picarro Inc."
        line += "</td></tr></table>"
        line += "</BODY></HTML>"
        
        self._line_source1 = self._source1
        self._line_source2 = self._source2
        self._line_data = line

        return line
        
    def _html_escape(self, text):
        """Produce entities within text."""
        stext = "%s" % (text)
        return "".join(self._html_escape_table.get(c,c) for c in stext)

    def export_to_spreadsheet(self, filename):
        self._ezxf = xlwt.easyxf
        self._heading_xf = self._ezxf('font: bold on; align: wrap on, vert centre, horiz center')
        self._heading_xf_left = self._ezxf('font: bold on; align: wrap on, vert centre, horiz left')
        self._text_fmt_left = self._ezxf('align: wrap on, vert top, horiz left')

        self._wb = None
        self._wb = xlwt.Workbook()
        self._sheet = self._wb.add_sheet("Config Differences")
        
        
        i = 0
        last_pth = None
        if self._diff:
            ### SPREADSHEET HEADING
            row = 0
            self._sheet.write_merge(row, 
                                    row, 
                                    0, 
                                    5, 
                                    "%s" % (filename), 
                                    self._heading_xf_left)
            row += 1
            
            self._sheet.write(row, 1, "File", self._heading_xf)
            self._sheet.write(row, 2, "Section", self._heading_xf)
            self._sheet.write(row, 3, "Keyword", self._heading_xf)
            self._sheet.write(row, 4, "%s" %(self._source1), self._heading_xf_left)
            self._sheet.write(row, 5, "%s" %(self._source1), self._heading_xf_left)
            row += 1
            
            for dkey in range(1,len(self._diff) + 1):
                path1 = self._diff[dkey]["path1"]
                path2 = self._diff[dkey]["path2"]
                file = self._diff[dkey]["file"]
                type = self._diff[dkey]["type"]
                section = self._diff[dkey]["section"]
                keyword = self._diff[dkey]["keyword"]
                value1 = self._diff[dkey]["value1"]
                value2 = self._diff[dkey]["value2"]
        
                if (("path1" in self._diff[dkey].keys())
                    and (self._diff[dkey]["path1"])):
                    
                    p1 = os.path.join(self._diff[dkey]["path1"], 
                                      "%s.%s" %(self._diff[dkey]["file"],
                                                self._diff[dkey]["type"])
                                      )
                else:
                    p1 = None

                if (("path2" in self._diff[dkey].keys()) 
                    and (self._diff[dkey]["path2"])):
                    
                    p2 = os.path.join(self._diff[dkey]["path2"], 
                                      "%s.%s" %(self._diff[dkey]["file"],
                                                self._diff[dkey]["type"])
                                      )
                else:
                    p2 = None
                
                if p1:
                    pth = p1
                else:
                    pth = p2
                
                
                if (not p1) or (not p2):
                    if pth == last_pth:
                        continue
                    else:
                        i += 1
                
                
                        last_pth = pth
                        
                        p1str = ""
                        p2str = ""

                        if (section == "Error" 
                            and keyword == "Error" 
                            and value1 == "Error"):
                            
                            p1str = "This file must be manually evaluated!"
                            p2str = "This file must be manually evaluated!"

                        else:
                            if not p1:
                                p1str = "Missing File"
                            if not p2:
                                p2str = "Missing File"

                    ### INSERT ROW INTO SPREADSHEET
                    self._sheet.write(row, 1, "%s.%s" %(file, type))
                    self._sheet.write(row, 2, section)
                    self._sheet.write(row, 3, keyword)
                    self._sheet.write(row, 4, p1str, self._text_fmt_left)
                    self._sheet.write(row, 5, p2str, self._text_fmt_left)
                    row += 1
                else:
                    i += 1

                    ### INSERT ROW INTO SPREADSHEET
                    self._sheet.write(row, 1, "%s.%s" %(file, type))
                    self._sheet.write(row, 2, section)
                    self._sheet.write(row, 3, keyword)
                    self._sheet.write(row, 4, "%s" %(value1), self._text_fmt_left)
                    self._sheet.write(row, 5, "%s" %(value2), self._text_fmt_left)
                    row += 1
        
        self._wb.save(filename)
        
        return

    def generate_plot(self, plot_parameters):
        '''
        '''
        return
                    
if __name__ == '__main__':
    raise RuntimeError, "%s %s" % ("configdiffmodel.py", STANDALONE_ERROR)
