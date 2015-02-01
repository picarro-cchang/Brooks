/**
 * 
 */
package common.source;

import java.util.Hashtable;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.CacheLookup;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
import org.openqa.selenium.support.PageFactory;

/**
 * @author zlu
 * 
 */
public class UserProfilePage extends BasePage {
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRURLPath = "/userprofile/";
	public static final String STRHeadProfile = "User Profile";
	private static final String STRFirstName = "SQA";
	private static final String STRLastName = "Picarro";
	private static final String STRDisplayName = "SQA Picarro user";
	private Hashtable<String, String> htUserProfile = null;
	private static final String STRPasswordErrorMessage = "Password must equal Confirm Password.";
	private static final int timeoutSeconds = 20;

	@FindBy(how = How.XPATH, using = "//h3")
	private WebElement headProfile;

	@FindBy(how = How.ID, using = "id_menu_drop")
	private WebElement menuProcess;

	@FindBy(how = How.LINK_TEXT, using = "Home")
	private WebElement linkHome;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'User ID')]/../div/input")
	private WebElement inputUserID;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'First Name')]/../div/input")
	private WebElement inputFirstName;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'Last Name')]/../div/input")
	private WebElement inputLastName;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'Display Name')]/../div/input")
	private WebElement inputDisplayName;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'Password')]/../div/input[@placeholder='Password']")
	private WebElement inputPassword;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'Confirm Password')]/../div/input")
	private WebElement inputConfirmPassword;

	@FindBy(how = How.XPATH, using = "//input[@type='submit' and @value='Save']")
	private WebElement btnSave;

	@FindBy(how = How.ID, using = "id_userid_site")
	private WebElement userIDSite;

	//@FindBy(how = How.XPATH, using = "//a[@href='/pgestage/plogin']")
	@FindBy(how = How.XPATH, using = "//li[4]/a")
	private WebElement linkSignOff;

	@FindBy(how = How.CLASS_NAME, using = "help-inline")
	private WebElement msgUserProfileSaved;

	@FindBy(how = How.LINK_TEXT, using = "User Administration")
	private WebElement linkUserAdmin;

	private By bySaveButton = By
			.xpath("//input[@type='submit' and @value='Save']");

	public UserProfilePage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;

		this.htUserProfile = new Hashtable<String, String>();
		System.out.println("\nThe UserProfilePage URL is: " + this.strPageURL);
	}

	public Hashtable<String, String> getUserProfile() throws Exception {
		String currentWH = driver.getWindowHandle();
		WebElement iFrame = driver.findElement(By.id("id_iframe"));
		driver.switchTo().frame(iFrame);
		findElement(driver, bySaveButton, timeoutSeconds);

		this.htUserProfile.put("User ID",
				this.inputUserID.getAttribute("value"));
		this.htUserProfile.put("First Name",
				this.inputFirstName.getAttribute("value"));
		this.htUserProfile.put("Last Name",
				this.inputLastName.getAttribute("value"));
		this.htUserProfile.put("Display Name",
				this.inputDisplayName.getAttribute("value"));

		driver.switchTo().window(currentWH);
		return this.htUserProfile;
	}

	public boolean isUserProfilePageOpen() throws Exception {
		TestSetup.slowdownInSeconds(3);
		return (this.headProfile.getText().contentEquals(STRHeadProfile));
	}

	public HomePage goBackToHomePage() throws Exception {
		this.menuProcess.click();
		driver.switchTo().defaultContent();
		TestSetup.slowdownInSeconds(1);
		this.linkHome.click();
		HomePage homePage = new HomePage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, homePage);
		return homePage;
	}

	public UserAdminPage goToUserAdminPage() throws Exception {
		TestSetup.slowdownInSeconds(1);
		driver.switchTo().defaultContent();
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		this.linkUserAdmin.click();
		UserAdminPage userAdminPage = new UserAdminPage(this.driver,
				this.strBaseURL);
		PageFactory.initElements(this.driver, userAdminPage);
		return userAdminPage;
	}

	public LoginPage logout() throws Exception {
		TestSetup.slowdownInSeconds(1);
		driver.switchTo().defaultContent();
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		this.linkSignOff.click();
		LoginPage loginPage = new LoginPage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, loginPage);
		return loginPage;
	}

	public void modifyUserDetails(String strModify) throws Exception {
		String currentWH = driver.getWindowHandle();
		WebElement iFrame = driver.findElement(By.id("id_iframe"));
		driver.switchTo().frame(iFrame);
		findElement(driver, bySaveButton, timeoutSeconds);

		// select the text present
		this.inputFirstName.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputFirstName.sendKeys(Keys.BACK_SPACE);
		this.inputFirstName.sendKeys(STRFirstName + strModify);

		// select the text present
		this.inputLastName.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputLastName.sendKeys(Keys.BACK_SPACE);
		this.inputLastName.sendKeys(STRLastName + strModify);

		// select the text present
		this.inputDisplayName.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputDisplayName.sendKeys(Keys.BACK_SPACE);
		this.inputDisplayName.sendKeys(STRDisplayName + strModify);

		this.btnSave.click();
		driver.switchTo().window(currentWH);
		TestSetup.slowdownInSeconds(1);
	}

	public boolean isUserProfileModifiedSuccesfull(String userId)
			throws Exception {
		String currentWH = driver.getWindowHandle();
		WebElement iFrame = driver.findElement(By.id("id_iframe"));
		driver.switchTo().frame(iFrame);
		findElement(driver, bySaveButton, timeoutSeconds);

		String userProfileSuccess = "User Profile changes for " + userId
				+ " successful.";
		boolean result = this.msgUserProfileSaved.getText().contains(
				userProfileSuccess);
		driver.switchTo().window(currentWH);
		return result;
	}

	public boolean providePassword(String password) throws Exception {
		String currentWH = driver.getWindowHandle();
		WebElement iFrame = driver.findElement(By.id("id_iframe"));
		driver.switchTo().frame(iFrame);
		findElement(driver, bySaveButton, timeoutSeconds);
		this.inputPassword.sendKeys(password);
		this.btnSave.click();
		boolean result = this.msgUserProfileSaved.getText().contains(
				STRPasswordErrorMessage);
		driver.switchTo().window(currentWH);
		return result;
	}

	public void providePasswordConfirmPassword(String newPassword)
			throws Exception {
		String currentWH = driver.getWindowHandle();
		WebElement iFrame = driver.findElement(By.id("id_iframe"));
		driver.switchTo().frame(iFrame);
		findElement(driver, bySaveButton, timeoutSeconds);
		this.inputPassword.sendKeys(newPassword);
		this.inputConfirmPassword.sendKeys(newPassword);
		this.btnSave.click();
		driver.switchTo().window(currentWH);
		TestSetup.slowdownInSeconds(1);
	}
}
