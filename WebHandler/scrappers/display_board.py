from sentry_sdk import capture_exception, capture_message
import traceback

from ..utils.sel import get_display_board_table_data_as_list, selenium_get_text_xpath
import WebHandler.scrappers.constants as constants

from datetime import datetime


def open_page(driver, highCourtId):
    url_trial = 1
    while url_trial < 11:
        try:
            url = constants.high_courts_codes[highCourtId]["display_board_url"]
            driver.get(url)
            break
        except Exception as exc:
            if url_trial >= 10:
                raise Exception("Causelist: Max url retries exceeded") from exc
            url_trial = url_trial + 1


def get_display_board(driver, highCourtId):
    try:
        open_page(driver, highCourtId)
        try:
            data = get_display_board_table_data_as_list(
                driver, "//table[@id='table1']")
            return data
        except Exception as e:
            try:
                if "SESSION ENDED" in selenium_get_text_xpath(driver, '/html/body/div[2]/form/center/table/tbody/tr/td/h1/font'):
                    return {"message": "SESSION ENDED", "code": "DB-1"}
                else:
                    raise Exception(
                        "displayboard: Somthing is wrong. Try again") from e
            except Exception as e_exc:
                raise Exception(
                    'displayboard: Somthing is wrong. Try again') from e_exc
    except Exception as e:
        cur_url = driver.current_url
        raise Exception("displayboard: Display Board failed" +
                        "\n" + f"currenturl: {cur_url}") from e
