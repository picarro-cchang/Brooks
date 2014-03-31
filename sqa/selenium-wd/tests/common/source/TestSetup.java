/**
 * 
 */
package common.source;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Hashtable;
import java.util.Properties;
import java.util.Random;
import java.util.concurrent.TimeUnit;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.firefox.FirefoxProfile;
import org.openqa.selenium.ie.InternetExplorerDriver;
import org.openqa.selenium.remote.CapabilityType;
import org.openqa.selenium.remote.DesiredCapabilities;
import org.openqa.selenium.remote.RemoteWebDriver;

/**
 * This is the initial class to setup up the testing environment and
 * configuration
 * 
 * 1. Load the testing property for test setup information.
 * 
 * 2. Setting up the drivers.
 * 
 * 3. It is ongoing and add more code here later when needed
 * 
 * @version 1.0
 * @author zlu
 * 
 */
public class TestSetup {

	private static final String testPropFileName = "test.properties";
	private Properties testProp;

	private String baseURL;
	private String runningOnRemoteServer;
	private String remoteServerHost;
	private String remoteServerPort;

	private String loginUser0000;
	private String loginPwd0000;
	private String loginUser0001;
	private String loginPwd0001;
	private String loginUserDisplayName;

	private String loginUserA;
	private String loginPwdA;
	private String loginUserADisplayName;

	private String loginUser00A;
	private String loginPwd00A;
	private String loginUser00ADisplayName;

	private String surveyor;
	private String logFile;
	private String analyzer;

	private String browser;
	private String chromeDriverPath;
	private String ieDriverPath;

	private String implicitlyWaitTimeOutInSeconds;
	private String implicitlyWaitSpecialTimeOutInMS;

	private String language;
	private boolean debug = false;

	private DateFormat dateFormat;
	private Calendar calendar;

	private String randomNumber;

	private WebDriver driver;

	private Hashtable<String, String> htReportData;

	private String slowdownInSeconds; // For debugging the code and not
										// recommended to use in real test case

	/**
	 * @author pmahajan
	 */
	FirefoxProfile firefoxProfile = null;
	private String timezone;
	private String timezoneToSelect;
	private String timezoneNotToSelect;
	private String show10Entries;
	private String show25Entries;
	private String surveyor2;
	private String logFile2;

