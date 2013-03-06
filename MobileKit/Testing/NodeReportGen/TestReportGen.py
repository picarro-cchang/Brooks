import urllib2
import json
import os
import shutil
import subprocess
import textwrap
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


class TestAccessServer(unittest.TestCase):
    def testGetIndexPage(self):
        op = urllib2.urlopen("http://localhost:5300/")
        self.assertIn("Surveyor Report Generation", op.read())
        op.close()


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

    def testBadQry(self):
        contents = 'dummy'
        qryparms = {'qry': 'floodle', 'contents': contents}
        # Submit a project via the report server
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertTrue("RptGen: Unknown or missing qry" in e.exception.__str__())
        qryparms = {'contents': contents}
        # Submit a project via the report server
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertTrue("RptGen: Unknown or missing qry" in e.exception.__str__())

    def testJsonSubmitNoContents(self):
        qryparms = {'qry': 'submit'}
        # Submit a project via the report server
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertTrue("Required parameter contents missing" in e.exception.__str__())

    def testBadJsonSubmit(self):
        contents = 'Bad Contents (not JSON)'
        qryparms = {'qry': 'submit', 'contents': contents}
        # Submit a project via the report server
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertTrue("Instructions are not in valid JSON notation" in e.exception.__str__())

    def testInvalidInstructionsSubmit(self):
        contents = json.dumps({"instructions_type": "invalid"})
        qryparms = {'qry': 'submit', 'contents': contents}
        # Submit a project via the report server
        print "First submission"
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        time.sleep(2)
        print "Second submission"
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))

        qryparms = {'qry': 'getStatus', 'contents_hash': result["rpt_contents_hash"],
                    'start_ts': result["rpt_start_ts"]}
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["status"], RptGenStatus.FAILED)
        self.assertIn('Bad instructions_type', result["msg"])

    def testGetPathsDataMissingInstructions(self):
        contents = json.dumps({"instructions_type": "getPathsData"})
        qryparms = {'qry': 'submit', 'contents': contents}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        print result
        while result["status"] >= 0 and result["status"] != RptGenStatus.DONE:
            time.sleep(5.0)
            qryparms = {'qry': 'getStatus', 'contents_hash': result["rpt_contents_hash"],
                        'start_ts': result["rpt_start_ts"]}
            result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertEqual(result["status"], RptGenStatus.BAD_PARAMETERS)
        self.assertIn("neCorner missing", result["msg"])
        self.assertIn("swCorner missing", result["msg"])
        self.assertIn("runs missing", result["msg"])


class TestGetPaths(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)

    def testGetPathsData(self):
        contents = textwrap.dedent("""\
        {
          "instructions_type": "getPathsData",
          "neCorner": "9q926ebvup1u",
          "runs": [
            {
              "analyzer": "FCDS2008",
              "endEtm": 1339354800,
              "startEtm": 1339333980
            },
            {
              "analyzer": "FCDS2008",
              "endEtm": 1339372740,
              "startEtm": 1339355100
            }
          ],
          "swCorner": "9q921ksqzbmh"
        }
        """)
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


class TestGetFovs(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)

    def testGetFovsData(self):
        contents = textwrap.dedent("""\
        {
          "instructions_type": "getFovsData",
          "neCorner": "9q926ebvup1v",
          "fovMinAmp": 0.03,
          "fovMinLeak": 1.0,
          "fovNWindow": 10,
          "runs": [
            {
              "analyzer": "FCDS2008",
              "endEtm": 1339335000,
              "stabClass": "D",
              "startEtm": 1339333980
            },
            {
              "analyzer": "FCDS2008",
              "endEtm": 1339336000,
              "stabClass": "D",
              "startEtm": 1339335001
            }
          ],
          "swCorner": "9q921ksqzbmh"
        }
        """)
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


