import time
import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

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


def get_highcourt_cases_by_name(driver, advoc_name, state_code, bench_code):
    is_failed_with_captach = True

    while is_failed_with_captach:
        driver.get('https://hcservices.ecourts.gov.in/hcservices/main.php')
        driver.maximize_window()

        selenium_click_id(driver, 'leftPaneMenuCS')
        logging.info("Successfully clicked")
        selenium_click_xpath(driver, '/html/body/div[2]/div/div/div[2]/button')
        logging.info("ok clicked")
        state_code = Select(selenium_get_element_id(driver, 'sess_state_code'))
        state_code.select_by_value(state_code)
        time.sleep(2)
        logging.info("Values selected")
        court_code = Select(selenium_get_element_id(
            driver, 'court_complex_code'))
        court_code.select_by_value(bench_code)
        logging.info("court code selected")
        selenium_click_id(driver, 'CSAdvName')
        logging.info("hypelink clicked")
        selenium_send_keys_xpath(
            driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[14]/div[2]/div[2]/input', advoc_name)
        logging.info("names sent")
        time.sleep(3)

        img_path = r"image.png"
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
                driver, '//*[@id="errSpan1"]')
            logging.info(failure_text)
            if 'THERE IS AN ERROR' in failure_text:
                is_failed_with_captach = False
        except:
            try:
                failure_text_other_page = selenium_get_text_xpath(
                    driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[26]/p')
                logging.info(failure_text_other_page)
                if "invalid" in failure_text_other_page.lower():
                    is_failed_with_captach = True
                else:
                    is_failed_with_captach = False
            except:
                pass
    try:
        # case details
        number_of_establishments_in_court_complex = selenium_get_text_xpath(
            driver, '//*[@id="showList2"]/div[1]/h3')
        logging.info(number_of_establishments_in_court_complex)
        number_of_cases = selenium_get_text_xpath(
            driver, '//*[@id="showList2"]/div[1]/h4')
        logging.info(number_of_cases)
        view_element = selenium_get_element_id(driver, 'dispTable')

        driver.execute_script(
            "arguments[0].scrollIntoView();", view_element)

        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table")))
        # list of case
        case_list = get_table_data_as_list(
            driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table')
        # list of case details
        case_details = []
        for link in driver.find_elements(by="xpath", value='/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table/tbody/tr/td[5]'):
            logging.info(link)
            time.sleep(3)
            driver.execute_script(
                "arguments[0].scrollIntoView();", link)
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'someclass')))
            selenium_click_class(link, 'someclass')
            logging.info("view clicked")
            time.sleep(3)
            # details behind the hyperlink
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
            try:
                case_status_data = get_table_data_as_list(
                    driver, '//*[@id="caseBusinessDiv4"]/table')
                case_status = {'status': True, 'data': case_status_data}
            except:
                case_status = {'status': False, 'data': {}}
            # paa = petitioned and advocate
            try:
                case_paa_data = selenium_get_text_xpath(
                    driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/span[1]')
                case_paa = {'status': True, 'data': case_paa_data}
            except:
                case_paa = {'status': False, 'data': {}}
            # raa = respondent and advocate
            try:
                case_raa_data = selenium_get_text_xpath(
                    driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/span[2]')
                case_raa = {'status': True, 'data': case_raa_data}
            except:
                case_raa = {'status': False, 'data': {}}
            # acts
            try:
                case_acts_data = get_table_data_as_list(
                    driver, '//*[@id="act_table"]')
                case_acts = {'status': True, 'data': case_acts_data}
            except:
                case_acts = {'status': False, 'data': {}}
            # history
            try:
                case_history_data = get_table_data_as_list(
                    driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/table[2]')
                case_history = {'status': True, 'data': case_history_data}
            except:
                case_history = {'status': False, 'data': {}}
            # orders
            try:
                case_orders_data = get_table_data_as_list(
                    driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/table[4]')
                case_orders = {'status': True, 'data': case_orders_data}
            except:
                case_orders = {'status': False, 'data': {}}

            # objections
            try:
                case_objections_data = get_table_data_as_list(
                    driver, '//*[@id="caseHistoryDiv"]/div[3]/table')
                case_objections = {'status': True,
                                   'data': case_objections_data}
            except:
                case_objections = {'status': False, 'data': {}}

            details = {
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
            }
            case_details.append(details)
            logging.info(case_details)
            selenium_click_xpath(driver, "/html/body/div[1]/div/p/a")
            time.sleep(3)
            selenium_click_xpath(
                driver, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[48]/input")
            view_link = selenium_get_element_id(driver, 'dispTable')

            driver.execute_script(
                "arguments[0].scrollIntoView();", view_link)

            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table")))

        data = {
            "number_of_establishments_in_court_complex": number_of_establishments_in_court_complex,
            "number_of_cases": number_of_cases,
            "case_list": case_list,
            "case_details": case_details
        }
        logging.info({"status": True, "data": data})
        return data
    except Exception as e_exception:
        logging.error(e_exception)
        return {'status': False, 'data': {}, "debugMessage": str(e_exception)}
