import logging

import azure.functions as func
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import Select
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.storage.blob import BlobServiceClient

from datetime import datetime
import base64
import os
import re
import json
import webbrowser
import traceback
import cv2
import easyocr
import time


# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def remove_noise(image):
    return cv2.medianBlur(image, 5)


def selenium_click_xpath(driver, xpath):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).click()


def selenium_send_keys_xpath(driver, xpath, text):
    WebDriverWait(driver, 40).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).send_keys(text)


def selenium_send_keys_id(driver, id, text):
    WebDriverWait(driver, 40).until(EC.element_to_be_clickable(
        (By.ID, id))).send_keys(text)


def selenium_get_text_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).text


def selenium_get_element_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath)))

def selenium_get_element_id(driver, id):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.ID, id)))

def selenium_get_element_class(driver, classname):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.CLASS_NAME, classname)))

def selenium_find_element_css_selector(driver, selector):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, selector)))

def selenium_click_id(driver, id):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.ID, id))).click()

def selenium_click_class(driver, classname):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.CLASS_NAME, classname))).click()



def get_table_data_as_list(driver, xpath):
    rows = []
    table = driver.find_element(by="xpath", value=xpath)
    for row in table.find_elements(by="xpath", value='.//tr'):
        rows.append(
            [td.text for td in row.find_elements(by="xpath", value=".//td")])
    return rows


def get_text_from_captcha(driver, img_path):
    reader = easyocr.Reader(["en"], gpu=False, model_storage_directory=os.path.join(os.getcwd()), download_enabled=False)
    result = reader.readtext(img_path)
    match = re.search(r'\(?([0-9A-Za-z]+)\)?', result[0][1])
    print(result[0][1])
    img_xpath = '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[1]/div[1]/img'
    if match is None:
        selenium_click_xpath(driver, img_xpath)
        get_captcha(driver)
        return get_text_from_captcha(driver, img_path)
    else:
        print(match.group(1))
        if (len(match.group(1)) != 6):
            selenium_click_xpath(driver, img_xpath)
            get_captcha(driver)
            return get_text_from_captcha(driver, img_path)
    return match.group(1)


def get_captcha(driver):

    img_base64 = driver.execute_script("""
    var ele = arguments[0];
    var cnv = document.createElement('canvas');
    cnv.width = ele.width + 100; cnv.height = ele.height + 100;
    cnv.getContext('2d').drawImage(ele, 0, 0);
    return cnv.toDataURL('image/jpeg').substring(22);
    """, WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="captcha_image"]'))))

    with open(r"image.png", 'wb') as f:
        f.write(base64.b64decode(img_base64))

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info(req)
    logging.info('Python HTTP trigger function processed a request.')
    logging.info(time.ctime())

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--window-size=1700x800");

    driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options=chrome_options)

    advoc_name='V Aneesh'
    # sess_state_code='High Court for State of Telangana'
    # court_complex_code='Principal Bench at Hyderabad'
    is_failed_with_captach = True

    while is_failed_with_captach:
        driver.get('https://hcservices.ecourts.gov.in/hcservices/main.php')
        driver.maximize_window()

        selenium_click_id(driver,'leftPaneMenuCS')
        print("Successfully clicked")
        selenium_click_xpath(driver,'/html/body/div[2]/div/div/div[2]/button')
        print("ok clicked")
        state_code= Select(selenium_get_element_id(driver ,'sess_state_code'))
        state_code.select_by_value('29')
        time.sleep(2)
        print("Values selected")
        court_code=Select(selenium_get_element_id(driver ,'court_complex_code'))
        court_code.select_by_value('1')
        print("court code selected")
        selenium_click_id(driver,'CSAdvName')
        print("hypelink clicked")
        selenium_send_keys_xpath(driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[14]/div[2]/div[2]/input', advoc_name)
        print("names sent")
        time.sleep(3)

        get_captcha(driver)
        text = get_text_from_captcha(driver, r"image.png")
        time.sleep(3)
        selenium_click_xpath(
        driver, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[2]/label")  
        selenium_send_keys_xpath(driver, '//*[@id="captcha"]', text)
        selenium_click_xpath(driver, '//*[@class="Gobtn"]')
        is_failed_with_captach = False
        try:
            failure_text = selenium_get_text_xpath(
                driver, '//*[@id="errSpan1"]')
            print(failure_text)
            if 'THERE IS AN ERROR' in failure_text:
                print("in first")
                is_failed_with_captach = False
        except:
            try:
                failure_text_other_page = selenium_get_text_xpath(
                    driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[1]/ul/li[2]/div/p')
                print(failure_text_other_page)
                if "invalid" in failure_text_other_page.lower():
                    selenium_click_xpath(driver, '//*[@id="bckbtn"]')
                    is_failed_with_captach = True
                else:
                    print("in second")
                    is_failed_with_captach = False
            except:
                pass
    try:
        # case details
        number_of_establishments_in_court_complex= selenium_get_text_xpath(
            driver, '//*[@id="showList2"]/div[1]/h3')
        print(number_of_establishments_in_court_complex)
        number_of_cases= selenium_get_text_xpath(
            driver, '//*[@id="showList2"]/div[1]/h4')
        print(number_of_cases)
        view_element = selenium_get_element_id(driver, 'dispTable')

        driver.execute_script(
        "arguments[0].scrollIntoView();", view_element)

        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table")))
        #list of case
        case_list= get_table_data_as_list(
            driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table')

        selenium_click_class(driver,'someclass')
        print("view clicked")
        #details behind the hyperlink
        # case details
        case_details_title = selenium_get_text_xpath(
            driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[52]/div[2]/div[1]/div/table/tbody/tr[1]/td[2]')
        case_details_registration_no = selenium_get_text_xpath(
            driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[2]/td[2]/label')
        case_details_cnr_no = selenium_get_text_xpath(
            driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[3]/td[2]/strong')
        case_details_filing_date = selenium_get_text_xpath(
            driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[1]/td[4]')
        case_details_registration_date = selenium_get_text_xpath(
            driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[2]/td[4]/label')
        # case status
        case_status = get_table_data_as_list(
            driver, '//*[@id="caseBusinessDiv4"]/table')
        # paa = petitioned and advocate
        case_paa = selenium_get_text_xpath(
            driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/span[1]')
        # raa = respondent and advocate
        case_raa = selenium_get_text_xpath(
            driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/span[2]')
        # acts
        case_acts = get_table_data_as_list(driver, '//*[@id="act_table"]')
        # history
        case_history = get_table_data_as_list(
            driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/table[2]')
        # orders
        case_orders = get_table_data_as_list(
            driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/table[4]')
        # objections
        case_objections = get_table_data_as_list(
            driver, '//*[@id="caseHistoryDiv"]/div[3]/table')
        data = {
            "number_of_establishments_in_court_complex":number_of_establishments_in_court_complex,
            "number_of_cases":number_of_cases,
            "case_list":case_list,
            "case_details":{
            "title": case_details_title,
            "registration_no": case_details_registration_no,
            "cnr_no": case_details_cnr_no,
            "filing_date": case_details_filing_date,
            "registration_date": case_details_registration_date,
            "status": case_status,
            "paa": case_paa,
            "raa": case_raa,
            "acts": case_acts,
            "history": case_history,
            "orders": case_orders,
            "objections": case_objections,
            },
        }
        print(data)
    except Exception as e:
        logging.info(e)
        return func.HttpResponse(
            body=json.dumps({"error": "error in getting data"}),
            mimetype="application/json",
            status_code=200
        )
    return func.HttpResponse(
        body=json.dumps(data),
        mimetype="application/json",
        status_code=200
    )
