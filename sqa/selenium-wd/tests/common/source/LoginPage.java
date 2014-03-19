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
 *         More general login related code should be added here
 * 
 */
public class LoginPage extends BasePage {
	public static final String STRWrongPage = "Not Login, wrong Page!";
	public static final String STRLabelBtnSignin = "Click to sign in";
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRLoginInValid = "The User/Password combination entered is not valid";
	public static final String STRURLPath = "/plogin/";
	private static LoginPage loginPage;
	
	@FindBy(how = How.XPATH, using = "//div/input")
	@CacheLookup
	private WebElement inputUserID;

	@FindBy(how = How.XPATH, using = "//div[2]/input")
	@CacheLookup
	private WebElement inputPassword;

	@FindBy(how = How.XPATH, using = "//td/input")
	@CacheLookup
	private WebElement btnSignin;

	@FindBy(how = How.CLASS_NAME, using = "help-inline")
	@CacheLookup
	private WebElement loginInValid;

	public LoginPage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;

		System.out.println("\nThe LoginPage URL is: " + this.strPageURL);
	}

	public HomePage loginNormalAs(String userName, String password)
			throws Exception {
		inputUserID.sendKeys(userName);
		inputPassword.sendKeys(password);
		btnSignin.click();
		// temporary solution now for getting rid of the
		// "Picarro End User Agreement" page.
		if (driver.getCurrentUrl().contains("/eula/")) {
			driver.findElement(By.xpath("//td[2]/input")).click();
		}
		return (new HomePage(this.driver, this.strBaseURL));
	}

	public boolean loginAsWrongPassword(String userName, String password)
			throws Exception {
		this.inputUserID.sendKeys(userName);
		this.inputPassword.sendKeys(password);
		this.btnSignin.click();
		return this.loginInValid.getText().contains(STRLoginInValid);
	}
	
	public NaturalGasLeaksPage loginAndNavigateToNGL(String baseURL, String user, String pwd)
			throws Exception {
		loginPage = new LoginPage(driver, baseURL);
		PageFactory.initElements(driver, loginPage);
		loginPage.open();
		loginPage.loginNormalAs(user, pwd);

		NaturalGasLeaksPage naturalGasLeaksPage = new NaturalGasLeaksPage(driver, baseURL);
		PageFactory.initElements(driver, naturalGasLeaksPage);
		return naturalGasLeaksPage;
	}
	
	public ReportGenerationPortalPage loginAndNavigateToReportPortal(String baseURL, String user, String pwd)
			throws Exception {
		loginPage = new LoginPage(driver, baseURL);
		PageFactory.initElements(driver, loginPage);
		loginPage.open();
		loginPage.loginNormalAs(user, pwd);

		ReportGenerationPortalPage pageReportGeneration = new ReportGenerationPortalPage(driver, baseURL);
		PageFactory.initElements(driver, pageReportGeneration);
		return pageReportGeneration;
	}
}
