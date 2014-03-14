/**
 * 
 */
package common.source;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.CacheLookup;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;

/**
 * @author zlu
 * 
 */
public class HomePage extends BasePage {
	public static final String STRWrongPage = "Not Home, Wrong Page!";
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRHeadHome = "Home";
	public static final String STRURLPath = "/index/";

	@FindBy(how = How.XPATH, using = "//h3")
	@CacheLookup
	private WebElement headHome;

	@FindBy(how = How.ID, using = "id_userid_site")
	@CacheLookup
	private WebElement userIDSite;

	@FindBy(how = How.XPATH, using = "//span[@id='id_menu_util_list']/li[4]/a")
	@CacheLookup
	private WebElement linkSignOff;

	@FindBy(how = How.ID, using = "id_menu_drop")
	@CacheLookup
	private WebElement menuProcess;

	@FindBy(how = How.XPATH, using = "//span[@id='id_menu_list']/li[2]/a")
	private WebElement linkNGL;

	@FindBy(how = How.XPATH, using = "//span[@id='id_menu_list']/li[3]/a")
	private WebElement linkRGP;

	@FindBy(how = How.LINK_TEXT, using = "Home")
	@CacheLookup
	private WebElement linkHome;

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
		return (new LoginPage(driver, strBaseURL));
	}

	public NaturalGasLeaksPage goToNGLPage() throws Exception {
		this.menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		this.linkNGL.click();
		return (new NaturalGasLeaksPage(this.driver, this.strBaseURL));
	}

	public ReportGenerationPortalPage goToRGPPage() {
		menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		linkRGP.click();
		return (new ReportGenerationPortalPage(this.driver, this.strBaseURL));
	}

	public HomePage goBackToHomePage() throws Exception {
		this.menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		this.linkHome.click();
		return (new HomePage(driver, this.strBaseURL));
	}
}