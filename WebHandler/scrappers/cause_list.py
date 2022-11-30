from sentry_sdk import capture_exception, capture_message
import traceback


from ..utils.sel import (
    selenium_click_xpath,
    get_cause_list_table_data_as_list, selenium_send_keys_id, selenium_get_text_xpath
)
import WebHandler.scrappers.constants as constants

import time
from datetime import datetime


def open_page(driver, highCourtId):
    url_trial = 1
    while url_trial < 11:
        try:
            url = constants.high_courts_codes[highCourtId]["causelist_url"]
            driver.get(url)
            break
        except Exception as exc:
            if url_trial >= 10:
                raise Exception("Causelist: Max url retries exceeded") from exc
            url_trial = url_trial + 1


def get_cause_list_data(driver, advocateName, highCourtId):
    try:
        open_page(driver, highCourtId)
        time.sleep(3)
        selenium_click_xpath(driver, "//input[@value='DAILY LIST']")
        time.sleep(3)
        selenium_click_xpath(driver, "//input[@value='ADVOCATE WISE']")
        time.sleep(3)
        selenium_send_keys_id(driver, "svalue", advocateName)
        selenium_click_xpath(driver, '//div[@id="advsearch"]/input[2]')
        time.sleep(3)

        try:
            data = get_cause_list_table_data_as_list(driver, "//table")
            return data
        except Exception as e:
            try:
                if 'No list available' in selenium_get_text_xpath(driver, 'html/body'):
                    return {"message": "No list available", "code": "CL-1"}
                else:
                    raise Exception(
                        "causelist: Somthing is wrong. Try again") from e
            except Exception as e_exc:
                raise Exception(
                    "causelist: Something is wrong. Try again") from e_exc
    except Exception as e:
        raise Exception("causelist: Causelist failed") from e
