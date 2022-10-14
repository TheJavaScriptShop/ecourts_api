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
    # WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
    # (By.XPATH, "/html/body/div/div[1]/center/div/article/div/div/div[1]/ul/li[1]/a")))
    # ipdb.set_trace()
    time.sleep(3)

    data = get_display_board_table_data_as_list(
        driver, "/html/body/div/form/center/div[1]/table")
    print(data)
    return data
