/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.*;

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
	@Test
	public void ReportGenerationPortalPage_TC0001() {
		pageReportGeneration.open();
		testSetup.slowdownInSeconds(15);
		
		pageReportGeneration.makeReport(testSetup.getSurveyor(), testSetup.getHTReportData());
		testSetup.slowdownInSeconds(3);
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "ReportGenerationPortalPage_TC0001");
	}
	
	/**
	 * Test Case: ReportGenerationPortalPage_TC0002
	 * Check a report created
	 * More scenarios and variations should be added ...
	 *  
	 */
	@Test
	public void ReportGenerationPortalPage_TC0002() {
		pageReportGeneration.open();
		testSetup.slowdownInSeconds(15);
		
		pageReportGeneration.viewReport(testSetup.getHTReportData().get("Title"));
		
		testSetup.slowdownInSeconds(5);
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "ReportGenerationPortalPage_TC0002_02");
	}
}
