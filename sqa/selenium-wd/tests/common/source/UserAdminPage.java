/**
 * 
 */
package common.source;

import java.util.ArrayList;
import java.util.List;

import org.openqa.selenium.By;
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
	
	@FindBy(how = How.ID, using = "id_p3adminlist_usrBtn")
	private WebElement btnAdminUserList;
	
	@FindBy(how = How.ID, using = "id_p3adminlist_psysBtn")
	private WebElement btnAdminSystemList;
	
	@FindBy(how = How.ID_OR_NAME, using ="id_useridTable_length")
	private WebElement selectShowUsersList;
	
	@FindBy(how = How.XPATH, using = "//*[@id='id_useridTable_filter']/label/input")
	private WebElement inputSearchBox;
	
	@FindBy(how = How.ID, using = "id_useridTable")
	private WebElement tableUserIDTable;
	
	@FindBy(how = How.CLASS_NAME, using = "paginate_disabled_next")
	private WebElement btnPageNext;
	
	@FindBy(how = How.CLASS_NAME, using = "paginate_disabled_previous")
	private WebElement btnPagePrevious;
	
	private String strXpathUserTableRows = "//*[@id='id_useridTable']/tbody/tr";
	private String strXpathSystemTableRows = "//*[@id='id_psysTable']/tbody/tr";
	
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
		
		List<WebElement> listTRUsers = driver.findElements(By.xpath(this.strXpathUserTableRows));
		
		WebElement tdUserID;
		for (int i = 1; i <= listTRUsers.size(); i++) {
			 tdUserID = driver.findElement(By.xpath(this.strXpathUserTableRows + "[" + i + "]" + "/td[1]"));
			 listTDUserIDs.add(tdUserID.getText());
		}
			
		return listTDUserIDs;
	}
	
	public List<String> getSystemList() {
		this.listTDSystems = new ArrayList<String>();
		if (this.btnAdminSystemList.getText().equals(STRShowSystemsList)) {
			this.btnAdminSystemList.click();
			
			TestSetup.slowdownInSeconds(5);
		}
		
		List<WebElement> listTRSystems = driver.findElements(By.xpath(this.strXpathSystemTableRows));
		
		WebElement tdSystem;
		for (int i = 1; i <= listTRSystems.size(); i++) {
			tdSystem = driver.findElement(By.xpath(this.strXpathSystemTableRows + "[" + i + "]" + "/td[1]"));
			listTDSystems.add(tdSystem.getText());
		}
		
		return listTDSystems;
	}
}
