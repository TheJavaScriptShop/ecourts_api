from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

TIMEOUT = 30


def selenium_click_xpath(driver, xpath):
    WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).click()


def selenium_send_keys_xpath(driver, xpath, text):
    WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).send_keys(text)


def selenium_send_keys_id(driver, el_id, text):
    WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.ID, el_id))).send_keys(text)


def selenium_get_text_xpath(driver, xpath):
    return WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).text


def selenium_get_element_xpath(driver, xpath):
    return WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.XPATH, xpath)))


def selenium_get_element_id(driver, el_id):
    return WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.ID, el_id)))


def selenium_get_element_class(driver, classname):
    WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.CLASS_NAME, classname)))


def selenium_find_element_css_selector(driver, selector):
    return WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, selector)))


def selenium_click_id(driver, el_id):
    WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.ID, el_id))).click()


def selenium_click_class(driver, classname):
    WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable(
        (By.CLASS_NAME, classname))).click()


def get_table_data_as_list(driver, xpath):
    rows = []
    table = driver.find_element(by="xpath", value=xpath)
    for row in table.find_elements(by="xpath", value='.//tr'):
        if row.find_elements(by="xpath", value=".//td"):
            rows.append(
                {"data": [td.text for td in row.find_elements(by="xpath", value=".//td")]})
        if row.find_elements(by="xpath", value=".//th"):
            rows.append(
                {"data": [th.text for th in row.find_elements(by="xpath", value=".//th")]})

    return rows


def get_display_board_table_data_as_list(driver, xpath):
    rows = []
    table = driver.find_element(by="xpath", value=xpath)
    for row in table.find_elements(by="xpath", value='.//tr'):
        if row.find_elements(by="xpath", value=".//td"):
            rows.append(
                [td.text for td in row.find_elements(by="xpath", value=".//td")])
        if row.find_elements(by="xpath", value=".//th"):
            rows.append(
                [th.text for th in row.find_elements(by="xpath", value=".//th")])

    return rows


def get_cause_list_table_data_as_list(driver, xpath):
    rows = []
    table = driver.find_element(by="xpath", value=xpath)
    for tbody in table.find_elements(by="xpath", value='.//tbody'):
        if tbody.find_elements(by="xpath", value=".//td"):
            rows.append(
                [td.text for td in tbody.find_elements(by="xpath", value=".//td")])
        if tbody.find_elements(by="xpath", value=".//th"):
            for row in table.find_elements(by="xpath", value='.//tr'):
                if len(row.find_elements(by="xpath", value=".//th")) > 1:
                    rows.append(
                        [th.text for th in row.find_elements(by="xpath", value=".//th")])
                else:
                    for th in row.find_elements(by="xpath", value=".//th"):
                        rows.append(th.text)

    return rows
