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
	 * Test Case: naturalGasLeaksPage_TC0001
	 * Get the list of the surveyors
	 * Fail the case if can't find one specific surveyor 
	 * 
	 */
	@Test
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
	@Test
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
	@Test
	public void naturalGasLeaksPage_TC0003() {
		naturalGasLeaksPage.open();
		
		naturalGasLeaksPage.showSurveyorLogMap(testSetup.getSurveyor(), testSetup.getLogFile());
		
		TestSetup.slowdownInSeconds(15);
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "naturalGasLeaksPage_TC0003");
	}
}
