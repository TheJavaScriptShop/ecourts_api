from sentry_sdk import capture_exception, capture_message
import traceback

from ..utils.sel import get_display_board_table_data_as_list, selenium_get_text_xpath
import WebHandler.scrappers.constants as constants

from datetime import datetime


def get_display_board(driver, highCourtId):
    try:
        url = constants.high_courts_codes[highCourtId]["display_board_url"]
        if not url:
            return {"status": False, "message": "Invalid request"}
        url_trial = 1
        while url_trial <= 11:
            try:
                driver.get(url)
                break
            except Exception as e_exception:
                if url_trial >= 10:
                    tb = traceback.TracebackException.from_exception(
                        e_exception)
                    capture_message("Message: displayboard-URL failed" + "\n" + "traceback: " + ''.join(
                        tb.format()))
                    return {'status': False, "message": ''.join(tb.format()), 'data': {}, "debugMessage": "Maximun retries reached", "code": "hc-1"}
                url_trial = url_trial + 1
        try:
            data = get_display_board_table_data_as_list(
                driver, "//table[@id='table1']")
            return data
        except Exception as e:
            try:
                if "SESSION ENDED" in selenium_get_text_xpath(driver, '/html/body/div[2]/form/center/table/tbody/tr/td/h1/font'):
                    return {"message": "SESSION ENDED", "code": "DB-1"}
                else:
                    tb = traceback.TracebackException.from_exception(e)
                    return {"message": "Somthing is wrong. Try again", "error": ''.join(tb.format()), "code": "DB-2"}
            except Exception as e_exc:
                tb = traceback.TracebackException.from_exception(e_exc)
                return {"message": "Something is wrong. Try again", "error": ''.join(tb.format()), "code": "DB-3"}
    except Exception as e:
        tb = traceback.TracebackException.from_exception(e)
        return {"message": "No Data Found", "error": ''.join(tb.format()), "datetime": datetime.now().isoformat(), "code": "DB-4"}
