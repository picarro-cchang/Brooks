/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.*;

import java.util.List;

import junit.framework.TestCase;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Assert;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.PageFactory;

import common.source.ImagingUtility;
import common.source.LoginPage;
import common.source.NaturalGasLeaksPage;
import common.source.ReportGenerationPortalPage;
import common.source.TestSetup;

/**
 * @author zlu
 *
 */
public class NaturalGasLeaksPageTest {
	private static WebDriver driver;
	private static TestSetup testSetup;
	private static String baseURL;
	private static String screenShotsDir;
	private static boolean debug;
	
	private static LoginPage loginPage;
	private static NaturalGasLeaksPage naturalGasLeaksPage;	
	private static String strListView = "List";
	private static String strCalView = "Calendar";
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
		
		naturalGasLeaksPage = new NaturalGasLeaksPage(driver, baseURL);
		PageFactory.initElements(driver, naturalGasLeaksPage);
	}

	/**
	 * @throws java.lang.Exception
	 */
	@AfterClass
	public static void tearDownAfterClass() throws Exception {
//		driver.quit();
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
	 * Test Case: naturalGasLeaksPage_TC0001
	 * Get the list of the surveyors
	 * Fail the case if can't find one specific surveyor 
	 * 
	 */
//	@Test
	public void naturalGasLeaksPage_TC0001() {
		naturalGasLeaksPage.open();
		
		List<String> strSurveyorList = naturalGasLeaksPage.getSurveyorList();
		
		System.out.println("\nThe Surveyor list: ");
		for (String strSurveyor: strSurveyorList) {
			 System.out.println(strSurveyor);
		}
		
		boolean surveyorFound = false;
		for (String strSurveyor: strSurveyorList) {
			if (strSurveyor.equals(testSetup.getSurveyor())) {
				surveyorFound = true;
				break;
			}
			else {
				continue;
			}
		}
		
		if (!surveyorFound) {
			fail("Didn't find the surveyor: " + testSetup.getSurveyor());
		}
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "naturalGasLeaksPage_TC0001");
	}
	
	/**
	 * Test Case: naturalGasLeaksPage_TC0002
	 * Get the log file list for a specific surveyor
	 * 
	 */
//	@Test
	public void naturalGasLeaksPage_TC0002() {
		naturalGasLeaksPage.open();
	
		System.out.println("\nThe selected surveyor is: " + testSetup.getSurveyor());
		
		List<String> strLogList = naturalGasLeaksPage.getSurveyorLogList(testSetup.getSurveyor());
		
		System.out.println("\nThe log file list: ");
		for (String strLogName: strLogList) {
			System.out.println(strLogName);
		}
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "naturalGasLeaksPage_TC0002");
	}
	
	/**
	 * Test Case: naturalGasLeaksPage_TC0003
	 * Show the map log for a specific surveyor
	 * 
	 */
