import json
import os
import shutil
import subprocess
import time
import unittest
from MobileKit.ReportGen.ReportCommon import Bunch, getMsUnixTime, getTicket
from MobileKit.ReportGen.ReportCommon import msUnixTimeToTimeString, ReportApiService, RptGenStatus
from MobileKit.ReportGen.ReportCommon import timeStringAsDirName

TEST_ROOT = os.path.join("C:\\", "temp", "ReportGen")


def raiseOnError(result):
    if 'error' in result and result['error'] is not None:
        raise RuntimeError(result['error'])
    result = result['return']
    if 'error' in result and result['error'] is not None:
        raise RuntimeError(result['error'])
    return result

GLOBALS = Bunch(
    reportServer=None,
    reportApi=None
)


class TestTimeStrings(unittest.TestCase):
    def testGetTime(self):
        self.assertTrue(abs(getMsUnixTime() - 1000 * time.time()) < 5)

    def testKnownTimeString(self):
        msUnixTime = getMsUnixTime("1971-01-01T00:00:00.000Z")
        self.assertEqual(msUnixTime, 365 * 24 * 3600 * 1000)

    def testGetTimeString(self):
        msUnixTime = getMsUnixTime()
        timeString = msUnixTimeToTimeString(msUnixTime)
        self.assertEqual(msUnixTime, getMsUnixTime(timeString))

    def testBadTimeString(self):
        self.assertRaises(ValueError, getMsUnixTime, "Bad")
        self.assertRaises(ValueError, getMsUnixTime, "1971-01-01T00:00:00.000A")
        self.assertRaises(ValueError, getMsUnixTime, "1971-01-01T00:00:00")


class TestRptGen(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)

    def testSubmit(self):
        contents = json.dumps({"instructions_type": "ignore", "aux": "dummy"})
        qryparms = {'qry': 'submit', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["rpt_contents_hash"], getTicket(contents))
        rpt_start_ts = result["rpt_start_ts"]
        self.assertEqual(rpt_start_ts, result["request_ts"])
        self.assertIn(result["status"], [RptGenStatus.IN_PROGRESS, RptGenStatus.NOT_STARTED])
        self.assertTrue(abs(getMsUnixTime(result["request_ts"]) - getMsUnixTime()) < 500)
        # Submit the same project a little later. We should detect it as a duplicate.
        time.sleep(2.0)
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["rpt_contents_hash"], getTicket(contents))
        self.assertEqual(result["rpt_start_ts"], rpt_start_ts)
        self.assertNotEqual(rpt_start_ts, result["request_ts"])
        self.assertEqual(RptGenStatus.DONE, result["status"])
        self.assertTrue(abs(getMsUnixTime(result["request_ts"]) - getMsUnixTime()) < 500)
        # Submit the project a little later with a force flag. This should be executed.
        time.sleep(2.0)
        qryparms["force"] = True
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["rpt_contents_hash"], getTicket(contents))
        self.assertEqual(result["rpt_start_ts"], result["request_ts"])
        self.assertIn(result["status"], [RptGenStatus.IN_PROGRESS, RptGenStatus.NOT_STARTED])
        self.assertTrue(abs(getMsUnixTime(result["request_ts"]) - getMsUnixTime()) < 500)
        # Check for the existence of the directories that indicate the two projects were
        #  started
        baseDir = os.path.join(TEST_ROOT, getTicket(contents))
        self.assertTrue(os.path.exists(baseDir))
        self.assertTrue(os.path.exists(os.path.join(baseDir, timeStringAsDirName(rpt_start_ts))))
        self.assertTrue(os.path.exists(os.path.join(baseDir, timeStringAsDirName(result["rpt_start_ts"]))))
        #
        time.sleep(2.0)
        # Test getting status
        qryparms = {'qry': 'getStatus', 'contents_hash': result["rpt_contents_hash"],
                    'start_ts': result["rpt_start_ts"]}
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["status"], RptGenStatus.DONE)
        # Test getting status
        qryparms = {'qry': 'getStatus', 'contents_hash': result["rpt_contents_hash"],
                    'start_ts': rpt_start_ts}
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["status"], RptGenStatus.DONE)
        self.assertEqual(result["start_ts"], rpt_start_ts)

    def testBadJsonSubmit(self):
        contents = 'Bad Contents (not JSON)'
        qryparms = {'qry': 'submit', 'contents': contents}
        # Submit a project via the report server
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertTrue("ValueError: Instructions are not in valid JSON notation" in e.exception.__str__())

    def testInvalidInstructionsSubmit(self):
        contents = json.dumps({"instructions_type": "invalid"})
        qryparms = {'qry': 'submit', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        time.sleep(1)
        qryparms = {'qry': 'getStatus', 'contents_hash': result["rpt_contents_hash"],
                    'start_ts': result["rpt_start_ts"]}
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["status"], RptGenStatus.FAILED)
        self.assertIn('Bad instructions_type', result["msg"])

    def testGetPathDataMissingInstructions(self):
        contents = json.dumps({"instructions_type": "getPathData"})
        qryparms = {'qry': 'submit', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        print result
        while result["status"] >= 0 and result["status"] != RptGenStatus.DONE:
            time.sleep(5.0)
            qryparms = {'qry': 'getStatus', 'contents_hash': result["rpt_contents_hash"],
                        'start_ts': result["rpt_start_ts"]}
            result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["status"], RptGenStatus.FAILED)
        self.assertIn("JsonReportSupport", result["msg"])
        self.assertIn("KeyError", result["msg"])


