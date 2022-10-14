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
    selenium_click_xpath, selenium_send_keys_xpath,
    selenium_send_keys_id, selenium_get_text_xpath,
    selenium_get_element_xpath, selenium_get_element_id,
    selenium_get_element_class, selenium_find_element_css_selector,
    selenium_click_class, selenium_click_id,
    get_table_data_as_list, get_display_board_table_data_as_list
)

import ipdb
import time


def get_display_board(driver):
    driver.get('https://tshc.gov.in/Hcdbs/displayboard.jsp')
    time.sleep(3)

    data = get_display_board_table_data_as_list(
        driver, "//table[@id='table1']")
    print(data)
    return data
