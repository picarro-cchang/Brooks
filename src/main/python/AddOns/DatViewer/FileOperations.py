import tables
import os
import Queue
import zipfile
import tempfile
import numpy as np
import time
from datetime import datetime
import pytz
from scipy.interpolate import interp1d
from timestamp import datetimeTzToUnixTime, unixTime

# Dictionary of known h5 column heading names that are too long and their
# shortened names for DAT files.
H5ColNamesToDatNames = {"ch4_splinemax_for_correction": "ch4_splinemax_for_correct",
                        "fineLaserCurrent_1_controlOn": "fineLaserCurr_1_ctrlOn",
                        "fineLaserCurrent_2_controlOn": "fineLaserCurr_2_ctrlOn",
                        "fineLaserCurrent_3_controlOn": "fineLaserCurr_3_ctrlOn",
                        "fineLaserCurrent_4_controlOn": "fineLaserCurr_4_ctrlOn",
                        "fineLaserCurrent_5_controlOn": "fineLaserCurr_5_ctrlOn",
                        "fineLaserCurrent_6_controlOn": "fineLaserCurr_6_ctrlOn",
                        "fineLaserCurrent_7_controlOn": "fineLaserCurr_7_ctrlOn",
                        "fineLaserCurrent_8_controlOn": "fineLaserCurr_8_ctrlOn"}

class FileInterpolation():
    def __init__(self, sourceFileName, destFileName, interval):
        self.sourceFileName = sourceFileName
        self.destFileName = destFileName
        self.interval = interval
        self.progress = 0
        self.message = "Interpolating..."
        
    def run(self):
        source, dest = None, None
        try:
            source = tables.openFile(self.sourceFileName, "r")
            dest = tables.openFile(self.destFileName, "w")
            filters = tables.Filters(complevel=1, fletcher32=True)
            totalColumns = 0
            col_index = 0
            for t in source.listNodes('/'):
                totalColumns += (len(t.dtype) - 1)
            for n in source.listNodes('/'):
                table = n.read()
                if "DATE_TIME" in n.colnames:
                    xCol = "DATE_TIME"
                elif "timestamp" in n.colnames:
                    xCol = "timestamp"
                    self.interval *= 1000
                elif "time" in n.colnames:
                    xCol = "time"
                else:
                    self.progress = -1
                    self.message = "No time-related data is found in table [%s]" % n.name
                    return 
                xData = table[xCol]
                rowNum = int((xData[-1] - xData[0]) / self.interval)
                newTable = np.zeros(rowNum, dtype=table.dtype)
                newTable[xCol] = np.linspace(xData[0], xData[0]+(rowNum-1)*self.interval, rowNum)
                for col in n.colnames:
                    if col != xCol:
                        f = interp1d(xData, table[col])
                        newTable[col] = f(newTable[xCol])
                        col_index += 1
                        self.progress = int(col_index * 100.0 / totalColumns)
                t = dest.createTable(dest.root, n.name, newTable, filters=filters)
                t.flush()
        except Exception, e:
            self.message = "%s: %s" % (Exception, e)
            self.progress = -1
        finally:
            if source is not None:
                source.close()
            if dest is not None:
                dest.close()

