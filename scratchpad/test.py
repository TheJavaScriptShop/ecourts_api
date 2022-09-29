from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import time
from selenium.webdriver.chrome.options import Options

import base64
import os
import re
import json
import webbrowser
import traceback
import datetime
import cv2
import easyocr
import time
import numpy as np


def selenium_click_xpath(driver, xpath):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).click()


def get_table_data_as_list(driver, xpath):
    rows = []
    table = driver.find_element(by="xpath", value=xpath)
    for row in table.find_elements(by="xpath", value='.//tr'):
        rows.append(
            [td.text for td in row.find_elements(by="xpath", value=".//td")])
    return rows


def main():
    # options = Options()
    # profile = webdriver.FirefoxProfile()
    # options.add_argument("--headless")
    # options.headless = True
    # profile.set_preference(
    #     "browser.helperApps.neverAsk.saveToDisk", "application/octet-stream;application/vnd.ms-excel;text/html;application/pdf")
    # profile.set_preference('pdfjs.disabled', True)
    # profile.set_preference('print.always_print_silent', True)
    # profile.set_preference('print.show_print_progress', False)
    # profile.set_preference('browser.download.show_plugins_in_list', False)
    # profile.set_preference('browser.download.folderList', 2)
    # profile.set_preference('browser.download.dir','/Users/chetnasingh/Desktop/arbito')

    # driver = webdriver.Firefox(service=Service(
    #     GeckoDriverManager().install()), options=options ,firefox_profile=profile)
    # profile.set_preference("print.always_print_silent", True)
    # profile.update_preferences()
    options = Options()
    DRIVER_PATH = '/usr/local/bin/chromedriver'
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--headless")

    prefs = {
        "browser.helperApps.neverAsk.saveToDisk": "application/octet-stream;application/vnd.ms-excel;text/html;application/pdf",
        "pdfjs.disabled": True,
        "print.always_print_silent": True,
        "network.proxy.autoconfig_url.include_path": True,
        "print.show_print_progress": False,
        "browser.download.show_plugins_in_list": False,
        "browser.download.folderList": 2,
        "download.default_directory": '/Users/chetnasingh/Desktop/arbito'
    }

    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(
        executable_path=DRIVER_PATH, chrome_options=options)

    driver.get('https://tshc.gov.in/')
    print("accessed website")
    # Cause list
    selenium_click_xpath(
        driver, '/html/body/header/div[2]/div/div/div/div/div[2]/ul/li[2]/a')
    print("hypelink clicked")
    print("Entered next page")
    # Live Status of Cause list
    selenium_click_xpath(
        driver, '/html/body/form/center/div/div/div[1]/div/input[6]')
    print("live status of cause list button clicked")

    time.sleep(3)
    status_on_leave = 'ON LEAVE'
    for item in get_table_data_as_list(driver, "/html/body/div[2]/form/center/table"):
        print("item==", item)
        try:
            print("item[2]", item[2])
            if item[2] == status_on_leave:
                print("No data for this case")
            else:
                selenium_click_xpath(
                    driver, '/html/body/div[2]/form/center/table/tbody/tr['+item[0]+']/td[5]/a')
                time.sleep(1)
                print("Downloaded data for id", item[0])

        except:
            print("Error for ID ", item)

    print("done")

    driver.close()
    driver.quit()


if __name__ == "__main__":
    try:
        start = datetime.datetime.now()
        main()
    except Exception as e:
        print(traceback.format_exc())
        print(str(e))
    finally:
        end = datetime.datetime.now()
        total = end - start
        print(total.seconds)
