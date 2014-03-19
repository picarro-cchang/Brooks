/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.PageFactory;

import common.source.ImagingUtility;
import common.source.LoginPage;
import common.source.ReportGenerationPortalPage;
import common.source.TestSetup;

/**
 * @author zlu
 * 
 */
public class ReportGenerationPortalPageTest {
	private static WebDriver driver;
	private static TestSetup testSetup;
	private static String baseURL;
	private static String screenShotsDir;
	private static boolean debug;

	private static LoginPage loginPage;
	private static ReportGenerationPortalPage pageReportGeneration;

	private static int timeoutSecondsToViewReport = 180;
	private static int timeoutSecondsElePresent = 20;
	private static String strPDFReport = "PDF";
	private static String strViewReport = "View";
	private static String strFigureValueYes = "Yes";
	private static String strFigureValueNo = "No";
	private static String strSWCorner = "swCorner";
	private static String strNeCorner = "neCorner";
	private static String strValidSearch = "valid";
	private static String strInvalidSearch = "invalid";

	/**
	 * @throws java.lang.Exception
	 */
	@BeforeClass
	public static void setUpBeforeClass() throws Exception {
		testSetup = new TestSetup();
		driver = testSetup.getDriver();
		baseURL = testSetup.getBaseUrl();
		// screenShotsDir = ".\\screenshots\\";
		screenShotsDir = "./screenshots/";
		debug = testSetup.isRunningDebug();
		driver.manage().deleteAllCookies();
		driver.manage().window().maximize();

		loginPage = new LoginPage(driver, baseURL);
		PageFactory.initElements(driver, loginPage);
		loginPage.open();
		loginPage.loginNormalAs(testSetup.getLoginUser0000(),
				testSetup.getLoginPwd0000());

		pageReportGeneration = new ReportGenerationPortalPage(driver, baseURL);
		PageFactory.initElements(driver, pageReportGeneration);
	}

	/**
	 * @throws java.lang.Exception
	 */
	@AfterClass
	public static void tearDownAfterClass() throws Exception {
		driver.quit();
	}

	/**
	 * @throws java.lang.Exception
	 */
	@Before
	public void setUp() throws Exception {
	}

	/**
	 * @throws java.lang.Exception
	 */
	@After
	public void tearDown() throws Exception {
	}

