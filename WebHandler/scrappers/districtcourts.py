from sys import exc_info
import time
import logging
import os
import shutil
from datetime import date
import traceback
from sentry_sdk import capture_exception


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
    get_table_data_as_list
)
from ..utils.ocr import (
    get_text_from_captcha,
    get_captcha
)

if os.environ.get("APP_ENV") == "local":
    load_dotenv()


def get_districtcourt_no_of_cases(props):
    is_failed_with_captach = True
    driver = props["driver"]
    logger = props["logger"]
    advoc_name = props["advocate_name"]
    district_id = props["district_id"]
    state_id = props["state_id"]
    court_complex_id = props["court_complex_id"]
    name = "".join(ch for ch in advoc_name if ch.isalnum())

    if props.get("iteration"):
        img_path = f'dc-{name}-img-{props["iteration"]}.png'
    else:
        img_path = f"{name}-image.png"

    counter_retry = 0
    url_trail = 1
    while url_trail < 11:
        try:
            driver.get('https://services.ecourts.gov.in/ecourtindia_v6/#')
            break
        except Exception as e_exception:
            if url_trail >= 10:
                capture_exception(e_exception)
                return {'status': False, 'data': {}, "debugMessage": "Maximun retries reached", "code": 0}
            url_trail = url_trail + 1
    try:
        while is_failed_with_captach:
            counter_retry += 1
            try:
                if "Invalid Request" in selenium_get_text_xpath(driver, "/html/body/div[7]/div/div/div[2]/div/div[1]"):
                    selenium_click_xpath(
                        driver, "/html/body/div[7]/div/div/div[1]/button")

            except Exception as e:
                pass
            selenium_click_id(driver, 'leftPaneMenuCS')
            logger.info("Successfully clicked")

            try:
                selenium_click_xpath(
                    driver, '/html/body/div[9]/div/div/div[1]/button')

                selenium_click_xpath(
                    driver, '/html/body/div[9]/div/div/div[1]/button')

            except:
                pass
            logger.info("ok clicked")
            state_select = Select(
                selenium_get_element_id(driver, 'sess_state_code'))
            state_select.select_by_value(state_id)

            logger.info("Values selected")
            district_select = Select(selenium_get_element_id(
                driver, 'sess_dist_code'))

            district_select.select_by_value("1")

            district_select.select_by_value(district_id)
            logger.info("district code selected")
            court_select = Select(selenium_get_element_id(
                driver, 'court_complex_code'))

            court_select.select_by_value(court_complex_id)
            logger.info("court code selected")
            selenium_click_id(driver, 'advname-tabMenu')
            logger.info("hypelink clicked")

            selenium_send_keys_xpath(
                driver, '//input[@id="advocate_name"]', advoc_name)
            logger.info("names sent")

            captcha_xpath = '//div[@id="div_captcha_adv"]//img[@id="captcha_image"]'
            get_captcha(driver, img_path, captcha_xpath)
            text = get_text_from_captcha(
                driver, img_path, '/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[2]/div/div/div/img', captcha_xpath)

            selenium_click_xpath(
                driver, "//input[@id='adv_captcha_code']")
            selenium_send_keys_xpath(
                driver, '//input[@id="adv_captcha_code"]', text)
            selenium_click_xpath(
                driver, '/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[3]/div[2]/button')
            is_failed_with_captach = False
            try:
                if 'Invalid Captcha' in selenium_get_text_xpath(
                        driver, '/html/body/div[9]/div/div/div[2]/div/div[1]'):
                    selenium_click_xpath(
                        driver, '/html/body/div[9]/div/div/div[1]/button')
                    is_failed_with_captach = True

                if 'Invalid Request' in selenium_get_text_xpath(driver, '//div[@id="msg-danger"]'):
                    selenium_click_xpath(driver, '/html/body/div/div/a')
                    is_failed_with_captach = True
            except:
                pass
        if os.path.isfile(img_path):
            os.remove(img_path)

    except Exception as e_exception:
        capture_exception(e_exception)
        if counter_retry > 10:
            return {'status': False, 'data': {}, "debugMessage": "Maximun retries reached", "code": 2}

    courts_info = []
    for div in driver.find_elements(by="xpath", value='.//div[@id="showList2"]/div')[1:]:
        courts_info.append(selenium_get_text_xpath(div, './/a'))
    number_of_establishments_in_court_complex = selenium_get_text_xpath(
        driver, '//*[@id="showList2"]/div[1]/h3')
    number_of_cases = selenium_get_text_xpath(
        driver, '//*[@id="showList2"]/div[1]/h4')
    data = {
        "number_of_establishments_in_court_complex": number_of_establishments_in_court_complex,
        "number_of_cases": number_of_cases,
        "courts_info": courts_info
    }
    logger.info(data)
    return data


