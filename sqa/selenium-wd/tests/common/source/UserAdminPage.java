/**
 * 
 */
package common.source;

import java.util.ArrayList;
import java.util.Hashtable;
import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.CacheLookup;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.Select;

/**
 * @author zlu
 * 
 */
public class UserAdminPage extends BasePage {
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRURLPath = "/adminlist/";
	public static final String STRHeadAdmin = "User Administration";
	public static final String STRShowUserList = "Show User List";
	public static final String STRShowSystemsList = "Show Systems List";
	private List<String> listTDUserIDs = null;
	private List<String> listTDSystems = null;
	private static final int timeoutSeconds = 20;
	private static final String STRNewUserId = "SQA";
	private static final String STRFirstName = "SQA";
	private static final String STRLastName = "Picarro";
	private static final String STRDisplayName = "SQA Picarro user";
	private static final String STRActive = "true";
	private static final String STRModifyUsrProfile = "Modify user profile";
	private static final String STRAnalyzerDescription = "SQADEMO2000 Analyzer";
	private static final String STRPasswordErrorMessage = "Password must equal Confirm Password.";

	@FindBy(how = How.XPATH, using = "//h3")
	@CacheLookup
	private WebElement headAdmin;

	@FindBy(how = How.ID, using = "id_userid_site")
	@CacheLookup
	private WebElement userIDSite;

	@FindBy(how = How.XPATH, using = "//a[@href='/stage/plogin']")
	@CacheLookup
	private WebElement linkSignOff;

	@FindBy(how = How.ID, using = "id_menu_drop")
	@CacheLookup
	private WebElement menuProcess;

	@FindBy(how = How.LINK_TEXT, using = "Home")
	@CacheLookup
	private WebElement linkHome;

	@FindBy(how = How.ID, using = "id_p3adminlist_usrBtn")
	private WebElement btnAdminUserList;

	@FindBy(how = How.ID, using = "id_p3adminlist_psysBtn")
	private WebElement btnAdminSystemList;

	@FindBy(how = How.ID_OR_NAME, using = "id_useridTable_length")
	private WebElement selectShowUsersList;

	@FindBy(how = How.XPATH, using = "//div[@id='id_useridTable_filter']/label/input")
	private WebElement inputSearchUser;

	@FindBy(how = How.XPATH, using = "//div[@id='id_psysTable_filter']/label/input")
	private WebElement inputSearchSystem;

	@FindBy(how = How.ID, using = "id_useridTable")
	private WebElement tableUserIDTable;

	@FindBy(how = How.CLASS_NAME, using = "paginate_disabled_next")
	private WebElement btnPageNext;

	@FindBy(how = How.CLASS_NAME, using = "paginate_disabled_previous")
	private WebElement btnPagePrevious;

