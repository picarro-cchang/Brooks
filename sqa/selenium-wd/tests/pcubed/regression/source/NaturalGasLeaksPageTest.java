/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.util.List;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.PageFactory;

import common.source.ImagingUtility;
import common.source.LoginPage;
import common.source.NaturalGasLeaksPage;
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
		screenShotsDir = "./screenshots/";
		debug = testSetup.isRunningDebug();
		driver.manage().deleteAllCookies();
		driver.manage().window().maximize();

		loginPage = new LoginPage(driver, baseURL);
		PageFactory.initElements(driver, loginPage);
		loginPage.open();
		loginPage.loginNormalAs(testSetup.getLoginUser0000(),
				testSetup.getLoginPwd0000());

		naturalGasLeaksPage = new NaturalGasLeaksPage(driver, baseURL);
		PageFactory.initElements(driver, naturalGasLeaksPage);

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
		naturalGasLeaksPage.logout();
	}

	/**
	 * Test Case: naturalGasLeaksPage_TC0001 Get the list of the surveyors Fail
	 * the case if can't find one specific surveyor
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_TC0001() {
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			List<String> strSurveyorList = naturalGasLeaksPage
					.getSurveyorList();

			System.out.println("\nThe Surveyor list: ");
			for (String strSurveyor : strSurveyorList) {
				System.out.println(strSurveyor);
			}

			boolean surveyorFound = false;
			for (String strSurveyor : strSurveyorList) {
				if (strSurveyor.equals(testSetup.getSurveyor())) {
					surveyorFound = true;
					break;
				} else {
					continue;
				}
			}

			if (!surveyorFound) {
				fail("Didn't find the surveyor: " + testSetup.getSurveyor());
			}

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_TC0001");
			TestSetup.slowdownInSeconds(1);
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_TC0001");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: naturalGasLeaksPage_TC0002 Get the log file list for a
	 * specific surveyor
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_TC0002() {
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			System.out.println("\nThe selected surveyor is: "
					+ testSetup.getSurveyor());

			List<String> strLogList = naturalGasLeaksPage
					.getSurveyorLogList(testSetup.getSurveyor());

			System.out.println("\nThe log file list: ");
			for (String strLogName : strLogList) {
				System.out.println(strLogName);
			}

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_TC0002");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_TC0002");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: naturalGasLeaksPage_TC0003 Show the map log for a specific
	 * surveyor
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_TC0003() {
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			naturalGasLeaksPage.showSurveyorLogMap(testSetup.getSurveyor(),
					testSetup.getLogFile());

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_TC0003");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_TC0003");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(testSetup.getSurveyor() + " not found!",
					naturalGasLeaksPage.getSelectedSurveyorName(testSetup
							.getSurveyor()));

			List<String> strLogList = naturalGasLeaksPage
					.getSurveyorLogList(testSetup.getSurveyor());

			for (String strLogName : strLogList) {
				assertTrue(
						testSetup.getLogFile()
								+ " log not found for surveyor : "
								+ testSetup.getSurveyor(),
						strLogName.contains(testSetup.getLogFile()));
			}
			naturalGasLeaksPage.showViewMetadata(testSetup.getLogFile());

			assertTrue(testSetup.getSurveyor()
					+ " not present in Metadata details!",
					naturalGasLeaksPage.getSurveyorNameFromMetadata(testSetup
							.getSurveyor()));
			assertTrue(testSetup.getLogFile()
					+ " log not present in Metadata details!",
					naturalGasLeaksPage.getLogNameFromMetadata(testSetup
							.getLogFile()));
			assertTrue("Duration details not present in Metadata view!",
					naturalGasLeaksPage.getDurationFromMetadata(testSetup
							.getLogFile()));

			naturalGasLeaksPage.clickCloseMetadataButton();
			naturalGasLeaksPage.showSurveyorLogMap(testSetup.getSurveyor(),
					testSetup.getLogFile());

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_GDU001");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU001");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			naturalGasLeaksPage.showSurveyorLiveMap(testSetup.getSurveyor(),
					strListView);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_GDU002_ListView");

			naturalGasLeaksPage.clickSelectSurveyorButton();
			naturalGasLeaksPage.showSurveyorLiveMap(testSetup.getSurveyor(),
					strCalView);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_GDU002_CalendarView");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU002");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertFalse("Surveyors list window is not closed!",
					naturalGasLeaksPage.closeSurveyorWindow());
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU003");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue("Refresh button not refreshing the page!",
					naturalGasLeaksPage.searchLogFile(testSetup.getSurveyor2(),
							testSetup.getLogFile2(), strValidSearch));
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_GDU004");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU004");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(
					"Log's time in List view not changed according to timezone!",
					naturalGasLeaksPage.changeTimezoneOfSurveyor(
							testSetup.getSurveyor(),
							testSetup.getTimezoneToSelect(), strListView));
			assertTrue(
					"Log's time in Calendar view not changed according to timezone!",
					naturalGasLeaksPage.changeTimezoneOfSurveyor(
							testSetup.getSurveyor(),
							testSetup.getTimezoneToSelect(), strCalView));
			naturalGasLeaksPage.closeSurveysWindow();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU005");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(
					"Searched Invalid log file : " + testSetup.getLogFile2(),
					naturalGasLeaksPage.searchLogFile(testSetup.getSurveyor(),
							testSetup.getLogFile2(), strInvalidSearch));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU006");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(
					"Not able to search log file : " + testSetup.getLogFile2(),
					naturalGasLeaksPage.searchLogFile(testSetup.getSurveyor2(),
							testSetup.getLogFile2(), strValidSearch));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU007");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: GDU008 - Verify log is present in List as well as Calendar
	 * view
	 * 
	 * @author pmahajan
	 * 
	 */
	@Test
	public void naturalGasLeaksPage_GDU008() {
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			/*
			 * ---- Working not yet completed -----
			 */
			assertTrue(naturalGasLeaksPage
					.compareUserLogsInListCalendarView(testSetup.getSurveyor2()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU008");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			naturalGasLeaksPage.selectSurveyor(testSetup.getSurveyor2());
			assertTrue("10 logs should be present in logs table!",
					naturalGasLeaksPage.showNLogEntries(testSetup
							.getShow10Entries()));

			assertTrue("25 logs should be present in logs table!",
					naturalGasLeaksPage.showNLogEntries(testSetup
							.getShow25Entries()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU010");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(testSetup.getSurveyor()
					+ " : surveyor not found in list!",
					naturalGasLeaksPage.searchSurveyor(testSetup.getSurveyor(),
							strValidSearch));
			assertTrue(testSetup.getLogFile()
					+ " : invalid surveyor was present in list!",
					naturalGasLeaksPage.searchSurveyor(testSetup.getLogFile(),
							strInvalidSearch));
			naturalGasLeaksPage.closeSurveyorListWindow();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU011");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			naturalGasLeaksPage.showSurveyorWindowLiveMap(testSetup
					.getSurveyor());

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_GDU012");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU012");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue("10 surveyors should be present in logs table!",
					naturalGasLeaksPage.showNSurveyorEntries(testSetup
							.getShow10Entries()));
			assertTrue("25 surveyors should be present in logs table!",
					naturalGasLeaksPage.showNSurveyorEntries(testSetup
							.getShow25Entries()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU013");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: GDU014 - Verify 'Timezone' is not changed if 'Cancel' button
	 * is clicked
	 * 
	 * @author pmahajan
	 */
	@Test
	public void naturalGasLeaksPage_GDU014() {
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertFalse("Timezone modified - Not Expected!",
					naturalGasLeaksPage.cancelTimezoneWindow(testSetup
							.getSurveyor(), testSetup.getTimezoneNotToSelect()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU014");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue("All logs are not present on 18th Feb 2014 for "
					+ testSetup.getSurveyor2(),
					naturalGasLeaksPage
							.compareUsersLogForSpecifiedDateInListCalendarView(
									testSetup.getSurveyor2(),
									testSetup.getShow25Entries()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU015");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			naturalGasLeaksPage.showSurveyorMapLogFromCalendarView(
					testSetup.getSurveyor(), testSetup.getLogFile());

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"naturalGasLeaksPage_GDU016");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU016");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(testSetup.getLogFile2() + " log file not searched!",
					naturalGasLeaksPage.searchLogFileInCalendarView(
							testSetup.getSurveyor2(), testSetup.getLogFile2(),
							strValidSearch));
			naturalGasLeaksPage.closeSurveysWindow();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU017");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(testSetup.getLogFile2()
					+ " invalid log file got searched!", naturalGasLeaksPage
					.searchLogFileInCalendarView(testSetup.getSurveyor2(),
							testSetup.getLogFile(), strInvalidSearch));
			naturalGasLeaksPage.closeSurveysWindow();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU018");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue("Surveyor list window present in Calendar view!",
					naturalGasLeaksPage
							.closeSurveysWindowInCalendarView(testSetup
									.getSurveyor()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU019");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			naturalGasLeaksPage.selectSurveyor(testSetup.getSurveyor2());
			assertTrue(
					"10 or less than 10 logs should be present in logs table for Calendar view!",
					naturalGasLeaksPage.showNLogListEntries(testSetup
							.getShow10Entries()));
			assertTrue(
					"25 or less than 25 logs should be present in logs table for Calendar view!",
					naturalGasLeaksPage.showNLogListEntries(testSetup
							.getShow25Entries()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU020");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(
					"Log's time in List view not changed according to timezone!",
					naturalGasLeaksPage.selectNoTimezoneForSurveyor(
							testSetup.getSurveyor(), strListView));
			assertTrue(
					"Log's time in Calendar view not changed according to timezone!",
					naturalGasLeaksPage.selectNoTimezoneForSurveyor(
							testSetup.getSurveyor(), strCalView));
			naturalGasLeaksPage.closeSurveysWindow();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU022");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			naturalGasLeaksPage.selectSurveyor(testSetup.getSurveyor());

			assertTrue(testSetup.getSurveyor()
					+ " : surveyor link not present!",
					naturalGasLeaksPage.surveyorLinkPresentBackFromLiveMap(
							testSetup.getSurveyor(), strListView));
			assertTrue(testSetup.getSurveyor()
					+ " : surveyor link not present!",
					naturalGasLeaksPage.surveyorLinkPresentBackFromLiveMap(
							testSetup.getSurveyor(), strCalView));

			assertTrue(testSetup.getSurveyor()
					+ " : surveyor link not present!",
					naturalGasLeaksPage
							.surveyorLinkPresentBackFromMapLogListView(
									testSetup.getSurveyor(),
									testSetup.getLogFile()));
			assertTrue(testSetup.getSurveyor()
					+ " : surveyor link not present!",
					naturalGasLeaksPage
							.surveyorLinkPresentBackFromMapLogCalendarView(
									testSetup.getSurveyor(),
									testSetup.getLogFile()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU023");
			fail("Exception Caught : " + e.getMessage());
		}
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
		try {
			naturalGasLeaksPage = loginPage.loginAndNavigateToNGL(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			naturalGasLeaksPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(
					testSetup.getSurveyor() + " : surveyor link not present!",
					naturalGasLeaksPage.surveyorLinkPresentForLiveMap(
							testSetup.getSurveyor(), strListView));
			assertTrue(
					testSetup.getSurveyor() + " : surveyor link not present!",
					naturalGasLeaksPage.surveyorLinkPresentForLiveMap(
							testSetup.getSurveyor(), strCalView));

			assertTrue(testSetup.getSurveyor()
					+ " : surveyor link not present!",
					naturalGasLeaksPage.surveyorLinkPresentForMapLogInListView(
							testSetup.getSurveyor(), testSetup.getLogFile()));
			assertTrue(testSetup.getSurveyor()
					+ " : surveyor link not present!",
					naturalGasLeaksPage
							.surveyorLinkPresentForMapLogInCalendarView(
									testSetup.getSurveyor(),
									testSetup.getLogFile()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_naturalGasLeaksPage_GDU024");
			fail("Exception Caught : " + e.getMessage());
		}
	}
}
