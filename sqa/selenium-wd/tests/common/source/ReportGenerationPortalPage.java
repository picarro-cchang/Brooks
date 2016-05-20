/**
 * 
 */
package common.source;

import java.util.Hashtable;
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
public class ReportGenerationPortalPage extends BasePage {
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRURLPath = "/gdurpt/";

	@FindBy(how = How.ID, using = "id_title")
	private WebElement reportTitle;
	
	@FindBy(how = How.ID, using = "id_swCorner")
	private WebElement inputSWCorner;
	
	@FindBy(how = How.ID, using = "id_neCorner")
	private WebElement inputNECorner;
	
	@FindBy(how = How.XPATH, using = "//table[@id='runTable']/thead/tr/th/button")
	private WebElement btnAddRun;
				
	@FindBy(how = How.ID, using = "id_analyzer")
	private WebElement selectAnalyzer;
	
	@FindBy(how = How.ID, using = "id_start_etm")
	private WebElement inputStartTime;
	
	@FindBy(how = How.ID, using = "id_end_etm")
	private WebElement inputEndTime;
	
	@FindBy(how = How.XPATH, using = "//div[@id='id_modal']/div[3]/button")
	private WebElement btnOKForAddNewRun;
	
	@FindBy(how = How.XPATH, using = "//div[@id='id_modal']/div[3]/button[2]")
	private WebElement btnCancelForAddNewRun;
	
	@FindBy(how = How.ID, using = "id_edit_template")
	private WebElement btnEditTemplate;
	
	@FindBy(how = How.ID, using = "id_summary_peaksTable")
	private WebElement cbSummaryPeaksTable;
	
	@FindBy(how = How.ID, using = "id_summary_analysesTable")
	private WebElement cbSummaryIsotopicTable;
	
	@FindBy(how = How.ID, using = "id_summary_runsTable")
	private WebElement cbSummaryRunsTable;
	
	@FindBy(how = How.ID, using = "id_summary_surveysTable")
	private WebElement cbSummarySurveysTable;
	
	@FindBy(how = How.ID, using = "id_submaps_peaksTable")
	private WebElement cbSubmapsPeaksTable;
	
	@FindBy(how = How.ID, using = "id_submaps_analysesTable")
	private WebElement cbSubmapsIsotopicTable;
	
	@FindBy(how = How.ID, using = "id_submaps_runsTable")
	private WebElement cbSubmapsRunsTable;
	
	@FindBy(how = How.ID, using = "id_submaps_surveysTable")
	private WebElement cbSubmapsSurveysTable;
	
	@FindBy(how = How.ID, using = "id_save_template")
	private WebElement btnSaveEditTemplate;
	
	@FindBy(how = How.XPATH, using = "//div[@id='id_editTemplateModal']/div[3]/button[2]")
	private WebElement btnCancelEditTemplate;
	
	@FindBy(how = How.ID, using = "id_make_report")
	private WebElement btnMakeReport;
	
	@FindBy(how = How.ID, using = "//*[@id='id_jobTable_next']")
	private WebElement btnPageNext;
	
	@FindBy(how = How.ID, using = "//*[@id='id_jobTable_previous']")
	private WebElement btnPagePrevious;
	
	public ReportGenerationPortalPage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath; 
		
		System.out.println("\nThe ReportGenerationPortalPage URL is: " + this.strPageURL);
	}
	
	public void makeReport(String strAnalyzer, Hashtable<String, String> reportData) {
		//***Refactoring this part of the code later***//		
		String currentWH = driver.getWindowHandle();
		driver.switchTo().frame("id_iframe");
		
		this.reportTitle.sendKeys(reportData.get("Title"));
		this.inputSWCorner.sendKeys(reportData.get("SWCornerLat") + ", " + reportData.get("SWCornerLong"));
		this.inputNECorner.sendKeys(reportData.get("NECornerLat") + ", " + reportData.get("NECornerLong"));
		
		this.btnAddRun.click();
		TestSetup.slowdownInSeconds(3);
		this.selectAnalyzer.sendKeys(strAnalyzer);
		TestSetup.slowdownInSeconds(1);
		this.inputStartTime.sendKeys(reportData.get("StartTime"));
		this.inputEndTime.sendKeys(reportData.get("EndTime"));
		
		ImagingUtility.takeScreenShot(driver, ".\\screenshots\\", "Add Run Settings");		
		
		this.btnOKForAddNewRun.click();
		TestSetup.slowdownInSeconds(1);
		
		this.btnEditTemplate.click();
		TestSetup.slowdownInSeconds(1);
		this.cbSummaryPeaksTable.click();
		this.cbSummaryIsotopicTable.click();
		this.cbSummaryRunsTable.click();
		this.cbSummarySurveysTable.click();
		this.cbSubmapsPeaksTable.click();
		this.cbSubmapsIsotopicTable.click();
		this.cbSubmapsRunsTable.click();
		this.cbSubmapsSurveysTable.click();
		this.btnSaveEditTemplate.click();
		
		TestSetup.slowdownInSeconds(5);
		
		this.btnMakeReport.click();
		
		TestSetup.slowdownInSeconds(10);
		driver.switchTo().window(currentWH);
	}
	
	public void viewReport(String strReportTitle) {
		String currentWH = driver.getWindowHandle();
		driver.switchTo().frame("id_iframe");
		
		List<WebElement> listReports = driver.findElements(By.xpath("//*[@id='id_jobTable']/tbody/tr"));
		
		WebElement targetWebElement;
		boolean flagForWhileLoop = true;
		while(flagForWhileLoop) {
			for (int i = 1; i <= listReports.size(); i++) {
				targetWebElement = driver.findElement(By.xpath("//*[@id='id_jobTable']/tbody/tr" + "[" + i + "]"+ "/" + "td[4]"));
				if (targetWebElement.getText().equals(strReportTitle)) {
					driver.findElement(By.xpath("//*[@id='id_jobTable']/tbody/tr" + "[" + i + "]"+ "/" + "td[5]")).click();
					flagForWhileLoop = false;
					break;
				}
				else {
					continue;
				}
			}
			
			if (flagForWhileLoop) {
				if (this.btnPageNext.isEnabled()) {
					this.btnPageNext.click();
				}
			}
		}
		
		driver.switchTo().window(currentWH);
	}
}
