from sentry_sdk import capture_exception

from ..utils.sel import get_display_board_table_data_as_list, selenium_get_text_xpath
import WebHandler.scrappers.constants as constants

from datetime import datetime


def get_display_board(driver, highCourtId):
    try:
        url = constants.high_courts_codes[highCourtId]["display_board_url"]
        if not url:
            return {"status": False, "message": "Invalid request"}
        driver.get(url)
        try:
            data = get_display_board_table_data_as_list(
                driver, "//table[@id='table1']")
        except Exception as e:
            capture_exception(e)
            if "SESSION ENDED" in selenium_get_text_xpath(driver, '/html/body/div[2]/form/center/table/tbody/tr/td/h1/font'):
                return {"message": "SESSION ENDED"}
        return data
    except Exception as e:
        capture_exception(e)
        return {"message": "No Data Found", "error": str(e), "datetime": datetime.now().isoformat()}