class FileBlockAverage():
    def __init__(self, sourceFileName, destFileName, blockSize):
        self.sourceFileName = sourceFileName
        self.destFileName = destFileName
        self.blockSize = blockSize
        self.progress = 0
        self.message = "Processing..."
        
    def run(self):
        source, dest = None, None
        try:
            source = tables.openFile(self.sourceFileName, "r")
            dest = tables.openFile(self.destFileName, "w")
            filters = tables.Filters(complevel=1, fletcher32=True)
            totalRows = 0
            row_index = 0
            for t in source.listNodes('/'):
                totalRows += (t.shape[0])
            for n in source.listNodes('/'):
                table = n.read()
                file_table = dest.createTable(dest.root, n.name, table.dtype, filters=filters)
                if "DATE_TIME" in n.colnames:
                    xCol = "DATE_TIME"
                elif "timestamp" in n.colnames:
                    xCol = "timestamp"
                    self.blockSize *= 1000
                elif "time" in n.colnames:
                    xCol = "time"
                else:
                    self.progress = -1
                    self.message = "No time-related data is found in table [%s]" % n.name
                    return 
                dataQueue = Queue.Queue()
                start_time = table[0][xCol]
                for row in table:
                    if row[xCol] > start_time + self.blockSize:
                        result = 0
                        items = 0
                        while True:
                            try:
                                data = dataQueue.get(block=False)
                                result += np.array(data.item())
                                items += 1.0
                            except Queue.Empty:
                                if items > 0:
                                    result /= items
                                    table_row = file_table.row
                                    for i, col in enumerate(row.dtype.names):
                                        table_row[col] = result[i]
                                    table_row.append()
                                    start_time = row[xCol]
                                    self.progress = int(row_index * 100.0 / totalRows)
                                break
                    dataQueue.put(row)
                    row_index += 1
                file_table.flush()
        except Exception, e:
            # self.message = "%s: %s" % (Exception, e)
            # self.progress = -1
            raise
        finally:
            if source is not None:
                source.close()
            if dest is not None:
                dest.close()
                
class Dat2h5BatchConvert():
    def __init__(self, dirPath):
        self.path = dirPath
        self.message = ""
        self.progress = 0
    
    def run(self):
        totalFile = 0
        for root, dirs, files in os.walk(self.path):
            totalFile += len(files)
        fileIndex = 0
        for root, dirs, files in os.walk(self.path):
            for name in files:
                fileIndex += 1
                if name.endswith(".dat"):
                    path = os.path.join(root, name)
                    c = Dat2h5(path, path[:-3] + "h5")
                    self.message = path 
                    c.run() 
                    if c.progress > 0:
                        self.progress = fileIndex * 100.0 / totalFile
                    else:
                        self.progress, self.message = -1, c.message
                        return
                                        
class Dat2h5():
    def __init__(self, datFileName, h5FileName):
        self.datFileName = datFileName
        self.h5FileName = h5FileName
        self.progress = 0
        self.message = ""
    
    def fixed_width(self, text, width):
        start = 0
        result = []
        while True:
            atom = text[start:start + width].strip()
            if not atom:
                return result
            result.append(atom)
            start += width

    def run(self):
        fp, h5f = None, None
        try:
            fp = open(self.datFileName, "r")
            data = fp.read().split('\n')
            h5f = tables.openFile(self.h5FileName, "w")
            filters = tables.Filters(complevel=1, fletcher32=True)
            headings = []
            table = None
            length = len(data)
            for i, line in enumerate(data):
                atoms = line.split()
                if len(atoms) < 2:
                    break
                if not headings:
                    headings = [a.replace(" ", "_") for a in atoms]
                    colDict = {"DATE_TIME": tables.Time64Col()}
                    for h in headings:
                        if h not in ["DATE", "TIME"]:
                            colDict[h] = tables.Float32Col()
                    TableType = type("TableType", (tables.IsDescription,), colDict)
                    table = h5f.createTable(h5f.root, "results", TableType, filters=filters)
                else:
                    minCol = 0
                    if headings[0] == "DATE" and headings[1] == "TIME":
                        minCol = 2
                        # atoms[0] is date, atoms[1] is time
                        dateTimeString = " ".join(atoms[0:2])
                        dp = dateTimeString.find(".")
                        if dp >= 0:
                            fracSec = float(dateTimeString[dp:])
                            dateTimeString = dateTimeString[:dp]
                        else:
                            fracSec = 0.0
                        try:
                            when = time.mktime(time.strptime(dateTimeString, "%m/%d/%Y %H:%M:%S")) + fracSec
                        except:
                            when = time.mktime(time.strptime(dateTimeString, "%Y-%m-%d %H:%M:%S")) + fracSec
                    entry = table.row
                    for h, a in zip(headings, atoms)[minCol:]:
                        try:
                            entry[h] = float(a)
                            if h == "EPOCH_TIME":
                                when = float(a)
                        except:
                            entry[h] = np.NaN
                    entry["DATE_TIME"] = when
                    entry.append()
                self.progress = int(i*100.0/length)
            table.flush()
            self.progress = 100
        except Exception, e:
            self.progress = -1
            self.message = "%s: %s" % (Exception, e)
            raise
        finally:
            if h5f is not None:
                h5f.close()
            if fp is not None:
                fp.close()

