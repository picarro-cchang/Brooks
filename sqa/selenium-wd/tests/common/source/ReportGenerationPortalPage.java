/**
 * 
 */
package common.source;

import java.util.Hashtable;
import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
import org.openqa.selenium.support.ui.Select;

/**
 * @author zlu
 * 
 */
public class ReportGenerationPortalPage extends BasePage {
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRURLPath = "/gdurpt/";
	public static final String STRPDFReport = "PDF";
	public static final String STRInvalid = "invalid";
	public static final String STRSWCorner = "swCorner";
	public static final String STRTableEmpty = "No matching records found";
	public static final String[] STRBlankStartEndTime = { "Invalid start time",
			"Invalid end time" };
	public static final String STREmptyReportTitle = "Title must be a non-empty string";
	public static final String STREmptySubmapTemplate = "Summary report refers to empty submap report - Edit Template to resolve grid reference.";
	public static final String STRNoSubmapGrid = "Submap report is unreachable from summary - Edit Template to resolve grid reference.";
	public static final String STREmptySummaryTemplate = "Empty report - Use Edit Template to define a non-empty summary report.";
	public static final String STREmptySurveyorTemplate = "No runs have been specified - do you want to make the report?";
	public static final String STRDuplicateReport = "This is a duplicate of a previously submitted report";
	public static final String[] invalidSwCorner = { "36.608, -121.910",
			"36.589, -121.886" };
	public static final String[] invalidNeCorner = { "36.589, -121.886",
			"36.608, -121.910" };
	public static final String[] STRInvalidCorners = {
			"SW corner latitude must be less than NE corner latitude.",
			"SW corner longitude must be less than NE corner longitude." };
	public static final String STRBlankCorners = "Invalid latitude, longitude pair";
	public static final String STRPeaksMinAmp = "0.10";
	public static final String STRShowSelected = "Show Selected";
	public static final String STRShowAll = "Show All";

	@FindBy(how = How.ID, using = "id_title")
	private WebElement reportTitle;

	@FindBy(how = How.ID, using = "id_swCorner")
	private WebElement inputSWCorner;

	@FindBy(how = How.ID, using = "id_neCorner")
	private WebElement inputNECorner;

	@FindBy(how = How.XPATH, using = "//table[@id='runTable']/thead/tr/th[1]/button")
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

	@FindBy(how = How.ID, using = "id_jobTable_next")
	private WebElement btnPageNext;

	@FindBy(how = How.ID, using = "id_jobTable_previous")
	private WebElement btnPagePrevious;

	@FindBy(how = How.ID, using = "id_peaksMinAmp")
	private WebElement inputPeaksMinAmp;

	@FindBy(how = How.ID, using = "id_submapsRows")
	private WebElement inputNoOfRows;

	@FindBy(how = How.ID, using = "id_submapsColumns")
	private WebElement inputNoOfCols;

	@FindBy(how = How.XPATH, using = "//table[@id='summarytable']/thead/tr/th[1]/button")
	private WebElement btnAddNewSummaryFigure;

	@FindBy(how = How.ID, using = "id_summary_paths")
	private WebElement selectSummaryPaths;

	@FindBy(how = How.ID, using = "id_summary_peaks")
	private WebElement selectSummaryPeaks;

	@FindBy(how = How.ID, using = "id_summary_wedges")
	private WebElement selectSummaryLISA;

	@FindBy(how = How.ID, using = "id_summary_analyses")
	private WebElement selectSummaryIsotopic;

	@FindBy(how = How.ID, using = "id_summary_fovs")
	private WebElement selectSummaryFOV;

	@FindBy(how = How.ID, using = "id_summary_grid")
	private WebElement selectSummaryGrid;

	@FindBy(how = How.XPATH, using = "//table[@id='submapstable']/thead/tr/th[1]/button")
	private WebElement btnAddNewSubmapFigure;

	@FindBy(how = How.ID, using = "id_submaps_paths")
	private WebElement selectSubmapPaths;

	@FindBy(how = How.ID, using = "id_submaps_peaks")
	private WebElement selectSubmapPeaks;

	@FindBy(how = How.ID, using = "id_submaps_wedges")
	private WebElement selectSubmapLISA;

	@FindBy(how = How.ID, using = "id_submaps_analyses")
	private WebElement selectSubmapIsotopic;

	@FindBy(how = How.ID, using = "id_submaps_fovs")
	private WebElement selectSubmapFOV;

	@FindBy(how = How.XPATH, using = "//button[contains(text(),'OK')]")
	private WebElement btnOKForAddNewFigure;

	@FindBy(how = How.XPATH, using = "//table[@id='id_jobTable']/tbody/tr")
	private List<WebElement> listReports;

	@FindBy(how = How.ID, using = "leftHead")
	private WebElement strReportTitle;

	@FindBy(how = How.ID, using = "id_make_pdf")
	private WebElement btnMakePDF;

	@FindBy(how = How.XPATH, using = "//div[@id='id_jobTable_filter']/label/input")
	private WebElement inputSearchReport;

	@FindBy(how = How.XPATH, using = "//table[@id='id_jobTable']/tbody/tr[1]/td[4]")
	private WebElement firstReportTitle;

	@FindBy(how = How.XPATH, using = "//td[@class='dataTables_empty']")
	private WebElement emptyTable;

