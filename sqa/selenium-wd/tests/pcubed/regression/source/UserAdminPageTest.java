/**
 * 
 */
package pcubed.regression.source;

import static org.junit.Assert.*;

import java.util.List;

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
import common.source.NaturalGasLeaksPage;
import common.source.ReportGenerationPortalPage;
import common.source.TestSetup;
import common.source.UserAdminPage;
import common.source.UserProfilePage;

/**
 * @author zlu
 * 
 */
public class UserAdminPageTest {
	private static WebDriver driver;
	private static TestSetup testSetup;
	private static String baseURL;
	private static String screenShotsDir;
	private static boolean debug;
	private static LoginPage loginPage;
	private static UserAdminPage userAdminPage;
	private static HomePage homePage;
	private static NaturalGasLeaksPage naturalGasLeakPage;
	private static ReportGenerationPortalPage reportGenerationPortalPage;
	private static UserProfilePage userProfilePage;
	private List<String> userList = null;
	private List<String> systemList = null;

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
		// Revert back the permissions modified to original
		userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
				testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
		userAdminPage.open();
		userAdminPage.provideAllPermission(testSetup.getLoginUser00A());
		assertTrue(testSetup.getLoginUser00A()
				+ " : user profile changes not saved successfully!",
				userAdminPage.isUserProfileModifiedSuccesfull(testSetup
						.getLoginUser00A()));
		userAdminPage.logout();
	}

	/**
	 * Test Case: UserAdminPage_TC0001 1. login as admin 2. The admin page is
	 * accessiable 3. Get a list with all the users on the system 4. Compare the
	 * list with the pre-built sample users and they should be consistent
	 * 
	 */
	@Test
	public void UserAdminPage_TC0001() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			userList = userAdminPage.getUserList();

			System.out.println("\nUser List:");
			for (String strUser : userList) {
				System.out.println(strUser);
			}

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"UserAdminPage_TC0001");
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_TC0001");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_TC0002 1. login as admin 2. The admin page is
	 * accessiable 3. Get a list with all the systems 4. Compare the list with
	 * the pre-built sample systems and they should be consistent
	 * 
	 */
	@Test
	public void UserAdminPage_TC0002() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			userAdminPage.open();
			TestSetup.slowdownInSeconds(3);
			systemList = userAdminPage.getSystemList();

			System.out.println("\nSystem List: ");
			for (String strList : systemList) {
				System.out.println(strList);
			}

			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"UserAdminPage_TC0002");
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_TC0002");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM001 Verify Admin is able to create new user,
	 * valid user details are displayed in 'Users List' table and new user is
	 * able to login the application
	 * 
	 */
	@Test
	public void UserAdminPage_ADM001() {
		try {
			String userId;

			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();

			userId = userAdminPage.createNewUserAndReturnToUser(
					testSetup.getRandomNumber(), testSetup.getLoginPwd0000());
			assertTrue(userId + " : user creation unsuccessfully!",
					userAdminPage.isUserCreatedSuccessfully(userId));

			loginPage = userAdminPage.logout();

			homePage = loginPage.loginNormalAs(userId,
					testSetup.getLoginPwd0000());
			assertTrue("Login was unsuccessfull!", homePage.isHomePageOpen());

			naturalGasLeakPage = homePage.goToNGLPage();
			assertTrue("User not navigated to NGL page!",
					naturalGasLeakPage.isNGLPageOpen());
			homePage = naturalGasLeakPage.goBackToHomePage();

			reportGenerationPortalPage = homePage.goToRGPPage();
			assertTrue("User not navigated to RGP page!",
					reportGenerationPortalPage.isRGPPageOpen());
			homePage = reportGenerationPortalPage.goBackToHomePage();

			userAdminPage = homePage.goToUserAdminPage();
			assertTrue("User not navigated to User Administration page!",
					userAdminPage.isUserAdminPageOpen());
			homePage = userAdminPage.goBackToHomePage();

			userProfilePage = homePage.goToUserProfilePage();
			assertTrue("User not navigated to User Profile page!",
					userProfilePage.isUserProfilePageOpen());

			loginPage = userProfilePage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM001");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM002 Verify deactivated user is not able to
	 * login the application and active status is FALSE for that user
	 * 
	 */
	@Test
	public void UserAdminPage_ADM002() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			userAdminPage.deactivateUser(testSetup.getLoginUser00A());
			assertFalse(testSetup.getLoginUser00A()
					+ " : user not deactivated!",
					userAdminPage.isUserActive(testSetup.getLoginUser00A()));
			loginPage = userAdminPage.logout();

			assertTrue("Deactive user " + testSetup.getLoginUser00A()
					+ " logged in successfully!", loginPage.loginUnsuccessfull(
					testSetup.getLoginUser00A(), testSetup.getLoginPwd00A()));
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM002");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM003 Verify 'User Profile' link is not present
	 * when user don't have 'Allow User Profile' permission
	 * 
	 */
	@Test
	public void UserAdminPage_ADM003() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			userAdminPage.removeUserProfilePermission(testSetup
					.getLoginUser00A());
			assertTrue(testSetup.getLoginUser00A()
					+ " : user profile changes not saved successfully!",
					userAdminPage.isUserProfileModifiedSuccesfull(testSetup
							.getLoginUser00A()));
			loginPage = userAdminPage.logout();

			homePage = loginPage.loginNormalAs(testSetup.getLoginUser00A(),
					testSetup.getLoginPwd00A());
			assertFalse("User Profile link is present!",
					homePage.isUserProfileLinkPresent());
			loginPage = homePage.clickOnSignOffLink();

			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser00A(), testSetup.getLoginPwd00A());
			userAdminPage.open();
			userAdminPage.provideUserProfilePermission(testSetup
					.getLoginUser00A());
			assertFalse(testSetup.getLoginUser00A()
					+ " : was able to modify user profile!",
					userAdminPage.isModifyUserProfilePage());
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM003");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM004 Verify 'User Administration' link is not
	 * present when user don't have 'Allow Administration' permission
	 * 
	 */
	@Test
	public void UserAdminPage_ADM004() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			userAdminPage
					.removeUserAdminPermission(testSetup.getLoginUser00A());
			assertTrue(testSetup.getLoginUser00A()
					+ " : user profile changes not saved successfully!",
					userAdminPage.isUserProfileModifiedSuccesfull(testSetup
							.getLoginUser00A()));
			loginPage = userAdminPage.logout();

			homePage = loginPage.loginNormalAs(testSetup.getLoginUser00A(),
					testSetup.getLoginPwd00A());
			assertFalse("User Administration link is present!",
					homePage.isUserAdministrationLinkPresent());
			loginPage = homePage.clickOnSignOffLink();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM004");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM005 Verify 'Picarro Surveyor for Natural Gas
	 * Leaks' link is not present when user don't have 'Allow Picarro Surveyor
	 * for Natural Gas Leaks' permission
	 * 
	 */
	@Test
	public void UserAdminPage_ADM005() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			userAdminPage.removeNGLPermission(testSetup.getLoginUser00A());
			assertTrue(testSetup.getLoginUser00A()
					+ " : user profile changes not saved successfully!",
					userAdminPage.isUserProfileModifiedSuccesfull(testSetup
							.getLoginUser00A()));
			loginPage = userAdminPage.logout();

			homePage = loginPage.loginNormalAs(testSetup.getLoginUser00A(),
					testSetup.getLoginPwd00A());
			assertFalse("NGL link is present!", homePage.isNGLLinkPresent());
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM005");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM006 Verify 'Picarro Surveyor™ Report
	 * Generation Portal' link is not present when user don't have 'Allow
	 * Picarro Surveyor™ Report Generation Portal' permission
	 * 
	 */
	@Test
	public void UserAdminPage_ADM006() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			userAdminPage.removeRGPPermission(testSetup.getLoginUser00A());
			assertTrue(testSetup.getLoginUser00A()
					+ " : user profile changes not saved successfully!",
					userAdminPage.isUserProfileModifiedSuccesfull(testSetup
							.getLoginUser00A()));
			loginPage = userAdminPage.logout();

			homePage = loginPage.loginNormalAs(testSetup.getLoginUser00A(),
					testSetup.getLoginPwd00A());
			assertFalse("NGL link is present!", homePage.isRGPLinkPresent());
			loginPage = homePage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM006");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM007 Verify user is not allowed to deactivate
	 * himself
	 * 
	 */
	@Test
	public void UserAdminPage_ADM007() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser00A(), testSetup.getLoginPwd00A());
			userAdminPage.open();
			assertFalse(testSetup.getLoginUser00A()
					+ " : user deactivated himself!",
					userAdminPage.deactivateUser(testSetup.getLoginUser00A()));
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM007");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM008 Verify analyzer details are present on
	 * 'Systems List' page
	 * 
	 */
	@Test
	public void UserAdminPage_ADM008() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			TestSetup.slowdownInSeconds(3);
			systemList = userAdminPage.getSystemList();

			for (int i = 1; i <= systemList.size(); i++) {
				if (systemList.get(i).contentEquals(testSetup.getAnalyzer())) {
					assertTrue(testSetup.getAnalyzer()
							+ " not able to search in the System list!",
							userAdminPage.searchAnalyzer(testSetup
									.getAnalyzer()));
					assertTrue(testSetup.getAnalyzer()
							+ " description not matched!",
							userAdminPage.isSystemDescriptionValid());
					assertTrue(testSetup.getAnalyzer() + " is not active!",
							userAdminPage.isSystemActive());
					assertTrue(testSetup.getAnalyzer()
							+ " view details are not valid!",
							userAdminPage.isViewSystemDetailsValid());
					userAdminPage.clickOnCloseSystemDetails();
					break;
				} else {
					assertFalse(testSetup.getAnalyzer()
							+ " not present in the System list!", systemList
							.get(i).contentEquals(testSetup.getAnalyzer()));
				}
			}
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM008");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM009 Verify Search functionality on 'User
	 * List' page to search the valid user
	 * 
	 */
	@Test
	public void UserAdminPage_ADM009() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			assertTrue(
					"Not able to search user : " + testSetup.getLoginUser00A(),
					userAdminPage.searchUser(testSetup.getLoginUser00A()));
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM009");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM010 Verify on selecting 'Show 'n' entries',
	 * the user list shows n entries in 'User List' table
	 * 
	 */
	@Test
	public void UserAdminPage_ADM010() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			assertTrue(
					"10 or less than 10 users should be present in users list table!",
					userAdminPage.showNUserEntries(testSetup.getShow10Entries()));
			assertTrue(
					"25 or less than 25 users should be present in users list table!",
					userAdminPage.showNUserEntries(testSetup.getShow25Entries()));
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM010");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM011 Verify Search functionality on 'User
	 * List' page to search the invalid user
	 * 
	 */
	@Test
	public void UserAdminPage_ADM011() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			assertFalse("Search invalid user : " + testSetup.getAnalyzer()
					+ " was successfull!",
					userAdminPage.searchUser(testSetup.getAnalyzer()));
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM011");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM012 Verify on selecting 'Show 'n' entries',
	 * the systems list shows n entries in 'Systems List' table
	 * 
	 */
	@Test
	public void UserAdminPage_ADM012() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(
					"10 or less than 10 Systems should be present in systems list table!",
					userAdminPage.showNSystemEntries(testSetup
							.getShow10Entries()));
			assertTrue(
					"25 or less than 25 Systems should be present in systems list table!",
					userAdminPage.showNSystemEntries(testSetup
							.getShow25Entries()));
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM012");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM013 Verify Search functionality on 'System
	 * List' page to search the valid analyzer
	 * 
	 */
	@Test
	public void UserAdminPage_ADM013() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			TestSetup.slowdownInSeconds(3);
			assertTrue(
					"Not able to search analyzer : " + testSetup.getAnalyzer(),
					userAdminPage.searchAnalyzer(testSetup.getAnalyzer()));
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM013");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM014 Verify Search functionality on 'System
	 * List' page to search the invalid analyzer
	 * 
	 */
	@Test
	public void UserAdminPage_ADM014() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			TestSetup.slowdownInSeconds(3);
			assertFalse(
					"Search invalid system : " + testSetup.getLoginUser00A()
							+ " was successfull!",
					userAdminPage.searchAnalyzer(testSetup.getLoginUser00A()));
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM014");
			fail("Exception Caught : " + e.getMessage());
		}
	}

	/**
	 * Test Case: UserAdminPage_ADM015 Verify admin cannot modify user details
	 * when same input value not provided to password/confirm password fields
	 * 
	 */
	@Test
	public void UserAdminPage_ADM015() {
		try {
			userAdminPage = loginPage.loginAndNavigateToUserAdmin(baseURL,
					testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
			userAdminPage.open();
			assertTrue("", userAdminPage.providePassword(
					testSetup.getLoginUser00A(), testSetup.getLoginPwd0000()));
			loginPage = userAdminPage.logout();
		} catch (Exception e) {
			ImagingUtility.takeScreenShot(driver, screenShotsDir,
					"Exception_UserAdminPage_ADM015");
			fail("Exception Caught : " + e.getMessage());
		}
	}
}
