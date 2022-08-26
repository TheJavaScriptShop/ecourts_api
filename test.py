# from selenium import webdriver
# import json
# from selenium.webdriver.firefox.service import Service
# from webdriver_manager.firefox import GeckoDriverManager
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
# import time


# def main():
#   profile = webdriver.FirefoxProfile()
#   profile.set_preference("print.always_print_silent", True)
#   profile.update_preferences()
#   driver = webdriver.Firefox(service=Service(
#           GeckoDriverManager().install()), firefox_profile=profile)
#   #driver= webdriver.Firefox(GeckoDriverManager().install(),firefox_profile=profile)
#   driver.get("http://www.google.com")
#   driver.execute_script('window.print();')
#   driver.quit()
  
  
  
# if __name__ == "__main__":
#         main()



import random
import time
import pyautogui
from selenium import webdriver
import os
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

class printing_browser(object):
    def __init__(self):
        self.profile = webdriver.FirefoxProfile()
        self.profile.set_preference("services.sync.prefs.sync.browser.download.manager.showWhenStarting", False)
        self.profile.set_preference("pdfjs.disabled", True)
        self.profile.set_preference("print.always_print_silent", True)
        self.profile.set_preference("print.show_print_progress", False)
        self.profile.set_preference("browser.download.show_plugins_in_list",False)
        self.driver = webdriver.Firefox(service=Service(
        GeckoDriverManager().install()),firefox_profile=self.profile)
        #self.driver = webdriver.Firefox(executable_path=foxdriver,firefox_profile = self.profile)
        time.sleep(5)

    def get_page_and_print(self, page):
        self.driver.get(page)
        time.sleep(5)
        self.driver.execute_script("window.print();")
        time.sleep(3)

        i=random.randint(0,1000)
        file_name=('cause_list_pdf '+str(i))
        print (file_name)


        pyautogui.typewrite(file_name)
        currentMouseX, currentMouseY = pyautogui.position()
        print(currentMouseX, currentMouseY)
        pyautogui.click(701,660)  

if __name__ == "__main__":
    browser_that_prints = printing_browser()
    browser_that_prints.get_page_and_print('http://www.python.org/')

# time.sleep(3)

# i=random.randint(0,1000)
# file_name=('name_pdf '+str(i))
# print (file_name)


# pyautogui.typewrite(file_name)
# pyautogui.click(512,449)