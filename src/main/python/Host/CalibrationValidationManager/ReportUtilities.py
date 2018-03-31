
import matplotlib
matplotlib.use("SVG")
import matplotlib.pyplot as plt

import io
import glob
import os
import re
import numpy
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
    if "Linear_Regression_Validation" in settings["Analysis"]:
        report += get_formatted_linear_regression_pass_fail_summary(results)
        report += get_formatted_linear_regression_results(results)
    if "Span_Validation" in settings["Analysis"]:
        report += get_formatted_span_pass_fail_summary(results)
    if "One_Point_Validation" in settings["Analysis"]:
        report += get_formatted_one_point_pass_fail_summary(results)

    report += get_formatted_task_details(settings, reference_gases, results)

    for e, g in sorted(reference_gases.items()): # sorted by GAS0, GAS1, GAS2 etc.
        report += g.getFormattedGasDetails(e)
    report += "\n"
    return report

def get_formatted_user_information(results):
    str = "{0} {1} {0}\n".format("=" * 15, "Report Authentication")
    str += "{0:20}:{1}\n".format("Username", results["username"])
    str += "{0:20}:{1}\n".format("Full name", results["fullname"])
    str += "{0:20}:{1}\n".format("Start time", results["start_time"])
    str += "{0:20}:{1}\n".format("End time", results["end_time"])
    return str

def get_formatted_span_pass_fail_summary(results):
    str = "{0} {1} {0}\n".format("=" * 15, "Summary")
    str += "|{0:10}|{1:20}|{2:15}|{3:10}|\n".format("Test", "Acceptance Criteria", "Result", "Status")

    # Sort to show the worst result.
    # Sort first to put all "Fails" up front, then sort on measurement with largest deviation from 0.0.
    if "Yes" in results["Zero_Air"]:
        sorted_zero_test = sorted(results["Zero_Air_Test"], key=lambda x: x[1])
        sorted_zero_test.sort(key=lambda x: x[1], reverse=True)
        (zeroMeas, zeroStatus, zeroMin, zeroMax) = sorted_zero_test[0]  # NEED TO RPT LARGEST AWAY FROM 0.0
        str += "|{0:10}|>{1:5}ppb <{2:5}ppb|{3:15}|{4}|\n".format("Zero Air", zeroMin, zeroMax, zeroMeas, zeroStatus)

    # Sort the percent deviation results so that we show the worst result.
    sorted_dev_test = sorted(results["Deviation_Test"], key=lambda x: float(x[1]), reverse=True)
    (measConc, percent_deviation, percent_status, percent_acceptance) = sorted_dev_test[0]
    str += "|{0:10}|<{1:10}%|{2:15}|{3:10}|\n".format("Deviation", percent_acceptance, percent_deviation, percent_status)
    return str

def get_formatted_one_point_pass_fail_summary(results):
    str = "{0} {1} {0}\n".format("=" * 15, "Summary")
    str += "|{0:10}|{1:20}|{2:15}|{3:10}|\n".format("Test", "Acceptance Criteria", "Result", "Status")
    # Sort the percent deviation results so that we show the worst result.
    sorted_dev_test = sorted(results["Deviation_Test"], key=lambda x: float(x[1]), reverse=True)
    (measConc, percent_deviation, percent_status, percent_acceptance) = sorted_dev_test[0]
    str += "|{0:10}|<{1:10}%|{2:15}|{3:10}|\n".format("Deviation", percent_acceptance, percent_deviation, percent_status)
    return str

def get_formatted_linear_regression_pass_fail_summary(results):
    str = "{0} {1} {0}\n".format("=" * 15, "Summary")
    str += "|{0:10}|{1:20}|{2:15}|{3:10}|\n".format("Test", "Acceptance Criteria", "Result", "Status")

    # Sort to show the worst result.
    # Sort first to put all "Fails" up front, then sort on measurement with largest deviation from 0.0.
    if "Yes" in results["Zero_Air"]:
        sorted_zero_test = sorted(results["Zero_Air_Test"], key=lambda x: x[1])
        sorted_zero_test.sort(key=lambda x: x[1], reverse=True)
        (zeroMeas, zeroStatus, zeroMin, zeroMax) = sorted_zero_test[0]  # NEED TO RPT LARGEST AWAY FROM 0.0
        str += "|{0:10}|>{1:5}ppb <{2:5}ppb|{3:15}|{4}|\n".format("Zero Air", zeroMin, zeroMax, zeroMeas, zeroStatus)

    (slope, slope_status, slope_min, slope_max) = results["Slope_Test"]
    str += "|{0:10}|>{1:5} <{2:5}|{3}|{4}|\n".format("Slope", slope_min, slope_max, slope, slope_status)

    # Sort the percent deviation results so that we show the worst result.
    sorted_dev_test = sorted(results["Deviation_Test"], key=lambda x: float(x[1]), reverse=True)
    (measConc, percent_deviation, percent_status, percent_acceptance) = sorted_dev_test[0]
    str += "|{0:10}|<{1:10}%|{2:15}|{3:10}|\n".format("Deviation", percent_acceptance, percent_deviation, percent_status)
    return str

def get_formatted_linear_regression_results(results):
    str = "{0} {1} {0}\n".format("=" * 15, "Linear Regression")
    str += "{0:30}: {1}\n".format("Linear Regression slope", results["slope"])
    str += "{0:30}: {1}\n".format("Linear Regression intercept", results["intercept"])
    str += "{0:30}: {1}\n".format("Linear Regression R^2", results["r2"])
    return str

def get_formatted_task_details(settings, reference_gases, results):
    line = "|{0}|\n".format("-" * 80)
    str = "|{0} {1} {2} {0}|\n".format("=" * 30, results["Gas_Name"], "Measurements")
    str += "|{0:^15}|{1:^15}|{2:^15}|{3:^15}|{4:^15}|\n".format("Gas Source",
                                                        "Measured PPM",
                                                        "Measured Std.",
                                                        "Reference PPM",
                                                        "% Deviation")
    str += line
    for idx, value in enumerate(results["Gas"]):
        percent_deviation = 0
        if not numpy.isnan(results["Percent_Deviation"][idx]):
            percent_deviation = results["Percent_Deviation"][idx]
        str += "|{0:^15}|{1:15.5f}|{2:15.5f}|{3:15.5f}|{4:15.5f}|\n".format(value,
                                                                  results["Meas_Conc"][idx],
                                                                  results["Meas_Conc_Std"][idx],
                                                                  results["Ref_Conc"][idx],
                                                                  percent_deviation)
        str += line
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
    font.setFamily("Courier New") # need a monospace font to line up numeric data
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