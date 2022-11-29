from selenium.webdriver.support.ui import Select
from sentry_sdk import capture_exceptio, capture_message
from datetime import date
import os
import traceback
import time

from ..utils.blob_storage import wait_for_download_and_rename

from ..utils.sel import (
    selenium_get_text_xpath,
    selenium_get_element_id,
    selenium_send_keys_id,
    selenium_click_xpath,
    get_table_data_as_list,
    selenium_get_element_xpath,
)
import WebHandler.scrappers.constants as constants

from datetime import datetime
import WebHandler.scrappers.constants as constants
from dotenv import load_dotenv


if os.environ.get("APP_ENV") == "local":
    load_dotenv()


def get_nclt_data(nclt_props):
    try:
        driver = nclt_props["driver"]
        bench_id = nclt_props["bench_id"]
        case_type_id = nclt_props["case_type_id"]
        case_num = nclt_props["case_num"]
        case_year = nclt_props["case_year"]
        location = nclt_props["location"]
        logger = nclt_props["logger"]
        start_time = nclt_props["start_time"]
        req_body = nclt_props["req_body"]
        url_trial = 1
        while url_trial < 11:
            try:
                url = constants.nclt_court_codes["url"]
                driver.get(url)
                break
            except Exception as e_exception:
                if url_trial >= 10:
                    tb = traceback.TracebackException.from_exception(
                        e_exception)
                    capture_message("message: Max URL tries Exceeded" + "\n" + "traceback: " + ''.join(
                        tb.format()) + "\n" + "start_time: " + start_time.isoformat() + "\n" + "req_body: " + req_body)
                    return {'status': False, 'data': {}, "debugMessage": "Maximun retries reached", "code": "nclt-1"}
                url_trial = url_trial + 1
        bench_select = Select(
            selenium_get_element_id(driver, 'bench'))
        bench_select.select_by_value(bench_id)
        logger.info("bench selected")
        case_type_select = Select(
            selenium_get_element_id(driver, 'case_type'))
        case_type_select.select_by_value(case_type_id)
        logger.info("case type selected")
        selenium_send_keys_id(
            driver, 'case_number', case_num)
        logger.info("case number entered")
        case_year_select = Select(
            selenium_get_element_id(driver, 'case_year'))
        case_year_select.select_by_value(case_year)
        logger.info("case year entered")
        selenium_click_xpath(
            driver, "/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div/form/div/div[5]/button")
        logger.info("clicked submit")
        selenium_get_element_xpath(
            driver, "/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div[2]/table")
        if "click here" in selenium_get_text_xpath(driver, "/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div[2]/table/tbody/tr/td/a"):
            data = "No Data"
            logger.info("No Data")
            return data
        preview_data = get_table_data_as_list(
            driver, "/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div[2]/table")
        button = selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div[2]/table/tbody/tr/td[6]/a')
        driver.execute_script("arguments[0].click();", button)

        # switch to other window
        original_window = driver.current_window_handle
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[1]/table/tbody/tr[1]/td[1]')
        logger.info("opened full deatails tab")
        # case info
        case_info = get_table_data_as_list(
            driver, '//div[@id="block-nclt-content"]/div/div/table')
        logger.info("case info")

        # All parties
        driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[1]/div[1]/h2/button'))
        selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[1]/div[2]/div/div/table/thead/tr/th[1]')
        all_parties_data = get_table_data_as_list(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[1]/div[2]/div/div/table')
        logger.info("All Parties")

        # Orders
        driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div[1]/h2/button'))
        selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/table/thead/tr/th[1]')
        orders_data = get_table_data_as_list(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/table')
        orders = driver.find_elements(
            by="xpath", value='/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/table/tbody/tr/td[4]')
        order_no = 1
        for pdf_link in orders:
            pdf_element = selenium_get_element_xpath(pdf_link, ".//a")
            driver.execute_script(
                "arguments[0].click();", pdf_element)
            blob_path_container = ""
            case = f"{bench_id}-{case_type_id}-{case_num}-{case_year}"
            blob_path_container = f"nclt/{case}/{date.today().month}/{date.today().day}/orders/{order_no}.pdf"
            file_name = 'filename.pdf'
            status = wait_for_download_and_rename(
                blob_path_container, location, file_name, case)
            if status["upload"] == False:
                blob_path_container = "File not Available"
            order = orders_data[order_no]
            order["file"] = blob_path_container
            orders_data[order_no] = order
            logger.info(f'downloaded {order_no}')
            order_no = order_no+1
            logger.info("orders")

        # IA/MA
        driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div[1]/h2/button'))
        selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div[2]/div/div/table/thead/tr/th[1]')
        ia_ma = get_table_data_as_list(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[3]/div[2]/div/div/table')
        logger.info("IA/MA")

        # Connected Matters
        driver.execute_script("arguments[0].click();", selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[4]/div[1]/h2/button'))
        selenium_get_element_xpath(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[4]/div[2]/div/div/table/thead/tr/th[1]')
        connected_matters_data = get_table_data_as_list(
            driver, '/html/body/div/div[2]/div/div/div/div/div/div/div/div[2]/div[4]/div[2]/div/div/table')
        logger.info("Connected Matters")

        case_details = {
            "case_info": case_info,
            "all_parties_data": all_parties_data,
            "orders_data": orders_data,
            "ia_ma": ia_ma,
            "connected_matters_data": connected_matters_data
        }
        data = {
            'preview_data': preview_data,
            "case_details": case_details
        }
        logger.info(data)
        return data

    except Exception as e:
        tb = traceback.TracebackException.from_exception(e)
        capture_message("message: No Data Found in NCLT" + "\n" + "traceback: " +
                        ''.join(tb.format()) + "\n" + "start_time: " + start_time.isoformat() + "\n" + "req_body: " + req_body)
        return {"message": "No Data Found", "error": ''.join(tb.format()), "datetime": datetime.now().isoformat()}
