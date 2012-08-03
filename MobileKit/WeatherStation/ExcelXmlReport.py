import xml.etree.cElementTree as ET
import functools

class _E(object):

    def __call__(self, tag, *children, **attrib):
        elem = ET.Element(tag, attrib)
        for item in children:
            if isinstance(item, dict):
                elem.attrib.update(item)
            elif isinstance(item, basestring):
                if len(elem):
                    elem[-1].tail = (elem[-1].tail or "") + item
                else:
                    elem.text = (elem.text or "") + item
            elif ET.iselement(item):
                elem.append(item)
            else:
                raise TypeError("bad argument: %r" % item)
        return elem

    def __getattr__(self, tag):
        return functools.partial(self, tag)

# create factory object
E = _E()

class ExcelXmlReport(object):
    def __init__(self):
        self.ss = ss = self.prependNs("ss")
        self.xmlns = self.prependNs("xmlns")
        self.col = lambda w: E.Column(ss(Width=w))
        self.strData = lambda d: E.Data(d,**ss(Type="String"))
        self.numData = lambda d: E.Data("%s" % d,**ss(Type="Number"))
        self.cell = lambda *c,**k: E.Cell(*c,**ss(**k))
        self.row  = lambda *c,**k: E.Row(*c,**ss(**k))
        self.tableChildren = []
        self.styleIds = {"Normal": "Default", "Hyperlink": "s1", "Title": "s2", "Heading": "s3"}
        
    def prependNs(self,ns):
        """Returns function which returns a dictionary consisting of its keyword arguments
         with the keys having ns: prepended"""
        def _prepend(**attr):
            result = {}
            for a in attr:
                result["%s:%s" % (ns,a)] = attr[a]
            return result
        return _prepend

    def makeStyles(self):
        ss = self.ss
        xmlns = self.xmlns
        self.styles = []
        name = "Normal"
        self.styles.append(E.Style(ss(ID=self.styleIds[name],Name=name),
            E.Font(ss(FontName="Calibri", Size="11", Color="#000000"), {"x:Family": "Swiss"})))
        name = "Hyperlink"
        self.styles.append(E.Style(ss(ID=self.styleIds[name],Name=name),
            E.Font(ss(FontName="Calibri", Size="11", Color="#0000FF", Underline="Single"), {"x:Family": "Swiss"})))
        name = "Title"
        self.styles.append(E.Style(ss(ID=self.styleIds[name],Name=name),
            E.Font(ss(FontName="Cambria", Size="20", Color="#000000"), {"x:Family": "Roman"})))
        name = "Heading"
        self.styles.append(E.Style(ss(ID=self.styleIds[name],Name=name),
            E.Font(ss(FontName="Cambria", Size="11", Color="#000000"), {"x:Family": "Roman"}),
            E.Alignment(ss(Horizontal="Center", Vertical="Bottom"))))
        return E.Styles(*self.styles)
    
    def makeHeader(self,title,colNames,colWidths):
        row, cell, col, strData = self.row, self.cell, self.col, self.strData
        self.tableChildren.extend([col("%s" % w) for w in colWidths])
        self.tableChildren.append(row(cell(strData(title),StyleID=self.styleIds["Title"])))
        headCells = [cell(strData(h),StyleID=self.styleIds["Heading"]) for h in colNames]
        self.tableChildren.append(row(Index="3",*headCells))
        
    def makeDataRow(self,rank,des,lat,lng,conc,ampl,zoom):
        row, cell, col = self.row, self.cell, self.col
        numData, strData = self.numData, self.strData
        coords = "%s,%s" % (lat,lng)
        url = "http://maps.google.com?q=%s+(%s)&z=%d" % (coords,des,zoom)
        self.tableChildren.append(row(
            cell(numData(rank)),
            cell(strData(des),StyleID=self.styleIds["Hyperlink"],HRef=url),
            cell(numData(lat)),
            cell(numData(lng)),
            cell(numData(conc)),
            cell(numData(ampl))))
           
    def xmlWorkbook(self,name):
        ss, xmlns = self.ss, self.xmlns
        worksheet = E.Worksheet(ss(Name=name),E.Table(*self.tableChildren))
        workbook = E.Workbook({"xmlns":"urn:schemas-microsoft-com:office:spreadsheet"},
                                xmlns(o="urn:schemas-microsoft-com:office:office",
                                      x="urn:schemas-microsoft-com:office:excel",
                                      ss="urn:schemas-microsoft-com:office:spreadsheet",
                                      html="http://www.w3.org/TR/REC-html40"),
                                self.makeStyles(),worksheet)
        xmlHdr = '<?xml version="1.0"?>'
        xmlHdr += '<?mso-application progid="Excel.Sheet"?>'
        return xmlHdr + ET.tostring(workbook)

if __name__ == "__main__":
    excelReport = ExcelXmlReport()
    excelReport.makeHeader("Report ABCD EFGH IJKL MNOP QRST",["Rank","Designation","Latitude","Longitude","Concentration","Amplitude"],[30,150,80,80,80,80])
    excelReport.makeDataRow(1,"FDDS2012_20120802T020444",37.416548352900001,-121.97474081999999,2.1812219882699999,0.153140599736,18)
    excelReport.makeDataRow(2,"FDDS2012_20120727T230013",37.4166703617,-121.974443104,2.0043892779600001,7.9034844053299996E-2,18)
    print excelReport.xmlWorkbook("peak.0")
