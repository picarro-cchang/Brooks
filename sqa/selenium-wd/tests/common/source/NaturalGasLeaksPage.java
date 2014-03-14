/**
 * 
 */
package common.source;

import static org.junit.Assert.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.How;
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

	// pmahajan
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
	private String surveyorPanel = "//div[@id='id_logModal' and @class='modal hide fade in']";

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
	private WebElement strTimezone;

	// pmahajan
	@FindBy(how = How.ID, using = "id_selectAnalyzerBtn")
	private WebElement btnSelectSurveyor;

	// pmahajan
	@FindBy(how = How.ID, using = "id_p3gdulist_Close_DaySelector")
	private WebElement btnCloseSurveysWindow;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//select[@name='id_logListTbl_length']")
	private WebElement btnShowNLogListEntries;

	// pmahajan
	// @FindBy(how = How.ID, using = "id_logModal")
	private String daySurveyWindow = "//div[@id='id_logModal' and @class='modal hide fade']";

	// pmahajan
	@FindBy(how = How.XPATH, using = "//button[contains(text(),'Next Month')]")
	private WebElement btnNextMonth;

	// pmahajan
	@FindBy(how = How.ID, using = "id_side_show_btn")
	private WebElement btnShowSide;

	// pmahajan
	@FindBy(how = How.XPATH, using = "//table[@id='id_logListTbl']/tbody/tr[1]/td[1]")
	private WebElement firstLogTimeClndrVw;

	private String strRefreshButton = "//button[@id='id_getLogBtn' and contains(text(),'Refresh')]";
	private String strSurveyorLink = "//div[@id='id_anzTitle']/a";
	private String strCloseButton = "//button[@id='id_p3gduclose_btn']";
	private String strLiveMapButton = "//button[contains(text(),'Live Map')]";
	private String strCloseViewMetadataButton = "//button[@id='id_p3gdulist_Close_log_log']";
	private By byShowSideButton = By.xpath("//btn[@id='id_side_show_btn']");
	private By byShowCalListButton = By.xpath("//button[@id='id_calListBtn']");
	private By byFirstLogButton = By.xpath("//button[contains(text(),'First Log')]");
	
	public NaturalGasLeaksPage(WebDriver driver, String baseURL) {
		super(driver, STRPageTitle);
		this.strBaseURL = baseURL;
		this.strPageURL = this.strBaseURL + STRURLPath;

		System.out.println("\nThe NaturalGasLeaksPage URL is: "
				+ this.strPageURL);
	}

	public List<String> getSurveyorList() throws Exception {
		findElement(driver, By.xpath(strSurveyorLink), timeoutInSeconds);
		this.linkSelectSurveyor.click();
		findElement(driver, By.xpath(strCloseButton), timeoutInSeconds);

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
		try {
			findElement(driver, By.xpath(strSurveyorLink), timeoutInSeconds);
			this.linkSelectSurveyor.click();
			findElement(driver, By.xpath(strCloseButton), timeoutInSeconds);

			Select selectNoOfAnalyzerEntries = new Select(
					this.showNAnalyzerEntries);
			selectNoOfAnalyzerEntries.selectByValue("100");
			for (int i = 1; i <= this.analyzersList.size(); i++) {
				if (isElementPresent(By.linkText(strSurveyor)))
					driver.findElement(By.linkText(strSurveyor)).click();
				else if (this.linkNextSurveyorList.isEnabled())
					this.linkNextSurveyorList.click();
				else
					System.out.println(strSurveyor + " Surveyor not found!!");
			}
		} catch (Exception e) {
			assertTrue("Exception Caught : " + e.getMessage(), false);
		}
		TestSetup.slowdownInSeconds(1);
	}

	public List<String> getSurveyorLogList(String strSurveyor) throws Exception {
		this.selectSurveyor(strSurveyor);
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();

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

		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();

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
		return this.linkSelectSurveyor.getText().contains(strSurveyor);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public String getDuration(String strLogName) throws Exception {
		String duration = "";
		String strXpath = "";

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
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();

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
		findElement(driver, By.xpath(strCloseViewMetadataButton),
				timeoutInSeconds);
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
		this.btnCloseViewMetadata.click();
		findElement(driver, By.xpath(strSurveyorLink), timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void showSurveyorLiveMap(String strSurveyor, String strView)
			throws Exception {
		if (strView.contains("List")) {
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}
		this.selectSurveyor(strSurveyor);
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
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}

		this.btnRefresh.click();
		if (this.btnRefresh.getText().contains(STRRefreshing))
			return true;
		else
			return false;
	}

	public boolean isRefreshButtonPresent() throws Exception {
		return isElementPresent(driver, By.xpath(strRefreshButton),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean closeSurveyorWindow() throws Exception {
		this.linkSelectSurveyor.click();
		findElement(driver, By.xpath(strCloseButton), timeoutInSeconds);
		this.btnClose.click();
		return isElementPresent(driver, By.xpath(this.surveyorPanel),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean changeTimezoneOfSurveyor(String strSurveyor,
			String strTimezoneToSelect, String strView) throws Exception {
		this.selectSurveyor(strSurveyor);
		if (strView.contains("List")) {
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}
		this.btnChangeTimezone.click();
		Select selectTimezoneValue = new Select(this.selectTimezone);
		selectTimezoneValue.selectByValue(strTimezoneToSelect);
		this.btnSaveTimezone.click();
		if (strView.contains("List"))
			return this.getFirstLogDateTime().contains(STRChangedTimezoneTime);
		else
			return this.getFirstLogDateTimeInCalendarView().contains(
					STRChangedTimezoneTime);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean selectNoTimezoneForSurveyor(String strSurveyor,
			String strView) throws Exception {
		this.selectSurveyor(strSurveyor);
		if (strView.contains("List")) {
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}
		this.btnChangeTimezone.click();
		Select selectTimezoneValue = new Select(this.selectTimezone);
		selectTimezoneValue.selectByValue("");
		this.btnSaveTimezone.click();
		if (strView.contains("List"))
			return this.getFirstLogDateTime().contains(
					STRNoTimezoneSelectedTime);
		else
			return this.getFirstLogDateTimeInCalendarView().contains(
					STRNoTimezoneSelectedTime);
	}

	/**
	 * 
	 * @author pmahajan
	 */
	public String getFirstLogDateTime() throws Exception {
		if (this.btnShowCalOrList.getText().contentEquals(STRShowList))
			this.btnShowCalOrList.click();

		return this.firstLogDate.getText();
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean searchLogFile(String strSurveyor, String strLogName,
			String validInvalidLog) throws Exception {
		this.selectSurveyor(strSurveyor);

		if (this.btnShowCalOrList.getText().contains(STRShowList))
			this.btnShowCalOrList.click();

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
		if (this.btnShowCalOrList.getText().contains(STRShowList))
			this.btnShowCalOrList.click();

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
		findElement(driver, By.xpath(strSurveyorLink), timeoutInSeconds);
		this.linkSelectSurveyor.click();
		findElement(driver, By.xpath(strCloseButton), timeoutInSeconds);

		this.inputSearchSurveyor.sendKeys(strSurveyor);
		if (validInvalidSurveyor.contentEquals("valid")) {
			for (int i = 1; i <= this.analyzersList.size();) {
				strXpath = "//table[@id='id_anzListTbl']/tbody/tr[" + i
						+ "]/td[1]";
				if (driver.findElement(By.xpath(strXpath)).getText()
						.contains(strSurveyor))
					return true;
				else
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
		findElement(driver, By.xpath(strSurveyorLink), timeoutInSeconds);
		this.linkSelectSurveyor.click();
		findElement(driver, By.xpath(strCloseButton), timeoutInSeconds);

		Select selectNoOfAnalyzerEntries = new Select(this.showNAnalyzerEntries);
		selectNoOfAnalyzerEntries.selectByValue(numberOfEntries);
		TestSetup.slowdownInSeconds(1);
		System.out.println(Integer.toString(this.analyzersList.size()));
		return (Integer.toString(this.analyzersList.size())
				.contentEquals(numberOfEntries));
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean searchLogFileInCalendarView(String strSurveyor,
			String strLogName, String validInvalidLog) throws Exception {
		this.selectSurveyor(strSurveyor);

		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		this.btnFirstLog.click();

		// time being tested to click on 15th Jan 2014 - FDDS2037
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[4]/button"))
				.click();

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

		Select selectTimezoneValue = new Select(this.selectTimezone);
		selectTimezoneValue.selectByValue(strTimezoneToChange);
		this.btnCancelTimezone.click();
		return (this.strTimezone.getAttribute("Value")
				.contains(strTimezoneToChange));
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void clickSelectSurveyorButton() throws Exception {
		this.btnSelectSurveyor.click();
		findElement(driver, By.xpath(strLiveMapButton), timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void showSurveyorWindowLiveMap(String strSurveyor) throws Exception {
		String strXpath = "";
		findElement(driver, By.xpath(strSurveyorLink), timeoutInSeconds);
		this.linkSelectSurveyor.click();
		findElement(driver, By.xpath(strCloseButton), timeoutInSeconds);

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

		if (this.btnShowCalOrList.getText().contains(STRShowList))
			this.btnShowCalOrList.click();

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
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		this.btnFirstLog.click();
		this.btnNextMonth.click();

		// time being tested to click on 18th Feb 2014 - FDDS2037
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[4]/td[3]/button"))
				.click();

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
				} else
					return false;
			}
		}
		return true;
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public void showSurveyorMapLogFromCalendarView(String strSurveyor,
			String strLogName) throws Exception {
		this.selectSurveyor(strSurveyor);

		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		this.btnFirstLog.click();

		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();

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

		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		this.btnFirstLog.click();

		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();

		this.btnCloseSurveysWindow.click();
		return isElementPresent(driver, By.xpath(this.daySurveyWindow),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 */
	public boolean showNLogListEntries(String numberOfEntries) throws Exception {
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		this.btnFirstLog.click();
		this.btnNextMonth.click();

		// time being tested to click on 18th Feb 2014 - FDDS2037
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[4]/td[3]/button"))
				.click();

		Select selectNoOfLogEntries = new Select(this.btnShowNLogListEntries);
		selectNoOfLogEntries.selectByValue(numberOfEntries);

		return (Integer.toString(this.surveysListCalendarView.size())
				.contentEquals(numberOfEntries));
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentForLiveMap(String strSurveyor,
			String strView) throws Exception {
		this.selectSurveyor(strSurveyor);
		if (strView.contains("List")) {
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}
		this.btnLiveMap.click();
		findElement(driver, byShowSideButton, timeoutInSeconds);
		if (this.btnShowSide.getText().contains(">>"))
			this.btnShowSide.click();
		this.clickSelectSurveyorButton();

		return isElementPresent(driver, By.xpath(strSurveyorLink),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentForMapLogInListView(String strSurveyor,
			String strLogName) throws Exception {
		this.selectSurveyor(strSurveyor);
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();

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
		return isElementPresent(driver, By.xpath(strSurveyorLink),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentForMapLogInCalendarView(
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

		this.inputSearchLogCalendarView.sendKeys(strLogName);
		if (this.surveysListCalendarView.get(0).getText().contains(strLogName))
			this.btnFirstMapLogCalendarView.click();
		findElement(driver, byShowSideButton, timeoutInSeconds);
		if (this.btnShowSide.getText().contains(">>"))
			this.btnShowSide.click();
		this.clickSelectSurveyorButton();

		return isElementPresent(driver, By.xpath(strSurveyorLink),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentBackFromLiveMap(String strSurveyor,
			String strView) throws Exception {
		if (strView.contains("List")) {
			if (this.btnShowCalOrList.getText().contains(STRShowList))
				this.btnShowCalOrList.click();
		} else {
			if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
				this.btnShowCalOrList.click();
		}
		this.btnLiveMap.click();
		driver.navigate().back();
		return isElementPresent(driver, By.xpath(strSurveyorLink),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentBackFromMapLogListView(
			String strSurveyor, String strLogName) throws Exception {
		if (btnShowCalOrList.getText().contains(STRShowList))
			btnShowCalOrList.click();

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
		return isElementPresent(driver, By.xpath(strSurveyorLink),
				timeoutInSeconds);
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean surveyorLinkPresentBackFromMapLogCalendarView(
			String strSurveyor, String strLogName) throws Exception {
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		this.btnFirstLog.click();
		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();

		this.inputSearchLogCalendarView.sendKeys(strLogName);
		if (this.surveysListCalendarView.get(0).getText().contains(strLogName))
			this.btnFirstMapLogCalendarView.click();
		driver.navigate().back();

		return isElementPresent(driver, By.xpath(strSurveyorLink),
				timeoutInSeconds);
	}

	/**
	 * 
	 * @author pmahajan
	 */
	public String getFirstLogDateTimeInCalendarView() throws Exception {
		if (this.btnShowCalOrList.getText().contentEquals(STRShowCalendar))
			this.btnShowCalOrList.click();
		this.btnFirstLog.click();
		// time being tested - click on 10th June 2012 - DEMO2000
		driver.findElement(
				By.xpath("//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[3]/td[1]/button"))
				.click();
		System.out.println(this.firstLogTimeClndrVw.getText());
		return this.firstLogTimeClndrVw.getText();
	}

	/**
	 * @author pmahajan
	 * @return
	 */
	public boolean compareUserLogsInListCalendarView(String strSurveyor)
			throws Exception {
		this.selectSurveyor(strSurveyor);

		if (this.btnShowCalOrList.getText().contains(STRShowList))
			this.btnShowCalOrList.click();

		Select selectNoOfLogEntries = new Select(this.btnShowNLogEntries);
		selectNoOfLogEntries.selectByValue(STRShow100Entries);
		List<String> strLogList = new ArrayList<String>();

		for (int i = 1; i <= this.logList.size(); i++) {
			strLogList.add(driver.findElement(
					By.xpath("//table[@id='id_logTable']/tbody/tr" + "[" + i
							+ "]" + "/" + "td[2]")).getText());
		}
		if (this.btnShowCalOrList.getText().contains(STRShowCalendar))
			this.btnShowCalOrList.click();

		this.btnFirstLog.click();

		/**
		 * how to get all logs from calendar view
		 */

		// time being tested to click on 18th Feb 2014 - FDDS2037
		/*
		 * driver.findElement( By.xpath(
		 * "//span[@id='id_right_content']/div/div/table/tbody/tr[4]/td/table/tbody/tr[4]/td[3]/button"
		 * )) .click();
		 * 
		 * selectNoOfLogEntries = new Select(this.btnShowNLogListEntries);
		 * selectNoOfLogEntries.selectByValue(numberOfEntries); List<String>
		 * strCalLog = new ArrayList<String>();
		 * 
		 * for (int i = 1; i <= this.surveysListCalendarView.size(); i++) {
		 * strCalLog.add(driver.findElement(
		 * By.xpath("//table[@id='id_logListTbl']/tbody/tr" + "[" + i + "]" +
		 * "/" + "td[2]")).getText()); } if
		 * (Integer.toString(this.surveysListCalendarView.size())
		 * .equalsIgnoreCase(strLogListSize)) { for (int i = 1; i <=
		 * this.surveysListCalendarView.size();) { if (strCalLog.get(i -
		 * 1).contains(strLogList.get(i - 1))) { i++; } else return false; } }
		 */
		return true;
	}
}