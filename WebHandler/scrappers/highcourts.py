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
from sentry_sdk import capture_exception

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


def get_highcourt_no_of_cases(props):
    is_failed_with_captach = True
    fetched_data = False
    driver = props["driver"]
    logger = props["logger"]
    advoc_name = props["advocate_name"]
    state_code = props["highcourt_id"]
    bench_code = props["bench_code"]
    name = "".join(ch for ch in advoc_name if ch.isalnum())

    if props.get("iteration"):
        img_path = f'dc-{name}-img-{props["iteration"]}.png'
    else:
        img_path = f"{name}-image.png"
    counter_retry = 0
    try:
        while is_failed_with_captach:
            counter_retry += 1
            driver.get('https://hcservices.ecourts.gov.in/hcservices/main.php')
            selenium_click_id(driver, 'leftPaneMenuCS')
            logger.info("Successfully clicked case status")
            try:
                selenium_click_xpath(
                    driver, '/html/body/div[2]/div/div/div[2]/button')

                logger.info("ok clicked")
            except:
                pass
            state_select = Select(
                driver.find_element(By.ID, 'sess_state_code'))
            state_select.select_by_value(state_code)

            logger.info("Values selected")
            court_select = Select(driver.find_element(
                By.ID, 'court_complex_code'))

            court_select.select_by_value(bench_code)
            logger.info("court code selected")
            selenium_click_id(driver, 'CSAdvName')
            logger.info("hypelink clicked")
            selenium_send_keys_xpath(
                driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[14]/div[2]/div[2]/input', advoc_name)
            logger.info("names sent")
            time.sleep(int(os.environ.get('WAIT_TIME')))
            captcha_xpath = '//*[@id="captcha_image"]'
            get_captcha(driver, img_path, captcha_xpath)
            text = get_text_from_captcha(
                driver, img_path, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[1]/div[1]/img', captcha_xpath)

            selenium_click_xpath(
                driver, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[2]/label")
            selenium_send_keys_xpath(driver, '//*[@id="captcha"]', text)
            selenium_click_xpath(driver, '//*[@class="Gobtn"]')
            is_failed_with_captach = False
            try:
                failure_text = selenium_get_text_xpath(
                    driver, '//*[@id="errSpan1"]')
                logger.info(failure_text)
                if 'THERE IS AN ERROR' in failure_text:
                    is_failed_with_captach = True
            except Exception as e_exception:
                try:
                    failure_text_other_page = selenium_get_text_xpath(
                        driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[26]/p')
                    logger.info(failure_text_other_page)
                    is_failed_with_captach = True

                    if 'Record Not Found' in failure_text_other_page:
                        data = {
                            "number_of_establishments_in_court_complex": 0,
                            "number_of_cases": 0,
                            "case_list": [],
                            'case_details': [],
                        }
                        fetched_data = True
                        is_failed_with_captach = False
                        capture_exception(e_exception)
                        return {'status': False, 'data': {}, "debugMessage": "No data found", "code": 1}

                except Exception as e:
                    pass
        if os.path.isfile(img_path):
            os.remove(img_path)
    except Exception as e_exception:
        is_failed_with_captach = True
        capture_exception(e_exception)
        if counter_retry > 10:
            is_failed_with_captach = False
            return {'status': False, 'data': {}, "debugMessage": "Maximun retries reached", "code": 2}

    if not fetched_data:
        number_of_establishments_in_court_complex = selenium_get_text_xpath(
            driver, '//*[@id="showList2"]/div[1]/h3')
        logger.info(number_of_establishments_in_court_complex)
        number_of_cases = selenium_get_text_xpath(
            driver, '//*[@id="showList2"]/div[1]/h4')
        logger.info(number_of_cases)
        data = {
            "number_of_establishments_in_court_complex": number_of_establishments_in_court_complex,
            "number_of_cases": number_of_cases,
        }
        return data


def get_highcourt_cases_by_name(props):
    driver = props["driver"]
    advoc_name = props["advocate_name"]
    __location__ = props["__location__"]
    start = props["start"]
    stop = props["stop"]
    logger = props["logger"]

    def wait_for_download_and_rename(blob_path):
        try:
            blob_service_client = BlobServiceClient.from_connection_string(
                os.environ.get('BLOB_STORAGE_CONTAINER'))
            blob_client = blob_service_client.get_blob_client(
                container="ecourtsapiservicebucketdev", blob=blob_path)
            while True:
                if os.path.isfile(f"{__location__}/display_pdf.pdf"):
                    with open(os.path.join(__location__, "display_pdf.pdf"), "rb") as data:
                        blob_client.upload_blob(data, overwrite=True)
                    break

            if os.path.isfile(f"{__location__}/display_pdf.pdf"):
                os.remove(f"{__location__}/display_pdf.pdf")
        except Exception as e:
            logger.error(str(e), exc_info=True)
            tb = traceback.print_exc()
            capture_exception(e)
            return {'status': False, 'error': str(e), "traceback": tb, "debugMessage": "Failed to upload file to blob", "code": 5}

    # case details

    table_element = selenium_get_element_id(driver, 'dispTable')

    driver.execute_script(
        "arguments[0].scrollIntoView();", table_element)

    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table")))
    # list of case
    case_list = get_table_data_as_list(
        driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table')
    data = {
        "case_list": case_list,
        'case_details': [],
    }

    # list of case details
    case_details = []
    case_sl_no = 1
    case_links = driver.find_elements(
        by="xpath", value='/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table/tbody/tr/td[5]/a')
    if start is not None and stop is not None:
        case_links = case_links[start:stop]
        case_sl_no = start + 1
    total_downloaded_files = 0
    for link in case_links:
        logger.info(link)
        logger.info(f'case no: {case_sl_no}')

        driver.execute_script(
            "arguments[0].click();", link)
        logger.info(f"{case_sl_no} view clicked")
        time.sleep(5)
        # details behind the hyperlink
        # case details
        case_details_title = WebDriverWait(driver, 30).until(EC.visibility_of_element_located(
            (By.XPATH, '//table[contains(@class, "case_details_table")]/tbody/tr[1]/td[2]'))).text
        case_details_registration_no = selenium_get_text_xpath(
            driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[2]/td[2]/label')
        case_details_cnr_no = selenium_get_text_xpath(
            driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[3]/td[2]/strong')
        case_details_filing_date = selenium_get_text_xpath(
            driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[1]/td[4]')
        case_details_registration_date = selenium_get_text_xpath(
            driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[2]/td[4]/label')

        driver.implicitly_wait(0)  # decrease wait time
        # case status
        try:
            if selenium_get_element_xpath(driver, '//*[@id="caseBusinessDiv4"]/table'):
                case_status_data = get_table_data_as_list(
                    driver, '//*[@id="caseBusinessDiv4"]/table')
                case_status = {'status': True, 'data': case_status_data}
                logger.info(f'{case_sl_no} case status')

        except:
            case_status = {'status': False, 'data': []}
        # paa = petitioned and advocate
        try:
            if selenium_get_element_xpath(driver, '//span[@class="Petitioner_Advocate_table"]'):
                case_paa_data = selenium_get_text_xpath(
                    driver, '//span[@class="Petitioner_Advocate_table"]')
                case_paa = {'status': True, 'data': case_paa_data}
                logger.info(f'{case_sl_no} paa')

        except:
            case_paa = {'status': False, 'data': []}
        # raa = respondent and advocate
        try:
            if selenium_get_element_xpath(driver, '//span[@class="Respondent_Advocate_table"]'):
                case_raa_data = selenium_get_text_xpath(
                    driver, '//span[@class="Respondent_Advocate_table"]')
                case_raa = {'status': True, 'data': case_raa_data}
                logger.info(f'{case_sl_no} raa')

        except:
            case_raa = {'status': False, 'data': []}
        # acts
        try:
            if selenium_get_element_xpath(driver, '//table[@id="act_table"]'):
                acts_data = get_table_data_as_list(
                    driver, '//table[@id="act_table"]')
                acts = {'status': True, 'data': acts_data}
                logger.info(f'{case_sl_no} acts')

        except:
            acts = {'status': False, 'data': []}

        # Category Details
        try:
            if selenium_get_element_xpath(driver, '//table[@id="subject_table"]'):
                cd_data = get_table_data_as_list(
                    driver, '//table[@id="subject_table"]')
                cd = {'status': True, 'data': cd_data}
                logger.info(f'{case_sl_no} category details')

        except:
            cd = {'status': False, 'data': []}

        # Subordinate Court Information
        try:
            if selenium_get_element_xpath(driver, '//span[@class="Lower_court_table"]'):
                sci_element = selenium_get_element_xpath(
                    driver, '//span[@class="Lower_court_table"]')
                court_number_and_name = selenium_get_text_xpath(
                    sci_element, ".//label[1]")
                case_number_and_year = selenium_get_text_xpath(
                    sci_element, ".//label[2]")
                case_decision_date = selenium_get_text_xpath(
                    sci_element, ".//label[3]")
                sci_data = {
                    'court_number_and_name': court_number_and_name,
                    'case_number_and_year': case_number_and_year,
                    'case_decision_date': case_decision_date
                }
                sci = {'status': True, "data": sci_data}
                logger.info(f'{case_sl_no} Subordinate Court Information')
        except:
            sci = {'status': False, "data": []}

        # IA Details
        try:
            if selenium_get_element_xpath(driver, '//table[@class="IAheading"]'):
                iad_data = get_table_data_as_list(
                    driver, '//table[@class="IAheading"]')
                iad = {'status': True, 'data': iad_data}
                logger.info(f'{case_sl_no} IA details')

        except:
            iad = {'status': False, 'data': []}
        # history
        try:
            if selenium_get_element_xpath(driver, '//table[@class="history_table"]'):
                case_history_data = get_table_data_as_list(
                    driver, '//table[@class="history_table"]')
                case_history = {'status': True, 'data': case_history_data}
                logger.info(f'{case_sl_no} case history')

        except:
            case_history = {'status': False, 'data': []}
        # orders
        try:
            if selenium_get_element_xpath(driver, '//table[@class="order_table"]'):
                case_orders_data = get_table_data_as_list(
                    driver, '//table[@class="order_table"]')
                no_of_orders = len(case_orders_data) - 1
                order_no = 1
                for n in range(0, no_of_orders):
                    pdf_xpath = f'//table[@class="order_table"]/tbody/tr[{(n+2)}]/td[5]/a'
                    pdf_element = selenium_get_element_xpath(
                        driver, pdf_xpath)
                    driver.execute_script(
                        "arguments[0].click();", pdf_element)
                    logger.info(f'{case_sl_no} clicked')
                    case_no = case_details_title.replace("/", "-")
                    try:
                        blob_path_container = f"{advoc_name}/{case_no}/{date.today().month}/{date.today().day}/orders/{order_no}.pdf"
                        wait_for_download_and_rename(
                            blob_path_container)
                        order = case_orders_data[order_no]
                        order["file"] = blob_path_container
                        case_orders_data[order_no] = order
                        logger.info(f'downloaded {order_no}')
                        order_no = order_no+1
                    except Exception as e:
                        traceback.print_exc()
                        logger.info({'err': str(e), 'case_no': case_sl_no})
                case_orders = {'status': True, 'data': case_orders_data,
                               'number_of_downloaded_files': order_no - 1}
                total_downloaded_files = total_downloaded_files + 1
                logger.info("case orders")
        except:
            traceback.print_exc()
            case_orders = {'status': False, 'data': [],
                           'number_of_downloaded_files': 0}

        #  Document details
        try:
            if selenium_get_element_xpath(driver, '//table[@class="transfer_table"]'):
                dd_data = get_table_data_as_list(
                    driver, '//table[@class="transfer_table"]')
                dd = {'status': True, 'data': dd_data}
                logger.info(f'{case_sl_no} dd')

        except:
            dd = {'status': False, 'data': []}

        # objections
        try:
            if selenium_get_element_xpath(driver, '//table[@class="obj_table"]'):
                case_objections_data = get_table_data_as_list(
                    driver, '//table[@class="obj_table"]')
                case_objections = {'status': True,
                                   'data': case_objections_data}
                logger.info(f'{case_sl_no} case objections')

        except:
            case_objections = {'status': False, 'data': []}

        details = {
            "title": case_details_title,
            "registration_no": case_details_registration_no,
            "cnr_no": case_details_cnr_no,
            "filing_date": case_details_filing_date,
            "registration_date": case_details_registration_date,
            "status": case_status,
            "paa": case_paa,
            "raa": case_raa,
            "acts": acts,
            "cd": cd,
            "iad": iad,
            "sci": sci,
            "history": case_history,
            "orders": case_orders,
            "dd": dd,
            "objections": case_objections,
        }
        case_details.append(details)
        driver.implicitly_wait(30)  # set default wait time
        logger.info({'case_details': case_details, "case_no": case_sl_no})
        back_button = selenium_get_element_xpath(
            driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[48]/input')
        driver.execute_script(
            "arguments[0].click();", back_button)
        case_sl_no = case_sl_no + 1

    data = {
        "case_list": case_list,
        "case_details": case_details
    }
    logger.info({"status": True, "data": data})
    return {"status": True, "data": data}
