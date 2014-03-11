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
import org.openqa.selenium.Alert;
import org.openqa.selenium.By;
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

	private static int timeoutSeconds = 60;
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
		//screenShotsDir = ".\\screenshots\\";
		screenShotsDir = "./screenshots/";
		debug = testSetup.isRunningDebug();
		driver.manage().deleteAllCookies();
		driver.manage().window().maximize();
		
		loginPage = new LoginPage(driver, baseURL);
		PageFactory.initElements(driver, loginPage);
		loginPage.open();
		loginPage.loginNormalAs(testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());		
		
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
	 * Test Case: ReportGenerationPortalPage_TC0001
	 * Make a report for a specific surveyor
	 *  
	 */
//	@Test
	public void ReportGenerationPortalPage_TC0001() {
		pageReportGeneration.open();
		testSetup.slowdownInSeconds(15);
		
		pageReportGeneration.makeReport(testSetup.getSurveyor(), testSetup.getHTReportData());
//		testSetup.slowdownInSeconds(3);
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "ReportGenerationPortalPage_TC0001");
	}
	
	/**
	 * Test Case: ReportGenerationPortalPage_TC0002
	 * Check a report created
	 * More scenarios and variations should be added ...
	 *  
	 */
//	@Test
	public void ReportGenerationPortalPage_TC0002() {
		pageReportGeneration.open();
		testSetup.slowdownInSeconds(15);
		
//		pageReportGeneration.viewReport(testSetup.getHTReportData().get("Title"));
//		testSetup.slowdownInSeconds(5);
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "ReportGenerationPortalPage_TC0002_02");
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT001 Verify report is getting
	 * generated successfully when all the valid details are provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT001() {
		pageReportGeneration.open();
		pageReportGeneration.makeReport(testSetup.getSurveyor(),
				testSetup.getHTReportData(), strViewReport, strFigureValueYes,
				strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT001_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT001_ViewReport");
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT002 Verify PDF report is getting
	 * generated successfully when all the valid details are provided
	 * 
	 */
	@Test
	public void reportGenerationPortalPage_RPT002() {
		pageReportGeneration.open();
		pageReportGeneration.makeReport(testSetup.getSurveyor(),
				testSetup.getHTReportData(), strPDFReport, strFigureValueYes,
				strFigureValueYes, timeoutSeconds);

		assertTrue(pageReportGeneration.isDownloadPDFButtonPresent(testSetup
				.getHTReportData().get("Title"), 150));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT002");
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT003 Verify report is not
	 * generated when 'Submap Grid' is 'Yes' and 'Submap Pages' details are not
	 * provided
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT003() {
		pageReportGeneration.open();

		assertTrue(pageReportGeneration.makeReportWithoutSubmapFigures(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, strFigureValueYes, timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT004 Verify PDF report is not
	 * generated when 'Submap Grid' is 'Yes' and 'Submap Pages' details are not
	 * provided
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT004() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration.makeReportWithoutSubmapFigures(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strPDFReport, strFigureValueYes, timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT005 Verify report is not
	 * generated when 'Submap Grid' value is 'NO' and user has provided 'Submap
	 * Pages' settings
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT005() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration.makeReport(testSetup.getSurveyor(),
				testSetup.getHTReportData(), strViewReport, strFigureValueNo,
				strFigureValueYes, timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT006 Verify empty report is not
	 * generated when no 'summary Page' settings are provided but 'Submap Grid'
	 * value is 'Yes'
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT006() {
		pageReportGeneration.open();
		pageReportGeneration.makeReportWithSubmapGridOnlyNoSummary(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT006_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT006_ViewReport");
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT007 Verify generated report
	 * don't have table details when Peaks, Isotopic, Runs and Surveys tables
	 * are not selected in template for 'Summary Pages'
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT007() {
		pageReportGeneration.open();
		pageReportGeneration.makeReportWithoutSummaryTables(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT007_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT007_ViewReport");
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT008 Verify generated report
	 * don't have peaks, LISA, FOV and isotopes details when peaks, LISA, FOV
	 * and isotopes figures are not selected in template for 'Summary Pages'
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT008() {
		pageReportGeneration.open();
		pageReportGeneration.makeReportWithoutSumarryFiguresSettings(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT008_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
		.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT008_ViewReport");
	}
	
	/**
	 * Test Case: ReportGenerationPortalPage_RPT009 Verify generated report
	 * don't have table details when Peaks, Isotopic, Runs and Surveys tables
	 * are not selected in template for 'Submap Pages'
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT009() {
		pageReportGeneration.open();
		pageReportGeneration.makeReportWithoutSubmapTables(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT009_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT009_ViewReport");

		// click on Cell - e.g. C5
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT010 Verify generated report
	 * don't have peaks, LISA, FOV and isotopes details when peaks, LISA, FOV
	 * and isotopes figures are not selected in template for 'Submap Pages'
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT010() {
		pageReportGeneration.open();
		pageReportGeneration.makeReportWithoutSubmapFiguresSettings(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT010_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT010_ViewReport");

		// click on Cell - e.g. C5 - remaining
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT011 Verify report is not
	 * generated when 'Submap Pages' details are provided but 'Summary Pages'
	 * details are not provided
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT011() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration.makeReportWithoutSummary(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, strFigureValueYes, timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT012 Verify report is generated
	 * when analyzer details are not provided, if user confirms 'OK' to generate
	 * the report
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT012() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration
				.cancelReportGenerationWhenNoAnalyzerProvided(
						testSetup.getHTReportData(), strViewReport,
						strFigureValueYes, strFigureValueYes, timeoutSeconds));

		assertFalse(pageReportGeneration.isViewLinkPresent(testSetup
				.getHTReportData().get("Title"), timeoutSeconds));

		assertTrue(pageReportGeneration.makeReportWithNoAnalyzerDetails());
		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT012");
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT013 Verify user having 'Add
	 * "FORCE" ' permission can generate duplicate reports
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT013() {
		/**
		 * Need to add code to check ADD FORCE permission
		 */
		pageReportGeneration.open();
		pageReportGeneration.makeReport(testSetup.getSurveyor(),
				testSetup.getHTReportData(), strViewReport, strFigureValueYes,
				strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT013_Report1_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT013_Report1_ViewReport");

		pageReportGeneration.makeDuplicateReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT013_Report2_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT013_Report2_ViewReport");
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT014 Verify user not having 'Add
	 * "FORCE" ' permission cannot generate duplicate reports
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT014() {
		/**
		 * Need to add code to check ADD FORCE permission
		 */
		pageReportGeneration.open();
		pageReportGeneration.makeReport(testSetup.getSurveyor(),
				testSetup.getHTReportData(), strViewReport, strFigureValueYes,
				strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT014_Report1_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT014_Report1_ViewReport");

		assertTrue(pageReportGeneration.makeDuplicateReport(testSetup
				.getHTReportData().get("Title"), timeoutSeconds));
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
		pageReportGeneration.open();
		pageReportGeneration.makeReport(testSetup.getSurveyor(),
				testSetup.getHTReportData(), strViewReport, strFigureValueYes,
				strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT016_Dashboard");

		assertTrue(pageReportGeneration.isViewLinkPresent(testSetup
				.getHTReportData().get("Title"), timeoutSeconds));

		assertTrue(pageReportGeneration.searchLogFile(testSetup
				.getHTReportData().get("Title"), strValidSearch, timeoutSeconds));
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
		pageReportGeneration.open();

		assertTrue(pageReportGeneration.makeReportWithInvalidLatitudeCorner(
				testSetup.getHTReportData().get("Title"), timeoutSeconds));

		assertTrue(pageReportGeneration.makeReportWithInvalidLongitudeCorner(
				testSetup.getHTReportData().get("Title"), timeoutSeconds));

		assertTrue(pageReportGeneration
				.makeReportWithBlankSWNECorners(strSWCorner));

		assertTrue(pageReportGeneration
				.makeReportWithBlankSWNECorners(strNeCorner));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT018 Verify error message is
	 * displayed when blank title report is generated
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT018() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration.makeReportWithNoTitle(
				testSetup.getHTReportData(), timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT019 Verify error message is
	 * displayed when start and end time is not provided
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT019() {
		pageReportGeneration.open();
		pageReportGeneration.provideBlankStartEndTime(testSetup.getSurveyor(),
				timeoutSeconds);

		assertTrue(pageReportGeneration.isStartTimeBlank());
		assertTrue(pageReportGeneration.isEndTimeBlank());
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT020 Verify user is able to
	 * delete analyzer details
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT020() {
		pageReportGeneration.open();
		assertFalse(pageReportGeneration.deleteAnalyzerDetails(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT021 Verify user is able to
	 * delete summary pages figure details
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT021() {
		pageReportGeneration.open();
		assertFalse(pageReportGeneration.deleteSummaryFigureDetails(
				testSetup.getSurveyor(), timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT022 Verify user is able to
	 * delete submap pages figure details
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT022() {
		pageReportGeneration.open();
		assertFalse(pageReportGeneration.deleteSubmapFigureDetails(
				testSetup.getSurveyor(), timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT023 Verify user is able to
	 * reload the report and edit it
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT023() {
		pageReportGeneration.open();
		pageReportGeneration.makeReport(testSetup.getSurveyor(),
				testSetup.getHTReportData(), strViewReport, strFigureValueYes,
				strFigureValueYes, timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT023_Dashboard");

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT023_ViewReport");

		pageReportGeneration.closeChildWindow(timeoutSeconds);
		String newReportTitle = pageReportGeneration.editAndMakeReport(
				testSetup.getHTReportData().get("Title"), timeoutSeconds);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT023_NewReport_Dashboard");

		assertTrue(pageReportGeneration.viewReport(newReportTitle,
				timeoutSeconds));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT023_NewReport_ViewReport");
	}
	
	/**
	 * Test Case: ReportGenerationPortalPage_RPT024 Verify in peaks table only
	 * peaks with min and greater than min ampl are shown
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT024() {
		pageReportGeneration.open();
		pageReportGeneration.makeReportPeaksMinAmpProvided(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, strFigureValueYes, strFigureValueYes,
				timeoutSeconds);

		assertTrue(pageReportGeneration.viewReport(testSetup.getHTReportData()
				.get("Title"), timeoutSeconds));
		assertTrue(pageReportGeneration
				.isPeaksAmpPresentGreaterThanMinAmp(timeoutSeconds));
	}
	
	/**
	 * Test Case: ReportGenerationPortalPage_RPT025 Verify 'Show All' and 'Show
	 * Selected' buttons are displaying the list of reports accordingly
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT025_ShowSelectedReports() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration.showSelectedReports(timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT025 Verify 'Show All' and 'Show
	 * Selected' buttons are displaying the list of reports accordingly
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT025_ShowAllReports() {
		pageReportGeneration.open();
		pageReportGeneration.makeReport(testSetup.getSurveyor(),
				testSetup.getHTReportData(), strViewReport, strFigureValueYes,
				strFigureValueYes, timeoutSeconds);
		String strNewReportTitle = pageReportGeneration.makeAndUncheckReport(
				testSetup.getHTReportData().get("Title"), timeoutSeconds);
		assertTrue(pageReportGeneration.showAllReports(testSetup
				.getHTReportData().get("Title"), strNewReportTitle,
				timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT026 Verfiy on selecting 'Show
	 * 'n' entries', the report list shows n entries on the dashboard
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT026() {
		pageReportGeneration.open();

		assertTrue(pageReportGeneration.showNReportEntries(
				testSetup.getShow10Entries(), timeoutSeconds));

		assertTrue(pageReportGeneration.showNReportEntries(
				testSetup.getShow25Entries(), timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT029 Verify empty PDF report is
	 * not generated when analyzer details are not provided
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT029() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration
				.cancelReportGenerationWhenNoAnalyzerProvided(
						testSetup.getHTReportData(), strPDFReport,
						strFigureValueYes, strFigureValueYes, timeoutSeconds));
		assertFalse(pageReportGeneration.isDownloadPDFButtonPresent(testSetup
				.getHTReportData().get("Title"), timeoutSeconds));

		assertTrue(pageReportGeneration.makeReportWithNoAnalyzerDetails());
		assertTrue(pageReportGeneration.isDownloadPDFButtonPresent(testSetup
				.getHTReportData().get("Title"), 150));

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"ReportGenerationPortalPage_RPT029");
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT030 Verify empty report is not
	 * generated when 'Summary and Submap Pages' template is empty
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT030() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration.makeReportWithNoSummarySubmapDetails(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strViewReport, timeoutSeconds));
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
		pageReportGeneration.open();
		assertTrue(pageReportGeneration.searchLogFile(testSetup.getLogFile(),
				strInvalidSearch, timeoutSeconds));
	}

	/**
	 * Test Case: ReportGenerationPortalPage_RPT032 Verify empty PDF report is
	 * not generated when 'Summary and Submap Pages' template is empty
	 * 
	 */
	 @Test
	public void reportGenerationPortalPage_RPT032() {
		pageReportGeneration.open();
		assertTrue(pageReportGeneration.makeReportWithNoSummarySubmapDetails(
				testSetup.getSurveyor(), testSetup.getHTReportData(),
				strPDFReport, timeoutSeconds));
	}
}
