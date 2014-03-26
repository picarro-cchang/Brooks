/**
 * 
 */
package common.source;

import java.util.Set;

import org.openqa.selenium.Alert;
import org.openqa.selenium.By;
import org.openqa.selenium.NoSuchElementException;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

/**
 * @author zlu
 * 
 *         Add more general code later for pages
 * 
 */
public class BasePage {

	protected String strBaseURL;
	protected String strPageURL;
	protected WebDriver driver;
	protected String pageTitle;
	protected String parentWindow;

	public BasePage(WebDriver driver, String pageTitle) {
		this.driver = driver;
		this.pageTitle = pageTitle;
	}

	public boolean isPageLoad() {
		return (driver.getTitle().contains(pageTitle));
	}

	public void open() {
		driver.get(strPageURL);
	}

	public String getTitle() {
		return pageTitle;
	}

	public String getStrPageURL() {
		return this.strPageURL;
	}

	public boolean isTextPresent(String text) {
		return driver.getPageSource().contains(text);
	}

	public boolean isElementPresent(By by) {
		try {
			driver.findElement(by);
			return true;
		} catch (NoSuchElementException e) {
			return false;
		}
	}

	public boolean isElementPresent(String _cssSelector) {
		try {
			driver.findElement(By.cssSelector(_cssSelector));
			return true;
		} catch (NoSuchElementException e) {
			return false;
		}
	}

	public boolean isElementPresentAndDisplay(By by) {
		try {
			return driver.findElement(by).isDisplayed();
		} catch (NoSuchElementException e) {
			return false;
		}
	}

	public WebElement getWebElement(By by) {
		return driver.findElement(by);
	}

	/**
	 * Method to find the element for provided time span
	 * 
	 * @param driver
	 * @param by
	 * @param timeoutInSeconds
	 * @return
	 */
	public WebElement findElement(WebDriver driver, By by, int timeoutInSeconds) {
		WebDriverWait wait = new WebDriverWait(driver, timeoutInSeconds);
		/*
		 * throws a timeout exception if element not present after waiting
		 * <timeoutInSeconds> seconds
		 */
		wait.until(ExpectedConditions.presenceOfElementLocated(by));
		return driver.findElement(by);
	}

	/**
	 * Method to verify element is present
	 * 
	 * @param driver
	 * @param by
	 * @param timeoutInSeconds
	 * @return
	 */
	public boolean isElementPresent(WebDriver driver, By by,
			int timeoutInSeconds) {
		try {
			for (int i = 0; i < timeoutInSeconds;) {
				if (findElement(driver, by, timeoutInSeconds) != null)
					return true;
				else
					i++;
			}
		} catch (NoSuchElementException e) {
			return false;
		} catch (TimeoutException e) {
			return false;
		} catch (Exception e) {
			return false;
		}
		return false;
	}

	/**
	 * Method to switch the window focus on new window
	 * 
	 * @param driver
	 * @return
	 */
	public void switchWindow() {
		parentWindow = driver.getWindowHandle();
		Set<String> handles = driver.getWindowHandles();
		for (String windowHandle : handles) {
			if (!windowHandle.equals(parentWindow)) {
				driver.switchTo().window(windowHandle);
			}
		}
	}

	/**
	 * Method to accept the alert generated
	 * 
	 * @param driver
	 * @return
	 */
	public String acceptAlert() {
		Alert alert = driver.switchTo().alert();
		String alertMessage = alert.getText();
		alert.accept();
		return alertMessage;
	}

	/**
	 * Method to cancel the alert
	 * 
	 * @param driver
	 * @return
	 */
	public String cancelAlert() {
		Alert alert = driver.switchTo().alert();
		String alertMessage = alert.getText();
		alert.dismiss();
		return alertMessage;
	}
}
