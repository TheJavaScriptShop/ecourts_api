from selenium.webdriver.support.ui import Select
from sentry_sdk import capture_exception

from ..utils.sel import selenium_get_text_xpath, selenium_get_element_id, selenium_send_keys_id, selenium_click_xpath, get_table_data_as_list, selenium_get_element_xpath
import WebHandler.scrappers.constants as constants

from datetime import datetime
import WebHandler.scrappers.constants as constants


def get_nclt_data(nclt_props):
    try:
        driver = nclt_props["driver"]
        bench_id = nclt_props["bench_id"]
        case_type_id = nclt_props["case_type_id"]
        case_num = nclt_props["case_num"]
        case_year = nclt_props["case_year"]
        url_trial = 1
        while url_trial < 11:
            try:
                url = constants.nclt_court_codes["url"]
                driver.get(url)
                break
            except Exception as e_exception:
                if url_trial >= 10:
                    capture_exception(e_exception)
                    return {'status': False, 'data': {}, "debugMessage": "Maximun retries reached", "code": "nclt-1"}
                url_trial = url_trial + 1
        driver.get(url)
        bench_select = Select(
            selenium_get_element_id(driver, 'bench'))
        bench_select.select_by_value(bench_id)
        case_type_select = Select(
            selenium_get_element_id(driver, 'case_type'))
        case_type_select.select_by_value(case_type_id)
        selenium_send_keys_id(
            driver, 'case_number', case_num)
        case_year_select = Select(
            selenium_get_element_id(driver, 'case_year'))
        case_year_select.select_by_value(case_year)
        selenium_click_xpath(
            driver, "/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div/form/div/div[5]/button")
        full_table_element = selenium_get_element_xpath(
            driver, "/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div[2]/table")
        if "click here" in selenium_get_text_xpath(driver, "/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div[2]/table/tbody/tr/td/a"):
            data = "No Data"
        else:
            data = get_table_data_as_list(
                driver, "/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div[2]/table")
        return data

    except Exception as e:
        capture_exception(e)
        return {"message": "No Data Found", "error": str(e), "datetime": datetime.now().isoformat()}
