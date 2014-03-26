/**
 * 
 */
package common.source;

import org.openqa.selenium.By;
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
public class HomePage extends BasePage {
	public static final String STRWrongPage = "Not Home, Wrong Page!";
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRHeadHome = "Home";
	public static final String STRURLPath = "/index/";
	private static final int timeoutSeconds = 30;

	@FindBy(how = How.XPATH, using = "//h3")
	@CacheLookup
	private WebElement headHome;

	@FindBy(how = How.ID, using = "id_userid_site")
	@CacheLookup
	private WebElement userIDSite;

	@FindBy(how = How.XPATH, using = "//a[@href='/stage/plogin']")
	@CacheLookup
	private WebElement linkSignOff;

	@FindBy(how = How.ID, using = "id_menu_drop")
	@CacheLookup
	private WebElement menuProcess;

	// @FindBy(how = How.XPATH, using = "//span[@id='id_menu_list']/li[2]/a")
	@FindBy(how = How.XPATH, using = "//a[contains(text(),'Natural Gas Leaks')]")
	private WebElement linkNGL;

	// @FindBy(how = How.XPATH, using = "//span[@id='id_menu_list']/li[3]/a")
	@FindBy(how = How.XPATH, using = "//a[contains(text(),'Report Generation Portal')]")
	private WebElement linkRGP;

	@FindBy(how = How.LINK_TEXT, using = "Home")
	@CacheLookup
	private WebElement linkHome;

	@FindBy(how = How.LINK_TEXT, using = "User Administration")
	@CacheLookup
	private WebElement linkUserAdmin;

	@FindBy(how = How.LINK_TEXT, using = "User Profile")
	@CacheLookup
	private WebElement linkUserProfile;

	private By byUserProfileLink = By
			.xpath("//a[contains(text(),'User Profile')]");

	private By byUserAdminLink = By
			.xpath("//a[contains(text(),'User Administration')]");

	private By byNGLLink = By
			.xpath("//a[contains(text(),'Natural Gas Leaks')]");

	private By byRGPLink = By
			.xpath("//a[contains(text(),'Report Generation Portal')]");

	public HomePage(WebDriver driver, String baseUrl) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseUrl;
		this.strPageURL = this.strBaseURL + STRURLPath;

		System.out.println("\nThe HomePage URL is: " + this.strPageURL);
	}

	public LoginPage logout() throws Exception {
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		this.linkSignOff.click();
		LoginPage loginPage = new LoginPage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, loginPage);
		return loginPage;
	}

	public NaturalGasLeaksPage goToNGLPage() throws Exception {
		this.menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		this.linkNGL.click();
		NaturalGasLeaksPage naturalGasLeaksPage = new NaturalGasLeaksPage(
				this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, naturalGasLeaksPage);
		return naturalGasLeaksPage;
	}

	public ReportGenerationPortalPage goToRGPPage() {
		menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		linkRGP.click();
		ReportGenerationPortalPage reportGenerationPortalPage = new ReportGenerationPortalPage(
				this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, reportGenerationPortalPage);
		return reportGenerationPortalPage;
	}

	public HomePage goBackToHomePage() throws Exception {
		this.menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		this.linkHome.click();
		HomePage homePage = new HomePage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, homePage);
		return homePage;
	}

	public UserAdminPage goToUserAdminPage() throws Exception {
		TestSetup.slowdownInSeconds(2);
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		this.linkUserAdmin.click();
		UserAdminPage userAdminPage = new UserAdminPage(this.driver,
				this.strBaseURL);
		PageFactory.initElements(this.driver, userAdminPage);
		return userAdminPage;
	}

	public UserProfilePage goToUserProfilePage() throws Exception {
		TestSetup.slowdownInSeconds(2);
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		this.linkUserProfile.click();
		UserProfilePage userProfilePage = new UserProfilePage(this.driver,
				this.strBaseURL);
		PageFactory.initElements(this.driver, userProfilePage);
		return userProfilePage;
	}

	public UserProfilePage clickOnUserProfileLink() throws Exception {
		this.linkUserProfile.click();
		UserProfilePage userProfilePage = new UserProfilePage(this.driver,
				this.strBaseURL);
		PageFactory.initElements(this.driver, userProfilePage);
		return userProfilePage;
	}

	public boolean isHomePageOpen() throws Exception {
		TestSetup.slowdownInSeconds(3);
		return (this.headHome.getText().contentEquals(STRHeadHome));
	}

	public boolean isUserProfileLinkPresent() throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		return (isElementPresent(driver, byUserProfileLink, timeoutSeconds));
	}

	public boolean isUserAdministrationLinkPresent() throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		return (isElementPresent(driver, byUserAdminLink, timeoutSeconds));
	}

	public boolean isNGLLinkPresent() throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		if (isElementPresent(driver, byNGLLink, timeoutSeconds)) {
			this.linkNGL.click();
			NaturalGasLeaksPage naturalGasLeaksPage = new NaturalGasLeaksPage(
					driver, this.strBaseURL);
			PageFactory.initElements(this.driver, naturalGasLeaksPage);
			return naturalGasLeaksPage.isNGLPageOpen();
		} else
			return false;
	}

	public boolean isRGPLinkPresent() throws Exception {
		TestSetup.slowdownInSeconds(1);
		this.menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		return (isElementPresent(driver, byRGPLink, timeoutSeconds));
	}

	public LoginPage clickOnSignOffLink() throws Exception {
		this.linkSignOff.click();
		LoginPage loginPage = new LoginPage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, loginPage);
		return loginPage;
	}
}