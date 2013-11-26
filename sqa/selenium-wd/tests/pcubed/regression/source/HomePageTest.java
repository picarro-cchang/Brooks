/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.*;
import junit.framework.Assert;
import junit.framework.TestCase;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.PageFactory;

import common.source.HomePage;
import common.source.ImagingUtility;
import common.source.LoginPage;
import common.source.NaturalGasLeaksPage;
import common.source.ReportGenerationPortalPage;
import common.source.TestSetup;

/**
 * @author zlu
 *
 */
public class HomePageTest {
	private static WebDriver driver;
	private static TestSetup testSetup;
	private static String baseURL;
	private static String screenShotsDir;
	private static boolean debug;
	
	private static LoginPage loginPage;
	private static HomePage homePage;

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
		
		homePage = new HomePage(driver, baseURL);
		PageFactory.initElements(driver, homePage);
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
	 * Test Case: homePage_TC0001
	 * Check the major links or accesses are available if login as admin user
	 * When Bug 444 fixed, should check the page title for each page
	 * Bug 444: Page Title is "Picarro P-Cubed" for all the pages
	 */
	@Test
	public void homePage_TC0001() {
		homePage.open();
		if (debug) { testSetup.slowdownInSeconds(5);}
		assertTrue(homePage.isPageLoad());
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "homePage_TC0001");
		
		NaturalGasLeaksPage pageNGL = homePage.goToNGLPage();
		if (debug) { testSetup.slowdownInSeconds(5);}
		assertTrue(driver.getCurrentUrl().equals(pageNGL.getStrPageURL()));
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "homePage_TC0001_NaturalGasLeaksPage");
		
		PageFactory.initElements(driver, homePage);
		ReportGenerationPortalPage pageRGP = homePage.goToRGPPage();
		if (debug) { testSetup.slowdownInSeconds(15);}
		assertTrue(driver.getCurrentUrl().equals(pageRGP.getStrPageURL()));
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "homePage_TC0001_ReportGenerationPortalPage");
		
		PageFactory.initElements(driver, homePage);
		HomePage pageHome = homePage.goBackToHomePage();
		if (debug) { testSetup.slowdownInSeconds(5);}
		assertTrue(driver.getCurrentUrl().equals(pageHome.getStrPageURL()));
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "homePage_TC0001_BackToHomePage");
	}
	
	/**
	 * Test Case: homePage_TC0002
	 * Check logout and get to the login page
	 */	
	@Test
	public void homePage_TC0002() {
		
	}
}
