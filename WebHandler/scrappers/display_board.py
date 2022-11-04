from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from sentry_sdk import capture_exception

from ..utils.sel import get_display_board_table_data_as_list, selenium_get_text_xpath
import WebHandler.scrappers.constants as constants

import time
from datetime import datetime


def get_display_board(driver, highCourtId):
    try:
        url = constants.high_courts_codes[highCourtId]["display_board_url"]
        if not url:
            return {"status": False, "message": "Invalid request"}
        driver.get(url)
        try:
            data = get_display_board_table_data_as_list(
                driver, "//table[@id='table1']")
        except Exception as e:
            capture_exception(e)
            if "SESSION ENDED" in selenium_get_text_xpath(driver, '/html/body/div[2]/form/center/table/tbody/tr/td/h1/font'):
                return {"message": "SESSION ENDED"}
        return data
    except Exception as e:
        capture_exception(e)
        return {"message": "No Data Found", "error": str(e), "datetime": datetime.now().isoformat()}
