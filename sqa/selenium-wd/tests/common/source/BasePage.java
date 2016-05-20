/**
 * 
 */
package common.source;

import org.openqa.selenium.By;
import org.openqa.selenium.NoSuchElementException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

/**
 * @author zlu
 * 
 * Add more general code later for pages
 * 
 */
public class BasePage {

	protected String strBaseURL;
	protected String strPageURL;
	protected WebDriver driver;
	protected String pageTitle;

	public BasePage (WebDriver driver, String pageTitle) {
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
}
