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

import common.source.ImagingUtility;
import common.source.LoginPage;
import common.source.UserAdminPage;
import common.source.TestSetup;

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
		//screenShotsDir = ".\\screenshots\\";
		screenShotsDir = "./screenshots/";
		debug = testSetup.isRunningDebug();
		driver.manage().deleteAllCookies();
		driver.manage().window().maximize();
		
		loginPage = new LoginPage(driver, baseURL);
		PageFactory.initElements(driver, loginPage);
		loginPage.open();
		loginPage.loginNormalAs(testSetup.getLoginUser0000(), testSetup.getLoginPwd0000());
		
		userAdminPage = new UserAdminPage(driver, baseURL);
		PageFactory.initElements(driver, userAdminPage);
		
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
	 * Test Case: UserAdminPage_TC0001
	 * 1. login as admin 
	 * 2. The admin page is accessiable
	 * 3. Get a list with all the users on the system
	 * 4. Compare the list with the pre-built sample users and they should be consistent
	 *  
	 */
	@Test
	public void UserAdminPage_TC0001() {
		userAdminPage.open();
		userList = userAdminPage.getUserList();
		
		System.out.println("\nUser List:");
		for (String strUser: userList) {
			System.out.println(strUser);
		}		
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "UserAdminPage_TC0001");
	}
	
	/**
	 * Test Case: UserAdminPage_TC0002
	 * 1. login as admin 
	 * 2. The admin page is accessiable
	 * 3. Get a list with all the systems
	 * 4. Compare the list with the pre-built sample systems and they should be consistent
	 *  
	 */
	@Test
	public void UserAdminPage_TC0002() {
		userAdminPage.open();
		TestSetup.slowdownInSeconds(3);
		systemList = userAdminPage.getSystemList();
		
		System.out.println("\nSystem List: ");
		for (String strList: systemList) {
			System.out.println(strList);
		}
		
		ImagingUtility.takeScreenShot(driver, screenShotsDir, "UserAdminPage_TC0002");
	}	
	
	/**
	 * Test Case: UserAdminPage_TC0003
	 * 1. login as non-admin user
	 * 2. The admin page is not accessiable
	 *  
	 */
	@Test
	public void UserAdminPage_TC0003() {
	}
}