class CombineDat():
    def __init__(self, dirPath, fileName, variableDict):
        self.dirPath = dirPath
        self.fileName = fileName
        self.variableDict = variableDict
        self.message = ""
        self.progress = 0
        
    def run(self):
        with open(self.outFileName, 'w') as output:
            columns = None
            totalFile = 0
            for root, dirs, files in os.walk(self.dirPath):
                totalFile += len(files)
            fileIndex = 0
            for root, dirs, files in os.walk(self.dirPath):
                for name in files:
                    fileIndex += 1
                    if name.endswith(".dat"):
                        path = os.path.join(root, name)
                        with open(path, 'r') as f:
                            data = f.read().split('\n')
                            if columns is None:
                                columns = data[0]
                                output.write(columns + "\n")
                            elif columns != data[0]:
                                self.message = "data columns are inconsistent"
                                self.progress = -1
                                return
                            for ii in range(1, len(data)):
                                output.write(data[ii] + "\n")
                    self.progress = fileIndex * 100.0 / totalFile            
                            
                
class h52DatBatchConvert():
    def __init__(self, dirPath):
        self.path = dirPath
        self.message = ""
        self.progress = 0
    
    def run(self):
        totalFile = 0
        for root, dirs, files in os.walk(self.path):
            totalFile += len(files)
        fileIndex = 0
        for root, dirs, files in os.walk(self.path):
            for name in files:
                fileIndex += 1
                if name.endswith(".h5"):
                    path = os.path.join(root, name)
                    c = h52Dat(path, path[:-2] + "dat")
                    self.message = path 
                    c.run()
                    if c.progress > 0:
                        self.progress = fileIndex * 100.0 / totalFile
                    else:
                        self.progress, self.message = -1, c.message
                        return
                
