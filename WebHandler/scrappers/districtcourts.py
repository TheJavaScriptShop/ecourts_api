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
    img_path = f"{name}-image.png"

    if props.get("iteration"):
        img_path = f'{name}-img-{props["iteration"]}.png'
    counter_retry = 0
    try:
        while is_failed_with_captach:
            counter_retry += 1
            driver.get('https://services.ecourts.gov.in/ecourtindia_v6/#')
            selenium_click_id(driver, 'leftPaneMenuCS')
            logger.info("Successfully clicked")
            selenium_click_xpath(
                driver, '/html/body/div[2]/div/div/div[2]/button')
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
            selenium_click_id(driver, 'CSAdvName')
            logger.info("hypelink clicked")
            selenium_send_keys_xpath(
                driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[14]/div[2]/div[2]/input', advoc_name)
            logger.info("names sent")
            time.sleep(3)

            captcha_xpath = '//*[@id="captcha_image"]'
            get_captcha(driver, img_path, captcha_xpath)
            text = get_text_from_captcha(
                driver, img_path, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[1]/div[1]/img', captcha_xpath)
            time.sleep(3)
            selenium_click_xpath(
                driver, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[2]/label")
            selenium_send_keys_xpath(driver, '//*[@id="captcha"]', text)
            selenium_click_xpath(driver, '//*[@class="Gobtn"]')
            is_failed_with_captach = False
            try:
                failure_text = selenium_get_text_xpath(
                    driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[24]/p')
                logger.info(failure_text)
                if 'Invalid Captcha' in failure_text:
                    is_failed_with_captach = True
            except:
                try:
                    failure_text_other_page = selenium_get_text_xpath(
                        driver, '/html/body/div[2]/div/div/div[1]')
                    logger.info(failure_text_other_page)
                    is_failed_with_captach = True
                    selenium_click_xpath(
                        driver, '/html/body/div[2]/div/div/div[2]/button')

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


def get_highcourt_cases_by_name_district_court(driver, logger):
    logger.info("entered")

    try:
        # case details
        logger.info("entered try")
        view_element = selenium_get_element_id(driver, 'dispTable')

        driver.execute_script(
            "arguments[0].scrollIntoView();", view_element)

        time.sleep(3)
        # list of case
        case_list = get_table_data_as_list(
            driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[43]/table')
        data = {
            "case_list": case_list,
            'case_details': [],
        }

        # list of case details
        case_details_list = []
        case_sl_no = 1
        case_links = driver.find_elements(
            by="xpath", value='/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[43]/table/tbody/tr/td[5]/a')

        total_downloaded_files = 0
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
                driver, '//table[@class="case_details_table"]')
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
                    driver, '//*[@class="case_details_table"]/table')
                case_status = {'status': True, 'data': case_status_data}
                logger.info(f'{case_sl_no} case status')

            except:
                case_status = {'status': False, 'data': []}
            # paa = petitioned and advocate
            try:
                case_paa_data = selenium_get_text_xpath(
                    driver, '//span[@class="Petitioner_Advocate_table"]')
                case_paa = {'status': True, 'data': case_paa_data}
                logger.info(f'{case_sl_no} paa')

            except:
                case_paa = {'status': False, 'data': []}
            # raa = respondent and advocate
            try:
                case_raa_data = selenium_get_text_xpath(
                    driver, '//span[@class="Respondent_Advocate_table"]')
                case_raa = {'status': True, 'data': case_raa_data}
                logger.info(f'{case_sl_no} raa')

            except:
                case_raa = {'status': False, 'data': []}
            # acts
            try:
                acts_data = get_table_data_as_list(
                    driver, '//table[@id="act_table"]')
                acts = {'status': True, 'data': acts_data}
                logger.info(f'{case_sl_no} acts')

            except:
                acts = {'status': False, 'data': []}

            # history
            try:
                case_history_data = get_table_data_as_list(
                    driver, '//table[@class="history_table"]')
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
                "history": case_history,
            }
            case_details_list.append(details)
            logger.info(
                {'case_details': case_details_list, "case_no": case_sl_no})
            selenium_click_xpath(driver, "/html/body/div[1]/div/p/a")
            time.sleep(3)
            selenium_click_xpath(
                driver, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[48]/input")
            view_link = selenium_get_element_id(driver, 'dispTable')

            driver.execute_script(
                "arguments[0].scrollIntoView();", view_link)

            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table")))
            case_sl_no = case_sl_no + 1

        data = {
            "case_list": case_list,
            "case_details": case_details_list
        }
        logger.info({"status": True, "data": data,
                    "total_downloaded_files": total_downloaded_files})
        return {"status": True, "data": data}
    except Exception as e_exception:
        logger.info("entered except")
        logger.info(e_exception, exc_info=True)
        tb = traceback.print_exc()

        return {'status': False, 'data': {}, "debugMessage": str(e_exception), "traceback": tb, "code": 6}
