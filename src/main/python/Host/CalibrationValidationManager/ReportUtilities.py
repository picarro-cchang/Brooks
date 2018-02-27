
import matplotlib
matplotlib.use("SVG")
import matplotlib.pyplot as plt

import io
import pprint
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
    report = ""
    # report = "Settings\n"
    # report += pprint.pformat(settings)
    # report += "\nResults\n"
    # report += pprint.pformat(results)
    # report += "\n"
    for e, g in sorted(reference_gases.items()): # sorted by GAS0, GAS1, GAS2 etc.
        report += g.getFormattedGasDetails(e)
    report += "\n"
    return report


def create_report(settings, reference_gases, results, obj):
    img = QtGui.QImage()
    img.loadFromData(obj.getvalue())

    myDoc = QtGui.QTextDocument("This is a demo document")
    font = myDoc.defaultFont()
    font.setFamily("Courier New") # need a monospace font to line up numeric data
    myDoc.setDefaultFont(font)

    myDoc.setPlainText(fill_report_template(settings, reference_gases, results))
    cursor = QtGui.QTextCursor(myDoc)
    cursor.movePosition(QtGui.QTextCursor.End)
    cursor.insertImage(img)

    printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
    printer.setPageSize(QtGui.QPrinter.Letter)
    printer.setColorMode(QtGui.QPrinter.Color)
    printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
    printer.setOutputFileName("demo_doc.pdf")
    myDoc.print_(printer)
    return myDoc