	/**
	 * 
	 */
	public TestSetup() {

		try {
			// InputStream inputStream = new FileInputStream("../"
			// + testPropFileName);

			InputStream inputStream = new FileInputStream(testPropFileName);

			testProp = new Properties();
			testProp.load(inputStream);

			this.dateFormat = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
			this.calendar = Calendar.getInstance();
			System.out.println(dateFormat.format(this.calendar.getTime())
					+ "\n");

			this.baseURL = this.testProp.getProperty("baseURL");
			System.out.println("The baseURL is: " + this.baseURL + "\n");

			this.runningOnRemoteServer = this.testProp
					.getProperty("runningOnRemoteServer");
			this.remoteServerHost = this.testProp
					.getProperty("remoteServerHost");
			this.remoteServerPort = this.testProp
					.getProperty("remoteServerPort");

			this.loginUser0000 = this.testProp.getProperty("loginUser0000");
			this.loginPwd0000 = this.testProp.getProperty("loginPwd0000");
			this.loginUser0001 = this.testProp.getProperty("loginUser0001");
			this.loginPwd0001 = this.testProp.getProperty("loginPwd0001");
			this.loginUserDisplayName = this.testProp
					.getProperty("loginUserDisplayName");

			this.loginUserA = this.testProp.getProperty("loginUserA");
			this.loginPwdA = this.testProp.getProperty("loginPwdA");
			this.loginUserADisplayName = this.testProp
					.getProperty("loginUserADisplayName");

			this.loginUser00A = this.testProp.getProperty("loginUser00A");
			this.loginPwd00A = this.testProp.getProperty("loginPwd00A");
			this.loginUser00ADisplayName = this.testProp
					.getProperty("loginUser00ADisplayName");

			this.surveyor = this.testProp.getProperty("surveyor");
			this.logFile = this.testProp.getProperty("logFile");
			this.analyzer = this.testProp.getProperty("analyzer");
			this.surveyor2 = this.testProp.getProperty("surveyor2");
			this.logFile2 = this.testProp.getProperty("logFile2");
			this.timezone = this.testProp.getProperty("Timezone");
			this.timezoneToSelect = this.testProp
					.getProperty("TimezoneToSelect");
			this.timezoneNotToSelect = this.testProp
					.getProperty("TimezoneNotToSelect");
			this.show10Entries = this.testProp.getProperty("show10Entries");
			this.show25Entries = this.testProp.getProperty("show25Entries");

			this.browser = this.testProp.getProperty("browser");
			System.out.println("The browser is: " + this.browser + "\n");

			this.ieDriverPath = this.testProp.getProperty("ieDriverPath");
			this.chromeDriverPath = this.testProp
					.getProperty("chromeDriverPath");

			this.implicitlyWaitTimeOutInSeconds = this.testProp
					.getProperty("implicitlyWaitTimeOutInSeconds");
			this.implicitlyWaitSpecialTimeOutInMS = this.testProp
					.getProperty("implicitlyWaitSpecialTimeOutInMS");

			this.language = this.testProp.getProperty("language");

			if (this.testProp.getProperty("debug").equals("true")) {
				this.debug = true;
			} else {
				this.debug = false;
			}

			this.slowdownInSeconds = this.testProp
					.getProperty("slowdownInSeconds");

			this.randomNumber = Long.toString((new Random()).nextInt(1000000));
			System.out.println("The random number is: " + this.randomNumber
					+ "\n");

			driverSetup();

			htReportDataSetup();

			if (debug) {
				for (String strKey : this.htReportData.keySet()) {
					System.out.println("The htReportData - key: " + strKey
							+ "   value: " + this.htReportData.get(strKey));
				}
			}

			inputStream.close();

		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	private void driverSetup() {

		try {
			if (this.runningOnRemoteServer != null
					&& this.runningOnRemoteServer.trim()
							.equalsIgnoreCase("Yes")) {
				switch (this.browser.trim()) {
				case "chrome":

					DesiredCapabilities capabilities = DesiredCapabilities
							.chrome();
					ChromeOptions options = new ChromeOptions();
					options.addArguments(Arrays.asList(
							"allow-running-insecure-content",
							"ignore-certificate-errors"));
					capabilities.setCapability(ChromeOptions.CAPABILITY,
							options);
					driver = new RemoteWebDriver(new URL("http://"
							+ this.remoteServerHost + ":4444/wd/hub/"),
							capabilities);
					break;
				case "ie":
					driver = new RemoteWebDriver(new URL("http://"
							+ this.remoteServerHost + ":4444/wd/hub/"),
							DesiredCapabilities.internetExplorer());
					break;
				case "ff":

					DesiredCapabilities capabilitiesFF = DesiredCapabilities
							.firefox();
					capabilitiesFF.setCapability(
							CapabilityType.ACCEPT_SSL_CERTS, true);
					driver = new RemoteWebDriver(new URL("http://"
							+ this.remoteServerHost + ":4444/wd/hub/"),
							capabilitiesFF);
					break;
				}

				System.out.println("The server is running remote on: "
						+ this.remoteServerHost + "\n");
			} else {
				switch (this.browser.trim()) {
				case "chrome":
					System.setProperty("webdriver.chrome.driver",
							this.chromeDriverPath);
					System.out
							.println("The System Propery 'webdriver.chrome.driver' is: "
									+ System.getProperty(
											"webdriver.chrome.driver")
											.toString() + "\n");
					driver = new ChromeDriver();
					break;
				case "ie":
					System.setProperty("webdriver.ie.driver", this.ieDriverPath);
					System.out
							.println("The System Propery 'webdriver.ie.driver' is: "
									+ System.getProperty("webdriver.ie.driver")
											.toString() + "\n");
					driver = new InternetExplorerDriver();
					break;
				case "ff":
					firefoxProfile = new FirefoxProfile();
					firefoxProfile.setPreference("browser.download.folderList", 2);
					firefoxProfile.setPreference(
							"browser.download.manager.showWhenStarting", false);
					firefoxProfile.setPreference("browser.download.dir", "c:\\downloads");
					firefoxProfile.setPreference("browser.helperApps.neverAsk.saveToDisk",
							"application/pdf, application/json");
					driver = new FirefoxDriver(firefoxProfile);
					break;
				}

				System.out.println("Running local without server\n");
			}

			driver.manage()
					.timeouts()
					.implicitlyWait(
							Long.parseLong(this.implicitlyWaitTimeOutInSeconds
									.trim()), TimeUnit.SECONDS);
			System.out
					.println("The default implicitlyWaitTimeOut has been set to "
							+ this.implicitlyWaitTimeOutInSeconds.trim()
							+ " seconds" + "\n\n");

		} catch (Exception e) {
			e.printStackTrace();
			System.exit(1);
		}
	}

	public WebDriver getDriver() {
		return this.driver;
	}

	public String getBaseUrl() {
		return this.baseURL;
	}

	public String getLoginUser0000() {
		return this.loginUser0000;
	}

	public String getLoginPwd0000() {
		return this.loginPwd0000;
	}

	public String getLoginUser0001() {
		return this.loginUser0001;
	}

	public String getLoginPwd0001() {
		return this.loginPwd0001;
	}

	public String getLoginUserDisplayName() {
		return this.loginUserDisplayName;
	}

	public String getLoginUserA() {
		return this.loginUserA;
	}

	public String getLoginPwdA() {
		return this.loginPwdA;
	}

	public String getLoginUserADisplayName() {
		return this.loginUserADisplayName;
	}

	public String getLoginUser00A() {
		return this.loginUser00A;
	}

	public String getLoginPwd00A() {
		return this.loginPwd00A;
	}

	public String getLoginUser00ADisplayName() {
		return this.loginUserADisplayName;
	}

	// for testing code debug only
	public static void slowdownInSeconds(int seconds) {
		try {
			Thread.sleep(seconds * 1000);
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	public boolean isRunningDebug() {
		if (debug)
			return true;
		else
			return false;
	}

	public String getSurveyor() {
		return this.surveyor;
	}

	public String getLogFile() {
		return this.logFile;
	}

	public String getAnalyzer() {
		return this.analyzer;
	}

	public String getSurveyor2() {
		return this.surveyor2;
	}

	public String getLogFile2() {
		return this.logFile2;
	}

	/**
	 * @author pmahajan
	 */
	public String getTimezoneToSelect() {
		return this.timezoneToSelect;
	}

	/**
	 * @author pmahajan
	 */
	public String getTimezone() {
		return this.timezone;
	}

	/**
	 * @author pmahajan
	 */
	public String getTimezoneNotToSelect() {
		return this.timezoneNotToSelect;
	}

	/**
	 * @author pmahajan
	 */
	public String getShow10Entries() {
		return this.show10Entries;
	}

	/**
	 * @author pmahajan
	 */
	public String getShow25Entries() {
		return this.show25Entries;
	}

	/**
	 * @author pmahajan
	 */
	public String getRandomNumber() {
		return this.randomNumber;
	}

	public void htReportDataSetup() {
		// ***Refactoring this part of the code later, should have object
		// class...***//

		htReportData = new Hashtable<String, String>();
		this.htReportData.put("Title", this.testProp.getProperty("surveyor")
				+ this.loginUser0000 + this.randomNumber);
		this.htReportData.put("SWCornerLat",
				this.testProp.getProperty("SWCornerLat"));
		this.htReportData.put("SWCornerLong",
				this.testProp.getProperty("SWCornerLong"));
		this.htReportData.put("NECornerLat",
				this.testProp.getProperty("NECornerLat"));
		this.htReportData.put("NECornerLong",
				this.testProp.getProperty("NECornerLong"));
		this.htReportData.put("peaksMinAmp",
				this.testProp.getProperty("peaksMinAmp"));
		this.htReportData.put("noOfRowsCols",
				this.testProp.getProperty("noOfRowsCols"));
		this.htReportData.put("StartTime",
				this.testProp.getProperty("StartTime"));
		this.htReportData.put("EndTime", this.testProp.getProperty("EndTime"));
	}

	public Hashtable<String, String> getHTReportData() {
		return this.htReportData;
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// for code testing
		TestSetup obj = new TestSetup();
		System.out.println();
		System.out.println(obj.toString());
		obj.getDriver().close();
	}
}
