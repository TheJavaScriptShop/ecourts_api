import time
import os

import traceback
from sentry_sdk import capture_exception
from datetime import datetime, date

from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv
import WebHandler.scrappers.constants as constants


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
from ..utils.blob_storage import wait_for_download_and_rename


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
    name = advoc_name.replace(" ", "_").lower()
    start_time = datetime.now()

    if props.get("iteration"):
        img_path = f'dc-{name}-img-{props["iteration"]}.png'
    else:
        img_path = f"{name}-image.png"

    counter_retry = 0
    url_trial = 1
    while url_trial < 11:
        try:
            url = constants.district_courts_codes["url"]
            driver.get(url)
            break
        except Exception as e_exception:
            if url_trial >= 10:
                capture_exception(e_exception)
                tb = traceback.TracebackException.from_exception(e_exception)
                return {'status': False, "message": ''.join(tb.format()), 'data': {}, "debugMessage": "Maximun retries reached", "code": "dc-1"}
            url_trial = url_trial + 1
    while is_failed_with_captach:
        try:
            counter_retry += 1
            try:
                if "Invalid Request" in selenium_get_text_xpath(driver, "/html/body/div[7]/div/div/div[2]/div/div[1]"):
                    driver.execute_script(
                        "arguments[0].click();", selenium_get_element_xpath(
                            driver, "/html/body/div[7]/div/div/div[1]/button"))

            except Exception as e:
                pass
            case_status_element = selenium_get_element_id(
                driver, 'leftPaneMenuCS')
            driver.execute_script(
                "arguments[0].click();", case_status_element)
            logger.info("Successfully clicked")

            try:
                driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
                    driver, '/html/body/div[9]/div/div/div[1]/button'))
                driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
                    driver, '/html/body/div[9]/div/div/div[1]/button'))

            except:
                pass
            logger.info("ok clicked")
            state_select = Select(
                selenium_get_element_id(driver, 'sess_state_code'))
            state_select.select_by_value(state_id)
            logger.info("Values selected")
            time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
            district_select = Select(selenium_get_element_id(
                driver, 'sess_dist_code'))
            district_select.select_by_value("1")
            district_select.select_by_value(district_id)
            logger.info("district code selected")
            time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
            court_select = Select(selenium_get_element_id(
                driver, 'court_complex_code'))
            court_select.select_by_value(court_complex_id)
            logger.info("court code selected")
            time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
            driver.execute_script(
                "arguments[0].click();", selenium_get_element_id(driver, 'advname-tabMenu'))
            logger.info("hypelink clicked")
            time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
            driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
                driver, '//input[@id="advocate_name"]'))
            selenium_send_keys_xpath(
                driver, '//input[@id="advocate_name"]', advoc_name)
            logger.info("names sent")

            captcha_xpath = '//div[@id="div_captcha_adv"]//img[@id="captcha_image"]'
            get_captcha(driver, img_path, captcha_xpath)
            text = get_text_from_captcha(
                driver, img_path, '/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[2]/div/div/div/a/img', captcha_xpath)
            if text == False:
                continue
            driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
                driver, "//input[@id='adv_captcha_code']"))
            selenium_send_keys_xpath(
                driver, '//input[@id="adv_captcha_code"]', text)
            driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
                driver, '/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[3]/div[2]/button'))

            is_failed_with_captach = False
            try:
                if 'Invalid Captcha' in selenium_get_text_xpath(
                        driver, '/html/body/div[9]/div/div/div[2]/div/div[1]'):
                    driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
                        driver, '/html/body/div[9]/div/div/div[1]/button'))
                    is_failed_with_captach = True

                if 'Invalid Request' in selenium_get_text_xpath(driver, '//div[@id="msg-danger"]'):
                    driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
                        driver, '/html/body/div/div/a'))
                    is_failed_with_captach = True
            except:
                pass
            if os.path.isfile(img_path):
                os.remove(img_path)

        except Exception as e_exception:
            is_failed_with_captach = True
            logger.info("Website is slow. Retrying")
            capture_exception(e_exception)
            tb = traceback.TracebackException.from_exception(e_exception)
            end_time = datetime.now()
            total_time = end_time - start_time
            print(total_time.seconds)
            if total_time.seconds > 300:
                is_failed_with_captach = False
                return {'status': False, "message": ''.join(tb.format()), 'data': {}, "debugMessage": "Maximun Time reached", "code": "dc-2"}

            if counter_retry > 10:
                return {'status': False, 'data': {}, "message": ''.join(tb.format()), "debugMessage": "Maximun retries reached", "code": "dc-3"}

    get_cases_trail = 1
    while get_cases_trail <= 11:
        try:
            time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
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
            return {"data": data, "status": True}
            break
        except:
            if get_cases_trail > 10:
                return {"message": "Somthing is wrong", "status": False, "code": "dc-4"}


def get_districtcourt_cases_by_name(props):
    driver = props["driver"]
    logger = props["logger"]
    start = props["start"]
    stop = props["stop"]
    __location__ = props["location"]
    advoc_name = props["advocate_name"]

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
        by="xpath", value='/html/body/div[1]/div/main/div[2]/div/div/div[4]/div[1]/form/div[4]/table/tbody/tr/td[5]/a')
    if start is not None and stop is not None:
        cases = cases[start:stop]
        case_sl_no = start + 1
    for case in cases:
        logger.info(f'case no: {case_sl_no}')
        time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
        driver.execute_script(
            "arguments[0].click();", case)
        logger.info(f"{case_sl_no} view clicked")
        try:
            if "THERE IS AN ERROR" in selenium_get_text_xpath(driver, '/html/body/div[9]/div/div/div[2]/div/div[1]'):
                driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
                    driver, '/html/body/div[9]/div/div/div[1]/button'))
                case_details_list.append(
                    {"status": False, "message": "THERE IS AN ERROR"})
                case_sl_no = case_sl_no + 1
                continue
        except:
            pass
        # details behind the hyperlink
        # case details
        case_detail_trail = 1
        skip_this_case = False
        while case_detail_trail <= 6:
            try:
                time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
                cur_url = driver.current_url
                logger.info({"current_url": cur_url})
                case_details_element = selenium_get_element_xpath(
                    driver, '//table[contains(@class, "case_details_table")]')
                break
            except Exception as e_exception:
                logger.info(e_exception)
                if case_detail_trail >= 5:
                    logger.info("max tries exceeded")
                    name = advoc_name.replace(" ", "_").lower()
                    driver.save_screenshot(
                        f'{__location__}/error_image.png')
                    try:
                        blob_path_container = f"{name}/districtcourts/{date.today().month}/{date.today().day}/error_img.png"
                        file_name = 'error_image.png'
                        wait_for_download_and_rename(
                            blob_path_container, __location__, file_name)
                    except Exception as e:
                        pass
                    try:
                        back_button = selenium_get_element_xpath(
                            driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[48]/input')
                        driver.execute_script(
                            "arguments[0].click();", back_button)
                    except:
                        pass
                    case_sl_no = case_sl_no + 1
                    skip_this_case = True
                    break
                case_detail_trail = case_detail_trail + 1

        if skip_this_case:
            continue
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
        driver.implicitly_wait(30)

        logger.info({'case_details': case_details_list, "case_no": case_sl_no})
        case_element = selenium_get_element_xpath(
            driver, '//div[@id="CSAdvName"]')
        driver.execute_script(
            "arguments[0].innerHTML = '';", case_element)
        time.sleep(int(os.environ.get('MIN_WAIT_TIME')))
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
