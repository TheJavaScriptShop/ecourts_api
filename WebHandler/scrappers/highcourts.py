from sys import exc_info
import time
import logging
import os
import shutil
from datetime import date

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


def get_no_of_cases(props):
    is_failed_with_captach = True
    fetched_data = False
    driver = props["driver"]
    logger = props["logger"]
    advoc_name = props["advocateName"]
    state_code = props["highCourtId"]
    bench_code = props["benchCode"]
    location = props["location"]
    name = "".join(ch for ch in advoc_name if ch.isalnum())
    img_path = f"local/images/{name}-image.png"

    if props.get("iteration"):
        img_path = f'local/images/{name}-img-{props["iteration"]}.png'
    counter_retry = 0
    try:
        while is_failed_with_captach:
            counter_retry += 1
            driver.get('https://hcservices.ecourts.gov.in/hcservices/main.php')
            selenium_click_id(driver, 'leftPaneMenuCS')
            logger.info("Successfully clicked")
            selenium_click_xpath(
                driver, '/html/body/div[2]/div/div/div[2]/button')
            time.sleep(3)
            logger.info("ok clicked")
            state_select = Select(
                selenium_get_element_id(driver, 'sess_state_code'))
            state_select.select_by_value(state_code)
            time.sleep(3)
            logger.info("Values selected")
            court_select = Select(selenium_get_element_id(
                driver, 'court_complex_code'))
            time.sleep(3)
            court_select.select_by_value(bench_code)
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
                    driver, '//*[@id="errSpan1"]')
                logger.info(failure_text)
                if 'THERE IS AN ERROR' in failure_text:
                    is_failed_with_captach = False
            except:
                try:
                    failure_text_other_page = selenium_get_text_xpath(
                        driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[26]/p')
                    logger.info(failure_text_other_page)
                    if 'Record Not Found' in failure_text_other_page:
                        data = {
                            "number_of_establishments_in_court_complex": 0,
                            "number_of_cases": 0,
                            "case_list": [],
                            'case_details': [],
                        }
                        fetched_data = True
                        return {'status': False, 'data': {}, "debugMessage": "No data found"}
                    if "invalid" in failure_text_other_page.lower():
                        is_failed_with_captach = True
                    else:
                        is_failed_with_captach = False
                except Exception as e:
                    if counter_retry > 10:
                        return {'status': False, 'data': {}, "debugMessage": "Maximun retries reached"}
        if not fetched_data:
            try:
                number_of_establishments_in_court_complex = selenium_get_text_xpath(
                    driver, '//*[@id="showList2"]/div[1]/h3')
                logger.info(number_of_establishments_in_court_complex)
                number_of_cases = selenium_get_text_xpath(
                    driver, '//*[@id="showList2"]/div[1]/h4')
                logger.info(number_of_cases)
                data = {
                    "number_of_establishments_in_court_complex": number_of_establishments_in_court_complex,
                    "number_of_cases": number_of_cases,
                    "driver": driver
                }
                return data
            except Exception as e:
                logger.info(str(e))
    except Exception as e:
        logger.info(str(e), exc_info=True)


def get_highcourt_cases_by_name(driver, advoc_name, __location__, start=None, stop=None, logger=None):
    def wait_for_download_and_rename(blob_path):
        try:
            # time.sleep(5)
            blob_service_client = BlobServiceClient.from_connection_string(
                os.environ.get('BLOB_STORAGE_CONTAINER'))
            blob_client = blob_service_client.get_blob_client(
                container="ecourtsapiservicebucketdev", blob=blob_path)
            while True:
                if os.path.isfile(f"{__location__}/display_pdf.pdf"):
                    with open(os.path.join(__location__, "display_pdf.pdf"), "rb") as data:
                        blob_client.upload_blob(data, overwrite=True)
                    break

            # time.sleep(3)
            if os.path.isfile(f"{__location__}/display_pdf.pdf"):
                os.remove(f"{__location__}/display_pdf.pdf")
        except Exception as e:
            logger.error(str(e), exc_info=True)

    try:
        # case details

        view_element = selenium_get_element_id(driver, 'dispTable')

        driver.execute_script(
            "arguments[0].scrollIntoView();", view_element)

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
            by="xpath", value='/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table/tbody/tr/td[5]')
        if start is not None and stop is not None:
            case_links = case_links[start:stop]
            case_sl_no = start + 1
        total_downloaded_files = 0
        for link in case_links:
            logger.info(link)
            logger.info(f'case no: {case_sl_no}')
            time.sleep(3)
            driver.execute_script(
                "arguments[0].scrollIntoView();", link)
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'someclass')))
            selenium_click_class(link, 'someclass')
            logger.info(f"{case_sl_no} view clicked")
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

            # Category Details
            try:
                cd_data = get_table_data_as_list(
                    driver, '//table[@id="subject_table"]')
                cd = {'status': True, 'data': cd_data}
                logger.info(f'{case_sl_no} category details')

            except:
                cd = {'status': False, 'data': []}

            # Subordinate Court Information
            try:
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

            except:
                sci = {'status': False, "data": []}

            # IA Details
            try:
                iad_data = get_table_data_as_list(
                    driver, '//table[@class="IAheading"]')
                iad = {'status': True, 'data': iad_data}
                logger.info(f'{case_sl_no} IA details')

            except:
                iad = {'status': False, 'data': []}
            # history
            try:
                case_history_data = get_table_data_as_list(
                    driver, '//table[@class="history_table"]')
                case_history = {'status': True, 'data': case_history_data}
                logger.info(f'{case_sl_no} case history')

            except:
                case_history = {'status': False, 'data': []}
            # orders
            try:
                case_orders_data = get_table_data_as_list(
                    driver, '//table[@class="order_table"]')
                no_of_orders = len(case_orders_data) - 1
                orders = selenium_get_element_xpath(
                    driver, '//table[@class="order_table"]')
                driver.implicitly_wait(5)
                driver.execute_script(
                    "arguments[0].scrollIntoView();", orders)
                driver.implicitly_wait(2)
                logger.info(f'{case_sl_no} first scroll')

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
                        # logger.error(exc_info=True)

                        logger.info({'err': str(e), 'case_no': case_sl_no})
                case_orders = {'status': True, 'data': case_orders_data,
                               'number_of_downloaded_files': order_no - 1}
                total_downloaded_files = total_downloaded_files + 1
                logger.info("case orders")
            except Exception as e:
                logger.info(
                    {"error": str(e), 'case_no': case_sl_no}, exc_info=True)
                case_orders = {'status': False, 'data': [],
                               'number_of_downloaded_files': 0}

            #  Document details
            try:
                dd_data = get_table_data_as_list(
                    driver, '//table[@class="transfer_table"]')
                dd = {'status': True, 'data': dd_data}
                logger.info(f'{case_sl_no} dd')

            except:
                dd = {'status': False, 'data': []}

            # objections
            try:
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
            logger.info({'case_details': case_details, "case_no": case_sl_no})
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
            "case_details": case_details
        }
        logger.info({"status": True, "data": data,
                    "total_downloaded_files": total_downloaded_files})
        return {"status": True, "data": data}
    except Exception as e_exception:
        logger.error(e_exception, exc_info=True)
        return {'status': False, 'data': {}, "debugMessage": str(e_exception)}