	@FindBy(how = How.XPATH, using = "//div[@class='control-group error']/div/div/span/input[@id='id_start_etm']/../span")
	private WebElement invalidStartTime;

	@FindBy(how = How.XPATH, using = "//div[@class='control-group error']/div/div/span/input[@id='id_end_etm']/../span")
	private WebElement invalidEndTime;

	@FindBy(how = How.XPATH, using = "//table[@id='runTable']/tbody/tr/td[10]/button")
	private WebElement btnDeleteAnalyzerDetails;

	@FindBy(how = How.XPATH, using = "//table[@id='summarytable']/tbody/tr/td[9]/button")
	private WebElement btnDeleteSummaryFigureDetails;

	@FindBy(how = How.XPATH, using = "//table[@id='submapstable']/tbody/tr/td[8]/button")
	private WebElement btnDeleteSubmapFigureDetails;

	@FindBy(how = How.XPATH, using = "//table[@id='runTable']/tbody/tr/td[2]")
	private WebElement strSurveyorName;

	@FindBy(how = How.XPATH, using = "//div[@id='id_peaksTable']/table/tbody/tr/td[7]")
	private List<WebElement> listPeaksAmp;
	
	@FindBy(how = How.XPATH, using = "//table[@id='id_jobTable']/thead/tr/th[7]/button")
	private WebElement btnShowSelectedOrAll;
	
	@FindBy(how = How.XPATH, using = "//select[@name='id_jobTable_length']")
	private WebElement selectShowNReportEntries;
	
	private String strSurveyorDetails = "//table[@id='runTable']/tbody/tr/td[2]";
	private String strSumarryDetails = "//table[@id='summarytable']/tbody/tr/td[2]";
	private String strSubmapDetails = "//table[@id='submapstable']/tbody/tr/td[2]";
	private String btnAddRuns = "//table[@id='runTable']/thead/tr/th[1]/button";
	private String formAnalyzerLoaded = "//div[@class='modal hide fade in']";
	private String linkView = "//table[@id='id_jobTable']/tbody/tr[1]/td[5]/b/a[@class='viewLink']";
	private By btnNextEnabled = By.xpath("//a[@class='paginate_enabled_next']");
	private By btnSaveChanges = By.xpath("//button[@id='id_save_template']");
	private By btnMakeRprt = By.xpath("//button[@id='id_save_template']");

	public ReportGenerationPortalPage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;

