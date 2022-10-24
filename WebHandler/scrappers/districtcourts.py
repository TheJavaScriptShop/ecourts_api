from sys import exc_info
import time
import logging
import os
import shutil
from datetime import date
import traceback

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


def get_no_of_cases_district_court(props):
    is_failed_with_captach = True
    driver = props["driver"]
    logger = props["logger"]
    advoc_name = props["advocateName"]
    district_id = props["district_id"]
    state_id = props["state_id"]
    court_complex_id = props["court_complex_id"]
    name = "".join(ch for ch in advoc_name if ch.isalnum())

    if props.get("iteration"):
        img_path = f'dc-{name}-img-{props["iteration"]}.png'
    counter_retry = 0
    try:
        while is_failed_with_captach:
            counter_retry += 1
            driver.get('https://services.ecourts.gov.in/ecourtindia_v6/#')
            time.sleep(5)
            selenium_click_id(driver, 'leftPaneMenuCS')
            logger.info("Successfully clicked")
            time.sleep(3)
            selenium_click_xpath(
                driver, '/html/body/div[9]/div/div/div[1]/button')
            time.sleep(3)
            logger.info("ok clicked")
            state_select = Select(
                selenium_get_element_id(driver, 'sess_state_code'))
            state_select.select_by_value(state_id)
            time.sleep(3)
            logger.info("Values selected")
            district_select = Select(selenium_get_element_id(
                driver, 'sess_dist_code'))
            time.sleep(3)
            district_select.select_by_value(district_id)
            logger.info("district code selected")
            court_select = Select(selenium_get_element_id(
                driver, 'court_complex_code'))
            time.sleep(3)
            court_select.select_by_value(court_complex_id)
            logger.info("court code selected")
            selenium_click_id(driver, 'advname-tabMenu')
            logger.info("hypelink clicked")
            time.sleep(10)
            selenium_send_keys_xpath(
                driver, '//input[@id="advocate_name"]', advoc_name)
            logger.info("names sent")
            time.sleep(3)

            captcha_xpath = '//div[@id="div_captcha_adv"]//img[@id="captcha_image"]'

            # captcha_element.screenshot(img_path)
            img_path = f"{name}-image.png"
            get_captcha(driver, img_path, captcha_xpath)
            text = get_text_from_captcha(
                driver, img_path, '/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[2]/div/div/div/img', captcha_xpath)
            time.sleep(3)
            selenium_click_xpath(
                driver, "//input[@id='adv_captcha_code']")
            selenium_send_keys_xpath(
                driver, '//input[@id="adv_captcha_code"]', text)
            selenium_click_xpath(
                driver, '/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[3]/div[2]/button')
            is_failed_with_captach = False
            try:
                failure_text = selenium_get_text_xpath(
                    driver, '/html/body/div[9]/div/div/div[2]/div/div[1]')
                logger.info(failure_text)
                if 'Invalid Captcha' in failure_text:
                    is_failed_with_captach = True
            except Exception as e:
                if counter_retry > 10:
                    return {'status': False, 'data': {}, "debugMessage": "Maximun retries reached", "code": 2}
            if os.path.isfile(img_path):
                os.remove(img_path)
        try:
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
        except Exception as e:
            logger.info(str(e), exc_info=True)
            tb = traceback.print_exc()
            return {'status': False, 'error': str(e), "traceback": tb, "debugMessage": "Unable to scrape data", "code": 3}

    except Exception as e:
        logger.info(str(e), exc_info=True)
        tb = traceback.print_exc()
        return {'status': False, 'error': str(e), "traceback": tb, "debugMessage": "Unable to scrape data", "code": 4}


