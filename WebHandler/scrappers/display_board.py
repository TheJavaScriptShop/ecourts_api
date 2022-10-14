from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from ..utils.sel import get_display_board_table_data_as_list
import WebHandler.scrappers.constants as constants

import time


def get_display_board(driver, advocateName, highCourtId):
    try:
        url = constants.high_courts_codes[highCourtId]["display_board_url"]
        if not url:
            return {"status": False, "message": "Invalid request"}
        driver.get(url)
        time.sleep(3)
        data = get_display_board_table_data_as_list(
            driver, "//table[@id='table1']")
        return data
    except Exception as e:
        return {"status": False, "message": "Failed to fetch data", "error": str(e)}