		System.out.println("\nThe ReportGenerationPortalPage URL is: "
				+ this.strPageURL);
	}

	public void makeReport(String strAnalyzer,
			Hashtable<String, String> reportData) {
		// ***Refactoring this part of the code later***//
		String currentWH = driver.getWindowHandle();
		driver.switchTo().frame("id_iframe");

		this.reportTitle.sendKeys(reportData.get("Title"));
		this.inputSWCorner.sendKeys(reportData.get("SWCornerLat") + ", "
				+ reportData.get("SWCornerLong"));
		this.inputNECorner.sendKeys(reportData.get("NECornerLat") + ", "
				+ reportData.get("NECornerLong"));

		this.btnAddRun.click();
		TestSetup.slowdownInSeconds(3);
		this.selectAnalyzer.sendKeys(strAnalyzer);
		TestSetup.slowdownInSeconds(1);
		this.inputStartTime.sendKeys(reportData.get("StartTime"));
		this.inputEndTime.sendKeys(reportData.get("EndTime"));

//		ImagingUtility.takeScreenShot(driver, ".\\screenshots\\",
//				"Add Run Settings");

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

		List<WebElement> listReports = driver.findElements(By
				.xpath("//*[@id='id_jobTable']/tbody/tr"));

		WebElement targetWebElement;
		boolean flagForWhileLoop = true;
		while (flagForWhileLoop) {
			for (int i = 1; i <= listReports.size(); i++) {
				targetWebElement = driver.findElement(By
						.xpath("//*[@id='id_jobTable']/tbody/tr" + "[" + i
								+ "]" + "/" + "td[4]"));
				if (targetWebElement.getText().equals(strReportTitle)) {
					driver.findElement(
							By.xpath("//*[@id='id_jobTable']/tbody/tr" + "["
									+ i + "]" + "/" + "td[5]")).click();
					flagForWhileLoop = false;
					break;
				} else {
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

	/**
	 * Method to provide title, SW Corner, NE Corner, no. of rows and columns
	 * 
	 * @param title
	 * @param swCorner
	 * @param neCorner
	 * @param rowsColumnsSize
	 */
	public void provideTitleCornerDetails(Hashtable<String, String> reportData,
			int timeoutSeconds) {
		driver.switchTo().frame("id_iframe");

		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);

		this.reportTitle.sendKeys(reportData.get("Title"));

		// select the text present
		this.inputSWCorner.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputSWCorner.sendKeys(Keys.BACK_SPACE);
		// select the text present
		this.inputNECorner.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputNECorner.sendKeys(Keys.BACK_SPACE);

		this.inputSWCorner.sendKeys(reportData.get("SWCornerLat") + ", "
				+ reportData.get("SWCornerLong"));
		this.inputNECorner.sendKeys(reportData.get("NECornerLat") + ", "
				+ reportData.get("NECornerLong"));

		// select the text present and delete it
		this.inputNoOfRows.sendKeys(Keys.BACK_SPACE);
		this.inputNoOfRows.sendKeys(reportData.get("noOfRowsCols"));

		// select the text present and delete it
		this.inputNoOfCols.sendKeys(Keys.BACK_SPACE);
		this.inputNoOfCols.sendKeys(reportData.get("noOfRowsCols"));

		// time being to delete the peaks min amp value - 0.10
		for (int i = 1; i <= 4; i++) {
			// deletes the selected text
			this.inputPeaksMinAmp.sendKeys(Keys.BACK_SPACE);
		}
		this.inputPeaksMinAmp.sendKeys(reportData.get("peaksMinAmp"));
	}

	/**
	 * Method to provide title, SW Corner, NE Corner, no. of rows and columns
	 */
	public void providePeaksMinAmp(String strPeaksMinAmp) {
		// time being to delete the peaks min amp value - 0.10
		for (int i = 1; i <= 4; i++) {
			// deletes the selected text
			this.inputPeaksMinAmp.sendKeys(Keys.BACK_SPACE);
		}
		this.inputPeaksMinAmp.sendKeys(strPeaksMinAmp);
	}

	/**
	 * 
	 * @param reportData
	 * @param timeoutSeconds
	 */
	public void provideBlankTitle(Hashtable<String, String> reportData,
			int timeoutSeconds) {
		driver.switchTo().frame("id_iframe");

		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);

		this.reportTitle.sendKeys("");

		this.inputSWCorner.sendKeys(reportData.get("SWCornerLat") + ", "
				+ reportData.get("SWCornerLong"));
		this.inputNECorner.sendKeys(reportData.get("NECornerLat") + ", "
				+ reportData.get("NECornerLong"));
	}

	/**
	 * Method to provide title, SW Corner, NE Corner, no. of rows and columns
	 * 
	 * @param title
	 * @param swCorner
	 * @param neCorner
	 * @param rowsColumnsSize
	 */
	public void provideTitleCornerDetails(String strReportTitle,
			String strSWCorner, String strNECorner, int timeoutSeconds) {
		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);

		this.reportTitle.sendKeys(strReportTitle);

		// select the text present
		this.inputSWCorner.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputSWCorner.sendKeys(Keys.BACK_SPACE);
		// select the text present
		this.inputNECorner.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputNECorner.sendKeys(Keys.BACK_SPACE);

		this.inputSWCorner.sendKeys(strSWCorner);
		this.inputNECorner.sendKeys(strNECorner);
	}
	
	/**
	 * Method to provide title, SW Corner, NE Corner, no. of rows and columns
	 * 
	 * @param title
	 * @param swCorner
	 * @param neCorner
	 * @param rowsColumnsSize
	 */
	public void provideTitleCorner(String strReportTitle,
			Hashtable<String, String> reportData, int timeoutSeconds) {
		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);

		this.reportTitle.sendKeys(strReportTitle);

		// select the text present
		this.inputSWCorner.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputSWCorner.sendKeys(Keys.BACK_SPACE);
		// select the text present
		this.inputNECorner.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputNECorner.sendKeys(Keys.BACK_SPACE);

		this.inputSWCorner.sendKeys(reportData.get("SWCornerLat") + ", "
				+ reportData.get("SWCornerLong"));
		this.inputNECorner.sendKeys(reportData.get("NECornerLat") + ", "
				+ reportData.get("NECornerLong"));
	}

	/**
	 * Method to provide blank SW corner
	 * 
	 * @param title
	 * @param swCorner
	 * @param neCorner
	 * @param rowsColumnsSize
	 */
	public void provideBlankSwCorner() {
		// select the text present
		this.inputSWCorner.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputSWCorner.sendKeys(Keys.BACK_SPACE);
	}

	/**
	 * Method to provide blank NE corner
	 * 
	 * @param title
	 * @param swCorner
	 * @param neCorner
	 * @param rowsColumnsSize
	 */
	public void provideBlankNeCorner() {
		// select the text present
		this.inputNECorner.sendKeys(Keys.chord(Keys.CONTROL, "a"));
		// deletes the selected text
		this.inputNECorner.sendKeys(Keys.BACK_SPACE);
	}

	/**
	 * Method to select analyzer, provide start and end time
	 * 
	 * @param analyzer
	 * @param startTime
	 * @param endTime
	 * @param timeoutSeconds
	 */
	public void provideAnalyzerDetails(String strAnalyzer,
			Hashtable<String, String> reportData, int timeoutSeconds) {

		this.btnAddRun.click();
		// Wait till form is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);
		this.selectAnalyzer.sendKeys(strAnalyzer);
		this.inputStartTime.sendKeys(reportData.get("StartTime"));
		this.inputEndTime.sendKeys(reportData.get("EndTime"));
		this.btnOKForAddNewRun.click();
	}

	/**
	 * Method to select analyzer, provide start and end time
	 * 
	 * @param analyzer
	 * @param startTime
	 * @param endTime
	 * @param timeoutSeconds
	 */
	public void provideBlankStartEndTime(String strAnalyzer, int timeoutSeconds) {
		driver.switchTo().frame("id_iframe");
		this.btnAddRun.click();
		// Wait till form is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);
		this.selectAnalyzer.sendKeys(strAnalyzer);
		this.inputStartTime.sendKeys(Keys.DELETE);
		this.inputEndTime.sendKeys(Keys.DELETE);

		this.btnOKForAddNewRun.click();
		// Wait till form is loaded
		findElement(
				driver,
				By.xpath("//div[@class='control-group error']/div/div/span/span"),
				timeoutSeconds);
	}

	/**
	 * Method to select all tables present in Summary template, select provided
	 * figureValue for paths,peaks,LISA, isotopic, FOV with Background Type as
	 * 'Street Map' and Submap Grid as 'Yes'
	 * 
	 * @param figureValue
	 * @param timeoutSeconds
	 */
	public void provideSummaryFigureDetails(String strFigureValue,
			int timeoutSeconds) {

		this.btnEditTemplate.click();
		// Wait till template is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);
		this.cbSummaryPeaksTable.click();
		this.cbSummaryIsotopicTable.click();
		this.cbSummaryRunsTable.click();
		this.cbSummarySurveysTable.click();

		this.btnAddNewSummaryFigure.click();

		this.selectSummaryPaths.sendKeys(strFigureValue);
		this.selectSummaryPeaks.sendKeys(strFigureValue);
		this.selectSummaryLISA.sendKeys(strFigureValue);
		this.selectSummaryIsotopic.sendKeys(strFigureValue);
		this.selectSummaryFOV.sendKeys(strFigureValue);
		this.selectSummaryGrid.sendKeys(strFigureValue);
		this.btnOKForAddNewFigure.click();
	}

	/**
	 * Method to select no summary settings but Submap Grid as 'Yes'
	 * 
	 * @param figureValue
	 * @param timeoutSeconds
	 */
	public void provideOnlySubmapGridSummaryFigure(int timeoutSeconds) {

		this.btnEditTemplate.click();
		// Wait till template is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);
		this.btnAddNewSummaryFigure.click();
		this.btnOKForAddNewFigure.click();
	}

	/**
	 * Method to select provided figureValue for paths,peaks,LISA, isotopic, FOV
	 * with Background Type as 'Street Map' and Submap Grid as 'Yes'
	 * 
	 * @param figureValue
	 * @param timeoutSeconds
	 */
	public void provideSummaryFigureDetailsNoTablesSelected(
			String strFigureValue, int timeoutSeconds) {

		this.btnEditTemplate.click();
		// Wait till template is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);
		this.btnAddNewSummaryFigure.click();

		this.selectSummaryPaths.sendKeys(strFigureValue);
		this.selectSummaryPeaks.sendKeys(strFigureValue);
		this.selectSummaryLISA.sendKeys(strFigureValue);
		this.selectSummaryIsotopic.sendKeys(strFigureValue);
		this.selectSummaryFOV.sendKeys(strFigureValue);
		this.selectSummaryGrid.sendKeys(strFigureValue);
		this.btnOKForAddNewFigure.click();
	}

	/**
	 * Method to select all tables present in Summary template, select Submap
	 * Grid as strFigureValue provided
	 * 
	 * @param figureValue
	 * @param timeoutSeconds
	 */
	public void selectSummaryTables(String strFigureValue, int timeoutSeconds) {
		this.btnEditTemplate.click();
		// Wait till template is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);
		this.cbSummaryPeaksTable.click();
		this.cbSummaryIsotopicTable.click();
		this.cbSummaryRunsTable.click();
		this.cbSummarySurveysTable.click();

		this.btnAddNewSummaryFigure.click();

		this.selectSummaryGrid.sendKeys(strFigureValue);
		this.btnOKForAddNewFigure.click();
	}

	/**
	 * Method to select all tables present in Submap section, select provided
	 * figureValue for paths,peaks,LISA, isotopic, FOV with Background Type as
	 * 'Street Map'
	 * 
	 * @param figureValue
	 */
	public void provideSubmapFigureDetailsWithNoTables(String strFigureValue, int timeoutSeconds) {
		this.btnAddNewSubmapFigure.click();

		this.selectSubmapPaths.sendKeys(strFigureValue);
		this.selectSubmapPeaks.sendKeys(strFigureValue);
		this.selectSubmapLISA.sendKeys(strFigureValue);
		this.selectSubmapIsotopic.sendKeys(strFigureValue);
		this.selectSubmapFOV.sendKeys(strFigureValue);
		this.btnOKForAddNewFigure.click();
		findElement(driver, btnSaveChanges, timeoutSeconds);
	}

	/**
	 * Method to select all tables present in Submap section, select provided
	 * figureValue for paths,peaks,LISA, isotopic, FOV with Background Type as
	 * 'Street Map'
	 * 
	 * @param figureValue
	 */
	public void selectSubmapTables() {
		this.cbSubmapsPeaksTable.click();
		this.cbSubmapsIsotopicTable.click();
		this.cbSubmapsRunsTable.click();
		this.cbSubmapsSurveysTable.click();

		this.btnAddNewSubmapFigure.click();
		this.btnOKForAddNewFigure.click();
	}

	/**
	 * Method to select all tables present in Submap section, select provided
	 * figureValue for paths,peaks,LISA, isotopic, FOV with Background Type as
	 * 'Street Map'
	 * 
	 * @param figureValue
	 */
	public void provideSubmapFigureDetails(String strFigureValue) {
		this.cbSubmapsPeaksTable.click();
		this.cbSubmapsIsotopicTable.click();
		this.cbSubmapsRunsTable.click();
		this.cbSubmapsSurveysTable.click();

		this.btnAddNewSubmapFigure.click();

		this.selectSubmapPaths.sendKeys(strFigureValue);
		this.selectSubmapPeaks.sendKeys(strFigureValue);
		this.selectSubmapLISA.sendKeys(strFigureValue);
		this.selectSubmapIsotopic.sendKeys(strFigureValue);
		this.selectSubmapFOV.sendKeys(strFigureValue);
		this.btnOKForAddNewFigure.click();
	}

	/**
	 * Method to click on Save Changes -> Make Report buttons and check report
	 * is in 'Working' status
	 * 
	 * @param timeoutSeconds
	 */
	public void clickSaveChangesMakeReport(int timeoutSeconds) {
		this.btnSaveEditTemplate.click();
		findElement(driver, btnMakeRprt, timeoutSeconds);
		this.btnMakeReport.click();
		TestSetup.slowdownInSeconds(1);
	}

	/**
	 * Method to click on Make Report button
	 * 
	 * @param timeoutSeconds
	 */
	public void clickOnMakeReport() {
		this.btnMakeReport.click();
		TestSetup.slowdownInSeconds(1);
	}

	/**
	 * Method to click on Edit Template button
	 * 
	 * @param timeoutSeconds
	 */
	public void clickOnEditTemplate(int timeoutSeconds) {
		this.btnEditTemplate.click();
		// Wait till template is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);
	}

	/**
	 * Method to check whether View link is present
	 * 
	 * @param timeoutSeconds
	 */
	public boolean isViewLinkPresent(String strReportTitle, int timeoutSeconds) {
		WebElement targetWebElement;
		boolean flagForWhileLoop = true;
		while (flagForWhileLoop) {
			for (int i = 1; i <= this.listReports.size(); i++) {
				targetWebElement = driver.findElement(By
						.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[4]"));

				if (targetWebElement.getText().equals(strReportTitle)) {
					return isElementPresent(driver, By.xpath(linkView),
							timeoutSeconds);
				} else {
					continue;
				}
			}

			if (flagForWhileLoop) {
				if (isElementPresent(this.btnNextEnabled)) {
					this.btnPageNext.click();
				} else {
					flagForWhileLoop = false;
					return false;
				}
			}
		}
		return false;
	}

	/**
	 * Method to click on View link present and get the focus on new report
	 * window
	 * 
	 * @param timeoutSeconds
	 */
	public void clickOnViewLink(String strReportTitle, int timeoutSeconds) {
		WebElement targetWebElement;
		boolean flagForWhileLoop = true;
		while (flagForWhileLoop) {
			for (int i = 1; i <= this.listReports.size(); i++) {
				targetWebElement = driver.findElement(By
						.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[4]"));
				if (targetWebElement.getText().equals(strReportTitle)) {
					isElementPresent(
							driver,
							By.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
									+ "]/td[5]/b/a"), timeoutSeconds);
					driver.findElement(
							By.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
									+ "]/td[5]/b/a")).click();
					flagForWhileLoop = false;
					break;
				} else {
					continue;
				}
			}

			if (flagForWhileLoop) {
				if (isElementPresent(this.btnNextEnabled)) {
					this.btnPageNext.click();
				} else {
					flagForWhileLoop = false;
					break;
				}
			}
		}
		// get the focus on new window
		switchWindow();
	}

	public boolean makeReport(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strSummaryFigureValue, String strSubmapFigureValue,
			int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.provideSummaryFigureDetails(strSummaryFigureValue, timeoutSeconds);
		this.provideSubmapFigureDetails(strSubmapFigureValue);
		this.clickSaveChangesMakeReport(timeoutSeconds);
		if (strSummaryFigureValue.contains("No")){
			String actualMessage = acceptAlert();
			return actualMessage.contains(STRNoSubmapGrid);
		}
		return false;
	}

	public boolean viewReport(String strReportTitle, int timeoutSeconds) {
		this.clickOnViewLink(strReportTitle, timeoutSeconds);

		findElement(driver,
				By.xpath("//div[contains(text(),'" + strReportTitle + "')]"),
				timeoutSeconds);

		return this.strReportTitle.getText().equals(strReportTitle);
	}
	
	public boolean isPeaksAmpPresentGreaterThanMinAmp(int timeoutSeconds) {
		WebElement targetWebElement;
		for (int i = 1; i <= this.listPeaksAmp.size(); i++) {
			targetWebElement = driver.findElement(By
					.xpath("//div[@id='id_peaksTable']/table/tbody/tr[" + i
							+ "]/td[7]"));
			if (targetWebElement.getText().compareTo(STRPeaksMinAmp) >= 0) {
				continue;
			} else {
				return false;
			}
		}
		return true;
	}

	public boolean isDownloadPDFButtonPresent(String strReportTitle,
			int timeoutSeconds) {
		WebElement targetWebElement;
		boolean flagForWhileLoop = true;
		while (flagForWhileLoop) {
			for (int i = 1; i <= this.listReports.size(); i++) {
				targetWebElement = driver.findElement(By
						.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[4]"));

				if (targetWebElement.getText().equals(strReportTitle)) {
					return isElementPresent(
							driver,
							By.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
									+ "]/td[5]/a"), timeoutSeconds);
				} else {
					continue;
				}
			}
			if (flagForWhileLoop) {
				if (isElementPresent(this.btnNextEnabled)) {
					this.btnPageNext.click();
				} else {
					flagForWhileLoop = false;
					return false;
				}
			}
		}
		return false;
	}

	/**
	 * Method to click on Edit Report button present window
	 * 
	 * @param timeoutSeconds
	 */
	public void clickOnEditReport(String strReportTitle, int timeoutSeconds) {
		WebElement targetWebElement;
		boolean flagForWhileLoop = true;
		while (flagForWhileLoop) {
			for (int i = 1; i <= this.listReports.size(); i++) {
				targetWebElement = driver.findElement(By
						.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[4]"));

				if (targetWebElement.getText().equals(strReportTitle)) {
					isElementPresent(
							driver,
							By.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
									+ "]/td[5]/b/a"), timeoutSeconds);
					driver.findElement(
							By.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
									+ "]/td[1]/button")).click();
					flagForWhileLoop = false;
					break;
				} else {
					continue;
				}
			}

			if (flagForWhileLoop) {
				if (isElementPresent(this.btnNextEnabled)) {
					this.btnPageNext.click();
				} else {
					flagForWhileLoop = false;
					break;
				}
			}
		}
	}

	public boolean makeReportWithoutSubmapFigures(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strFigureValue, int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.provideSummaryFigureDetails(strFigureValue, timeoutSeconds);
		this.clickSaveChangesMakeReport(timeoutSeconds);
		String actualMessage = acceptAlert();
		return actualMessage.contains(STREmptySubmapTemplate);
	}

	public void makeReportWithSubmapGridOnlyNoSummary(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strSubmapFigureValue, int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.provideOnlySubmapGridSummaryFigure(timeoutSeconds);
		this.provideSubmapFigureDetails(strSubmapFigureValue);
		this.clickSaveChangesMakeReport(timeoutSeconds);
	}

	public void makeReportWithoutSummaryTables(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strFigureValue, int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.provideSummaryFigureDetailsNoTablesSelected(strFigureValue,
				timeoutSeconds);
		this.provideSubmapFigureDetails(strFigureValue);
		this.clickSaveChangesMakeReport(timeoutSeconds);
	}

	public void makeReportWithoutSumarryFiguresSettings(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strFigureValue, int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.selectSummaryTables(strFigureValue, timeoutSeconds);
		this.provideSubmapFigureDetails(strFigureValue);
		this.clickSaveChangesMakeReport(timeoutSeconds);
	}

	public void makeReportWithoutSubmapTables(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strFigureValue, int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.provideSummaryFigureDetails(strFigureValue, timeoutSeconds);
		this.provideSubmapFigureDetailsWithNoTables(strFigureValue, timeoutSeconds);
		this.clickSaveChangesMakeReport(timeoutSeconds);
	}

	public void makeReportWithoutSubmapFiguresSettings(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strFigureValue, int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.provideSummaryFigureDetails(strFigureValue, timeoutSeconds);
		this.selectSubmapTables();
		this.clickSaveChangesMakeReport(timeoutSeconds);
	}

	public boolean makeReportWithoutSummary(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strSubmapFigureValue, int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.clickOnEditTemplate(timeoutSeconds);
		this.provideSubmapFigureDetails(strSubmapFigureValue);
		this.clickSaveChangesMakeReport(timeoutSeconds);
		String actualMessage = acceptAlert();
		return actualMessage.contains(STREmptySummaryTemplate);
	}

	
	public void makeDuplicateReport(String strReportTitle, int timeoutSeconds) {
		// closing child window
		driver.close();

		// switch control to parent window
		driver.switchTo().window(parentWindow);
		driver.switchTo().frame("id_iframe");

		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);

		this.clickOnEditReport(strReportTitle, timeoutSeconds);
	}
	
	public boolean makeDuplicateReportNotAllowed(String strReportTitle, int timeoutSeconds) {
		// closing child window
		driver.close();

		// switch control to parent window
		driver.switchTo().window(parentWindow);
		driver.switchTo().frame("id_iframe");

		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);

		this.clickOnEditReport(strReportTitle, timeoutSeconds);
		this.clickOnMakeReport();
		String actualMessage = acceptAlert();
		return actualMessage.contains(STRDuplicateReport);
	}

	public boolean makeReportWithNoAnalyzerDetails() {
		this.clickOnMakeReport();
		String actualMessage = acceptAlert();
		return actualMessage.contains(STREmptySurveyorTemplate);
	}

	public boolean cancelReportGenerationWhenNoAnalyzerProvided(
			String strReportTitle, Hashtable<String, String> reportData,
			String reportType, String strSummaryFigureValue,
			String strSubmapFigureValue, int timeoutSeconds) {
		driver.switchTo().frame("id_iframe");
		this.provideTitleCorner(strReportTitle, reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideSummaryFigureDetails(strSummaryFigureValue, timeoutSeconds);
		this.provideSubmapFigureDetails(strSubmapFigureValue);
		this.clickSaveChangesMakeReport(timeoutSeconds);
		String actualMessage = cancelAlert();
		return actualMessage.contains(STREmptySurveyorTemplate);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean searchLogFile(String strReportTitle,
			String validInvalidReport, int timeoutSeconds) {
		this.inputSearchReport.sendKeys(strReportTitle);

		if (validInvalidReport.contentEquals(STRInvalid)) {
			if (this.emptyTable.getText().contains(STRTableEmpty))
				return true;
			else
				return false;
		} else {
			if (this.firstReportTitle.getText().contains(strReportTitle))
				return true;
			else
				return false;
		}
	}

	public boolean makeReportWithNoSummarySubmapDetails(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.clickOnMakeReport();
		String actualMessage = acceptAlert();
		return actualMessage.contains(STREmptySummaryTemplate);
	}

	public boolean makeReportWithInvalidLatitudeCorner(String strReportTitle,
			int timeoutSeconds) {
		driver.switchTo().frame("id_iframe");
		this.provideTitleCornerDetails(strReportTitle, invalidSwCorner[0],
				invalidNeCorner[0], timeoutSeconds);
		this.clickOnMakeReport();
		String actualMessage = acceptAlert();
		return actualMessage.contains(STRInvalidCorners[0]);
	}

	public boolean makeReportWithInvalidLongitudeCorner(String strReportTitle,
			int timeoutSeconds) {
		this.provideTitleCornerDetails(strReportTitle, invalidSwCorner[1],
				invalidNeCorner[1], timeoutSeconds);
		this.clickOnMakeReport();
		String actualMessage = acceptAlert();
		return actualMessage.contains(STRInvalidCorners[1]);
	}

	public boolean makeReportWithBlankSWNECorners(String blankCorner) {
		if (blankCorner.contentEquals(STRSWCorner))
			this.provideBlankSwCorner();
		else
			this.provideBlankNeCorner();
		this.clickOnMakeReport();
		String actualMessage = acceptAlert();
		return actualMessage.contains(STRBlankCorners);
	}

	public boolean makeReportWithNoTitle(Hashtable<String, String> reportData,
			int timeoutSeconds) {
		this.provideBlankTitle(reportData, timeoutSeconds);
		this.clickOnMakeReport();
		String actualMessage = acceptAlert();
		return actualMessage.contains(STREmptyReportTitle);
	}

	public boolean isStartTimeBlank() {
		return this.invalidStartTime.getText().contentEquals(
				STRBlankStartEndTime[0]);
	}

	public boolean isEndTimeBlank() {
		return this.invalidEndTime.getText().contentEquals(
				STRBlankStartEndTime[1]);
	}

	public boolean deleteAnalyzerDetails(String strAnalyzer,
			Hashtable<String, String> reportData, int timeoutSeconds) {
		driver.switchTo().frame("id_iframe");
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.btnDeleteAnalyzerDetails.click();
		return isElementPresent(driver, By.xpath(strSurveyorDetails),
				timeoutSeconds);
	}

	public boolean deleteSummaryFigureDetails(String strFigureValue,
			int timeoutSeconds) {
		driver.switchTo().frame("id_iframe");
		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);

		this.provideSummaryFigureDetails(strFigureValue, timeoutSeconds);
		this.btnDeleteSummaryFigureDetails.click();
		return isElementPresent(driver, By.xpath(strSumarryDetails),
				timeoutSeconds);
	}

	public boolean deleteSubmapFigureDetails(String strFigureValue,
			int timeoutSeconds) {
		driver.switchTo().frame("id_iframe");
		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);

		this.btnEditTemplate.click();
		// Wait till template is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);

		this.provideSubmapFigureDetails(strFigureValue);
		this.btnDeleteSubmapFigureDetails.click();
		return isElementPresent(driver, By.xpath(strSubmapDetails),
				timeoutSeconds);
	}

	/**
	 * Method to unselect all tables present in Summary template
	 * 
	 * @param timeoutSeconds
	 */
	public void unselectSummaryTables(int timeoutSeconds) {

		this.btnEditTemplate.click();
		// Wait till template is loaded
		findElement(driver, By.xpath(formAnalyzerLoaded), timeoutSeconds);
		if (this.cbSummaryPeaksTable.isSelected())
			this.cbSummaryPeaksTable.click();
		if (this.cbSummaryIsotopicTable.isSelected())
			this.cbSummaryIsotopicTable.click();
		if (this.cbSummaryRunsTable.isSelected())
			this.cbSummaryRunsTable.click();
		if (this.cbSummarySurveysTable.isSelected())
			this.cbSummarySurveysTable.click();
	}
	
	public void closeChildWindow(int timeoutSeconds) {
		// closing child window
		driver.close();

		// switch control to parent window
		driver.switchTo().window(parentWindow);
		driver.switchTo().frame("id_iframe");

		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);
	}
	
	public String editAndMakeReport(String strReportTitle, int timeoutSeconds) {
		this.clickOnEditReport(strReportTitle, timeoutSeconds);
		TestSetup.slowdownInSeconds(2);
		this.reportTitle.sendKeys(" New");
		String strNewTitle = strReportTitle + " New";
		this.unselectSummaryTables(timeoutSeconds);
		this.clickSaveChangesMakeReport(timeoutSeconds);
		return strNewTitle;
	}
	
	public void makeReportPeaksMinAmpProvided(String strAnalyzer,
			Hashtable<String, String> reportData, String reportType,
			String strSummaryFigureValue, String strSubmapFigureValue,
			int timeoutSeconds) {
		this.provideTitleCornerDetails(reportData, timeoutSeconds);
		this.providePeaksMinAmp(STRPeaksMinAmp);
		if (reportType.contains(STRPDFReport))
			this.btnMakePDF.click();
		this.provideAnalyzerDetails(strAnalyzer, reportData, timeoutSeconds);
		this.provideSummaryFigureDetails(strSummaryFigureValue, timeoutSeconds);
		this.provideSubmapFigureDetails(strSubmapFigureValue);
		this.clickSaveChangesMakeReport(timeoutSeconds);
	}
	
	/**
	 * Method to un-check the specified Report present on dashboard
	 * 
	 * @param timeoutSeconds
	 */
	public void unCheckReport(String strReportTitle, int timeoutSeconds) {
		WebElement targetWebElement;
		boolean flagForWhileLoop = true;
		while (flagForWhileLoop) {
			for (int i = 1; i <= this.listReports.size(); i++) {
				targetWebElement = driver.findElement(By
						.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[4]"));

				if (targetWebElement.getText().equals(strReportTitle)) {
					if (driver
							.findElement(
									By.xpath("//table[@id='id_jobTable']/tbody/tr["
											+ i + "]/td[7]/input"))
							.getAttribute("checked").compareTo("true") == 0) {
						driver.findElement(
								By.xpath("//table[@id='id_jobTable']/tbody/tr["
										+ i + "]/td[7]/input")).click();
						flagForWhileLoop = false;
						break;
					}
				} else {
					continue;
				}
			}

			if (flagForWhileLoop) {
				if (isElementPresent(this.btnNextEnabled)) {
					this.btnPageNext.click();
				} else {
					flagForWhileLoop = false;
					break;
				}
			}
		}
	}

	public String makeAndUncheckReport(String strReportTitle,
			int timeoutSeconds) {
		String newReportTitle = this.editAndMakeReport(strReportTitle,
				timeoutSeconds);
		this.unCheckReport(newReportTitle, timeoutSeconds);
		return newReportTitle;
	}
	
	/**
	 * Method to show selected reports on dashboard
	 * 
	 * @param timeoutSeconds
	 */
	public boolean showSelectedReports(int timeoutSeconds) {
		boolean flagForWhileLoop = true;
		String strCheckAttribute;
		if (btnShowSelectedOrAll.getText().contains(STRShowSelected))
			btnShowSelectedOrAll.click();

		while (flagForWhileLoop) {
			for (int i = 1; i <= this.listReports.size(); i++) {
				strCheckAttribute = driver.findElement(
						By.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[7]/input")).getAttribute("checked");
				
				if (strCheckAttribute.compareTo("true") == 0)
					continue;
				else
					return false;
			}

			if (flagForWhileLoop) {
				if (isElementPresent(this.btnNextEnabled)) {
					this.btnPageNext.click();
				} else {
					flagForWhileLoop = false;
					break;
				}
			}
		}
		return true;
	}
	
	/**
	 * Method to show all reports on dashboard
	 * 
	 * @param timeoutSeconds
	 */
	public boolean showAllReports(String strReportTitle,
			String strNewReportTitle, int timeoutSeconds) {
//		boolean flagForWhileLoop = true;
		WebElement targetWebElement;
		String strCheckAttribute;
		if (btnShowSelectedOrAll.getText().contains(STRShowAll))
			btnShowSelectedOrAll.click();

			for (int i = 1; i <= 2; i++) {
				targetWebElement = driver.findElement(By
						.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[4]"));
				strCheckAttribute = driver.findElement(
						By.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[7]/input")).getAttribute("checked");
				if (targetWebElement.getText().equals(strReportTitle)
						&& strCheckAttribute.compareTo("true") == 0)
					continue;
				else if (targetWebElement.getText().equals(strNewReportTitle)
						&& strCheckAttribute == null)
					continue;
				else
					return false;
				
				/* while (flagForWhileLoop) {
				for (int i = 1; i <= this.listReports.size(); i++) {
				strCheckAttribute = driver.findElement(
						By.xpath("//table[@id='id_jobTable']/tbody/tr[" + i
								+ "]/td[7]/input")).getAttribute("checked");
				if (strCheckAttribute == null
						|| strCheckAttribute.compareTo("true") == 0)
					continue;
				else
					return false;
				}
				if (flagForWhileLoop) {
				if (isElementPresent(this.btnNextEnabled)) {
					this.btnPageNext.click();
				} else {
					flagForWhileLoop = false;
					break;
				}
			}
		}*/
	}
	return true;
	}
	
	public void waitForReportPageLoading(int timeoutSeconds){
		driver.switchTo().frame("id_iframe");
		// Wait till page is loaded
		findElement(driver, By.xpath(btnAddRuns), timeoutSeconds);
	}
	
	public boolean showNReportEntries(String numberOfEntries) {
		Select selectNoOfReportEntries = new Select(this.selectShowNReportEntries);
		selectNoOfReportEntries.selectByValue(numberOfEntries);

		return (Integer.toString(this.listReports.size())
				.contentEquals(numberOfEntries));
	}
}