//	@Test
	public void naturalGasLeaksPage_TC0003() {
		naturalGasLeaksPage.open();
		
		naturalGasLeaksPage.showSurveyorLogMap(testSetup.getSurveyor(), testSetup.getLogFile());
		
		TestSetup.slowdownInSeconds(15);
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "naturalGasLeaksPage_TC0003");
	}
	
	/**
	 * Test Case: GDU001 - Verify Surveyor, 'View Metadata' and 'Map Log' valid
	 * details are displayed
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU001() {
		naturalGasLeaksPage.open();

		assertTrue(naturalGasLeaksPage.getSelectedSurveyorName(testSetup
				.getSurveyor()));

		List<String> strLogList = naturalGasLeaksPage
				.getSurveyorLogList(testSetup.getSurveyor());

		for (String strLogName : strLogList) {
			assertTrue(strLogName.contains(testSetup.getLogFile()));
		}

		naturalGasLeaksPage.showViewMetadata(testSetup.getLogFile());

		assertTrue(naturalGasLeaksPage.getSurveyorNameFromMetadata(testSetup
				.getSurveyor()));
		assertTrue(naturalGasLeaksPage.getLogNameFromMetadata(testSetup
				.getLogFile()));
		assertTrue(naturalGasLeaksPage.getDurationFromMetadata(testSetup
				.getLogFile()));

		naturalGasLeaksPage.clickCloseMetadataButton();

		naturalGasLeaksPage.showSurveyorLogMap(testSetup.getSurveyor(),
				testSetup.getLogFile());

		TestSetup.slowdownInSeconds(15);

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"naturalGasLeaksPage_GDU001");
	}
	
	/**
	 * Test Case: GDU002 - Verify live google map is displayed after clicking
	 * 'Live Map' button on Main Page
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU002() {
		naturalGasLeaksPage.open();
		naturalGasLeaksPage.showSurveyorLiveMap(testSetup.getSurveyor(), strListView);

		TestSetup.slowdownInSeconds(15);
		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"naturalGasLeaksPage_GDU002_ListView");
		
		naturalGasLeaksPage.clickSelectSurveyorButton();
		naturalGasLeaksPage.showSurveyorLiveMap(testSetup.getSurveyor(), strCalView);

		TestSetup.slowdownInSeconds(15);
		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"naturalGasLeaksPage_GDU002_CalendarView");
	}

	/**
	 * Test Case: GDU003 - Verify Surveyor List window is getting closed after
	 * clicking 'Close' button
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU003() {
		naturalGasLeaksPage.open();
		assertFalse(naturalGasLeaksPage.closeSurveyorWindow());

		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"naturalGasLeaksPage_GDU003");
	}

	/**
	 * Test Case: GDU004 - Verify logs are getting refreshed after clicking
	 * 'Refresh' button
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU004() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.refreshSurveyorLogList(
				testSetup.getSurveyor2(), strListView));
		assertTrue(naturalGasLeaksPage.refreshSurveyorLogList(
				testSetup.getSurveyor2(), strCalView));
		/*
		 * need to add few more verifications if required
		 */
	}

	/**
	 * Test Case: GDU005 - Verify log's time changes according to change in
	 * 'Time zone' in 'List' and 'Calendar' view
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU005() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.changeTimezoneOfSurveyor(
				testSetup.getSurveyor(), testSetup.getTimezoneToSelect(),
				strListView));
		assertTrue(naturalGasLeaksPage.changeTimezoneOfSurveyor(
				testSetup.getSurveyor(),testSetup.getTimezoneToSelect(), strCalView));
	}
	
	/**
	 * Test Case: GDU006 -Verify the search functionality on Main page to search
	 * the log with invalid log name
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU006() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.searchLogFile(testSetup.getSurveyor(),
				testSetup.getLogFile2(), strInvalidSearch));
	}

	/**
	 * Test Case: GDU007 - Verify the search functionality to search the log
	 * with valid name
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU007() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.searchLogFile(testSetup.getSurveyor2(),
				testSetup.getLogFile2(), strValidSearch));
	}

	/**
	 * Test Case: GDU008 - Verify log is present in List as well as Calendar
	 * view
	 * 
	 * @author pmahajan
	 * 
	 */
