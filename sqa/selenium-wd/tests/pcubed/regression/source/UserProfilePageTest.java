/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.assertTrue;

import java.util.Hashtable;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.PageFactory;

import common.source.ImagingUtility;
import common.source.LoginPage;
import common.source.TestSetup;
import common.source.UserProfilePage;

/**
 * @author zlu
 * 
 */
public class UserProfilePageTest {
	private static WebDriver driver;
	private static TestSetup testSetup;
	private static String baseURL;
	private static String screenShotsDir;
	private static boolean debug;
	private static LoginPage loginPage;
	private static UserProfilePage userProfilePage;

	private Hashtable<String, String> userProfileHT;

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

		userProfilePage = new UserProfilePage(driver, baseURL);
		PageFactory.initElements(driver, userProfilePage);
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
	 * Test Case: UserProfilePage_TC0001 1. login as admin 2. Check the login
	 * user profile
	 * 
	 */
	@Test
	public void UserProfilePage_TC0001() {
		try {
			userProfilePage.open();
			userProfileHT = userProfilePage.getUserProfile();

			System.out.println("\nLogin User Profile:");
			for (String key : userProfileHT.keySet()) {
				System.out.println(key + " : " + userProfileHT.get(key));
			}

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"UserProfilePage_TC0001");
		} catch (Exception e) {
			assertTrue("Exception Caught : " + e.getMessage(), false);
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserProfilePage_TC0001");
		}
	}

}
