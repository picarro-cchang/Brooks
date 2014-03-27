/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.openqa.selenium.JavascriptExecutor;
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
	private static int timeoutSecondsElePresent = 40;
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
		screenShotsDir = "./screenshots/";
		debug = testSetup.isRunningDebug();
		driver.manage().deleteAllCookies();
		driver.manage().window().maximize();

		loginPage = new LoginPage(driver, baseURL);
		PageFactory.initElements(driver, loginPage);
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
		pageReportGeneration.logout();
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
			TestSetup.slowdownInSeconds(5);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_TC0001");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_TC0001");
			fail("Exception Caught : " + e.getMessage());
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
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_TC0002");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT001_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT001_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated successfully!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT001_ViewReport");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT001");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strPDFReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strPDFReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT002_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated successfully!",
					pageReportGeneration.isDownloadPDFButtonPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT002");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT002");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertTrue(
					"Report should not be generated when submap details were not provided!",
					pageReportGeneration.makeReportWithoutSubmapFigures(
							testSetup.getSurveyor(),
							testSetup.getHTReportData(), strViewReport,
							strFigureValueYes, timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT003");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertTrue(
					"PDF report should not be generated when submap details were not provided!",
					pageReportGeneration.makeReportWithoutSubmapFigures(
							testSetup.getSurveyor(),
							testSetup.getHTReportData(), strPDFReport,
							strFigureValueYes, timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT004");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertTrue(
					"Report should not be generated as submap pages are not reachable!",
					pageReportGeneration.makeReport(testSetup.getSurveyor(),
							testSetup.getHTReportData(), strViewReport,
							strFigureValueNo, strFigureValueYes,
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT005");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReportWithSubmapGridOnlyNoSummary(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT006_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT006_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT006_ViewReport");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT006");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReportWithoutSummaryTables(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT007_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT007_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT007_ViewReport");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT007");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReportWithoutSumarryFiguresSettings(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT008_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT008_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT008_ViewReport");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT008");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReportWithoutSubmapTables(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT009_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT009_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT009_ViewReport");

			// click on Cell - e.g. C5

			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT009");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReportWithoutSubmapFiguresSettings(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT010_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT0010_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT010_ViewReport");

			// click on Cell - e.g. C5 - remaining

			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT010");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertTrue(
					"Report should not be generated for empty summary figure and tables template!",
					pageReportGeneration.makeReportWithoutSummary(
							testSetup.getSurveyor(),
							testSetup.getHTReportData(), strViewReport,
							strFigureValueYes, timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT011");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT012 Verify report is generated
	 * when analyzer details are not provided, if user confirms to generate the
	 * report
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT012() {
		try {
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			String strReportTitle = testSetup.getHTReportData().get("Title")
					+ "RPT012";

			assertTrue("Alert not present for empty analyzer details!",
					pageReportGeneration
							.cancelReportGenerationWhenNoAnalyzerProvided(
									strReportTitle,
									testSetup.getHTReportData(), strViewReport,
									strFigureValueYes, strFigureValueYes,
									timeoutSecondsElePresent));
			assertFalse(
					"Report should not be generated if alert is dismissed!",
					pageReportGeneration.isViewLinkPresent(strReportTitle,
							timeoutSecondsElePresent));

			assertTrue(
					"Alert not present for empty analyzer details!",
					pageReportGeneration
							.makeReportWithNoAnalyzerDetails(timeoutSecondsElePresent));

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT012_ErrorCode");
			}

			assertTrue(strReportTitle + " : report not generated!",
					pageReportGeneration.isViewLinkPresent(strReportTitle,
							timeoutSecondsToViewReport));
			assertTrue(strReportTitle
					+ " report should be generated if alert is accepted!",
					pageReportGeneration.viewReport(strReportTitle,
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT012");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT012");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT013 Verify user having 'Add
	 * "FORCE"' permission can generate duplicate reports
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT013() {
		try {
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT013_Report1_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT013_Report1_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT013_Report1_ViewReport");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);

			pageReportGeneration.makeDuplicateReport(testSetup
					.getHTReportData().get("Title"), timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT013_Report2_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT013_Report2_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT013_Report2_ViewReport");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT013");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUserA(),
					testSetup.getLoginPwdA());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT014_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT014_Report_Dashboard");

			assertTrue(
					"Alert not present when user not allowed to generate duplicate reports!",
					pageReportGeneration.makeDuplicateReportNotAllowed(
							testSetup.getHTReportData().get("Title"),
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT014");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT016_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT016_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not present!",
					pageReportGeneration.searchReport(testSetup
							.getHTReportData().get("Title"), strValidSearch,
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT016");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertTrue("Alert not present for invlaid latitude corners!",
					pageReportGeneration.makeReportWithInvalidLatitudeCorner(
							testSetup.getHTReportData().get("Title"),
							timeoutSecondsElePresent));
			assertTrue("Alert not present for invlaid longitude corners!",
					pageReportGeneration.makeReportWithInvalidLongitudeCorner(
							testSetup.getHTReportData().get("Title"),
							timeoutSecondsElePresent));
			assertTrue("Alert not present for blank SW corners!",
					pageReportGeneration.makeReportWithBlankSWNECorners(
							strSWCorner, timeoutSecondsElePresent));
			assertTrue("Alert not present for blank NE corners!",
					pageReportGeneration.makeReportWithBlankSWNECorners(
							strNeCorner, timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT017");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertTrue("Alert not present for blank report title!",
					pageReportGeneration.makeReportWithNoTitle(
							testSetup.getHTReportData(),
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT018");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.provideBlankStartEndTime(
					testSetup.getSurveyor(), timeoutSecondsElePresent);

			assertTrue("Error message not present for blank start time!",
					pageReportGeneration.isStartTimeBlank());
			assertTrue("Error message not present for blank end time!",
					pageReportGeneration.isEndTimeBlank());
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT019");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertFalse("Analyzer details not get deleted!",
					pageReportGeneration.deleteAnalyzerDetails(
							testSetup.getSurveyor(),
							testSetup.getHTReportData(),
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT020");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertFalse(
					"Summary Figure details not get deleted!",
					pageReportGeneration.deleteSummaryFigureDetails(
							testSetup.getSurveyor(), timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT021");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertFalse(
					"Submap figure details not get deleted!",
					pageReportGeneration.deleteSubmapFigureDetails(
							testSetup.getSurveyor(), timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT022");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReport(testSetup.getSurveyor(),
					testSetup.getHTReportData(), strViewReport,
					strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT023_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT023_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT023_ViewReport");

			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
			String newReportTitle = pageReportGeneration.editAndMakeReport(
					testSetup.getHTReportData().get("Title"),
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT023_NewReport_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility
						.takeScreenShot(driver, screenShotsDir,
								"ReportGenerationPortalPage_RPT023_NewReport_ErrorCode");
			}

			assertTrue(newReportTitle + " : report not generated!",
					pageReportGeneration.isViewLinkPresent(newReportTitle,
							timeoutSecondsToViewReport));
			assertTrue(newReportTitle + " report not generated!",
					pageReportGeneration.viewReport(newReportTitle,
							timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT023_NewReport_ViewReport");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT023");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReportPeaksMinAmpProvided(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT024_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report not generated!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));
			assertTrue(
					"Peaks present in report have Ampl lesses than specified Min Ampl!",
					pageReportGeneration
							.isPeaksAmpPresentGreaterThanMinAmp(timeoutSecondsElePresent));
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT024");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);

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
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration
					.waitForReportPageLoading(timeoutSecondsElePresent);
			assertTrue(pageReportGeneration
					.showSelectedReports(timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility
					.takeScreenShot(driver, screenShotsDir,
							"Exception_ReportGenerationPortalPage_RPT025_ShowSelectedReports");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT026 Verify on selecting 'Show
	 * 'n' entries', the report list shows n entries on the dashboard
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT026() {
		try {
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration
					.waitForReportPageLoading(timeoutSecondsElePresent);
			assertTrue("10 report entries should be present on Dashboard!",
					pageReportGeneration.showNReportEntries(testSetup
							.getShow10Entries()));
			assertTrue("25 report entries should be present on Dashboard!",
					pageReportGeneration.showNReportEntries(testSetup
							.getShow25Entries()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT026");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT027 Verify report is generated
	 * for 1*1 grid, when user provides rows and columns value as '1' and Submap
	 * page settings
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT027() {
		try {
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration.makeReportOfSingleRowCol(
					testSetup.getSurveyor(), testSetup.getHTReportData(),
					strViewReport, strFigureValueYes, strFigureValueYes,
					timeoutSecondsElePresent);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT027_Dashboard");

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strViewReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT027_ErrorCode");
			}

			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated!",
					pageReportGeneration.isViewLinkPresent(testSetup
							.getHTReportData().get("Title"),
							timeoutSecondsToViewReport));
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " : report not generated successfully!",
					pageReportGeneration.viewReport(testSetup.getHTReportData()
							.get("Title"), timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT027_ViewReport");
			pageReportGeneration.closeChildWindow(timeoutSecondsElePresent);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT001");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			String strReportTitle = testSetup.getHTReportData().get("Title")
					+ "RPT029";

			assertTrue("Alert not present for empty analyzer details!",
					pageReportGeneration
							.cancelReportGenerationWhenNoAnalyzerProvided(
									strReportTitle,
									testSetup.getHTReportData(), strPDFReport,
									strFigureValueYes, strFigureValueYes,
									timeoutSecondsElePresent));
			assertFalse(
					"Report should not be generated if alert is dismissed!",
					pageReportGeneration.isDownloadPDFButtonPresent(
							strReportTitle, timeoutSecondsElePresent));

			assertTrue(
					"Alert not present for empty analyzer details!",
					pageReportGeneration
							.makeReportWithNoAnalyzerDetails(timeoutSecondsElePresent));

			if (pageReportGeneration.isErrorCodePresent(testSetup
					.getHTReportData().get("Title"), strPDFReport,
					timeoutSecondsToViewReport)) {
				fail("Bug -> 632 : Intermittently error code is displayed when user tries to generate the report");
				ImagingUtility.takeScreenShot(driver, screenShotsDir,
						"ReportGenerationPortalPage_RPT029_ErrorCode");
			}

			assertTrue(strReportTitle
					+ " PDF report should be generated if alert is accepted!",
					pageReportGeneration.isDownloadPDFButtonPresent(
							strReportTitle, timeoutSecondsToViewReport));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"ReportGenerationPortalPage_RPT029");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT029");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertTrue(
					"Report should not be generated when Summary nad submap template is empty!",
					pageReportGeneration.makeReportWithNoSummarySubmapDetails(
							testSetup.getSurveyor(),
							testSetup.getHTReportData(), strViewReport,
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT030");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			pageReportGeneration
					.waitForReportPageLoading(timeoutSecondsElePresent);
			assertTrue(testSetup.getHTReportData().get("Title")
					+ " report should not be present!",
					pageReportGeneration.searchReport(testSetup.getLogFile(),
							strInvalidSearch, timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT031");
			fail("Exception Caught : " + e.getMessage());
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
			pageReportGeneration = loginPage.loginAndNavigateToReportPortal(
					baseURL, testSetup.getLoginUser0000(),
					testSetup.getLoginPwd0000());
			pageReportGeneration.open();
			TestSetup.slowdownInSeconds(5);
			assertTrue(
					"PDF report should not be generated when Summary nad submap template is empty!",
					pageReportGeneration.makeReportWithNoSummarySubmapDetails(
							testSetup.getSurveyor(),
							testSetup.getHTReportData(), strPDFReport,
							timeoutSecondsElePresent));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_ReportGenerationPortalPage_RPT032");
			fail("Exception Caught : " + e.getMessage());
		}
	}
}
