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
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.PageFactory;

import common.source.HomePage;
import common.source.ImagingUtility;
import common.source.LoginPage;
import common.source.TestSetup;

/**
 * @author zlu
 * 
 *         For Login page, more test cases should be added later for the
 *         following categories: 1. right userName/wrong password 2. wrong
 *         userName 3. special chars as login name 4. some more negative test
 *         cases 5. etc.
 * 
 */
public class LoginPageTest {
	private static WebDriver driver;
	private static TestSetup testSetup;
	private static String baseURL;
	private static String screenShotsDir;
	private static boolean debug;

	private static LoginPage loginPage;

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
	 * Test Case: loginPage_TC0001 Check if a user with right loginName and
	 * password can successfully login and get to the home page Also check the
	 * normal logout successful
	 * 
	 */
	@Test
	public void loginPage_TC0001() {
		try {
			loginPage.open();
			if (debug) {
				testSetup.slowdownInSeconds(3);
			}

			HomePage homePage = loginPage.loginNormalAs(
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			assertTrue(homePage != null);
			PageFactory.initElements(driver, homePage);
			loginPage = homePage.logout();
			assertTrue(loginPage != null);

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"login_TC0001");
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_loginPage_TC0001");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: loginPage_TC0002 Empty password and login should fail
	 */
	@Test
	public void loginPage_TC0002() {
		try {
			PageFactory.initElements(driver, loginPage);
			loginPage.open();
			if (debug) {
				testSetup.slowdownInSeconds(3);
			}

			assertTrue(loginPage.loginUnsuccessfull(
					testSetup.getLoginUser0000(), ""));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"login_TC0002");

			if (debug) {
				testSetup.slowdownInSeconds(3);
			}
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_loginPage_TC0002");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}

	/**
	 * Test Case: loginPage_TC0003 Wrong password and login should fail
	 */
	@Test
	public void loginPage_TC0003() {
		try {
			PageFactory.initElements(driver, loginPage);
			loginPage.open();
			if (debug) {
				testSetup.slowdownInSeconds(3);
			}

			assertTrue(loginPage.loginUnsuccessfull(
					testSetup.getLoginUser0000(), "wrongPwd"));

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"login_TC0003");

			if (debug) {
				testSetup.slowdownInSeconds(3);
			}
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_loginPage_TC0003");
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
	}
}
