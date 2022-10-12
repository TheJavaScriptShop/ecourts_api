import logging
import os
import json
import time
import requests
import threading
import tempfile

import azure.functions as func
from selenium import webdriver
# import sentry_sdk

from .scrappers.highcourts import get_highcourt_cases_by_name, get_no_of_cases

# sentry_sdk.init(
#     dsn="https://7818402c6eff4a99a87db4ceaf0ce3e5@o1183470.ingest.sentry.io/6776130",
#     traces_sample_rate=1.0
# )

version = "2.0.4"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)

path = r"/home/site/wwwroot"
logger.info(path)


def create_driver(__location__):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1700x800")
    prefs = {
        "browser.helperApps.neverAsk.saveToDisk": "application/octet-stream;application/vnd.ms-excel;text/html;application/pdf",
        "pdfjs.disabled": True,
        "print.always_print_silent": True,
        "print.show_print_progress": False,
        "browser.download.show_plugins_in_list": False,
        "browser.download.folderList": 2,
        # Change default directory for downloads
        "download.default_directory": __location__,
        "download.prompt_for_download": False,  # To auto download the file
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }

    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(
        "/usr/local/bin/chromedriver", chrome_options=chrome_options)
    driver.maximize_window()
    return driver


def fire_and_forget(f):
    def wrapped():
        threading.Thread(target=f).start()

    return wrapped


def main_handler(req: func.HttpRequest) -> func.HttpResponse:
    logger.info(req)
    logger.info('Called ECourts Service.')
    logger.info(time.ctime())
    cases_per_iteration = int(os.environ.get('CASES_PER_ITERATION', 50))

    is_valid_request = True
    if (req.method.lower() != "post"):
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": "Method not supported", "version": version}),
            status_code=200
        )

    if req_params.get("method") == "advocatecasesbyname":
        req_body = {}
        try:
            req_body = req.get_json()
        except Exception as e_exception:
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debugMessage": str(e_exception), "version": version}),
                status_code=200
            )
        req_params = dict(req.params.items())
        if not req_body.get("advocateName"):
            is_valid_request = False
        if not req_body.get("highCourtId"):
            is_valid_request = False
        if not req_body.get("benchCode"):
            is_valid_request = False
        if not req_body.get("callBackUrl"):
            is_valid_request = False

    if not is_valid_request:
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": "Insufficient parameters", "version": version}),
            status_code=200
        )

    if req_params.get("method") == "advocatecasesbyname":

        req_body = {}
        try:
            req_body = req.get_json()
        except Exception as e_exception:
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debugMessage": str(e_exception), "version": version}),
                status_code=200
            )
        req_params = dict(req.params.items())

        @ fire_and_forget
        def get_total_no_of_cases_wrapper():
            logger.info("get_highcourt_cases_by_name_wrapper")
            try:
                __location__ = f'{path}/{req_body.get("advocateName")}'
                chrome_driver = create_driver(__location__)
                get_no_of_cases_props = {"driver": chrome_driver,
                                         "advocateName": req_body["advocateName"], "highCourtId": req_body["highCourtId"], "benchCode": req_body["benchCode"], "logger": logger, "location": __location__}
                case_details = get_no_of_cases(get_no_of_cases_props)
                total_cases = int(case_details["number_of_cases"][23:])
                if total_cases <= cases_per_iteration:
                    data = get_highcourt_cases_by_name(
                        chrome_driver, req_body["advocateName"], __location__, logger)
                    data["number_of_establishments_in_court_complex"] = case_details["number_of_establishments_in_court_complex"]
                    data["number_of_cases"] = case_details["number_of_cases"]
                    logger.info(json.dumps(data))
                    requests.post(url=req_body["callBackUrl"], timeout=10, json={
                        "data": data, "request": {"body": req_body, "params": req_params}})
                else:
                    n = total_cases/cases_per_iteration
                    start = 0
                    stop = cases_per_iteration
                    iteration = 1
                    while (n > 0):
                        req_body["start"] = start
                        req_body["iteration"] = iteration
                        if stop > total_cases:
                            req_body["stop"] = total_cases
                        else:
                            req_body["stop"] = stop
                        try:
                            requests.post(
                                url="https://ecourtsapiservice-dev.azurewebsites.net/api/WebHandler?method=advocatecasesbyname", timeout=1, json=req_body)
                        except:
                            pass
                        start = start + cases_per_iteration
                        stop = stop + cases_per_iteration
                        n = n - 1
                        iteration = iteration + 1
                chrome_driver.close()
                chrome_driver.quit()
            except Exception as e:
                logger.info(e)
                requests.post(url=req_body["callBackUrl"], timeout=10, json={
                    "error": e, "request": {"body": req_body, "params": req_params}})
        get_total_no_of_cases_wrapper()
        # sentry_sdk.capture_message("return")
        return func.HttpResponse(
            body=json.dumps(
                {"status": True, "debugMessage": "Request Received and processing", "request": {"body": req_body, "params": req_params, "version": version}}),
        )

    if req_params.get("method") == "advocatecasesbynamepagination":
        req_body = {}
        try:
            req_body = req.get_json()
        except Exception as e_exception:
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debugMessage": str(e_exception), "version": version}),
                status_code=200
            )
        req_params = dict(req.params.items())

        logger.info("url request made")

        @fire_and_forget
        def get_highcourt_cases_by_name_wrapper():
            try:
                __location__ = f'{path}/{req_body["advocateName"]}/{req_body["iteration"]}'
                chrome_driver = create_driver(__location__)  # open browser
                get_no_of_cases_pagination_props = {
                    "driver": chrome_driver,
                    "advocateName": req_body["advocateName"],
                    "highCourtId": req_body["highCourtId"],
                    "benchCode": req_body["benchCode"],
                    "logger": logger,
                    "iteration": req_body["iteration"],
                    "location": __location__
                }
                case_details = get_no_of_cases(
                    get_no_of_cases_pagination_props)
                cases = get_highcourt_cases_by_name(
                    chrome_driver, req_body["advocateName"], __location__, req_body["start"], req_body["stop"], logger)
                cases["number_of_establishments_in_court_complex"] = case_details["number_of_establishments_in_court_complex"]
                cases["number_of_cases"] = case_details["number_of_cases"]
                cases_data = {"start": req_body["start"],
                              "stop": req_body["stop"], "data": cases}
                requests.post(url=req_body["callBackUrl"], timeout=10, json={
                              "data": cases_data, "request": {"body": req_body, "params": req_params}})
                chrome_driver.close()
                chrome_driver.quit()
            except Exception as e:
                logger.info(str(e))
                requests.post(url=req_body["callBackUrl"], timeout=10, json={
                    "error": str(e), "request": {"body": req_body, "params": req_params}})
        get_highcourt_cases_by_name_wrapper()

        return func.HttpResponse(
            body=json.dumps(
                {"status": True, "debugMessage": "Request Received and processing", "request": {"body": req_body, "params": req_params, "version": version}}),
        )


def main(req: func.HttpRequest) -> func.HttpResponse:
    """ Main function for Azure Function """
    try:
        return main_handler(req)
    except Exception as e_exception:
        # sentry_sdk.capture_exception(e_exception)
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": str(e_exception), "version": version}),
            status_code=200
        )
