"""Access SQA3 database to get report information and check aggregation algorithm"""

import sys
import time
from pyodbc import connect
import numpy as np
from numpy import arctan, arctan2, asarray, cos, pi, sin, sqrt, tan
from ReportExclusionRadiusTest import SQA3Database, distVincenty
from Host.Pipeline.EthaneAggregation import EthaneAggregation
from traitlets.config import Config

def get_peaks(name):
    results = db.get_report(name)
    report_id = None
    if len(results) == 1:
        print "%s at %s" % (results[0]["title"], results[0]["date_start"])
        ok = raw_input("Use this report? [Y/n]").strip().lower()
        if len(ok) == 0 or ok[0] == 'y':
            report_id = results[0]["report_id"]
        else:
            sys.exit(1)
    elif len(results) > 1:
        for i, result in enumerate(results):
            print "%d) %s at %s" % (i+1, results[i]["title"], results[i]["date_start"])
        while True:
            ok = raw_input("Enter row number of report: ").strip()
            if len(ok) == 0:
                sys.exit(1)
            try:
                ok = int(ok)
                if 0 < ok <= len(results):
                    report_id = results[ok-1]["report_id"]
                    break
            except:
                continue
    else:
        print "Report not found"
        exit(1)
    return db.get_report_peaks(report_id)
         
if __name__ == "__main__":
    db = SQA3Database()
    print "Specify two reports with identical parameters, except for exclusion radius"

    peaks0 = get_peaks(raw_input('Zero exclusion radius Report Title: ').strip())
    peaksER = get_peaks(raw_input('Non-zero exclusion radius Report Title: ').strip())
    excl_radius = float(raw_input('Exclusion radius for second report: '))

    print
    print "Checking that all peaks in second report are present in the first"
    peak_times = np.asarray([peak["EPOCH_TIME"] for peak in peaks0])
    peak_numbers = np.asarray([peak["PEAK_NUM"] for peak in peaks0])
    perm = np.argsort(peak_times)
    peak_times = peak_times[perm]
    peak_numbers = peak_numbers[perm]

    peak_map = {}
    matches0 = []
    for peak in peaksER:
        epoch_time = peak["EPOCH_TIME"]
        min_pos = np.argmin(abs(peak_times - epoch_time))
        ok = True
        if abs(peak_times[min_pos] - epoch_time) > 1.0:
            ok = False
            print "Peak number %d from second file not in first" % (peak["PEAK_NUM"],)
            break
        else:
            peak_map[peak["PEAK_NUM"]] = (perm[min_pos], peak_numbers[min_pos])

            match = peaks0[perm[min_pos]]
            exact_list = ["VERDICT", "PASSED_THRESHOLD"]
            for e in exact_list:
                if peak[e] != match[e]:
                    ok = False
            approx_list = ["AMPLITUDE", "ETHANE_RATIO_SDEV", "GPS_ABS_LAT", "GPS_ABS_LONG", "ETHANE_RATIO", "CONFIDENCE"]
            for e in approx_list:
                if abs(peak[e] - match[e]) > 1e-5:
                    ok = False
        if ok:
            matches0.append(perm[min_pos])
        else:
            print "--------------------------- NON-MATCHING PEAK ---------------------------" 
            print "Peak from zero ER file", match
            print "Peak from non-zero ER file", peak
            
    print
    print "Comparing results with Python code" 
    config = Config()
    config.EthaneClassifier.nng_lower = 0.0  # Lower limit of ratio for not natural gas hypothesis
    config.EthaneClassifier.nng_upper = 0.1e-2  # Upper limit of ratio for not natural gas hypothesis
    config.EthaneClassifier.ng_lower = 2e-2  # Lower limit of ratio for natural gas hypothesis
    config.EthaneClassifier.ng_upper = 10e-2  # Upper limit of ratio for natural gas hypothesis
    config.EthaneClassifier.nng_prior = 0.2694  # Prior probability of not natural gas hypothesis
    #config.EthaneClassifier.nng_prior = 0.27  # Prior probability of not natural gas hypothesis
    config.EthaneClassifier.thresh_confidence = 0.9  # Threshold confidence level for definite hypothesis
    config.EthaneClassifier.reg = 0.05  # Regularization parameter
    config.VehicleExhaustClassifier.ve_ethylene_sdev_factor = 2.0  # Ethylene standard deviation factor for vehicle exhaust
    config.VehicleExhaustClassifier.ve_ethylene_lower = 0.15  # Ethylene lower level for vehicle exhaust
    config.VehicleExhaustClassifier.ve_ethane_sdev_factor = 0.0  # Ethane standard deviation factor for vehicle exhaust
    config.VehicleExhaustClassifier.ve_ethane_upper = 10.0  # Ethane upper level for vehicle exhaust

    # Pass the peaks from the first file through Python processor
    ea  = EthaneAggregation(indications=peaks0, exclusion_radius=excl_radius, config=config)
    sorted_indications = ea.process()

    # Go through the sorted indications and compare them with the results from the second file

    matchesP = []
    peak_times = np.asarray([peak["EPOCH_TIME"] for peak in peaksER])
    perm = np.argsort(peak_times)
    peak_times = peak_times[perm]
    missing = []
    python_peaks = 0
    for indication in sorted_indications:
        if indication["AGG_VERDICT"] not in ["EXCLUDED", "BELOW_THRESHOLD"]:
            python_peaks += 1
            # We should find it in peaksER        
            epoch_time = indication["EPOCH_TIME"]
            min_pos = np.argmin(abs(peak_times - epoch_time))
            if abs(peak_times[min_pos] - epoch_time) > 1.0:
                missing.append(indication.copy())
            else:
                peak = peaksER[perm[min_pos]]
                exact_list = ["AGG_VERDICT"]
                ok = True
                for e in exact_list:
                    if peak[e] != indication[e]:
                        ok = False
                if peak["AGG_VERDICT"] != "VEHICLE_EXHAUST":
                    approx_list = ["AGG_ETHANE_RATIO", "AGG_ETHANE_RATIO_SDEV", "AGG_CONFIDENCE"]
                    for e in approx_list:
                        if abs(peak[e] - indication[e]) > 1e-5:
                            ok = False
                if ok:
                    matchesP.append(perm[min_pos])
                else:
                    print "========================== NON-MATCHING PEAK ==========================" 
                    print "Peak from C# code", peak
                    print "Peak from Python", indication
            
    if missing:
        for peak in missing:
            print "========================== MISSING PEAK ==========================" 
            print "Peak from Python", indication
            

    print "Matched %d out of %d peaks from non-zero ER file" % (len(matches0), len(peaksER))       
    print "Matched %d out of %d peaks between Python and non-zero ER file" % (len(matchesP), len(peaksER))
    print "Total number of Python peaks %d" % (python_peaks,)
    if missing:
        print "%d peaks from Python are missing from non-zero ER file" % (len(missing),)