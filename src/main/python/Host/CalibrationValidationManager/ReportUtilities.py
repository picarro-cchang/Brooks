
import matplotlib
matplotlib.use("SVG")
import matplotlib.pyplot as plt

import io
import glob
import os
import re
import numpy
from terminaltables import AsciiTable
from datetime import datetime, date
from PyQt4 import QtCore, QtGui

def make_plot(xdata, ydata, yfitting, title, xlabel, ylabel):
    """
    Plot measured vs reference along with the regression.
    Typical usecase is plotting measured gas concentrations against known
    standards.
    :param xdata: Reference concentrations
    :param ydata: Measured concentrations
    :param yfitting: y regression points (x's on xdata)
    :param title:
    :param xlabel:
    :param ylabel:
    :return:
    """
    fig = plt.figure(figsize=(6, 5), facecolor=(1, 1, 1))
    ax = fig.gca()
    ax.plot(xdata, ydata, 'bo', xdata, yfitting, 'r-')
    ax.grid('on')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    max_x, min_x = max(xdata), min(xdata)
    offset = (max_x - min_x) * 0.05
    ax.set_xlim([min_x - offset, max_x + offset])
    ax.set_ylim([min_x - offset, max_x + offset])

    # Save matplotlib to an in memory png and pass it to
    # the Qt based report generator.
    buf = io.BytesIO()  # .StringIO()
    plt.savefig(buf, format='png')
    return buf

def fill_report_template(settings, reference_gases, results):
    report = get_formatted_user_information(results)
    report += "\n"
    if "Linear_Regression_Validation" in settings["Analysis"]:
        report += get_formatted_pass_fail_summary(results,
                                                  show_zero_air_test=True,
                                                  show_slope_test=True,
                                                  show_percent_deviation_test=True)
        report += "\n"
        report += get_formatted_linear_regression_results(results)
    if "Span_Validation" in settings["Analysis"]:
        report += get_formatted_pass_fail_summary(results,
                                                  show_zero_air_test=True,
                                                  show_slope_test=False,
                                                  show_percent_deviation_test=True)
    if "One_Point_Validation" in settings["Analysis"]:
        report += get_formatted_pass_fail_summary(results,
                                                  show_zero_air_test=False,
                                                  show_slope_test=False,
                                                  show_percent_deviation_test=True)
    report += "\n"
    report += get_formatted_task_details(settings, reference_gases, results)
    report += "\n"

    for e, g in sorted(reference_gases.items()): # sorted by GAS0, GAS1, GAS2 etc.
        report += g.getFormattedGasDetails(e)
        report += "\n"
    report += "\n"
    return report

def get_formatted_user_information(results):
    table_data = []
    table_data.append(["Username", results["username"]])
    table_data.append(["Full name", results["fullname"]])
    table_data.append(["Instrument SN", "TBD"])
    table_data.append(["Start time", results["start_time"]])
    table_data.append(["End time", results["end_time"]])
    table = AsciiTable(table_data)
    table.title = "Report Authentication"
    table.inner_heading_row_border = False
    return table.table + "\n"

def get_formatted_pass_fail_summary(results,
                                    show_zero_air_test = False,
                                    show_slope_test = False,
                                    show_percent_deviation_test = True):
    table_data = []
    table_data.append(["Test", "Acceptance Criteria", "Result", "Status"])

    if show_zero_air_test:
        # Sort to show the worst result.
        # Sort first to put all "Fails" up front, then sort on measurement with largest deviation from 0
        if results["Zero_Air_Test"]:
            sorted_zero_test = sorted(results["Zero_Air_Test"], key=lambda x: x[1])
            sorted_zero_test.sort(key=lambda x: x[1], reverse=True)
            (zeroMeas, zeroStatus, zeroMin, zeroMax) = sorted_zero_test[0]  # NEED TO RPT LARGEST AWAY FROM 0.0
            table_data.append(["Zero Air",
                               "{0:5.3f} ppm < [{1}] < {2:5.3f} ppm".format(zeroMin, results["Gas_Name"], zeroMax),
                               "{0:.4f}".format(zeroMeas),
                               "{0}".format(zeroStatus)])

    if show_slope_test:
        (slope, slope_status, slope_min, slope_max) = results["Slope_Test"]
        table_data.append(["Slope Test",
                           "{0:5.3f} < m < {1:5.3f}".format(slope_min, slope_max),
                           "{0:.4f}".format(slope),
                           "{0}".format(slope_status)])

    if show_percent_deviation_test:
        # Sort the percent deviation results so that we show the worst result.
        sorted_dev_test = sorted(results["Deviation_Test"], key=lambda x: float(x[1]), reverse=True)
        if sorted_dev_test:
            (measConc, percent_deviation, percent_status, percent_acceptance) = sorted_dev_test[0]
            table_data.append(["% Deviation",
                              "%dev < {0:5.3f}".format(percent_acceptance),
                               "{0:.4f}".format(percent_deviation),
                               "{0}".format(percent_status)])

    table = AsciiTable(table_data)
    table.title = "Pass/Fail Summary"
    table.justify_columns[0] = "center"
    table.justify_columns[1] = "center"
    table.justify_columns[2] = "right"
    table.justify_columns[3] = "center"
    return table.table + "\n"

