/**
 * 
 */
package common.source;

import java.util.Hashtable;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;

/**
 * @author zlu
 *
 */
public class UserProfilePage extends BasePage {
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRURLPath = "/userprofile/";
	
	private Hashtable<String, String> htUserProfile = null;
	
	@FindBy(how = How.XPATH, using = "//*[@id='id_content_title']/form/div/table/tbody/tr[2]/td/fieldset/div[1]/div/input")
	private WebElement inputUserID;
	
	@FindBy(how = How.XPATH, using = "//*[@id='id_content_title']/form/div/table/tbody/tr[2]/td/fieldset/div[2]/div/input")
	private WebElement inputFirstName;
	
	@FindBy(how = How.XPATH, using = "//*[@id='id_content_title']/form/div/table/tbody/tr[2]/td/fieldset/div[3]/div/input")
	private WebElement inputLastName;
	
	@FindBy(how = How.XPATH, using = "//*[@id='id_content_title']/form/div/table/tbody/tr[2]/td/fieldset/div[4]/div/input")
	private WebElement inputDisplayName;
	
	public UserProfilePage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;
		
		this.htUserProfile = new Hashtable<String, String>();
	}
	
	public Hashtable<String, String> getUserProfile() {
		TestSetup.slowdownInSeconds(5);
		
		String currentWH = driver.getWindowHandle();		
		WebElement iFrame = driver.findElement(By.id("id_iframe"));
		driver.switchTo().frame(iFrame);
		
		this.htUserProfile.put("User ID", this.inputUserID.getAttribute("value"));
		this.htUserProfile.put("First Name", this.inputFirstName.getAttribute("value"));
		this.htUserProfile.put("Last Name", this.inputLastName.getAttribute("value"));
		this.htUserProfile.put("Display Name", this.inputDisplayName.getAttribute("value"));
		
		driver.switchTo().window(currentWH);
		
		return this.htUserProfile;
	}
}