class TestGetPath(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)

    def testGetPathData(self):
        contents = json.dumps({"instructions_type": "getPathData",
                               "swCorner": [36.58838, -121.93108],
                               "neCorner": [36.62807, -121.88112],
                               "runs": [{"analyzer": "FCDS2008",
                                         "startEtm": "2012-06-10  13:13",
                                         "endEtm": "2012-06-10  23:59",
                                         "minAmpl": 0.05,
                                         "stabClass": "D"}]})
        qryparms = {'qry': 'submit', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        print result
        while result["status"] >= 0 and result["status"] != RptGenStatus.DONE:
            time.sleep(5.0)
            qryparms = {'qry': 'getStatus', 'contents_hash': result["rpt_contents_hash"],
                        'start_ts': result["rpt_start_ts"]}
            result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["status"], RptGenStatus.DONE)

class TestGetStatus(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)

    def testMissingParameters(self):
        qryparms = {'qry': 'getStatus', 'contents_hash': 'f1d0deadf1d0deadf1d0deadf1d0dead'}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertIn(result["status"], [RptGenStatus.BAD_PARAMETERS])
        self.assertIn('Required parameter start_ts missing', result["msg"])

    def testBadParameters(self):
        qryparms = {'qry': 'getStatus', 'contents_hash': 'f1d0dead',
                    'start_ts': msUnixTimeToTimeString(getMsUnixTime())}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertIn(result["status"], [RptGenStatus.BAD_PARAMETERS])
        self.assertIn('contents_hash fails regex', result["msg"])

    def testMissingDirectories(self):
        qryparms = {'qry': 'getStatus', 'contents_hash': 'f1d0deadf1d0deadf1d0deadf1d0dead',
                    'start_ts': msUnixTimeToTimeString(getMsUnixTime())}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertIn(result["status"], [RptGenStatus.TASK_NOT_FOUND])


def setup_module():
    GLOBALS.reportServer = subprocess.Popen(["python.exe",
                                             r"..\..\ReportGen\reportServerNew.py", "-r", TEST_ROOT])
                                             # , stderr=file("NUL", "w"))
    GLOBALS.reportApi = ReportApiService()
    assert GLOBALS.reportApi
    GLOBALS.reportApi.csp_url = "http://localhost:5300"
    GLOBALS.reportApi.debug = True


def teardown_module():
    GLOBALS.reportServer.terminate()
    GLOBALS.reportServer.wait()

if __name__ == '__main__':
    unittest.main()