def get_formatted_linear_regression_results(results):
    table_data = []
    table_data.append(["Slope", "{0:15.5f}".format(results["slope"])])
    table_data.append(["Intercept", "{0:15.5f}".format(results["intercept"])])
    table_data.append(["R^2", "{0:15.5f}".format(results["r2"])])
    table = AsciiTable(table_data)
    table.title = "Linear Regression"
    table.inner_heading_row_border = False
    return table.table + "\n"

def get_formatted_task_details(settings, reference_gases, results):
    str = ""
    table_data = []
    table_data.append(["Gas Source", "Measured PPM", "Measured Std.", "Ref. ppm", "Ref. Acc %", "% Deviation"])
    for idx, value in enumerate(results["Gas"]):
        percent_deviation = 0
        if not numpy.isnan(results["Percent_Deviation"][idx]):
            percent_deviation = results["Percent_Deviation"][idx]
        table_data.append([value,
                           "{0:>.4f}".format(results['Meas_Conc'][idx]),
                           "{0:>.4f}".format(results['Meas_Conc_Std'][idx]),
                           "{0:>.4f}".format(results['Ref_Conc'][idx]),
                           "{0:^8}".format(results['Ref_Acc'][idx]),
                           "{0:>.4f}".format(percent_deviation)])
    table = AsciiTable(table_data)
    table.title = results["Gas_Name"] + " " + "Measurements"
    table.justify_columns[0] = "center"
    table.justify_columns[1] = "right"
    table.justify_columns[2] = "right"
    table.justify_columns[3] = "right"
    table.justify_columns[4] = "center"
    table.justify_columns[5] = "right"
    str += table.table + "\n"
    return str

def getDateNow():
    """
    Return the current date in YYYYMMDD format.
    The timezone is the local (system) setting.
    """
    dateStr = date.today().strftime("%Y%m%d")
    return dateStr

def getFileCounter(path, which = 0):
    """
    Examine the files in the directory defined by 'path' and determine
    the counter to apply to the next file to be created.

    'which' determines this method returns the counter for the oldest
    file in the path, the newest (or current), or the next (newest + 1).
    The default is to return the next file counter for new file creation.

    which = 0 : next
    which = 1 : newest
    which = 2 : oldest
    """

    # If there are no file in the path, start with file '0000'
    nextCounter = 0

    # '*' allows matching to filenames that have a compression extension
    # such as '.gz.'
    generalFileName = getDateNow() + "_CH4_" + "[0-9][0-9][0-9][0-9]" + "*"
    fileList = glob.glob(os.path.join(path, generalFileName))

    # If one or more valid counters are found, return the max + 1
    # as a zero padded 4 character string.
    # If no matches are found, we start with the first file '0000'.
    #
    myRegExp = r"(\d{4})\." + "pdf"
    counterList = [ int(re.search(myRegExp, x).group(1)) for x in fileList]
    if counterList:
        if 0 == which:
            nextCounter = max(counterList) + 1
        elif 1 == which:
            nextCounter = max(counterList)
        elif 2 == which:
            nextCounter = min(counterList)
        else:
            print("Error in FileManager::getFileCounter")
    return str(nextCounter).zfill(4)

def create_report(settings, reference_gases, results, obj=None):

    destinationPath = "/home/picarro/I2000/Log/ValidationReport"
    counter = getFileCounter(destinationPath, 0)
    outputFileName = "{0}/{1}_{2}_{3}.pdf".format(destinationPath, getDateNow(), settings["Data_Key"], counter)

    if obj:
        img = QtGui.QImage()
        img.loadFromData(obj.getvalue())

    myDoc = QtGui.QTextDocument("This is a demo document")
    font = myDoc.defaultFont()
    font.setFamily("Courier New")   # need a monospace font to line up numeric data
    font.setPointSize(8)            # default is 11pt and is too big to fit the task summary on 8x11 paper
    myDoc.setDefaultFont(font)

    myDoc.setPlainText(fill_report_template(settings, reference_gases, results))
    cursor = QtGui.QTextCursor(myDoc)
    cursor.movePosition(QtGui.QTextCursor.End)
    if obj:
        cursor.insertImage(img)

    printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
    printer.setPageSize(QtGui.QPrinter.Letter)
    printer.setColorMode(QtGui.QPrinter.Color)
    printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
    printer.setOutputFileName(outputFileName)
    myDoc.print_(printer)
    return (outputFileName, myDoc)