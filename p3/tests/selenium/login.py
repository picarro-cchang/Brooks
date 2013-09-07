"""
Copyright 2013, Picarro Inc.
"""


from selenium import webdriver


driver = webdriver.Firefox()
driver.get('https://p3.picarro.com/stage')

user_input = driver.find_elements_by_xpath('//html/body/div[2]/div/div[2]/div[2]/form/table/tbody/tr[3]/td/fieldset/div/div[1]/input')[0]
user_input.send_keys('test@TEST')

driver.get_screenshot_as_file('test.png')

driver.quit()
