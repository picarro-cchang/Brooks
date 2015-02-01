/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

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
import common.source.UserAdminPage;
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
	private static UserAdminPage userAdminPage;
	private Hashtable<String, String> userProfileHT;
	private static String newUserId;

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

		userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
				testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
		userAdminPage.open();

		newUserId = userAdminPage.createNewUserAndReturnToUser(
				testSetup.getRandomNumber(), testSetup.getLoginPwd0000());
		assertTrue(newUserId + " : new user creation unsuccessfully!",
				userAdminPage.isUserCreatedSuccessfully(newUserId));
		loginPage = userAdminPage.logout();
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
		userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
				testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
		userAdminPage.open();
		TestSetup.slowdownInSeconds(1);

		// Revert back the password
		userAdminPage.providePasswordConfirmPassword(newUserId,
				testSetup.getLoginPwd0000());
		assertTrue(newUserId + " : user profile not modified!",
				userAdminPage.isUserProfileModifiedSuccesfull(newUserId));
		loginPage = userAdminPage.logout();
	}

	/**
	 * Test Case: UserProfilePage_TC0001 1. login as admin 2. Check the login
	 * user profile
	 * 
	 */
	@Test
	public void UserProfilePage_TC0001() {
		try {
			userProfilePage = loginPage.loginAndNavigateToUserProfile(baseURL,
					newUserId, testSetup.getLoginPwd0000());
			userProfilePage.open();
			TestSetup.slowdownInSeconds(5);
			userProfileHT = userProfilePage.getUserProfile();

			System.out.println("\nLogin User Profile:");
			for (String key : userProfileHT.keySet()) {
				System.out.println(key + " : " + userProfileHT.get(key));
			}

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"UserProfilePage_TC0001");
			userProfilePage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_TC0001");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserProfilePage_UPF001 Verify modified user details are
	 * displayed on 'User Profile' page
	 * 
	 */
	@Test
	public void UserProfilePage_UPF001() {
		try {
			userProfilePage = loginPage.loginAndNavigateToUserProfile(baseURL,
					newUserId, testSetup.getLoginPwd0000());
			userProfilePage.open();
			TestSetup.slowdownInSeconds(5);

			userProfilePage.modifyUserDetails(testSetup.getRandomNumber());
			assertTrue(newUserId + " : user profile not modified!",
					userProfilePage.isUserProfileModifiedSuccesfull(newUserId));

			Hashtable<String, String> userNewProfile = userProfilePage
					.getUserProfile();
			userAdminPage = userProfilePage.goToUserAdminPage();
			assertTrue(newUserId
					+ " : user modified profile not present in Users List!",
					userAdminPage.isUserDetailsModified(newUserId,
							userNewProfile));

			userProfilePage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_UPF001");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserProfilePage_UPF002 Verify user is able to change the
	 * password and able to login with new password
	 */
	@Test
	public void UserProfilePage_UPF002() {
		try {
			userProfilePage = loginPage.loginAndNavigateToUserProfile(baseURL,
					newUserId, testSetup.getLoginPwd0000());
			userProfilePage.open();
			TestSetup.slowdownInSeconds(5);
			userProfilePage.providePasswordConfirmPassword(newUserId);
			assertTrue(newUserId + " : user profile not modified!",
					userProfilePage.isUserProfileModifiedSuccesfull(newUserId));
			loginPage = userProfilePage.logout();

			userProfilePage = loginPage.loginAndNavigateToUserProfile(baseURL,
					newUserId, newUserId);
			userProfilePage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue("Login Successful!",
					userProfilePage.isUserProfilePageOpen());
			loginPage = userProfilePage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_UPF002");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserProfilePage_UPF003 Verify error message is displayed when
	 * password and confirm password does not match
	 * 
	 */
	@Test
	public void UserProfilePage_UPF003() {
		try {
			userProfilePage = loginPage.loginAndNavigateToUserProfile(baseURL,
					newUserId, testSetup.getLoginPwd0000());
			userProfilePage.open();
			TestSetup.slowdownInSeconds(5);

			assertTrue(
					"Error message not displayed when different password and confirm password was provided!",
					userProfilePage.providePassword(testSetup.getLoginPwd0000()));
			userProfilePage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_UPF003");
			fail("Exception Caught : " + e.getMessage());
		}
	}
}