def get_highcourt_cases_by_name_district_court(driver, logger, start=None, stop=None):

    try:
        # case details
        view_element = selenium_get_element_id(driver, 'dispTable')

        driver.execute_script(
            "arguments[0].scrollIntoView();", view_element)

        time.sleep(3)
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
        case_links = driver.find_elements(
            by="xpath", value='/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[4]/table/tbody/tr/td[5]/a')
        if start is not None and stop is not None:
            case_links = case_links[start:stop]
            case_sl_no = start + 1
        for link in case_links:
            logger.info(link)
            logger.info(f'case no: {case_sl_no}')
            time.sleep(3)
            driver.execute_script(
                "arguments[0].scrollIntoView();", link)
            time.sleep(3)
            view_link = selenium_get_element_class(driver, 'someclass')
            driver.execute_script(
                "arguments[0].click();", view_link)
            logger.info(f"{case_sl_no} view clicked")
            time.sleep(3)
            # details behind the hyperlink
            # case details
            case_details_element = selenium_get_element_xpath(
                driver, '//table[contains(@class, "case_details_table")]')
            case_type = selenium_get_text_xpath(
                case_details_element, './/tr[1]/td[2]')
            filing_number = selenium_get_text_xpath(
                case_details_element, './/tr[2]/td[2]')
            filing_date = selenium_get_text_xpath(
                case_details_element, './/tr[2]/td[4]')
            registration_number = selenium_get_text_xpath(
                case_details_element, './/tr[3]/td[2]')
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
            # case status
            try:
                case_status_data = get_table_data_as_list(
                    driver, '//table[contains(@class, "case_status_table")]')
                case_status = {'status': True, 'data': case_status_data}
                logger.info(f'{case_sl_no} case status')

            except:
                case_status = {'status': False, 'data': []}
            # paa = petitioned and advocate
            try:
                case_paa_data = get_table_data_as_list(
                    driver, '//table[contains(@class, "Petitioner_Advocate_table")]')
                case_paa = {'status': True, 'data': case_paa_data}
                logger.info(f'{case_sl_no} paa')

            except:
                case_paa = {'status': False, 'data': []}
            # raa = respondent and advocate
            try:
                case_raa_data = get_table_data_as_list(
                    driver, '//table[contains(@class, "Respondent_Advocate_table")]')
                case_raa = {'status': True, 'data': case_raa_data}
                logger.info(f'{case_sl_no} raa')

            except:
                case_raa = {'status': False, 'data': []}
            # acts
            try:
                acts_data = get_table_data_as_list(
                    driver, '//table[contains(@class, "acts_table")]')
                acts = {'status': True, 'data': acts_data}
                logger.info(f'{case_sl_no} acts')

            except:
                acts = {'status': False, 'data': []}

            # FIR Details
            try:
                fir_details_data = get_table_data_as_list(
                    driver, '//table[contains(@class, "FIR_details_table")]')
                fir_details = {'status': True, 'data': fir_details_data}
                logger.info(f'{case_sl_no} FIR details')

            except:
                fir_details = {'status': False, 'data': []}

            # history
            try:
                case_history_data = get_table_data_as_list(
                    driver, '//table[contains(@class, "history_table")]')
                case_history = {'status': True, 'data': case_history_data}
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
            logger.info(
                {'case_details': case_details_list, "case_no": case_sl_no})

            back_button_element = selenium_get_element_xpath(
                driver, '//button[@id="main_back_AdvName"]')
            driver.execute_script(
                "arguments[0].click();", back_button_element)
            time.sleep(3)
            view_link = selenium_get_element_id(driver, 'dispTable')

            driver.execute_script(
                "arguments[0].scrollIntoView();", view_link)
            time.sleep(3)

            case_sl_no = case_sl_no + 1

        data = {
            "case_list": case_list,
            "case_details": case_details_list
        }
        logger.info({"status": True, "data": data})
        return {"status": True, "data": data}
    except Exception as e_exception:
        logger.info("entered except")
        logger.info(e_exception, exc_info=True)
        tb = traceback.print_exc()

        return {'status': False, 'data': {}, "debugMessage": str(e_exception), "traceback": tb, "code": 6}