def get_districtcourt_cases_by_name(props):
    driver = props["driver"]
    logger = props["logger"]
    start = props["start"]
    stop = props["stop"]

    # case details
    table_element = selenium_get_element_id(driver, 'dispTable')

    driver.execute_script(
        "arguments[0].scrollIntoView();", table_element)

    # list of case
    case_list = get_table_data_as_list(
        driver, '/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[4]/table')
    data = {
        "case_list": case_list,
        'case_details': [],
    }

    # list of case details
    case_details_list = []
    case_sl_no = 1
    cases = driver.find_elements(
        by="xpath", value='/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[4]/table/tbody/tr')[1:]
    if start is not None and stop is not None:
        cases = cases[start:stop]
        case_sl_no = start + 1
    for case in cases:
        logger.info(f'case no: {case_sl_no}')
        link = selenium_get_element_xpath(case, ".//td[5]/a")
        case_name = selenium_get_text_xpath(case, './/td[2]')
        logger.info(link)
        driver.execute_script(
            "arguments[0].click();", link)
        logger.info(f"{case_sl_no} view clicked")

        # details behind the hyperlink
        # case details
        case_trail = 1
        while case_trail <= 10:
            time.sleep(5)
            registration_number = selenium_get_text_xpath(
                driver, '//table[contains(@class, "case_details_table")]/tbody/tr[3]/td[2]')
            reg_no = "".join(
                ch for ch in registration_number if ch.isalnum())
            case_name = "".join(ch for ch in case_name if ch.isalnum())
            if (case_name == reg_no):
                case_details_element = selenium_get_element_xpath(
                    driver, '//table[contains(@class, "case_details_table")]')
                case_type = selenium_get_text_xpath(
                    case_details_element, './/tr[1]/td[2]')
                filing_number = selenium_get_text_xpath(
                    case_details_element, './/tr[2]/td[2]')
                filing_date = selenium_get_text_xpath(
                    case_details_element, './/tr[2]/td[4]')
                registration_date = selenium_get_text_xpath(
                    case_details_element, './/tr[3]/td[4]')
                cnr_number = selenium_get_text_xpath(
                    case_details_element, './/tr[4]/td[3]')
                case_details = {
                    "case_type": case_type,
                    "filing_number": filing_number,
                    "filing_date": filing_date,
                    "registration_number": registration_number,
                    "registration_date": registration_date,
                    "cnr_number": cnr_number
                }
                driver.implicitly_wait(0)  # decrease wait time
                # case status
                try:
                    if selenium_get_element_xpath(driver, '// table[contains(@class , "case_status_table")]'):
                        case_status_data = get_table_data_as_list(
                            driver, '//table[contains(@class, "case_status_table")]')
                        case_status = {'status': True,
                                       'data': case_status_data}
                        logger.info(f'{case_sl_no} case status')

                except:
                    case_status = {'status': False, 'data': []}
                # paa = petitioned and advocate
                try:
                    if selenium_get_element_xpath(driver, '//table[contains(@class, "Petitioner_Advocate_table")]'):
                        case_paa_data = get_table_data_as_list(
                            driver, '//table[contains(@class, "Petitioner_Advocate_table")]')
                        case_paa = {'status': True, 'data': case_paa_data}
                        logger.info(f'{case_sl_no} paa')

                except:
                    case_paa = {'status': False, 'data': []}
                # raa = respondent and advocate
                try:
                    if selenium_get_element_xpath(driver, '//table[contains(@class, "Respondent_Advocate_table")]'):
                        case_raa_data = get_table_data_as_list(
                            driver, '//table[contains(@class, "Respondent_Advocate_table")]')
                        case_raa = {'status': True, 'data': case_raa_data}
                        logger.info(f'{case_sl_no} raa')

                except:
                    case_raa = {'status': False, 'data': []}
                # acts
                try:
                    if selenium_get_element_xpath(driver, '//table[contains(@class, "acts_table")]'):
                        acts_data = get_table_data_as_list(
                            driver, '//table[contains(@class, "acts_table")]')
                        acts = {'status': True, 'data': acts_data}
                        logger.info(f'{case_sl_no} acts')

                except:
                    acts = {'status': False, 'data': []}

                # FIR Details
                try:
                    if selenium_get_element_xpath(driver, '//table[contains(@class, "FIR_details_table")]e'):
                        fir_details_data = get_table_data_as_list(
                            driver, '//table[contains(@class, "FIR_details_table")]')
                        fir_details = {'status': True,
                                       'data': fir_details_data}
                        logger.info(f'{case_sl_no} FIR details')

                except:
                    fir_details = {'status': False, 'data': []}

                # history
                try:
                    if selenium_get_element_xpath(driver, '//table[contains(@class, "history_table")]'):
                        case_history_data = get_table_data_as_list(
                            driver, '//table[contains(@class, "history_table")]')
                        case_history = {'status': True,
                                        'data': case_history_data}
                        logger.info(f'{case_sl_no} case history')

                except:
                    case_history = {'status': False, 'data': []}

                details = {
                    "case_details": case_details,
                    "status": case_status,
                    "paa": case_paa,
                    "raa": case_raa,
                    "acts": acts,
                    "fir_details": fir_details,
                    "history": case_history,
                }
                case_details_list.append(details)

                break
            else:
                case_trail = case_trail + 1

        logger.info({'case_details': case_details_list, "case_no": case_sl_no})

        back_button_element = selenium_get_element_xpath(
            driver, '//button[@id="main_back_AdvName"]')
        driver.execute_script(
            "arguments[0].click();", back_button_element)

        case_sl_no = case_sl_no + 1

    data = {
        "case_list": case_list,
        "case_details": case_details_list
    }
    logger.info({"status": True, "data": data})
    return {"status": True, "data": data}
