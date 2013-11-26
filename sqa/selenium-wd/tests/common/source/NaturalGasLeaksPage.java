/**
 * 
 */
package common.source;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.CacheLookup;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
import org.openqa.selenium.support.ui.WebDriverWait;

/**
 * @author zlu
 *
 */
public class NaturalGasLeaksPage extends BasePage {
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRURLPath = "/gdulist/";
	public static final String STRShowList = "Show List";
	public static final String STRShowCalendar = "Show Calendar";
	
	@FindBy(how = How.ID, using = "id_calListBtn")
	private WebElement btnShowCalOrList;
	
	@FindBy(how = How.XPATH, using = "//td[2]/button")
	private WebElement btnLiveMap;
	
	@FindBy(how = How.XPATH, using = "//*[@id='id_logTable']/tbody/tr/td[2]")
	private WebElement firstCellLogFile;
	
	@FindBy(how = How.CSS, using = "#id_getLogBtn")
	private WebElement btnRefresh;
	
	@FindBy(how = How.ID, using = "id_menu_drop")
	private WebElement menuProcess;
	
	@FindBy(how = How.CSS, using = "#id_menu_list > li > a")
	private WebElement linkHome; 
	
	//@FindBy(how = How.LINK_TEXT, using = "Picarro Surveyor� for Natural Gas Leaks")
	@FindBy(how = How.XPATH, using = "//span[@id='id_menu_list']/li[2]/a")
	private WebElement linkNGL;
	
	//@FindBy(how = How.ID, using = "id_anzTitle")
	@FindBy(how = How.XPATH, using = "//*[@id='id_anzTitle']/a/h3")
	private WebElement linkSelectSurveyor;
	
	@FindBy(how = How.ID, using = "id_logModal")
	private WebElement logModal;
	
	@FindBy(how = How.ID, using = "id_p3gduclose_btn")
	private WebElement btnClose;
	
	public NaturalGasLeaksPage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;
		
		System.out.println("\nThe NaturalGasLeaksPage URL is: " + this.strPageURL);
	}	
	
	public List<String> getSurveyorList() {
		//***Refactoring this part of the code later***//
		TestSetup.slowdownInSeconds(5);
		this.linkSelectSurveyor.click();
		TestSetup.slowdownInSeconds(1);
		
		List<WebElement> trList = driver.findElements(By.xpath("//*[@id='id_anzListTbl']/tbody/tr"));
		
		List<String> strSurveyorList = new ArrayList<String>();
		
		for (int i = 1; i <= trList.size(); i++) {
			strSurveyorList.add(driver.findElement(By.xpath("//*[@id='id_anzListTbl']/tbody/tr" + "[" + i + "]" + "/"+ "td[1]")).getText());
		}
		
		this.btnClose.click();
		
		return strSurveyorList;
	}
	
	public void selectSurveyor(String strSurveyor) {
		TestSetup.slowdownInSeconds(5);
		this.linkSelectSurveyor.click();
		TestSetup.slowdownInSeconds(1);
		
		driver.findElement(By.linkText(strSurveyor)).click();
	}
	
	public List<String> getSurveyorLogList(String strSurveyor) {
		this.selectSurveyor(strSurveyor);
		TestSetup.slowdownInSeconds(3);
		
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();
		
		List<WebElement> trList = driver.findElements(By.xpath("//*[@id='id_logTable']/tbody/tr"));
		List<String> strLogList = new ArrayList<String>();
		
		for (int i = 1; i <= trList.size(); i++) {
			strLogList.add(driver.findElement(By.xpath("//*[@id='id_logTable']/tbody/tr" + "[" + i + "]" + "/" + "td[2]")).getText());
		}
		
		return strLogList;
	}
	
	public void showSurveyorLogMap(String strSurveyor, String strLogName) {
		TestSetup.slowdownInSeconds(5);
		this.selectSurveyor(strSurveyor);
		
		TestSetup.slowdownInSeconds(3);
		
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();		
		
		List<WebElement> trList = driver.findElements(By.xpath("//*[@id='id_logTable']/tbody/tr"));
		List<String> strLogList = new ArrayList<String>();

		String strXpath = "";
		WebElement tdLogFile = null;
		for (int i = 1; i <= trList.size(); i++) {
			strXpath = "//*[@id='id_logTable']/tbody/tr" + "[" + i + "]" + "/" + "td[2]";
			if (driver.findElement(By.xpath(strXpath)).getText().equals(strLogName)) {
				driver.findElement(By.xpath("//*[@id='id_logTable']/tbody/tr" + "[" + i + "]" + "/" + "td[5]")).click();
				break;
			}
		}
		
		TestSetup.slowdownInSeconds(15);
	}
}