	/**
	 * Test Case: ReportGenerationPortalPage_TC0001 Make a report for a specific
	 * surveyor
	 * 
	 */
	// @Test
	public void ReportGenerationPortalPage_TC0001() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData());
			testSetup.slowdownInSeconds(3);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_TC0001");
		} catch (Exception e) {
			assertTrue("Exception Caught : " + e.getMessage(), false);
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_TC0001");
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_TC0002 Check a report created More
	 * scenarios and variations should be added ...
	 * 
	 */
	// @Test
	public void ReportGenerationPortalPage_TC0002() {
		try {
			pageReportGeneration.open();
			testSetup.slowdownInSeconds(15);

			pageReportGeneration.viewReport(testSetup.getHTReportData().get(
					"Title"));
			testSetup.slowdownInSeconds(5);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_TC0002");
		} catch (Exception e) {
			assertTrue("Exception Caught : " + e.getMessage(), false);
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_TC0002");
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT001 Verify report is getting
	 * generated successfully when all the valid details are provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT001() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT001_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT001_ViewReport");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT001");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT002 Verify PDF report is getting
	 * generated successfully when all the valid details are provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT002() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strPDFReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			assertTrue(pageReportGeneration.isDownloadPDFButtonPresent(
					testSetup.getHTReportData().get("Title"),
					timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT002");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT002");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT003 Verify report is not
	 * generated when 'Submap Grid' is 'Yes' and 'Submap Pages' details are not
	 * provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT003() {
		try {
			pageReportGeneration.open();
			assertTrue(pageReportGeneration.makeReportWithoutSubmapFigures(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT003");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT004 Verify PDF report is not
	 * generated when 'Submap Grid' is 'Yes' and 'Submap Pages' details are not
	 * provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT004() {
		try {
			pageReportGeneration.open();
			assertTrue(pageReportGeneration.makeReportWithoutSubmapFigures(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strPDFReport, strFigureValueYes, timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT004");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT005 Verify report is not
	 * generated when 'Submap Grid' value is 'NO' and user has provided 'Submap
	 * Pages' settings
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT005() {
		try {
			pageReportGeneration.open();
			assertTrue(pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueNo, strFigureValueYes,
					timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT005");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT006 Verify empty report is not
	 * generated when no 'summary Page' settings are provided but 'Submap Grid'
	 * value is 'Yes'
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT006() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReportWithSubmapGridOnlyNoSummary(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT006_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT006_ViewReport");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT006");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT007 Verify generated report
	 * don't have table details when Peaks, Isotopic, Runs and Surveys tables
	 * are not selected in template for 'Summary Pages'
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT007() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReportWithoutSummaryTables(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT007_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT007_ViewReport");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT007");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT008 Verify generated report
	 * don't have peaks, LISA, FOV and isotopes details when peaks, LISA, FOV
	 * and isotopes figures are not selected in template for 'Summary Pages'
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT008() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReportWithoutSumarryFiguresSettings(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT008_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT008_ViewReport");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT008");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT009 Verify generated report
	 * don't have table details when Peaks, Isotopic, Runs and Surveys tables
	 * are not selected in template for 'Submap Pages'
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT009() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReportWithoutSubmapTables(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT009_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT009_ViewReport");

			// click on Cell - e.g. C5
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT009");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT010 Verify generated report
	 * don't have peaks, LISA, FOV and isotopes details when peaks, LISA, FOV
	 * and isotopes figures are not selected in template for 'Submap Pages'
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT010() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReportWithoutSubmapFiguresSettings(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT010_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT010_ViewReport");

			// click on Cell - e.g. C5 - remaining
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT010");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT011 Verify report is not
	 * generated when 'Submap Pages' details are provided but 'Summary Pages'
	 * details are not provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT011() {
		try {
			pageReportGeneration.open();
			assertTrue(pageReportGeneration.makeReportWithoutSummary(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT011");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT012 Verify report is generated
	 * when analyzer details are not provided, if user confirms 'OK' to generate
	 * the report
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT012() {
		try {
			pageReportGeneration.open();
			String strReportTitle = testSetup.getHTReportData().get("Title")
					+ "RPT012";

			assertTrue(pageReportGeneration
					.cancelReportGenerationWhenNoAnalyzerProvided(
							strReportTitle, testSetup.getHTReportData(),
							strViewReport, strFigureValueYes,
							strFigureValueYes, timeoutSecondsElePresent));
			assertFalse(pageReportGeneration.isViewLinkPresent(strReportTitle,
					timeoutSecondsElePresent));

			assertTrue(pageReportGeneration.makeReportWithNoAnalyzerDetails());
			assertTrue(pageReportGeneration.viewReport(strReportTitle,
					timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT012");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT012");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT013 Verify user having 'Add
	 * "FORCE" ' permission can generate duplicate reports
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT013() {
		try {
			/**
			 * Need to add code to check ADD FORCE permission
			 */
			pageReportGeneration.open();
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT013_Report1_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT013_Report1_ViewReport");

			pageReportGeneration.makeDuplicateReport(testSetup
					.getHTReportData().get("Title"), timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT013_Report2_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT013_Report2_ViewReport");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT013");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT014 Verify user not having 'Add
	 * "FORCE" ' permission cannot generate duplicate reports
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT014() {
		try {
			/**
			 * Need to add code to check ADD FORCE permission
			 */
			pageReportGeneration.open();
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT014_Report1_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT014_Report1_ViewReport");

			assertTrue(pageReportGeneration.makeDuplicateReportNotAllowed(
					testSetup.getHTReportData().get("Title"),
					timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT014");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT016 - Verify Search
	 * functionality on 'Dashboard' Section to search the valid generated report
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT016() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT016_Dashboard");

			assertTrue(pageReportGeneration
					.isViewLinkPresent(
							testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			assertTrue(pageReportGeneration.searchLogFile(testSetup
					.getHTReportData().get("Title"), strValidSearch,
					timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT016");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT017 - Verify error messages are
	 * displayed when blank/invalid SW and NE corners are provided
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT017() {
		try {
			pageReportGeneration.open();

			assertTrue(pageReportGeneration
					.makeReportWithInvalidLatitudeCorner(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsElePresent));

			assertTrue(pageReportGeneration
					.makeReportWithInvalidLongitudeCorner(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsElePresent));

			assertTrue(pageReportGeneration
					.makeReportWithBlankSWNECorners(strSWCorner));

			assertTrue(pageReportGeneration
					.makeReportWithBlankSWNECorners(strNeCorner));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT017");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT018 Verify error message is
	 * displayed when blank title report is generated
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT018() {
		try {
			pageReportGeneration.open();
			assertTrue(pageReportGeneration.makeReportWithNoTitle(
					testSetup.getHTReportData(), timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT018");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT019 Verify error message is
	 * displayed when start and end time is not provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT019() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.provideBlankStartEndTime(
					testSetup.getSurveyor(), timeoutSecondsElePresent);

			assertTrue(pageReportGeneration.isStartTimeBlank());
			assertTrue(pageReportGeneration.isEndTimeBlank());
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT019");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT020 Verify user is able to
	 * delete analyzer details
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT020() {
		try {
			pageReportGeneration.open();
			assertFalse(pageReportGeneration.deleteAnalyzerDetails(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT020");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT021 Verify user is able to
	 * delete summary pages figure details
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT021() {
		try {
			pageReportGeneration.open();
			assertFalse(pageReportGeneration.deleteSummaryFigureDetails(
					testSetup.getSurveyor(), timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT021");

			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT022 Verify user is able to
	 * delete submap pages figure details
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT022() {
		try {
			pageReportGeneration.open();
			assertFalse(pageReportGeneration.deleteSubmapFigureDetails(
					testSetup.getSurveyor(), timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT022");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT023 Verify user is able to
	 * reload the report and edit it
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT023() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT023_Dashboard");

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT023_ViewReport");

			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
			String newReportTitle = pageReportGeneration.editAndMakeReport(
					testSetup.getHTReportData().get("Title"),
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT023_NewReport_Dashboard");

			assertTrue(pageReportGeneration.viewReport(newReportTitle,
					timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT023_NewReport_ViewReport");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT023");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT024 Verify in peaks table only
	 * peaks with min and greater than min ampl are shown
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT024() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReportPeaksMinAmpProvided(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			assertTrue(pageReportGeneration
					.viewReport(testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(pageReportGeneration
					.isPeaksAmpPresentGreaterThanMinAmp(timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT024");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT025 Verify 'Show All' and 'Show
	 * Selected' buttons are displaying the list of reports accordingly
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT025_ShowSelectedReports() {
		try {
			pageReportGeneration.open();
			pageReportGeneration
					.waitForReportPageLoading(timeoutSecondsElePresent);
			assertTrue(pageReportGeneration
					.showSelectedReports(timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility
					.takeScreenShot(driver, screenShotsDir,
							"Exception_ReportGenerationPortalPage_RPT025_ShowSelectedReports");

			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT025 Verify 'Show All' and 'Show
	 * Selected' buttons are displaying the list of reports accordingly
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT025_ShowAllReports() {
		try {
			pageReportGeneration.open();
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);
			String strNewReportTitle = pageReportGeneration
					.makeAndUncheckReport(
							testSetup.getHTReportData().get("Title"),
							timeoutSecondsToViewReport);
			assertTrue(pageReportGeneration.showAllReports(testSetup
					.getHTReportData().get("Title"), strNewReportTitle,
					timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility
					.takeScreenShot(driver, screenShotsDir,
							"Exception_ReportGenerationPortalPage_RPT025_ShowAllReports");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT026 Verfiy on selecting 'Show
	 * 'n' entries', the report list shows n entries on the dashboard
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT026() {
		try {
			pageReportGeneration.open();

			pageReportGeneration
					.waitForReportPageLoading(timeoutSecondsElePresent);
			assertTrue(pageReportGeneration.showNReportEntries(testSetup
					.getShow10Entries()));
			assertTrue(pageReportGeneration.showNReportEntries(testSetup
					.getShow25Entries()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT026");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT029 Verify empty PDF report is
	 * not generated when analyzer details are not provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT029() {
		try {
			pageReportGeneration.open();
			String strReportTitle = testSetup.getHTReportData().get("Title")
					+ "RPT029";

			assertTrue(pageReportGeneration
					.cancelReportGenerationWhenNoAnalyzerProvided(
							strReportTitle, testSetup.getHTReportData(),
							strPDFReport, strFigureValueYes, strFigureValueYes,
							timeoutSecondsElePresent));
			assertFalse(pageReportGeneration.isDownloadPDFButtonPresent(
					strReportTitle, timeoutSecondsElePresent));

			assertTrue(pageReportGeneration.makeReportWithNoAnalyzerDetails());
			assertTrue(pageReportGeneration.isDownloadPDFButtonPresent(
					strReportTitle, timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT029");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT029");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT030 Verify empty report is not
	 * generated when 'Summary and Submap Pages' template is empty
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT030() {
		try {
			pageReportGeneration.open();
			assertTrue(pageReportGeneration
					.makeReportWithNoSummarySubmapDetails(
							testSetup.getSurveyor(),
							testSetup.getHTReportData(), strViewReport,
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT030");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT031 - Verify Search
	 * functionality on 'Dashboard' Section to search the invalid report title
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT031() {
		try {
			pageReportGeneration.open();
			pageReportGeneration
					.waitForReportPageLoading(timeoutSecondsElePresent);
			assertTrue(pageReportGeneration.searchLogFile(
					testSetup.getLogFile(), strInvalidSearch,
					timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT031");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT032 Verify empty PDF report is
	 * not generated when 'Summary and Submap Pages' template is empty
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT032() {
		try {
			pageReportGeneration.open();
			assertTrue(pageReportGeneration
					.makeReportWithNoSummarySubmapDetails(
							testSetup.getSurveyor(),
							testSetup.getHTReportData(), strPDFReport,
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT032");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}
}