class TestGetPeaks(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)

    def testGetPeaksData(self):
        contents = textwrap.dedent("""\
        {
          "instructions_type": "getPeaksData",
          "neCorner": "9q926ebvup1u",
          "exclRadius": 10.0,
          "runs": [
            {
              "analyzer": "FCDS2008",
              "endEtm": 1339354800,
              "startEtm": 1339333980
            },
            {
              "analyzer": "FCDS2008",
              "endEtm": 1339372740,
              "startEtm": 1339355100
            }
          ],
          "swCorner": "9q921ksqzbmh"
        }
        """)
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


class TestGetAnalyses(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)

    def testGetAnalysesData(self):
        contents = textwrap.dedent("""\
        {
          "instructions_type": "getAnalysesData",
          "neCorner": "9q926ebvup1u",
          "runs": [
            {
              "analyzer": "FCDS2008",
              "endEtm": 1339354800,
              "startEtm": 1339333980
            },
            {
              "analyzer": "FCDS2008",
              "endEtm": 1339372740,
              "startEtm": 1339355100
            }
          ],
          "swCorner": "9q921ksqzbmh"
        }
        """)
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


class TestMakeReport(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(os.path.join(TEST_ROOT), ignore_errors=True)
        pass

    def testMakeReport(self):
        contents = json.dumps({"instructions_type": "makeReport",
                               "swCorner": [36.58838, -121.93108],
                               "neCorner": [36.62807, -121.88112],
                               "submaps": {"nx": 2, "ny": 2},
                               "exclRadius": 10,
                               "peaksMinAmp": 0.1,
                               "fovMinAmp": 0.03,
                               "fovMinLeak": 1.0,
                               "fovNWindow": 10,
                               "runs": [{"analyzer": "FCDS2008",
                                         "startEtm": "2012-06-10  13:13",
                                         "endEtm": "2012-06-10  19:00",
                                         "peaks": "#00FFFF",
                                         "stabClass": "D",
                                         "wedges": "#FFFF00",
                                         "fovs": "#00FF00"
                                         },
                                        {"analyzer": "FCDS2008",
                                         "startEtm": "2012-06-10  19:05",
                                         "endEtm": "2012-06-10  23:59",
                                         "peaks": "#FFFF00",
                                         "stabClass": "D",
                                         "wedges": "#0000FF",
                                         "fovs": "#FF0000"
                                         }
                                        ],
                               "template": {
                               "summary": [{"peaks": True}],
                               "submaps": [{"paths": True,
                                            "peaks": True,
                                            "wedges": True},
                                           {"baseType": "satellite",
                                            "fovs": True,
                                            "paths": True,
                                            "peaks": True,
                                            "wedges": True},
                                           ]
                               }})
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
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertTrue("Required parameter start_ts missing" in e.exception.__str__())

    def testBadParameters(self):
        qryparms = {'qry': 'getStatus', 'contents_hash': 'f1d0dead',
                    'start_ts': msUnixTimeToTimeString(getMsUnixTime())}
        # Submit a project via the report server
        with self.assertRaises(RuntimeError) as e:
            raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertTrue("contents_hash fails regex" in e.exception.__str__())

    def testMissingDirectories(self):
        qryparms = {'qry': 'getStatus', 'contents_hash': 'f1d0deadf1d0deadf1d0deadf1d0dead',
                    'start_ts': msUnixTimeToTimeString(getMsUnixTime())}
        # Submit a project via the report server
        result = raiseOnError(GLOBALS.reportApi.get("gdu", "1.0", "RptGen", qryparms))
        self.assertIn(result["status"], [RptGenStatus.TASK_NOT_FOUND])


def setup_module():
    GLOBALS.reportServer = subprocess.Popen(["node.exe",
                                             r"..\..\NodeReportGen\reportServer.js", "-r", TEST_ROOT])
    GLOBALS.reportApi = ReportApiService()
    assert GLOBALS.reportApi
    GLOBALS.reportApi.csp_url = "http://localhost:5300"
    GLOBALS.reportApi.debug = True


def teardown_module():
    GLOBALS.reportServer.terminate()
    GLOBALS.reportServer.wait()

if __name__ == '__main__':
    unittest.main()