class h52Dat():
    def __init__(self, h5FileName, datFileName):
        self.datFileName = datFileName
        self.h5FileName = h5FileName
        self.progress = 0
        self.message = ""

    def run(self):
        ip, dat = None, None
        try:
            ip = tables.openFile(self.h5FileName, "r")
            try:
                resultsTable = ip.root.results
            except:
                resultsTable = ip.root.results_0

            # TODO: Use resultsTable.itterows() to iterate rather than reading the whole
            #       thing into memory. The ability to concatenate a folder of ZIP H5 archives
            #       into an H5 will probably expose this as a problem.
            dataRows = resultsTable.read()
            colNames = resultsTable.colnames
            numCols = len(colNames)
            timeMode = "DATE_TIME"

            # find any column headings that are too long (more than 25 chars)
            # and convert them or truncate them
            #
            # H5ColNamesToDatNames is a dict of known abbreviations so they
            # will properly roundtrip (H5 -> DAT -> H5).
            #
            # TODO: log this information, and let user view it in a Done dialog
            for ii in range(numCols):
                if len(colNames[ii]) > 25:
                    colNameTrunc = colNames[ii]
                    if colNames[ii] in H5ColNamesToDatNames:
                        colNameTrunc = H5ColNamesToDatNames[colNames[ii]]
                        print "converted '%s' to '%s'" % (colNames[ii], colNameTrunc)
                        colNames[ii] = colNameTrunc
                    else:
                        # column name not in table, all we can do is truncate it
                        # this will be a problem if this DAT is converted back to H5
                        # as it won't have identical column headings to the original
                        colNameTrunc = colNameTrunc[:25]
                        print "truncated '%s' to '%s'" % (colNames[ii], colNameTrunc)
                        colNames[ii] = colNameTrunc

            # before we remove columns, print out some example timestamp
            # column names and values so I can look at them (only those in the first data row)

            if "DATE_TIME" in colNames:
                dateTimeIndex = colNames.index("DATE_TIME")
                colNames.remove("DATE_TIME")
            elif "time" in colNames:
                dateTimeIndex = colNames.index("time")
                colNames.remove("time")
                timeMode = "time"
            else:
                dateTimeIndex = colNames.index("timestamp")
                colNames.remove("timestamp")
                timeMode = "timestamp"

            # close the H5 input file
            ip.close()

            headingFormat = "%-26s" * (numCols - 1) + "\n"
            dataFormat = "%-26f" * (numCols - 1) + "\n"
            headings = headingFormat % tuple(colNames)
            linesToBeWritten = ["%-26s%-26s" % ("DATE", "TIME") + headings]
            length = len(dataRows)
            for i, row in enumerate(dataRows):
                # print "row[dateTimeIndex]=", row[dateTimeIndex]
                # print "timeMode=", timeMode

                if timeMode in ["timestamp", "time"]:
                    timestamp = row[dateTimeIndex]

                    # hack to test origin timestamp
                    #timestamp = 63513400570000 + (950 * i)
                    # print "i=%d timestamp=%s" % (i, timestamp)

                    # If timestamp is over 60 trillion we can assume it is
                    # for msec since 1/1/0000, so convert to epoch time
                    # (msec since 1/1/1970). Otherwise, assume timestamp
                    # is already epoch time.
                    if timestamp > 6e13:
                        timestamp = unixTime(timestamp)

                else:
                    timestamp = row[dateTimeIndex]

                dateTimeField = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                fracSec = timestamp - int(timestamp)
                dateTimeField += (".%02d" % round(100 * fracSec))
                dateTimeCols = "%-26s%-26s" % tuple(dateTimeField.split(" "))

                row = list(row)
                row.remove(row[dateTimeIndex])
                data = dateTimeCols + (dataFormat % tuple(row))
                linesToBeWritten.append(data)
                self.progress = int(i*100.0/length)
            
            dat = open(self.datFileName, "w")
            dat.writelines(linesToBeWritten)
            dat.close()
            self.progress = 100
        except Exception, e:
            self.progress = -1
            self.message = "%s: %s" % (Exception, e)
        finally:
            if dat is not None:
                dat.close()
            if ip is not None:
                ip.close()

