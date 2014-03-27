/**
 * 
 */
package common.source;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.List;

import org.openqa.selenium.By;
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
public class NaturalGasLeaksPage extends BasePage {
	public static final String STRPageTitle = "Picarro P-Cubed";
	public static final String STRURLPath = "/gdulist/";
	public static final String STRShowList = "Show List";
	public static final String STRShowCalendar = "Show Calendar";
	public static final String STRHeadNGL = "Natural Gas Leaks";
	public static String screenShotsDir;
	public static final int timeoutInSeconds = 30;
	public static final String STRTableEmpty = "No matching records found";
	public static final String STRRefreshing = "Working";
	public static final String STRRefresh = "Refresh";
	public static final String STRDateToSelect = "2014-02-18";
	public static final String STRShow100Entries = "100";
	public static final String STRChangedTimezoneTime = "First: 2012-06-10 09:13:19-0400 (EDT)"
			+ "\n" + "Last: 2012-06-10 14:03:02-0400 (EDT)";
	public static final String STRNoTimezoneSelectedTime = "First: 2012-06-10 13:13:19+0000 (UTC)"
			+ "\n" + "Last: 2012-06-10 18:03:02+0000 (UTC)";
	public static final String STRSurveyorTableEmpty = "No data available in table";
	private Hashtable<String, String> htLogDate = new Hashtable<>();
	private String[] month = { "", "January", "February", "March", "April",
			"May", "June", "July", "August", "September", "October",
			"November", "December" };
	public static final String STRShowFirst = "first";

	@FindBy(how = How.XPATH, using = "//h3")
	@CacheLookup
	private WebElement headNGL;

	@FindBy(how = How.ID, using = "id_userid_site")
	@CacheLookup
	private WebElement userIDSite;

	@FindBy(how = How.XPATH, using = "//a[@href='/stage/plogin']")
	@CacheLookup
	private WebElement linkSignOff;

	@FindBy(how = How.ID, using = "id_calListBtn")
	private WebElement btnShowCalOrList;

	// @FindBy(how = How.XPATH, using = "//td[2]/button")
	// pmahajan
	@FindBy(how = How.XPATH, using = "//button[contains(text(),'Live Map')]")
	private WebElement btnLiveMap;

	@FindBy(how = How.XPATH, using = "//*[@id='id_logTable']/tbody/tr/td[2]")
	private WebElement firstCellLogFile;

	@FindBy(how = How.CSS, using = "#id_getLogBtn")
	private WebElement btnRefresh;

	@FindBy(how = How.ID, using = "id_menu_drop")
	private WebElement menuProcess;

	@FindBy(how = How.CSS, using = "#id_menu_list > li > a")
	private WebElement linkHome;

	@FindBy(how = How.XPATH, using = "//span[@id='id_menu_list']/li[2]/a")
	private WebElement linkNGL;

	// @FindBy(how = How.ID, using = "id_anzTitle")
	@FindBy(how = How.XPATH, using = "//div[@id='id_anzTitle']/a")
	private WebElement linkSelectSurveyor;

	@FindBy(how = How.ID, using = "id_logModal")
	private WebElement logModal;

	@FindBy(how = How.ID, using = "id_p3gduclose_btn")
	private WebElement btnClose;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//table[@id='id_logTable']/tbody/tr/td[2]")
	private List<WebElement> logList;

	// pmahajan
	@FindBy(how = How.ID, using = "id_inp_ANALYZER")
	private WebElement inputSurveyorName;

	// pmahajan
	@FindBy(how = How.ID, using = "id_inp_name")
	private WebElement inputLogName;

	// pmahajan
	@FindBy(how = How.ID, using = "id_inp_durrstr")
	private WebElement inputDuration;

	// pmahajan
	@FindBy(how = How.ID, using = "id_p3gdulist_Close_log_log")
	private WebElement btnCloseViewMetadata;

	// pmahajan
	// @FindBy(how = How.XPATH, using =
	// "//div[@id='id_logModal' and @class='modal hide fade in']")
	private By bySurveyorPanel = By
			.xpath("//div[@id='id_logModal' and @class='modal hide fade in']");

	// pmahajan
	@FindBy(how = How.XPATH, using = "//button[@class='btn btn-inverse']")
	private WebElement btnChangeTimezone;

	// pmahajan
	@FindBy(how = How.ID, using = "edit-date-default-timezone")
	private WebElement selectTimezone;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//div[@class='modal-footer']/button[@id='id_save_timezone']")
	private WebElement btnSaveTimezone;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//div[@id='id_logTable_filter']/label/input")
	private WebElement inputSearchLog;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//td[@class='dataTables_empty']")
	private WebElement emptyTable;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//table[@id='id_logTable']/tbody/tr[1]/td[1]")
	private WebElement firstLogDate;

	@FindBy(how = How.XPATH, using = "//table[@id='id_logTable']/tbody/tr[1]/td[2]")
	private WebElement firstLogName;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//select[@name='id_logTable_length']")
	private WebElement btnShowNLogEntries;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//select[@name='id_anzListTbl_length']")
	private WebElement showNAnalyzerEntries;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//table[@id='id_anzListTbl']/tbody/tr/td[1]")
	private List<WebElement> analyzersList;

