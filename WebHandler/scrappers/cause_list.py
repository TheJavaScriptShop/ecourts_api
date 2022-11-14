from sentry_sdk import capture_exception


from ..utils.sel import (
    selenium_click_xpath,
    get_cause_list_table_data_as_list, selenium_send_keys_id, selenium_get_text_xpath
)
import WebHandler.scrappers.constants as constants

import time
from datetime import datetime


def get_cause_list_data(driver, advocateName, highCourtId):
    try:
        url = constants.high_courts_codes[highCourtId]["causelist_url"]
        if not url:
            return {"status": False, "message": "invalid request"}
        driver.get(url)
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
        except Exception as e:
            capture_exception(e)
            if 'No list available' in selenium_get_text_xpath(driver, 'html/body'):
                return {"message": "No list available"}

        return data
    except Exception as e:
        capture_exception(e)
        return {"message": "No Data Found", "error": str(e), "datetime": datetime.now().isoformat()}
