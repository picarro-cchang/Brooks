"""Access SQA3 database to get report information and check aggregation algorithm"""

import time
from pyodbc import connect
from numpy import arctan, arctan2, asarray, cos, pi, sin, sqrt, tan

def distVincenty(lat1, lon1, lat2, lon2):
    # WGS-84 ellipsiod. lat and lon in DEGREES
    a = 6378137
    b = 6356752.3142
    f = 1/298.257223563
    toRad = pi/180.0
    L = (lon2-lon1)*toRad
    U1 = arctan((1-f) * tan(lat1*toRad))
    U2 = arctan((1-f) * tan(lat2*toRad))
    sinU1 = sin(U1)
    cosU1 = cos(U1)
    sinU2 = sin(U2)
    cosU2 = cos(U2)

    Lambda = L
    iterLimit = 100
    for _ in range(iterLimit):
        sinLambda = sin(Lambda)
        cosLambda = cos(Lambda)
        sinSigma = sqrt((cosU2*sinLambda) * (cosU2*sinLambda) +
                        (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda))
        if sinSigma == 0:
            return 0  # co-incident points
        cosSigma = sinU1*sinU2 + cosU1*cosU2*cosLambda
        sigma = arctan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha*sinAlpha
        if cosSqAlpha == 0:
            cos2SigmaM = 0
        else:
            cos2SigmaM = cosSigma - 2*sinU1*sinU2/cosSqAlpha
        C = f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha))
        lambdaP = Lambda
        Lambda = L + (1-C) * f * sinAlpha * \
          (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)))
        if abs(Lambda-lambdaP) <= 1.e-12: break
    else:
        raise ValueError("Failed to converge")

    uSq = cosSqAlpha * (a*a - b*b) / (b*b)
    A = 1 + uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)))
    B = uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)))
    deltaSigma = B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)-
                                            B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)))
    return b*A*(sigma-deltaSigma)

class SQA3Database(object):
    """ Access the database  """
    def __init__(self, *args, **kwargs):
        self.server = "20.20.130.238"
        self.database = "SurveyorSQA3"
        self.uid = "awssa"
        self.password = "j!RuL1Gd7A"
        if args:
            raise ValueError("Only keyword arguments are allowed in constructor")
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise ValueError("%s has no attribute %s" % (type(self).__name__, key))

    def _open_db_connection(self):
        """Open connection to database and return a cursor"""
        connection = connect('DRIVER={SQL Server}; SERVER=%s; DATABASE=%s; UID=%s; PWD=%s' %
                             (self.server, self.database, self.uid, self.password))
        return connection.cursor()
    
    def get_report(self, title):
        cursor = self._open_db_connection()
        query = """
            SELECT id, ReportTitle, DateStarted
            FROM [SurveyorSQA3].[dbo].[Report]
            WHERE [ReportTitle] LIKE '%s'
        """ % title
        cursor.execute(query)
        results = []
        for row in cursor:
            report_id, title, date_start = row
            results.append({"title":title, "date_start":date_start, "report_id":report_id})
        return results

    def get_report_peaks(self, report_id):
        cursor = self._open_db_connection()
        verdicts = ["ERROR", "NATURAL_GAS", "NOT_NATURAL_GAS", "POSSIBLE_NATURAL_GAS", "VEHICLE_EXHAUST", "BELOW_THRESHOLD", "EXCLUDED", "EMPTY"]

        query = """
            SELECT EpochTime, PeakNumber, Amplitude, CH4, GpsLatitude, GpsLongitude, PassedAutoThreshold, EthaneRatio, EthaneRatioSdev, Disposition,
            ClassificationConfidence, AggregatedEthaneRatio, AggregatedEthaneRatioSdev, AggregatedDisposition, AggregatedClassificationConfidence
            FROM [SurveyorSQA3].[dbo].[ReportPeak]
            WHERE [ReportId] = '%s' ORDER BY [PeakNumber]
        """ % report_id
        cursor.execute(query)
        results = []
        for row in cursor:
            EpochTime, PeakNumber, Amplitude, CH4, GpsLatitude, GpsLongitude, PassedAutoThreshold, EthaneRatio, EthaneRatioSdev, Disposition, ClassificationConfidence, \
                AggregatedEthaneRatio, AggregatedEthaneRatioSdev, AggregatedDisposition, AggregatedClassificationConfidence = row
            results.append(dict(EPOCH_TIME=EpochTime, VERDICT=verdicts[Disposition], AMPLITUDE=Amplitude, ETHANE_RATIO_SDEV=EthaneRatioSdev, GPS_ABS_LAT=GpsLatitude,
                GPS_ABS_LONG=GpsLongitude, ETHANE_RATIO=EthaneRatio, PEAK_NUM=PeakNumber, PASSED_THRESHOLD=1 if PassedAutoThreshold else 0, CONFIDENCE=ClassificationConfidence,
                AGG_ETHANE_RATIO=AggregatedEthaneRatio, AGG_ETHANE_RATIO_SDEV=AggregatedEthaneRatioSdev, AGG_VERDICT=verdicts[AggregatedDisposition], 
                AGG_CONFIDENCE=AggregatedClassificationConfidence))
        return results
         
if __name__ == "__main__":
    db = SQA3Database()
    name = raw_input('Report Title: ').strip()
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
    peaks = db.get_report_peaks(report_id)
    # Check that all peaks are above threshold
    print "Checking all peaks passed threshold"
    for peak in peaks:
        if not peak["PASSED_THRESHOLD"]:
            print "Peak %d did not pass threshold" % peak["PEAK_NUM"]  
    print "Checking minimum distances between peaks which are not vehicle exhaust"
    lat_list = []
    lng_list = []
    for peak in peaks:
        if peak["VERDICT"] != "VEHICLE_EXHAUST":
            lat_list.append(peak["GPS_ABS_LAT"])
            lng_list.append(peak["GPS_ABS_LONG"])
    print "Number of peaks to check: %d" % len(lat_list)
    # Check representatives are further apart than exclusion radius
    min_dist = float('inf')
    for i, (lat1, lng1) in enumerate(zip(lat_list, lng_list)):
        for (lat2, lng2) in zip(lat_list[:i], lng_list[:i]):
            min_dist = min(min_dist, distVincenty(lat1, lng1, lat2, lng2))
    print "Minimum distance: %.2f meters" % (min_dist, )
    