class ConcatenateZip2File():
    def __init__(self, zipName, fileName, variableDict):
        self.zipName = zipName
        self.fileName = fileName
        self.variableDict = variableDict
        self.DateRange = self.variableDict.pop("user_DateRange", None)
        self.PrivateLog = self.variableDict.pop("user_PrivateLog", None)
        self.TimeZone = self.variableDict.pop("user_TimeZone", None)
        self.largeFile = self.variableDict.pop("user_LargeDateset", False)
        if self.TimeZone is not None:
            self.TimeZone = pytz.timezone(self.TimeZone)
        self.progress = 0
        self.message = ""
    
    def openFile(self):
        try:
            self.fileHandle = tables.openFile(self.fileName, "w")
        except:
            return False
        return True
        
    def analyzeFileName(self, fileName):
        logName = fileName.split("/")[-1]
        timeStr = "".join(logName.split("-")[1:3])
        if timeStr.endswith("Z"):   # UTC time
            utcTime = datetimeTzToUnixTime(datetime.strptime(timeStr[:-1], "%Y%m%d%H%M%S"), pytz.utc)
        else:   # local time
            utcTime = datetimeTzToUnixTime(datetime.strptime(timeStr, "%Y%m%d%H%M%S"), self.TimeZone)
        if utcTime > self.DateRange[0]-10000 and utcTime <= self.DateRange[1]:
            return True
        else:
            return False
        
    def run(self):
        variableDict = self.variableDict
        allData = {}
        for k in variableDict:
            allData[k] = []
        # open zip archive
        zipArchive = zipfile.ZipFile(self.zipName, 'r')
        tmpDir = tempfile.gettempdir()
        try:
            zipfiles = zipArchive.namelist()
            totalFile = len(zipfiles)
            # enumerate files in the .zip archive
            for i, zfname in enumerate(zipfiles):
                # look for .h5 files
                if zfname.endswith(".h5"):
                    if self.DateRange is not None:
                        if not self.analyzeFileName(zfname):
                            continue
                    zf = zipArchive.extract(zfname, tmpDir)
                    ip = tables.openFile(zf, "r")
                    self.progress = int(i*99/totalFile)
                    self.message = zfname
                    try:
                        for k in variableDict:
                            t = ip.getNode(k).read()
                            if set(variableDict[k]).issubset(t.dtype.names):
                                allData[k].append(t[variableDict[k]])
                    except:
                        self.message = "Error reading file, possibly missing specified groups or variables: %s" % zfname
                        self.progress = -1
                        self.fileHandle.close()
                        return 
                    finally:
                        ip.close()
                        os.remove(zf)  # delete the extracted temp file
        finally:
            zipArchive.close()
        filters = tables.Filters(complevel=1, fletcher32=True)
        for k in variableDict:
            data = np.concatenate([dm for dm in allData[k]])
            if 'DATE_TIME' in variableDict[k]:
                perm = np.argsort(data['DATE_TIME'])
                data = data[perm]
            elif 'timestamp' in variableDict[k]:
                perm = np.argsort(data['timestamp'])
                data = data[perm]
            elif 'time' in variableDict[k]:
                perm = np.argsort(data['time'])
                data = data[perm] 
            table = self.fileHandle.createTable(self.fileHandle.root, k[1:], data, filters=filters)
            table.flush()
        self.progress = 100
        self.fileHandle.close()