	@FindBy(how = How.ID, using = "id_p3adminlist_addid")
	private WebElement btnAddUser;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'User ID')]/../div/input")
	private WebElement inputUserId;

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

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][1]")
	private WebElement cbAllowNGL;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][2]")
	private WebElement cbAllowNGLPrimeView;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][3]")
	private WebElement cbAllowRGP;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][4]")
	private WebElement cbAddForce;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][5]")
	private WebElement cbAllowUsrProfile;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][6]")
	private WebElement cbAllowUsrAdmn;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][7]")
	private WebElement cbActivateUsr;

	@FindBy(how = How.XPATH, using = "//a[@class='btn']")
	private WebElement btnRturnToUsrLst;

	@FindBy(how = How.XPATH, using = "//input[@type='submit' and @value='Save']")
	private WebElement btnSave;

	@FindBy(how = How.XPATH, using = "//td[@class='dataTables_empty']")
	private WebElement tableEmpty;

	@FindBy(how = How.XPATH, using = "//table[@id='id_useridTable']/tbody/tr[1]/td")
	private WebElement firstUserDetails;

	@FindBy(how = How.XPATH, using = "//table[@id='id_useridTable']/tbody/tr[1]/td[1]")
	private WebElement firstUserId;

	@FindBy(how = How.XPATH, using = "//table[@id='id_useridTable']/tbody/tr[1]/td[2]")
	private WebElement firstUserAcrive;

	@FindBy(how = How.ID, using = "id_p3adminlist_userid")
	private WebElement btnViewDetails;

	@FindBy(how = How.ID, using = "id_savBtn_")
	private WebElement btnModifyUser;

	@FindBy(how = How.CLASS_NAME, using = "help-inline")
	private WebElement msgUserProfileSaved;

	@FindBy(how = How.XPATH, using = "//table[@id='id_psysTable']/tbody/tr[1]/td[1]")
	private WebElement firstSystemName;

	@FindBy(how = How.XPATH, using = "//table[@id='id_psysTable']/tbody/tr[1]/td[2]")
	private WebElement firstSystemActive;

	@FindBy(how = How.XPATH, using = "//table[@id='id_psysTable']/tbody/tr[1]/td[3]")
	private WebElement firstSystemDescription;

	@FindBy(how = How.ID, using = "id_p3adminlist_psys")
	private WebElement btnSystemViewDetails;

	@FindBy(how = How.XPATH, using = "//select[@name='id_psysTable_length']")
	private WebElement showNSystemEntries;

	@FindBy(how = How.XPATH, using = "//select[@name='id_useridTable_length']")
	private WebElement showNUserEntries;

	@FindBy(how = How.ID, using = "id_p3adminlist_Close_psys")
	private WebElement btnCloseSystemDetails;

	@FindBy(how = How.ID, using = "id_inp_desc")
	private WebElement inputSystemDescritionDetails;

	@FindBy(how = How.ID, using = "id_inp_active")
	private WebElement inputSystemActiveDetails;

	@FindBy(how = How.XPATH, using = "//table[@id='id_useridTable']/tbody/tr")
	private List<WebElement> userList;

	@FindBy(how = How.XPATH, using = "//table[@id='id_psysTable']/tbody/tr")
	private List<WebElement> systemList;

	private By byAddButton = By.xpath("//button[@id='id_p3adminlist_addid']");
	private By bySaveButton = By
			.xpath("//input[@type='submit' and @value='Save']");
	private By byAdmnUsrLstBtn = By
			.xpath("//button[@id='id_p3adminlist_usrBtn']");
	private By byFormUserDetailsLoaded = By
			.xpath("//div[@class='modal hide fade in']");

	private String strXpathUserTableRows = "//table[@id='id_useridTable']/tbody/tr";
	private String strXpathSystemTableRows = "//table[@id='id_psysTable']/tbody/tr";
	private String strFirstUserDetails = "//table[@id='id_useridTable']/tbody/tr[1]/td";

	public UserAdminPage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;

		System.out.println("\nThe UserAdminPage URL is: " + this.strPageURL);
	}

	public List<String> getUserList() {
		this.listTDUserIDs = new ArrayList<String>();
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}
		List<WebElement> listTRUsers = driver.findElements(By
				.xpath(this.strXpathUserTableRows));

		WebElement tdUserID;
		for (int i = 1; i <= listTRUsers.size(); i++) {
			tdUserID = driver.findElement(By.xpath(this.strXpathUserTableRows
					+ "[" + i + "]" + "/td[1]"));
			listTDUserIDs.add(tdUserID.getText());
		}

		return listTDUserIDs;
	}

	public List<String> getSystemList() throws Exception {
		this.listTDSystems = new ArrayList<String>();
		if (this.btnAdminSystemList.getText().equals(STRShowSystemsList)) {
			this.btnAdminSystemList.click();
			TestSetup.slowdownInSeconds(3);
		}

		Select selectNoOfSystemEntries = new Select(this.showNSystemEntries);
		selectNoOfSystemEntries.selectByValue("100");

		List<WebElement> listTRSystems = driver.findElements(By
				.xpath(this.strXpathSystemTableRows));

		WebElement tdSystem;
		for (int i = 1; i <= listTRSystems.size(); i++) {
			tdSystem = driver.findElement(By.xpath(this.strXpathSystemTableRows
					+ "[" + i + "]" + "/td[1]"));
			listTDSystems.add(tdSystem.getText());
		}
		return listTDSystems;
	}

	public String createNewUserAndReturnToUser(String randomNumber,
			String password) throws Exception {
		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}
		TestSetup.slowdownInSeconds(1);
		findElement(driver, byAddButton, timeoutSeconds);
		this.btnAddUser.click();

		String currentWH = driver.getWindowHandle();
		driver.switchTo().frame("id_iframe");
		findElement(driver, bySaveButton, timeoutSeconds);

		String newUserId = STRNewUserId + randomNumber;
		this.inputUserId.sendKeys(newUserId);

		// select the text present
		this.inputFirstName.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputFirstName.sendKeys(Keys.BACK_SPACE);
		this.inputFirstName.sendKeys(STRFirstName);

		// select the text present
		this.inputLastName.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputLastName.sendKeys(Keys.BACK_SPACE);
		this.inputLastName.sendKeys(STRLastName);

		// select the text present
		this.inputDisplayName.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputDisplayName.sendKeys(Keys.BACK_SPACE);
		this.inputDisplayName.sendKeys(STRDisplayName);

		this.inputPassword.sendKeys(password);
		this.inputConfirmPassword.sendKeys(password);

		this.cbAllowNGL.click();
		this.cbAllowNGLPrimeView.click();
		this.cbAllowRGP.click();
		this.cbAddForce.click();
		this.cbAllowUsrProfile.click();
		this.cbAllowUsrAdmn.click();
		this.cbActivateUsr.click();

		this.btnSave.click();
		this.btnRturnToUsrLst.click();

		return newUserId;
	}

	public boolean isUserCreatedSuccessfully(String userId) {
		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}
		findElement(driver, byAddButton, timeoutSeconds);
		this.inputSearchUser.sendKeys(userId);

		List<WebElement> listUserDetails = driver.findElements(By
				.xpath(this.strFirstUserDetails));

		String tdUserID;
		for (int i = 1; i <= listUserDetails.size(); i++) {
			tdUserID = driver.findElement(
					By.xpath(this.strFirstUserDetails + "[" + i + "]"))
					.getText();
			i++;
			if (tdUserID.contains(userId)) {
				if (driver
						.findElement(
								By.xpath(this.strFirstUserDetails + "[" + i
										+ "]")).getText().contains(STRActive)) {
					i++;
					if (driver
							.findElement(
									By.xpath(this.strFirstUserDetails + "[" + i
											+ "]")).getText()
							.contains(STRDisplayName)) {
						i++;
						if (driver
								.findElement(
										By.xpath(this.strFirstUserDetails + "["
												+ i + "]")).getText()
								.contains(STRFirstName)) {
							i++;
							if (driver
									.findElement(
											By.xpath(this.strFirstUserDetails
													+ "[" + i + "]")).getText()
									.contains(STRLastName)) {
								return true;
							}
						}
					}
				}
			}
		}
		return false;
	}

	public LoginPage logout() throws Exception {
		TestSetup.slowdownInSeconds(2);
		driver.switchTo().defaultContent();
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		this.linkSignOff.click();
		LoginPage loginPage = new LoginPage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, loginPage);
		return loginPage;
	}

	public boolean isUserAdminPageOpen() throws Exception {
		TestSetup.slowdownInSeconds(3);
		return (this.headAdmin.getText().contentEquals(STRHeadAdmin));
	}

	public HomePage goBackToHomePage() throws Exception {
		this.menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		this.linkHome.click();
		HomePage homePage = new HomePage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, homePage);
		return homePage;
	}

	public boolean searchUser(String userId) {
		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}
		findElement(driver, byAddButton, timeoutSeconds);
		this.inputSearchUser.sendKeys(userId);

		return this.firstUserId.getText().contentEquals(userId);
	}

	public void clickOnViewDetails() {
		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}
		findElement(driver, byAddButton, timeoutSeconds);
		this.btnViewDetails.click();
	}

	public void clickOnModifyUser() {
		findElement(driver, byFormUserDetailsLoaded, timeoutSeconds);
		this.btnModifyUser.click();
	}

	public void getFocusOnFrame() {
		String currentWH = driver.getWindowHandle();
		driver.switchTo().frame("id_iframe");
	}

	public void uncheckUserActive() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (this.cbActivateUsr.isSelected())
			this.cbActivateUsr.click();
		this.btnSave.click();
	}

	public void checkUserActive() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (!(this.cbActivateUsr.isSelected()))
			this.cbActivateUsr.click();
		this.btnSave.click();
	}

	public void uncheckUserProfile() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (this.cbAllowUsrProfile.isSelected())
			this.cbAllowUsrProfile.click();
		this.btnSave.click();
	}

	public void checkUserProfile() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (!(this.cbAllowUsrProfile.isSelected()))
			this.cbAllowUsrProfile.click();
		this.btnSave.click();
	}

	public void checkAllPermission() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (!(this.cbAllowNGL.isSelected()))
			this.cbAllowNGL.click();
		if (!(this.cbAllowNGLPrimeView.isSelected()))
			this.cbAllowNGLPrimeView.click();
		if (!(this.cbAllowRGP.isSelected()))
			this.cbAllowRGP.click();
		if (!(this.cbAddForce.isSelected()))
			this.cbAddForce.click();
		if (!(this.cbAllowUsrProfile.isSelected()))
			this.cbAllowUsrProfile.click();
		if (!(this.cbAllowUsrAdmn.isSelected()))
			this.cbAllowUsrAdmn.click();
		if (!(this.cbActivateUsr.isSelected()))
			this.cbActivateUsr.click();

		this.btnSave.click();
	}

	public void clickOnReturnToUserList() {
		findElement(driver, bySaveButton, timeoutSeconds);
		this.btnRturnToUsrLst.click();
		findElement(driver, byAddButton, timeoutSeconds);
	}

	public boolean deactivateUser(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		if (this.cbActivateUsr.isEnabled()) {
			this.uncheckUserActive();
			clickOnReturnToUserList();
			return true;
		} else
			return false;
	}

	public void activateUser(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		this.checkUserActive();
		clickOnReturnToUserList();
	}

	public void uncheckUserAdmin() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (this.cbAllowUsrAdmn.isSelected())
			this.cbAllowUsrAdmn.click();
		this.btnSave.click();
	}

	public void uncheckNGL() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (this.cbAllowNGL.isSelected())
			this.cbAllowNGL.click();
		this.btnSave.click();
	}

	public void uncheckNGLPrime() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (this.cbAllowNGLPrimeView.isSelected())
			this.cbAllowNGLPrimeView.click();
		this.btnSave.click();
	}

	public void checkNGLPrime() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (!(this.cbAllowNGLPrimeView.isSelected()))
			this.cbAllowNGLPrimeView.click();
		this.btnSave.click();
	}

	public void uncheckRGP() {
		findElement(driver, bySaveButton, timeoutSeconds);
		if (this.cbAllowRGP.isSelected())
			this.cbAllowRGP.click();
		this.btnSave.click();
	}

	public boolean isUserActive(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		return this.firstUserAcrive.getText().contains(STRActive);
	}

	public void removeUserProfilePermission(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		this.uncheckUserProfile();
	}

	public void provideUserProfilePermission(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		this.checkUserProfile();
	}

	public void removeUserAdminPermission(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		this.uncheckUserAdmin();
	}

	public void removeNGLPermission(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		this.uncheckNGL();
	}

	public void removeRGPPermission(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		this.uncheckRGP();
	}

	public void provideAllPermission(String userId) throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		this.checkAllPermission();
	}

	public boolean isUserProfileModifiedSuccesfull(String userId)
			throws Exception {
		String userProfileSuccess = "User Profile changes for " + userId
				+ " successful.";
		return this.msgUserProfileSaved.getText().contains(userProfileSuccess);
	}

	public boolean isModifyUserProfilePage() throws Exception {
		return this.headAdmin.getText().contains(STRModifyUsrProfile);
	}

	public boolean searchAnalyzer(String analyzerName) {
		if (this.btnAdminSystemList.getText().equals(STRShowSystemsList)) {
			this.btnAdminSystemList.click();
			TestSetup.slowdownInSeconds(3);
		}
		this.inputSearchSystem.sendKeys(analyzerName);
		return this.firstSystemName.getText().contentEquals(analyzerName);
	}

	public boolean isSystemDescriptionValid() throws Exception {
		return this.firstSystemDescription.getText().contains(
				STRAnalyzerDescription);
	}

	public boolean isSystemActive() throws Exception {
		return this.firstSystemActive.getText().contains(STRActive);
	}

	public boolean isViewSystemDetailsValid() throws Exception {
		this.btnSystemViewDetails.click();
		TestSetup.slowdownInSeconds(1);
		if (this.inputSystemDescritionDetails.getAttribute("value").contains(
				STRAnalyzerDescription)) {
			if (this.inputSystemActiveDetails.getAttribute("value").contains(
					STRActive))
				return true;
			else
				return false;
		} else
			return false;
	}

	public void clickOnCloseSystemDetails() throws Exception {
		this.btnCloseSystemDetails.click();
		TestSetup.slowdownInSeconds(1);
	}

	public boolean showNUserEntries(String numberOfEntries) throws Exception {
		boolean result = false;

		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}
		findElement(driver, byAddButton, timeoutSeconds);

		Select selectNoOfUserEntries = new Select(this.showNUserEntries);
		selectNoOfUserEntries.selectByValue(numberOfEntries);

		if (Integer.toString(this.userList.size()).compareTo(numberOfEntries) == 0)
			result = true;
		if (Integer.toString(this.userList.size()).compareTo(numberOfEntries) == -1)
			result = true;
		return result;
	}

	public boolean showNSystemEntries(String numberOfEntries) throws Exception {
		boolean result = false;

		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminSystemList.getText().equals(STRShowSystemsList)) {
			this.btnAdminSystemList.click();
			TestSetup.slowdownInSeconds(3);
		}

		Select selectNoOfSystemEntries = new Select(this.showNSystemEntries);
		selectNoOfSystemEntries.selectByValue(numberOfEntries);

		if (Integer.toString(this.systemList.size()).compareTo(numberOfEntries) == 0)
			result = true;
		if (Integer.toString(this.systemList.size()).compareTo(numberOfEntries) == -1)
			result = true;
		return result;
	}

	public boolean providePassword(String userId, String password)
			throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		findElement(driver, bySaveButton, timeoutSeconds);
		this.inputPassword.sendKeys(password);
		this.btnSave.click();
		return this.msgUserProfileSaved.getText().contains(
				STRPasswordErrorMessage);
	}

	public boolean isUserDetailsModified(String userId,
			Hashtable<String, String> usrProfile) {
		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}
		findElement(driver, byAddButton, timeoutSeconds);
		this.inputSearchUser.sendKeys(userId);

		List<WebElement> listUserDetails = driver.findElements(By
				.xpath(this.strFirstUserDetails));

		String tdUserID;
		for (int i = 1; i <= listUserDetails.size(); i++) {
			tdUserID = driver.findElement(
					By.xpath(this.strFirstUserDetails + "[" + i + "]"))
					.getText();
			i++;
			if (tdUserID.contains(userId)) {
				if (driver
						.findElement(
								By.xpath(this.strFirstUserDetails + "[" + i
										+ "]")).getText().contains(STRActive)) {
					i++;
					if (driver
							.findElement(
									By.xpath(this.strFirstUserDetails + "[" + i
											+ "]")).getText()
							.contains(usrProfile.get("Display Name"))) {
						i++;
						if (driver
								.findElement(
										By.xpath(this.strFirstUserDetails + "["
												+ i + "]")).getText()
								.contains(usrProfile.get("First Name"))) {
							i++;
							if (driver
									.findElement(
											By.xpath(this.strFirstUserDetails
													+ "[" + i + "]")).getText()
									.contains(usrProfile.get("Last Name"))) {
								return true;
							}
						}
					}
				}
			}
		}
		return false;
	}

	public boolean providePasswordConfirmPassword(String userId, String password)
			throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.searchUser(userId);
		this.clickOnViewDetails();
		this.clickOnModifyUser();
		this.getFocusOnFrame();
		findElement(driver, bySaveButton, timeoutSeconds);
		this.inputPassword.sendKeys(password);
		this.inputConfirmPassword.sendKeys(password);
		this.btnSave.click();
		return this.msgUserProfileSaved.getText().contains(
				STRPasswordErrorMessage);
	}
}
