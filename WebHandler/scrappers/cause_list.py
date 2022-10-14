from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from ..utils.sel import (
    selenium_click_xpath,
    get_display_board_table_data_as_list, selenium_send_keys_id
)
import WebHandler.scrappers.constants as constants

import time


def get_cause_list_data(driver, advocateName, highCourtId):
    try:
        url = constants.high_courts_codes[highCourtId]["causelist_url"]
        if not url:
            return {"status": False, "message": "invalid request"}
        driver.get(url)
        time.sleep(3)
        selenium_click_xpath(driver, "//input[@value='DAILY LIST']")
        time.sleep(3)
        selenium_click_xpath(driver, "//input[@value='ADVOCATE WISE']")
        time.sleep(3)
        selenium_send_keys_id(driver, "svalue", advocateName)
        selenium_click_xpath(driver, '//div[@id="advsearch"]/input[2]')
        time.sleep(3)
        data = get_display_board_table_data_as_list(driver, "//table")
        return data
    except Exception as e:
        return {"message": 'No Data Found'}