class ConcatenateFolder2File():
# HDF5 files and zip => HDF5
    def __init__(self, dirPath, fileName, variableDict):
        self.dirPath = dirPath
        self.fileName = fileName
        self.extension = os.path.splitext(fileName)[1]
        self.variableDict = variableDict
        self.DateRange = self.variableDict.pop("user_DateRange", None)
        self.PrivateLog = self.variableDict.pop("user_PrivateLog", None)
        self.TimeZone = self.variableDict.pop("user_TimeZone", None)
        self.largeFile = self.variableDict.pop("user_LargeDateset", False)
        if self.TimeZone is not None:
            self.TimeZone = pytz.timezone(self.TimeZone)
        self.progress = 0
        self.message = ""
        
    def openFile(self):
        try:
            if self.extension == ".h5":
                self.fileHandle = tables.openFile(self.fileName, "w")
                return True
            elif self.extension == ".dat":
                self.fileHandle = open(self.fileName, "w")
                return True
        except:
            pass
        return False
    
    def analyzeFileName(self, fileName):
        logName = fileName.split("/")[-1]
        timeStr = "".join(logName.split("-")[1:3])
        if timeStr.endswith("Z"):   # UTC time
            utcTime = datetimeTzToUnixTime(datetime.strptime(timeStr[:-1], "%Y%m%d%H%M%S"), pytz.utc)
        else:   # local time
            utcTime = datetimeTzToUnixTime(datetime.strptime(timeStr, "%Y%m%d%H%M%S"), self.TimeZone)
        if utcTime > self.DateRange[0]-10000 and utcTime <= self.DateRange[1]:
            return True
        else:
            return False
    
    def getFileList(self):
        def splitall(path):
            allparts = []
            while 1:
                parts = os.path.split(path)
                if parts[0] == path:  # sentinel for absolute paths
                    allparts.insert(0, parts[0])
                    break
                elif parts[1] == path: # sentinel for relative paths
                    allparts.insert(0, parts[1])
                    break
                else:
                    path = parts[0]
                    allparts.insert(0, parts[1])
            return allparts
            
        self.fileList = []
        self.zipFileDict = {}
        for root, dirs, files in os.walk(self.dirPath):
            if self.DateRange is not None and self.PrivateLog:
                # filter out folders that are out of selected date range
                canDelete = []
                for d in dirs:
                    dcomps = splitall(os.path.join(root, d))
                    k = -1
                    trailingDirName = []
                    for i in range(6):
                        try:
                            trailingDirName.append(int(dcomps[k]))
                            k -= 1
                        except ValueError:
                            break
                    if len(trailingDirName) >= 3:
                        trailingDirName.reverse()
                        dirDate = datetime(*trailingDirName[:3])
                        dirDate = datetimeTzToUnixTime(dirDate, self.TimeZone)
                        if dirDate < self.DateRange[0]-86400 or dirDate > self.DateRange[1]:
                            canDelete.append(d)
                for d in canDelete:
                    dirs.remove(d)
                
            dirs.sort()
            for fname in files:
                path = os.path.join(root, fname)
                if self.DateRange is None:
                    if fname.endswith(self.extension) or fname.endswith('.zip'):
                        self.fileList.append(path)
                else:
                    if fname.endswith(self.extension):
                        if self.analyzeFileName(fname):
                            self.fileList.append(path)
                    elif fname.endswith(".zip"):
                        self.zipFileDict[path] = []
                        with zipfile.ZipFile(path, 'r') as zfile:
                            zlist = [zz for zz in zfile.namelist() if zz.lower().endswith(self.extension)]
                            zlist.sort()
                            for zpath in zlist:    # search files in zip file
                                if self.analyzeFileName(zpath):
                                    self.zipFileDict[path].append(zpath)
                            if len(self.zipFileDict[path]) > 0:
                                self.fileList.append(path)
    
    def run(self):
        if self.extension == ".h5":
            if self.largeFile:
                self.run_largeFile()
            else:
                self.run_sort()
        elif self.extension == ".dat":
            self.run_dat()
    
    def run_dat(self):
        import pandas as pd
        
        variableDict = self.variableDict
        numCols = len(variableDict["results"])
        headingFormat = "%-26s" * (numCols) + "\n"
        dataFormat = "%-26f" * (numCols) + "\n"
        self.getFileList()
        totalFile = len(self.fileList)
        self.fileHandle.write(headingFormat % tuple(variableDict["results"]))
        for fileIndex, fname in enumerate(self.fileList):
            if fname.endswith('.dat'):
                df = pd.read_csv(fname, delim_whitespace=True)
                for row in df[variableDict["results"]].values:
                    self.fileHandle.write(dataFormat % tuple(row))
            self.progress = fileIndex*100.0 / totalFile
    
    def run_sort(self):
        """
        This method keeps data in the memory so it will cause memory error 
        if resulting file is too large (for example, 200Mb)
        One unique feature of this method is that data set is sorted by timestamp
        """
        variableDict = self.variableDict
        allData = {}
        for k in variableDict:
            allData[k] = []
            
        self.getFileList()
        totalFile = len(self.fileList)
        for fileIndex, fname in enumerate(self.fileList):
            if fname.endswith('.h5'):
                ip = tables.openFile(fname, "r")
                try:
                    for k in variableDict:
                        # read the whole table from file and then select columns, which could be inefficient
                        t = ip.getNode(k).read()    
                        if set(variableDict[k]).issubset(t.dtype.names):
                            allData[k].append(t[variableDict[k]])
                finally:
                    ip.close()
                self.message = fname
            elif fname.endswith(".zip"):
                with zipfile.ZipFile(fname, 'r') as zipArchive:
                    tmpDir = tempfile.gettempdir()
                    if self.DateRange is not None:
                        zlist = self.zipFileDict[fname]
                    else:
                        zlist = [zz for zz in zipArchive.namelist() if zz.lower().endswith(".h5")]
                        zlist.sort()
                    # enumerate files in the .zip archive
                    for zfname in zlist:
                        # extract the .h5 file from the zip archive into the temp dir
                        zf = zipArchive.extract(zfname, tmpDir)
                        ip = tables.openFile(zf, "r")
                        try:
                            for k in variableDict:
                                t = ip.getNode(k).read()
                                if set(variableDict[k]).issubset(t.dtype.names):
                                    allData[k].append(t[variableDict[k]])
                        finally:
                            ip.close()
                            os.remove(zf)  # delete the extracted temp file
                        self.message = zfname
            self.progress = int(fileIndex * 99 / totalFile)    # the extra 1% is for writing file

        # check whether any valid .h5 data files were found and concatenated
        if self.progress == 0:
            self.progress = -1
            self.message = "No HDF5 files found!"
            self.fileHandle.close()
            return
        self.message = "Writing output file..."

        filters = tables.Filters(complevel=1, fletcher32=True)
        try:
            for k in variableDict:
                data = np.concatenate([dm for dm in allData[k]])
                if 'DATE_TIME' in variableDict[k]:
                    perm = np.argsort(data['DATE_TIME'])
                    data = data[perm]
                elif 'timestamp' in variableDict[k]:
                    perm = np.argsort(data['timestamp'])
                    data = data[perm]
                elif 'time' in variableDict[k]:
                    perm = np.argsort(data['time'])
                    data = data[perm] 
                table = self.fileHandle.createTable(self.fileHandle.root, k[1:], data, filters=filters)
                table.flush()
            self.progress = 100
        except Exception, e:
            self.progress = -1
            self.message = "%s: %s" % (Exception, e)
        finally:
            self.fileHandle.close()
        
    def run_largeFile(self):
        variableDict = self.variableDict
        filters = tables.Filters(complevel=1, fletcher32=True)
        allData = {}
            
        self.getFileList()
        totalFile = len(self.fileList)
        for fileIndex, fname in enumerate(self.fileList):
            if fname.endswith('.h5'):
                ip = tables.openFile(fname, "r")
                try:
                    for k in variableDict:
                        t = ip.getNode(k).read()
                        if set(variableDict[k]).issubset(t.dtype.names):
                            if k not in allData:
                                allData[k] = self.fileHandle.createTable(self.fileHandle.root, k[1:], t[variableDict[k]], filters=filters)
                            else:
                                allData[k].append(t[variableDict[k]])
                            allData[k].flush()
                finally:
                    ip.close()
                self.message = fname
            elif fname.endswith(".zip"):
                with zipfile.ZipFile(fname, 'r') as zipArchive:
                    tmpDir = tempfile.gettempdir()
                    if self.DateRange is not None:
                        zlist = self.zipFileDict[fname]
                    else:
                        zlist = [zz for zz in zipArchive.namelist() if zz.lower().endswith(".h5")]
                        zlist.sort()
                    # enumerate files in the .zip archive
                    for zfname in zlist:
                        # extract the .h5 file from the zip archive into the temp dir
                        zf = zipArchive.extract(zfname, tmpDir)
                        ip = tables.openFile(zf, "r")
                        try:
                            for k in variableDict:
                                t = ip.getNode(k).read()
                                if set(variableDict[k]).issubset(t.dtype.names):
                                    if k not in allData:
                                        allData[k] = self.fileHandle.createTable(self.fileHandle.root, k[1:], t[variableDict[k]], filters=filters)
                                    else:
                                        allData[k].append(t[variableDict[k]])
                                    allData[k].flush()
                        finally:
                            ip.close()
                            os.remove(zf)  # delete the extracted temp file
                        self.message = zfname
            self.progress = int(fileIndex * 99 / totalFile)    # the extra 1% is for writing file

        # check whether any valid .h5 data files were found and concatenated
        if self.progress == 0:
            self.progress = -1
            self.message = "No HDF5 files found!"
        else:
            self.progress = 100
        self.fileHandle.close()        