	// pmahajan
	@FindBy(how = How.ID, using = "id_anzListTbl_next")
	private WebElement linkNextSurveyorList;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//div[@id='id_anzListTbl_filter']/label/input")
	private WebElement inputSearchSurveyor;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//button[contains(text(),'First Log')]")
	private WebElement btnFirstLog;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//div[@id='id_logListTbl_filter']/label/input")
	private WebElement inputSearchLogCalendarView;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//table[@id='id_logListTbl']/tbody/tr/td[2]")
	private List<WebElement> surveysListCalendarView;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//table[@id='id_logListTbl']/tbody/tr/td[3]/button")
	private WebElement btnFirstMapLogCalendarView;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//div[@class='modal-footer']/button[contains(text(),'Cancel')]")
	private WebElement btnCancelTimezone;

	// pmahajan
	@FindBy(how = How.ID, using = "id_p3Timezone")
	private WebElement inputTimezone;

	// pmahajan
	@FindBy(how = How.ID, using = "id_selectAnalyzerBtn")
	private WebElement btnSelectSurveyor;

	// pmahajan
	@FindBy(how = How.ID, using = "id_p3gdulist_Close_DaySelector")
	private WebElement btnCloseSurveysWindow;

	@FindBy(how = How.XPATH, using = "//select[@name='id_logListTbl_length']")
	private WebElement btnShowNLogListEntries;

	// pmahajan
	// @FindBy(how = How.ID, using = "id_logModal")
	private String daySurveyWindow = "//div[@id='id_logModal' and @class='modal hide fade']";

	@FindBy(how = How.XPATH, using = "//button[contains(text(),'Next Month')]")
	private WebElement btnNextMonth;

	@FindBy(how = How.ID, using = "id_side_show_btn")
	private WebElement btnShowSide;

	@FindBy(how = How.ID, using = "id_anzListTbl_info")
	private WebElement surveyorTableInfo;

	@FindBy(how = How.XPATH, using = "//table[@id='id_logListTbl']/tbody/tr[1]/td[1]")
	private WebElement firstLogTimeClndrVw;

	@FindBy(how = How.XPATH, using = "//table[@id='id_anzListTbl']/tbody/tr/td")
	private WebElement surveyorTable;

	@FindBy(how = How.XPATH, using = "//th[@class='sorting_asc']")
	private WebElement ascLogList;

	@FindBy(how = How.XPATH, using = "//th[@class='sorting_desc']")
	private WebElement descLogList;

	@FindBy(how = How.XPATH, using = "//span[@id='id_right_content']/div/div/table/tbody/tr[1]/td/table/tbody/tr/td[2]/h3")
	private WebElement txtMonthYear;

	@FindBy(how = How.XPATH, using = "//button[contains(text(),'Last Log')]")
	private WebElement btnLastLog;

	@FindBy(how = How.XPATH, using = "//button[contains(text(),'Prev Month')]")
	private WebElement btnPrevMonth;

	@FindBy(how = How.XPATH, using = "//button[contains(text(),'Prev Year')]")
	private WebElement btnPrevYear;

	@FindBy(how = How.XPATH, using = "//button[contains(text(),'Next Year')]")
	private WebElement btnNextYear;

	@FindBy(how = How.XPATH, using = "//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr")
	private List<WebElement> rowsInCal;

	@FindBy(how = How.XPATH, using = "//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[1]/td")
	private List<WebElement> colsInCal;

	private By byLogListAsc = By.xpath("//th[@class='sorting_asc']");
	private By byRefreshButton = By
			.xpath("//button[@id='id_getLogBtn' and contains(text(),'Refresh')]");
	private By bySurveyorLink = By.xpath("//div[@id='id_anzTitle']/a");
	private By byCloseButton = By.id("id_p3gduclose_btn");
	private By byCloseViewMetadataButton = By.id("id_p3gdulist_Close_log_log");
	private By byShowSideButton = By.id("id_side_show_btn");
	private By byShowCalListButton = By.id("id_calListBtn");
	private By byFirstLogButton = By
			.xpath("//button[contains(text(),'First Log')]");
	private By bySearchBox = By
			.xpath("//div[@id='id_logTable_filter']/label/input");
	private By byLiveMapBtn = By.xpath("//button[contains(text(),'Live Map')]");
	private By bySaveTimezoneBtn = By
			.xpath("//div[@class='modal-footer']/button[@id='id_save_timezone']");

	public NaturalGasLeaksPage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;

