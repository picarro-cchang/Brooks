/**
 * 
 */
package common.source;

import java.util.ArrayList;
import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;

/**
 * @author zlu
 * 
 */
public class UserAdminPage extends BasePage {
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRURLPath = "/adminlist/";
	public static final String STRShowUserList = "Show User List";
	public static final String STRShowSystemsList = "Show Systems List";

	private List<String> listTDUserIDs = null;
	private List<String> listTDSystems = null;

	private static final int timeoutSeconds = 20;
	private static TestSetup testSetup;
	private static final String STRNewUserId = "SQA"
			+ testSetup.getRandomNumber();
	private static final String STRFirstName = "SQA";
	private static final String STRLastName = "Picarro";
	private static final String STRDisplayName = "SQA Picarro user";
	private static final String STRPwd = "sqa#Picarro%0";
	private static final String STRUsrActive = "true";

	@FindBy(how = How.ID, using = "id_p3adminlist_usrBtn")
	private WebElement btnAdminUserList;

	@FindBy(how = How.ID, using = "id_p3adminlist_psysBtn")
	private WebElement btnAdminSystemList;

	@FindBy(how = How.ID_OR_NAME, using = "id_useridTable_length")
	private WebElement selectShowUsersList;

	@FindBy(how = How.XPATH, using = "//div[@id='id_useridTable_filter']/label/input")
	private WebElement inputSearchBox;

	@FindBy(how = How.ID, using = "id_useridTable")
	private WebElement tableUserIDTable;

	@FindBy(how = How.CLASS_NAME, using = "paginate_disabled_next")
	private WebElement btnPageNext;

	@FindBy(how = How.CLASS_NAME, using = "paginate_disabled_previous")
	private WebElement btnPagePrevious;

	@FindBy(how = How.ID, using = "id_p3adminlist_addid")
	private WebElement btnAddUser;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'User ID')]/../div[@class='input']/input")
	private WebElement inputUserId;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'First Name')]/../div[@class='input']/input")
	private WebElement inputFirstName;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'Last Name')]/../div[@class='input']/input")
	private WebElement inputLastName;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'Display Name')]/../div[@class='input']/input")
	private WebElement inputDisplayName;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'Password')]/../div[@class='input']/input[@placeholder='Password']")
	private WebElement inputPassword;

	@FindBy(how = How.XPATH, using = "//label[contains(text(),'Confirm Password')]/../div[@class='input']/input")
	private WebElement inputConfirmPassword;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][1]")
	private WebElement inputAllowNGL;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][2]")
	private WebElement inputAllowNGLPrimeView;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][3]")
	private WebElement inputAllowRPT;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][4]")
	private WebElement inputAddForce;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][5]")
	private WebElement inputAllowUsrProfile;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][6]")
	private WebElement inputAllowUsrAdmn;

	@FindBy(how = How.XPATH, using = "//input[@type='checkbox'][7]")
	private WebElement inputActivateUsr;

	@FindBy(how = How.XPATH, using = "//a[@class='btn']")
	private WebElement btnRturnToUsrLst;

	@FindBy(how = How.XPATH, using = "//input[@type='submit' and @value='Save']")
	private WebElement btnSave;

	@FindBy(how = How.XPATH, using = "//td[@class='dataTables_empty']")
	private WebElement tableEmpty;

	@FindBy(how = How.XPATH, using = "//table[@id='id_useridTable']/tbody/tr[1]/td")
	private WebElement firstUserDetails;

	private By byAddButton = By.xpath("//button[@id='id_p3adminlist_addid']");
	private By bySaveButton = By
			.xpath("//input[@type='submit' and @value='Save']");
	private By byAdmnUsrLstBtn = By
			.xpath("//button[@id='id_p3adminlist_usrBtn']");

	private String strXpathUserTableRows = "//table[@id='id_useridTable']/tbody/tr";
	private String strXpathSystemTableRows = "//table[@id='id_psysTable']/tbody/tr";
	private String strFirstUserDetails = "//table[@id='id_useridTable']/tbody/tr[1]/td";

	public UserAdminPage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;
		System.out.println("\nThe UserAdminPage URL is: " + this.strPageURL);
	}

	public List<String> getUserList() throws Exception {
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

			TestSetup.slowdownInSeconds(5);
		}

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

	public boolean createNewUser() throws Exception {
		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}

		findElement(driver, byAddButton, timeoutSeconds);
		this.btnAddUser.click();
		findElement(driver, bySaveButton, timeoutSeconds);

		this.inputUserId.sendKeys(STRNewUserId);

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

		this.inputPassword.sendKeys(STRPwd);
		this.inputConfirmPassword.sendKeys(STRPwd);

		this.inputAllowNGL.click();
		this.inputAllowNGLPrimeView.click();
		this.inputAllowRPT.click();
		this.inputAddForce.click();
		this.inputAllowUsrProfile.click();
		this.inputAllowUsrAdmn.click();
		this.inputActivateUsr.click();

		this.btnSave.click();
		this.btnRturnToUsrLst.click();

		findElement(driver, byAdmnUsrLstBtn, timeoutSeconds);
		if (this.btnAdminUserList.equals(STRShowUserList)) {
			this.btnAdminUserList.click();
		}
		findElement(driver, byAddButton, timeoutSeconds);
		this.inputSearchBox.sendKeys(STRNewUserId);

		List<WebElement> listUserDetails = driver.findElements(By
				.xpath(this.strFirstUserDetails));

		String tdUserID;
		for (int i = 1; i <= listUserDetails.size(); i++) {
			tdUserID = driver.findElement(
					By.xpath(this.strFirstUserDetails + "[" + i + "]"))
					.getText();
			i++;
			System.out.println("User Id : " + tdUserID);
			if (tdUserID.contains(STRNewUserId)) {
				if (driver
						.findElement(
								By.xpath(this.strFirstUserDetails + "[" + i
										+ "]")).getText()
						.contains(STRUsrActive)) {
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
}
