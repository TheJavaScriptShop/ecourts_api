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

from .scrappers.highcourts import get_highcourt_cases_by_name

# sentry_sdk.init(
#     dsn="https://7818402c6eff4a99a87db4ceaf0ce3e5@o1183470.ingest.sentry.io/6776130",
#     traces_sample_rate=1.0
# )

version = "2.0.3"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)

__location__ = tempfile.gettempdir()
logger.info(__location__)


def fire_and_forget(f):
    def wrapped():
        threading.Thread(target=f).start()

    return wrapped


def main_handler(req: func.HttpRequest) -> func.HttpResponse:
    logger.info(req)
    logger.info('Called ECourts Service.')
    logger.info(time.ctime())
    if (req.method.lower() != "post"):
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": "Method not supported", "version": version}),
            status_code=200
        )

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

    is_valid_request = True
    if req_params.get("method") == "advocatecasesbyname":
        if not req_body.get("advocateName"):
            is_valid_request = False
        if not req_body.get("highCourtId"):
            is_valid_request = False
        if not req_body.get("benchCode"):
            is_valid_request = False
        if not req_body.get("callBackUrl"):
            is_valid_request = False
    else:
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": "Method not supported", "version": version}),
            status_code=200
        )

    if not is_valid_request:
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": "Insufficient parameters", "version": version}),
            status_code=200
        )

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument('--headless')
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

    if req_params.get("method") == "advocatecasesbyname":
        @ fire_and_forget
        def get_highcourt_cases_by_name_wrapper():
            logger.info("get_highcourt_cases_by_name_wrapper")
            try:
                data = get_highcourt_cases_by_name(driver, req_body.get(
                    "advocateName"), req_body.get("highCourtId"), req_body.get("benchCode"), __location__)
                logger.info(json.dumps(data))
                requests.post(url=req_body.get("callBackUrl"), timeout=10, json={
                              "data": data, "request": {"body": req_body, "params": req_params}})
            except Exception as e:
                logger.info(e)
        get_highcourt_cases_by_name_wrapper()
        # sentry_sdk.capture_message("return")
        return func.HttpResponse(
            body=json.dumps(
                {"status": True, "debugMessage": "Request Received and processing", "request": {"body": req_body, "params": req_params, "version": version}}),
        )
    return func.HttpResponse(
        body=json.dumps(
            {"status": False, "debugMessage": "Method not supported", "request": {"body": req_body, "params": req_params, "version": version}}),
        status_code=200
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