		System.out.println("\nThe NaturalGasLeaksPage URL is: "
				+ this.strPageURL);
	}

	public List<String> getSurveyorList() throws Exception {
		findElement(driver, bySurveyorLink, timeoutInSeconds);
		this.linkSelectSurveyor.click();
		findElement(driver, byCloseButton, timeoutInSeconds);

		List<WebElement> trList = driver.findElements(By
				.xpath("//*[@id='id_anzListTbl']/tbody/tr"));
		List<String> strSurveyorList = new ArrayList<String>();

		for (int i = 1; i <= trList.size(); i++) {
			strSurveyorList.add(driver.findElement(
					By.xpath("//*[@id='id_anzListTbl']/tbody/tr" + "[" + i
							+ "]" + "/" + "td[1]")).getText());
		}

		this.btnClose.click();
		return strSurveyorList;
	}

	public void selectSurveyor(String strSurveyor) throws Exception {
		findElement(driver, bySurveyorLink, timeoutInSeconds);
		this.linkSelectSurveyor.click();
		TestSetup.slowdownInSeconds(3);
		findElement(driver, byCloseButton, timeoutInSeconds);

		Select selectNoOfAnalyzerEntries = new Select(this.showNAnalyzerEntries);
		selectNoOfAnalyzerEntries.selectByValue("100");
		for (int i = 1; i <= this.analyzersList.size(); i++) {
			if (isElementPresent(By.linkText(strSurveyor)))
				driver.findElement(By.linkText(strSurveyor)).click();
			else if (this.linkNextSurveyorList.isEnabled())
				this.linkNextSurveyorList.click();
			else
				System.out.println(strSurveyor + " Surveyor not found!!");
		}
		TestSetup.slowdownInSeconds(2);
	}

	public List<String> getSurveyorLogList(String strSurveyor) throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();

		findElement(driver, bySearchBox, timeoutInSeconds);
		List<WebElement> trList = driver.findElements(By
				.xpath("//*[@id='id_logTable']/tbody/tr"));
		List<String> strLogList = new ArrayList<String>();

		for (int i = 1; i <= trList.size(); i++) {
			strLogList.add(driver.findElement(
					By.xpath("//*[@id='id_logTable']/tbody/tr" + "[" + i + "]"
							+ "/" + "td[2]")).getText());
		}
		return strLogList;
	}

	public void showSurveyorLogMap(String strSurveyor, String strLogName)
			throws Exception {
		this.selectSurveyor(strSurveyor);

		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();

		findElement(driver, bySearchBox, timeoutInSeconds);
		List<WebElement> trList = driver.findElements(By
				.xpath("//*[@id='id_logTable']/tbody/tr"));
		String strXpath = "";
		for (int i = 1; i <= trList.size(); i++) {
			strXpath = "//*[@id='id_logTable']/tbody/tr" + "[" + i + "]" + "/"
					+ "td[2]";
			if (driver.findElement(By.xpath(strXpath)).getText()
					.equals(strLogName)) {
				driver.findElement(
						By.xpath("//*[@id='id_logTable']/tbody/tr" + "[" + i
								+ "]" + "/" + "td[5]/button")).click();
				break;
			}
		}
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean getSelectedSurveyorName(String strSurveyor) throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, bySurveyorLink, timeoutInSeconds);
		return this.linkSelectSurveyor.getText().contains(strSurveyor);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public String getDuration(String strLogName) throws Exception {
		String duration = "";
		String strXpath = "";

		findElement(driver, bySearchBox, timeoutInSeconds);
		for (int i = 1; i <= this.logList.size(); i++) {
			strXpath = "//table[@id='id_logTable']/tbody/tr" + "[" + i + "]"
					+ "/" + "td[2]";
			if (driver.findElement(By.xpath(strXpath)).getText()
					.equals(strLogName)) {
				duration = driver.findElement(
						By.xpath("//table[@id='id_logTable']/tbody/tr" + "["
								+ i + "]" + "/" + "td[3]")).getText();
				break;
			}
		}
		return duration;
	}

	/**
	 * 
	 * @param strLogName
	 * @author pmahajan
	 */
	public void showViewMetadata(String strLogName) throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();
		TestSetup.slowdownInSeconds(1);
		findElement(driver, bySearchBox, timeoutInSeconds);
		String strXpath = "";
		for (int i = 1; i <= this.logList.size(); i++) {
			strXpath = "//table[@id='id_logTable']/tbody/tr" + "[" + i + "]"
					+ "/" + "td[2]";
			if (driver.findElement(By.xpath(strXpath)).getText()
					.equals(strLogName)) {

				driver.findElement(
						By.xpath("//table[@id='id_logTable']/tbody/tr" + "["
								+ i + "]" + "/" + "td[4]/button")).click();
				break;
			}
		}
		findElement(driver, byCloseViewMetadataButton, timeoutInSeconds);
		TestSetup.slowdownInSeconds(2);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean getSurveyorNameFromMetadata(String strSurveyor)
			throws Exception {
		return this.inputSurveyorName.getAttribute("Value").contains(
				strSurveyor);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean getLogNameFromMetadata(String strLogName) throws Exception {
		return this.inputLogName.getAttribute("Value").contains(strLogName);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean getDurationFromMetadata(String strLogName) throws Exception {
		String duration = getDuration(strLogName);
		return this.inputDuration.getAttribute("Value").contains(duration);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void clickCloseMetadataButton() throws Exception {
		findElement(driver, byCloseViewMetadataButton, timeoutInSeconds);
		this.btnCloseViewMetadata.click();
		TestSetup.slowdownInSeconds(2);
		findElement(driver, bySurveyorLink, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void showSurveyorLiveMap(String strSurveyor, String strView)
			throws Exception {
		if (strView.contains("List")) {
			findElement(driver, byShowCalListButton, timeoutInSeconds);
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			findElement(driver, byShowCalListButton, timeoutInSeconds);
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}
		this.selectSurveyor(strSurveyor);
		findElement(driver, byLiveMapBtn, timeoutInSeconds);
		this.btnLiveMap.click();
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean refreshSurveyorLogList(String strSurveyor, String strView)
			throws Exception {
		this.isRefreshButtonPresent();
		this.selectSurveyor(strSurveyor);
		if (strView.contains("List")) {
			findElement(driver, byShowCalListButton, timeoutInSeconds);
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			findElement(driver, byShowCalListButton, timeoutInSeconds);
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}

		findElement(driver, byRefreshButton, timeoutInSeconds);
		this.btnRefresh.click();
		if (this.btnRefresh.getText().contains(STRRefreshing))
			return true;
		else
			return false;
	}

	public boolean isRefreshButtonPresent() throws Exception {
		return isElementPresent(driver, byRefreshButton, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean closeSurveyorWindow() throws Exception {
		findElement(driver, bySurveyorLink, timeoutInSeconds);
		this.linkSelectSurveyor.click();
		findElement(driver, byCloseButton, timeoutInSeconds);
		TestSetup.slowdownInSeconds(1);
		this.btnClose.click();
		findElement(driver, bySurveyorLink, timeoutInSeconds);
		return isElementPresent(driver, bySurveyorPanel, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean changeTimezoneOfSurveyor(String strSurveyor,
			String strTimezoneToSelect, String strView) throws Exception {
		this.selectSurveyor(strSurveyor);
		if (strView.contains("List")) {
			findElement(driver, byShowCalListButton, timeoutInSeconds);
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			findElement(driver, byShowCalListButton, timeoutInSeconds);
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}

		this.btnChangeTimezone.click();
		TestSetup.slowdownInSeconds(1);
		findElement(driver, bySaveTimezoneBtn, timeoutInSeconds);
		Select selectTimezoneValue = new Select(this.selectTimezone);
		selectTimezoneValue.selectByValue(strTimezoneToSelect);
		this.btnSaveTimezone.click();
		TestSetup.slowdownInSeconds(1);
		if (strView.contains("List")) {
			findElement(driver, bySearchBox, timeoutInSeconds);
			return this.getFirstLogDateTime().contains(STRChangedTimezoneTime);
		} else {
			findElement(driver, byFirstLogButton, timeoutInSeconds);
			return this.getFirstLogDateTimeInCalendarView().contains(
					STRChangedTimezoneTime);
		}
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean selectNoTimezoneForSurveyor(String strSurveyor,
			String strView) throws Exception {
		this.selectSurveyor(strSurveyor);
		if (strView.contains("List")) {
			findElement(driver, byShowCalListButton, timeoutInSeconds);
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			findElement(driver, byShowCalListButton, timeoutInSeconds);
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}

		this.btnChangeTimezone.click();
		TestSetup.slowdownInSeconds(1);
		findElement(driver, bySaveTimezoneBtn, timeoutInSeconds);
		Select selectTimezoneValue = new Select(this.selectTimezone);
		selectTimezoneValue.selectByValue("");
		this.btnSaveTimezone.click();
		TestSetup.slowdownInSeconds(2);
		if (strView.contains("List")) {
			findElement(driver, bySearchBox, timeoutInSeconds);
			return this.getFirstLogDateTime().contains(
					STRNoTimezoneSelectedTime);
		} else {
			findElement(driver, byFirstLogButton, timeoutInSeconds);
			return this.getFirstLogDateTimeInCalendarView().contains(
					STRNoTimezoneSelectedTime);
		}
	}

	/**
	 * 
	 * @author pmahajan
	 */
	public String getFirstLogDateTime() throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contentEquals(STRShowList))
			this.btnShowCalOrList.click();
		findElement(driver, bySearchBox, timeoutInSeconds);
		return this.firstLogDate.getText();
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean searchLogFile(String strSurveyor, String strLogName,
			String validInvalidLog) throws Exception {
		this.selectSurveyor(strSurveyor);

		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowList))
			this.btnShowCalOrList.click();

		findElement(driver, bySearchBox, timeoutInSeconds);
		this.inputSearchLog.sendKeys(strLogName);
		if (validInvalidLog.contentEquals("valid")) {
			if (this.firstCellLogFile.getText().contains(strLogName))
				return true;
			else
				return false;
		} else {
			if (this.emptyTable.getText().contains(STRTableEmpty))
				return true;
			else
				return false;
		}
	}

	/**
	 * @author pmahajan
	 */
	public boolean showNLogEntries(String numberOfEntries) throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowList))
			this.btnShowCalOrList.click();

		findElement(driver, bySearchBox, timeoutInSeconds);
		Select selectNoOfLogEntries = new Select(this.btnShowNLogEntries);
		selectNoOfLogEntries.selectByValue(numberOfEntries);

		return (Integer.toString(this.logList.size())
				.contentEquals(numberOfEntries));
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean searchSurveyor(String strSurveyor,
			String validInvalidSurveyor) throws Exception {
		String strXpath = "";
		findElement(driver, bySurveyorLink, timeoutInSeconds);
		TestSetup.slowdownInSeconds(1);
		this.linkSelectSurveyor.click();
		findElement(driver, byCloseButton, timeoutInSeconds);

		this.inputSearchSurveyor.sendKeys(strSurveyor);
		if (validInvalidSurveyor.contentEquals("valid")) {
			for (int i = 1; i <= this.analyzersList.size();) {
				strXpath = "//table[@id='id_anzListTbl']/tbody/tr[" + i
						+ "]/td[1]";
				if (driver.findElement(By.xpath(strXpath)).getText()
						.contains(strSurveyor)) {
					TestSetup.slowdownInSeconds(1);
					this.btnClose.click();
					return true;
				} else
					i++;
			}
		} else {
			if (this.emptyTable.getText().contains(STRTableEmpty))
				return true;
			else
				return false;
		}
		return false;
	}

	/**
	 * @author pmahajan
	 */
	public boolean showNSurveyorEntries(String numberOfEntries)
			throws Exception {
		findElement(driver, bySurveyorLink, timeoutInSeconds);
		this.linkSelectSurveyor.click();
		TestSetup.slowdownInSeconds(1);
		findElement(driver, byCloseButton, timeoutInSeconds);

		Select selectNoOfAnalyzerEntries = new Select(this.showNAnalyzerEntries);
		selectNoOfAnalyzerEntries.selectByValue(numberOfEntries);
		boolean result = surveyorTableInfo.getText().contains(
				"Showing 1 to " + numberOfEntries);
		this.btnClose.click();
		TestSetup.slowdownInSeconds(1);
		return result;
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void closeSurveyorListWindow() {
		this.btnClose.click();
		TestSetup.slowdownInSeconds(1);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void closeSurveysWindow() {
		this.btnCloseSurveysWindow.click();
		TestSetup.slowdownInSeconds(1);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean searchLogFileInCalendarView(String strSurveyor,
			String strLogName, String validInvalidLog) throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		findElement(driver, byFirstLogButton, timeoutInSeconds);
		this.btnFirstLog.click();

		// time being tested to click on 15th Jan 2014 - FDDS2037
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[4]/button"))
				.click();
		TestSetup.slowdownInSeconds(1);
		this.inputSearchLogCalendarView.sendKeys(strLogName);
		if (validInvalidLog.contentEquals("valid")) {
			if (this.surveysListCalendarView.get(0).getText()
					.contains(strLogName))
				return true;
			else
				return false;
		} else {
			if (this.emptyTable.getText().contains(STRTableEmpty))
				return true;
			else
				return false;
		}
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean cancelTimezoneWindow(String strSurveyor,
			String strTimezoneToChange) throws Exception {
		this.selectSurveyor(strSurveyor);
		this.btnChangeTimezone.click();
		TestSetup.slowdownInSeconds(1);
		findElement(driver, bySaveTimezoneBtn, timeoutInSeconds);
		Select selectTimezoneValue = new Select(this.selectTimezone);
		selectTimezoneValue.selectByValue(strTimezoneToChange);
		this.btnCancelTimezone.click();
		TestSetup.slowdownInSeconds(1);
		findElement(driver, byRefreshButton, timeoutInSeconds);

		System.out.println(this.inputTimezone.getAttribute("Value"));
		System.out.println(this.inputTimezone.getAttribute("Value").contains(
				strTimezoneToChange));
		return (this.inputTimezone.getAttribute("Value")
				.contains(strTimezoneToChange));
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void clickSelectSurveyorButton() throws Exception {
		findElement(driver, byShowSideButton, timeoutInSeconds);
		if (this.btnShowSide.getText().contains(">>"))
			this.btnShowSide.click();
		this.btnSelectSurveyor.click();
		findElement(driver, byLiveMapBtn, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void showSurveyorWindowLiveMap(String strSurveyor) throws Exception {
		String strXpath = "";
		findElement(driver, bySurveyorLink, timeoutInSeconds);
		TestSetup.slowdownInSeconds(1);
		this.linkSelectSurveyor.click();
		findElement(driver, byCloseButton, timeoutInSeconds);

		this.inputSearchSurveyor.sendKeys(strSurveyor);
		for (int i = 1; i <= this.analyzersList.size();) {
			strXpath = "//table[@id='id_anzListTbl']/tbody/tr[" + i + "]/td[1]";
			if (driver.findElement(By.xpath(strXpath)).getText()
					.contains(strSurveyor)) {
				strXpath = "//table[@id='id_anzListTbl']/tbody/tr[" + i
						+ "]/td[2]/button";
				driver.findElement(By.xpath(strXpath)).click();
				break;
			} else
				i++;
		}
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean compareUsersLogForSpecifiedDateInListCalendarView(
			String strSurveyor, String numberOfEntries) throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowList))
			this.btnShowCalOrList.click();
		findElement(driver, bySearchBox, timeoutInSeconds);
		this.inputSearchLog.sendKeys(STRDateToSelect);

		Select selectNoOfLogEntries = new Select(this.btnShowNLogEntries);
		selectNoOfLogEntries.selectByValue(numberOfEntries);
		String strLogListSize = Integer.toString(this.logList.size());
		List<String> strLogList = new ArrayList<String>();

		for (int i = 1; i <= this.logList.size(); i++) {
			strLogList.add(driver.findElement(
					By.xpath("//table[@id='id_logTable']/tbody/tr" + "[" + i
							+ "]" + "/" + "td[2]")).getText());
		}
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();
		findElement(driver, byFirstLogButton, timeoutInSeconds);
		this.btnFirstLog.click();
		this.btnNextMonth.click();

		// time being tested to click on 18th Feb 2014 - FDDS2037
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[4]/td[3]/button"))
				.click();
		TestSetup.slowdownInSeconds(1);
		selectNoOfLogEntries = new Select(this.btnShowNLogListEntries);
		selectNoOfLogEntries.selectByValue(numberOfEntries);
		List<String> strCalLog = new ArrayList<String>();

		for (int i = 1; i <= this.surveysListCalendarView.size(); i++) {
			strCalLog.add(driver.findElement(
					By.xpath("//table[@id='id_logListTbl']/tbody/tr" + "[" + i
							+ "]" + "/" + "td[2]")).getText());
		}
		if (Integer.toString(this.surveysListCalendarView.size())
				.equalsIgnoreCase(strLogListSize)) {
			for (int i = 1; i <= this.surveysListCalendarView.size();) {
				if (strCalLog.get(i - 1).contains(strLogList.get(i - 1))) {
					i++;
				} else {
					this.btnCloseSurveysWindow.click();
					TestSetup.slowdownInSeconds(1);
					return false;
				}
			}
		}
		this.btnCloseSurveysWindow.click();
		TestSetup.slowdownInSeconds(1);
		return true;
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void showSurveyorMapLogFromCalendarView(String strSurveyor,
			String strLogName) throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();
		findElement(driver, byFirstLogButton, timeoutInSeconds);
		this.btnFirstLog.click();

		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();
		TestSetup.slowdownInSeconds(1);
		this.inputSearchLogCalendarView.sendKeys(strLogName);
		if (this.surveysListCalendarView.get(0).getText().contains(strLogName))
			this.btnFirstMapLogCalendarView.click();
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean closeSurveysWindowInCalendarView(String strSurveyor)
			throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();
		findElement(driver, byFirstLogButton, timeoutInSeconds);
		this.btnFirstLog.click();

		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();
		TestSetup.slowdownInSeconds(1);
		this.btnCloseSurveysWindow.click();
		TestSetup.slowdownInSeconds(1);
		return isElementPresent(driver, By.xpath(this.daySurveyWindow),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 */
	public boolean showNLogListEntries(String numberOfEntries) throws Exception {
		boolean result = false;

		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();
		findElement(driver, byFirstLogButton, timeoutInSeconds);
		this.btnFirstLog.click();
		this.btnNextMonth.click();

		// time being tested to click on 18th Feb 2014 - FDDS2037
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[4]/td[3]/button"))
				.click();
		TestSetup.slowdownInSeconds(1);
		Select selectNoOfLogEntries = new Select(this.btnShowNLogListEntries);
		selectNoOfLogEntries.selectByValue(numberOfEntries);

		if (Integer.toString(this.surveysListCalendarView.size()).compareTo(
				numberOfEntries) == 0)
			result = true;
		if (Integer.toString(this.surveysListCalendarView.size()).compareTo(
				numberOfEntries) == -1)
			result = true;
		this.closeSurveysWindow();
		return result;
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentForLiveMap(String strSurveyor,
			String strView) throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (strView.contains("List")) {
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}
		findElement(driver, byLiveMapBtn, timeoutInSeconds);
		this.btnLiveMap.click();
		findElement(driver, byShowSideButton, timeoutInSeconds);
		if (this.btnShowSide.getText().contains(">>"))
			this.btnShowSide.click();
		this.clickSelectSurveyorButton();
		TestSetup.slowdownInSeconds(2);
		return isElementPresent(driver, bySurveyorLink, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentForMapLogInListView(String strSurveyor,
			String strLogName) throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();
		findElement(driver, bySearchBox, timeoutInSeconds);
		String strXpath = "";
		for (int i = 1; i <= this.logList.size(); i++) {
			strXpath = "//table[@id='id_logTable']/tbody/tr" + "[" + i + "]"
					+ "/" + "td[2]";
			if (driver.findElement(By.xpath(strXpath)).getText()
					.equals(strLogName)) {
				driver.findElement(
						By.xpath("//table[@id='id_logTable']/tbody/tr" + "["
								+ i + "]" + "/" + "td[5]/button")).click();
				break;
			}
		}
		findElement(driver, byShowSideButton, timeoutInSeconds);
		if (this.btnShowSide.getText().contains(">>"))
			this.btnShowSide.click();
		this.clickSelectSurveyorButton();
		TestSetup.slowdownInSeconds(2);
		return isElementPresent(driver, bySurveyorLink, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentForMapLogInCalendarView(
			String strSurveyor, String strLogName) throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowList))
			findElement(driver, bySearchBox, timeoutInSeconds);

		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		findElement(driver, byFirstLogButton, timeoutInSeconds);
		this.btnFirstLog.click();
		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();

		this.inputSearchLogCalendarView.sendKeys(strLogName);
		if (this.surveysListCalendarView.get(0).getText().contains(strLogName))
			this.btnFirstMapLogCalendarView.click();
		findElement(driver, byShowSideButton, timeoutInSeconds);
		if (this.btnShowSide.getText().contains(">>"))
			this.btnShowSide.click();
		this.clickSelectSurveyorButton();
		TestSetup.slowdownInSeconds(2);
		return isElementPresent(driver, bySurveyorLink, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentBackFromLiveMap(String strSurveyor,
			String strView) throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (strView.contains("List")) {
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}
		this.btnLiveMap.click();
		driver.navigate().back();
		findElement(driver, byLiveMapBtn, timeoutInSeconds);
		TestSetup.slowdownInSeconds(2);
		return isElementPresent(driver, bySurveyorLink, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentBackFromMapLogListView(
			String strSurveyor, String strLogName) throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();
		findElement(driver, bySearchBox, timeoutInSeconds);
		String strXpath = "";
		for (int i = 1; i <= this.logList.size(); i++) {
			strXpath = "//table[@id='id_logTable']/tbody/tr" + "[" + i + "]"
					+ "/" + "td[2]";
			if (driver.findElement(By.xpath(strXpath)).getText()
					.equals(strLogName)) {
				driver.findElement(
						By.xpath("//table[@id='id_logTable']/tbody/tr" + "["
								+ i + "]" + "/" + "td[5]/button")).click();
				break;
			}
		}
		driver.navigate().back();
		TestSetup.slowdownInSeconds(2);
		return isElementPresent(driver, bySurveyorLink, timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentBackFromMapLogCalendarView(
			String strSurveyor, String strLogName) throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();
		findElement(driver, byFirstLogButton, timeoutInSeconds);
		this.btnFirstLog.click();
		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();
		TestSetup.slowdownInSeconds(1);
		this.inputSearchLogCalendarView.sendKeys(strLogName);
		if (this.surveysListCalendarView.get(0).getText().contains(strLogName))
			this.btnFirstMapLogCalendarView.click();
		driver.navigate().back();
		TestSetup.slowdownInSeconds(2);
		return isElementPresent(driver, bySurveyorLink, timeoutInSeconds);
	}

	/**
	 * 
	 * @author pmahajan
	 */
	public String getFirstLogDateTimeInCalendarView() throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contentEquals(STRShowCalendar))
			this.btnShowCalOrList.click();
		findElement(driver, byFirstLogButton, timeoutInSeconds);
		this.btnFirstLog.click();
		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();
		TestSetup.slowdownInSeconds(1);
		System.out.println(this.firstLogTimeClndrVw.getText());
		return this.firstLogTimeClndrVw.getText();
	}

	public LoginPage logout() throws Exception {
		this.userIDSite.click();
		TestSetup.slowdownInSeconds(1);
		this.linkSignOff.click();
		LoginPage loginPage = new LoginPage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, loginPage);
		return loginPage;
	}

	public boolean isNGLPageOpen() throws Exception {
		TestSetup.slowdownInSeconds(3);
		return (this.headNGL.getText().contains(STRHeadNGL));
	}

	public HomePage goBackToHomePage() throws Exception {
		this.menuProcess.click();
		TestSetup.slowdownInSeconds(1);
		this.linkHome.click();
		HomePage homePage = new HomePage(this.driver, this.strBaseURL);
		PageFactory.initElements(this.driver, homePage);
		return homePage;
	}

	public Hashtable<String, String> getLogDate(String strSurveyor,
			String strFirstLast) throws Exception {
		this.selectSurveyor(strSurveyor);
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowList))
			this.btnShowCalOrList.click();
		findElement(driver, bySearchBox, timeoutInSeconds);

		if (strFirstLast.contains("first")) {
			if (!(isElementPresent(driver, byLogListAsc, timeoutInSeconds)))
				this.descLogList.click();
		} else {
			if (isElementPresent(driver, byLogListAsc, timeoutInSeconds))
				this.ascLogList.click();
		}
		TestSetup.slowdownInSeconds(1);
		String dateTime = this.firstLogDate.getText();
		String year = dateTime.substring(7, 11);
		String month = dateTime.substring(12, 14);
		String day = dateTime.substring(15, 17);

		this.htLogDate.put("Year", year);
		this.htLogDate.put("Month", month);
		this.htLogDate.put("Day", day);
		return this.htLogDate;
	}

	public String getLogName(String strSurveyor) throws Exception {
		TestSetup.slowdownInSeconds(1);
		return this.firstLogName.getText();
	}

	public boolean checkLogPresentInCalVw(String strYear, String strMonth,
			String strDay, String strLogName) throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();
		findElement(driver, byFirstLogButton, timeoutInSeconds);

		String monthName = this.month[Integer.parseInt(strMonth)];
		System.out.println(monthName);
		String monthYear = monthName + " " + strYear;
		System.out.println(monthYear);
		boolean flagForWhileLoop = true;

		while (flagForWhileLoop) {
			if (!(this.txtMonthYear.getText().contains(monthYear))) {
				if (!(this.txtMonthYear.getText().contains(monthName))) {
					this.btnPrevMonth.click();
					continue;
				} else {
					if (this.txtMonthYear.getText().contains(strYear)) {
						flagForWhileLoop = false;
						break;
					} else {
						String year = this.txtMonthYear.getText().trim();
						year = year.substring(monthName.length() + 1);
						System.out.println(year);
						if (year.compareTo(strYear) <= -1) {
							this.btnNextYear.click();
							continue;
						}
						if (year.compareTo(strYear) >= 1) {
							this.btnPrevYear.click();
							continue;
						}
					}
				}
			} else {
				flagForWhileLoop = false;
				break;
			}
		}

		flagForWhileLoop = true;
		for (int rows = 1; rows <= this.rowsInCal.size(); rows++) {
			for (int cols = 1; cols <= this.colsInCal.size(); cols++) {
				WebElement eleDay = driver
						.findElement(By
								.xpath("// span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[ "
										+ rows
										+ "]/td["
										+ cols
										+ "]/div/button"));
				String day = eleDay.getText();
				if (day.length() == 1)
					day = "0" + day;
				System.out.println(day);
				if (day.contentEquals(strDay)) {
					eleDay.click();
					flagForWhileLoop = false;
					break;
				}
			}
			if (!flagForWhileLoop)
				break;
		}
		TestSetup.slowdownInSeconds(1);
		this.inputSearchLogCalendarView.sendKeys(strLogName);
		String logName = this.surveysListCalendarView.get(0).getText();
		System.out.println(logName);
		return logName.contains(strLogName);
	}

	public boolean compareUserLogsInListCalendarView(String strSurveyor,
			String strFirstLast) throws Exception {
		htLogDate = this.getLogDate(strSurveyor, strFirstLast);
		System.out.println(htLogDate.size());
		System.out.println(htLogDate.get("Day"));
		String logNameList = this.getLogName(strSurveyor);
		System.out.println(logNameList);
		boolean result = this.checkLogPresentInCalVw(htLogDate.get("Year"),
				htLogDate.get("Month"), htLogDate.get("Day"), logNameList);
		this.closeSurveysWindow();

		return result;
	}

	public boolean checkLogPresentInCalVw(String strYear, String strMonth,
			String strDay, String strFirstLast, String strLogName)
			throws Exception {
		findElement(driver, byShowCalListButton, timeoutInSeconds);
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();
		findElement(driver, byFirstLogButton, timeoutInSeconds);

		if (strFirstLast.contains(STRShowFirst))
			this.btnFirstLog.click();
		else
			this.btnLastLog.click();

		boolean flagForWhileLoop = true;
		for (int rows = 1; rows <= this.rowsInCal.size(); rows++) {
			for (int cols = 1; cols <= this.colsInCal.size(); cols++) {
				WebElement eleDay = driver
						.findElement(By
								.xpath("// span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[ "
										+ rows
										+ "]/td["
										+ cols
										+ "]/div/button"));
				String day = eleDay.getText();
				if (day.length() == 1)
					day = "0" + day;
				System.out.println(day);
				if (day.contentEquals(strDay)) {
					eleDay.click();
					flagForWhileLoop = false;
					break;
				}
			}
			if (!flagForWhileLoop)
				break;
		}
		TestSetup.slowdownInSeconds(1);
		this.inputSearchLogCalendarView.sendKeys(strLogName);
		String logName = this.surveysListCalendarView.get(0).getText();
		System.out.println(logName);
		return logName.contains(strLogName);
	}

	public boolean compareUserFirstLastLogsInListCalendarView(
			String strSurveyor, String strFirstLast) throws Exception {
		htLogDate = this.getLogDate(strSurveyor, strFirstLast);
		System.out.println(htLogDate.size());
		System.out.println(htLogDate.get("Day"));
		String logNameList = this.getLogName(strSurveyor);
		System.out.println(logNameList);
		boolean result = this.checkLogPresentInCalVw(htLogDate.get("Year"),
				htLogDate.get("Month"), htLogDate.get("Day"), strFirstLast,
				logNameList);
		this.closeSurveysWindow();

		return result;
	}
}