//	@Test
	public void naturalGasLeaksPage_GDU008() {
		naturalGasLeaksPage.open();

		/*
		 * ---- Working not yet completed -----
		 */
		assertTrue(naturalGasLeaksPage.compareUserLogsInListCalendarView(testSetup.getSurveyor2()));
	}
	
	/**
	 * Test Case: GDU010 - Verify on selecting 'Show 'n' entries', the n entries
	 * are listed in logs list
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU010() {
		naturalGasLeaksPage.open();
		naturalGasLeaksPage.selectSurveyor(testSetup.getSurveyor2());
		assertTrue(naturalGasLeaksPage.showNLogEntries(testSetup
				.getShow10Entries()));

		assertTrue(naturalGasLeaksPage.showNLogEntries(testSetup
				.getShow25Entries()));
	}

	/**
	 * Test Case: GDU011 - Verify the search functionality to search the
	 * surveyor with valid name
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU011() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.searchSurveyor(testSetup.getSurveyor(),
				strValidSearch));
		assertTrue(naturalGasLeaksPage.searchSurveyor(testSetup.getLogFile(),
				strInvalidSearch));
	}

	/**
	 * Test Case: GDU012 - Verify live google map is displayed after clicking
	 * 'Live Map' button on Select Surveyor window
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU012() {
		naturalGasLeaksPage.open();
		naturalGasLeaksPage.showSurveyorWindowLiveMap(testSetup.getSurveyor());

		TestSetup.slowdownInSeconds(15);
		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"naturalGasLeaksPage_GDU012");
	}

	/**
	 * Test Case: GDU013 - Verify on selecting 'Show 'n' entries', the n
	 * surveyors are listed on Select Surveyor window
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU013() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.showNSurveyorEntries(testSetup
				.getShow10Entries()));
		assertTrue(naturalGasLeaksPage.showNSurveyorEntries(testSetup
				.getShow25Entries()));
	}
	
	/**
	 * Test Case: GDU014 - Verify 'Timezone' is not changed if 'Cancel' button
	 * is clicked
	 * 
	 * @author pmahajan
	 */
	@Test
	public void naturalGasLeaksPage_GDU014() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.cancelTimezoneWindow(testSetup.getSurveyor(),
				testSetup.getTimezoneToSelect()));
	}
	
	/**
	 * Test Case: GDU015 - Verify all logs are present for specified date in
	 * Calendar view
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU015() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage
				.compareUsersLogForSpecifiedDateInListCalendarView(
						testSetup.getSurveyor2(), testSetup.getShow25Entries()));
	}
	
	/**
	 * Test Case: GDU016 - Verify map page is opened when user clicks on map log
	 * button present for specified date in Calendar view
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU016() {
		naturalGasLeaksPage.open();
		naturalGasLeaksPage.showSurveyorMapLogFromCalendarView(
				testSetup.getSurveyor(), testSetup.getLogFile());

		TestSetup.slowdownInSeconds(15);
		ImagingUtility.takeScreenShot(driver, screenShotsDir,
				"naturalGasLeaksPage_GDU016");
	}

	/**
	 * Test Case: GDU017 - Verify Search functionality for valid log name in
	 * Calendar view
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU017() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.searchLogFileInCalendarView(
				testSetup.getSurveyor2(), testSetup.getLogFile2(),
				strValidSearch));
	}

	/**
	 * Test Case: GDU018 - Verify Search functionality for invalid log name in
	 * Calendar view
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU018() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.searchLogFileInCalendarView(
				testSetup.getSurveyor2(), testSetup.getLogFile(),
				strInvalidSearch));
	}
	
	/**
	 * Test Case: GDU019 - Verify Surveyor Logs window is getting closed after
	 * clicking 'Close' button in Calendar View
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU019() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage
				.closeSurveysWindowInCalendarView(testSetup.getSurveyor()));
	}
	
	/**
	 * Test Case: GDU020 - Verfiy on selecting 'Show 'n' entries', n logs are
	 * displayed in Calendar View for specified date window
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU020() {
		naturalGasLeaksPage.open();
		naturalGasLeaksPage.selectSurveyor(testSetup.getSurveyor2());
		assertTrue(naturalGasLeaksPage.showNLogListEntries(testSetup
				.getShow10Entries()));
	}

	
	/**
	 * Test Case: GDU022 - Verify log's time changes to UTC time if no 'Time
	 * zone' is selected in 'List' and 'Calendar' view
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU022() {
		naturalGasLeaksPage.open();
		assertTrue(naturalGasLeaksPage.selectNoTimezoneForSurveyor(
				testSetup.getSurveyor(), strListView));
		assertTrue(naturalGasLeaksPage.selectNoTimezoneForSurveyor(
				testSetup.getSurveyor(), strCalView));
	}
	
	/**
	 * Test Case: GDU023 - Verify Surveyor link is present after coming back
	 * from Live Map or Map Log page
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU023() {
		naturalGasLeaksPage.open();
		naturalGasLeaksPage.selectSurveyor(testSetup.getSurveyor());

		assertTrue(naturalGasLeaksPage.surveyorLinkPresentBackFromLiveMap(
				testSetup.getSurveyor(), strListView));

		assertTrue(naturalGasLeaksPage.surveyorLinkPresentBackFromLiveMap(
				testSetup.getSurveyor(), strCalView));

		naturalGasLeaksPage.surveyorLinkPresentBackFromMapLogListView(
				testSetup.getSurveyor(), testSetup.getLogFile());

		naturalGasLeaksPage.surveyorLinkPresentBackFromMapLogCalendarView(
				testSetup.getSurveyor(), testSetup.getLogFile());
	}
	
	/**
	 * Test Case: GDU024 - Verfiy on selecting 'Show 'n' entries', n logs are
	 * displayed in Calendar View for specified date window
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU024() {
		naturalGasLeaksPage.open();
		naturalGasLeaksPage.selectSurveyor(testSetup.getSurveyor());

		assertTrue(naturalGasLeaksPage.surveyorLinkPresentForLiveMap(
				testSetup.getSurveyor(), strListView));

		assertTrue(naturalGasLeaksPage.surveyorLinkPresentForLiveMap(
				testSetup.getSurveyor(), strCalView));

		naturalGasLeaksPage.surveyorLinkPresentForMapLogInListView(
				testSetup.getSurveyor(), testSetup.getLogFile());

		naturalGasLeaksPage.surveyorLinkPresentForMapLogInCalendarView(
				testSetup.getSurveyor(), testSetup.getLogFile());
	}
}
