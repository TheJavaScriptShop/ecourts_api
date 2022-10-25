import logging
import os
import json
import time
import requests
import threading
import tempfile
import datetime
import traceback

import azure.functions as func
from selenium import webdriver
import sentry_sdk
from sentry_sdk import capture_exception
from .scrappers.highcourts import get_highcourt_no_of_cases, get_highcourt_cases_by_name
from .scrappers.display_board import get_display_board
from .scrappers.cause_list import get_cause_list_data
from .scrappers.districtcourts import get_districtcourt_no_of_cases, get_districtcourt_cases_by_name

sentry_sdk.init(
    dsn="https://94c7a2c09b7140a9ac611581cfb3b33a@o4504008607924224.ingest.sentry.io/4504008615460864",
    traces_sample_rate=1.0
)

version = "2.3.0"

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
                {"status": False, "debug_message": "Method not supported", "version": version}),
            status_code=200
        )

    req_params = dict(req.params.items())

    if req_params.get("method") == "advocatecasesbyname":
        req_body = {}
        try:
            req_body = req.get_json()
        except Exception as e_exception:
            capture_exception(e_exception)
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debug_message": str(e_exception), "version": version, "code": 1}),
                status_code=200
            )
        if req_body.get("highcourt_id"):
            if not req_body.get("advocate_name"):
                is_valid_request = False
            if not req_body.get("highcourt_id"):
                is_valid_request = False
            if not req_body.get("bench_code"):
                is_valid_request = False
            if not req_body.get("callback_url"):
                is_valid_request = False
        if req_body.get("district_id"):
            if not req_body.get("advocate_name"):
                is_valid_request = False
            if not req_body.get("callback_url"):
                is_valid_request = False
            if not req_body.get("state_id"):
                is_valid_request = False
            if not req_body.get("district_id"):
                is_valid_request = False
            if not req_body.get("court_complex_id"):
                is_valid_request = False

    if req_params.get("method") == "advocatecauselist":
        req_body = {}
        try:
            req_body = req.get_json()
        except Exception as e_exception:
            capture_exception(e_exception)
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debug_message": str(e_exception), "version": version, "code": 2}),
                status_code=200
            )
        if not req_body.get("advocate_name"):
            is_valid_request = False
        if not req_body.get("highcourt_id"):
            is_valid_request = False

    if req_params.get("method") == "displayboard":
        req_body = {}
        try:
            req_body = req.get_json()
        except Exception as e_exception:
            capture_exception(e_exception)
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debug_message": str(e_exception), "version": version, "code": 3}),
                status_code=200
            )
        if not req_body.get("highcourt_id"):
            is_valid_request = False

    if not is_valid_request:
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debug_message": "Insufficient parameters", "version": version, "code": 4}),
            status_code=200
        )

    if req_params.get('method') == "advocatecauselist":
        try:
            start_time = datetime.datetime.now()
            req_body = {}
            try:
                req_body = req.get_json()
            except Exception as e_exception:
                capture_exception(e_exception)
                return func.HttpResponse(
                    body=json.dumps(
                        {"status": False, "debug_message": str(e_exception), "version": version, "code": 5}),
                    status_code=200
                )

            chrome_driver = create_driver(__location__=None)  # open browse
            data = get_cause_list_data(
                chrome_driver, req_body["advocate_name"], req_body["highcourt_id"])
            data = {
                "status": True,
                "data": data,
                "request": {"body": req_body, "params": req_params}
            }
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            return func.HttpResponse(
                body=json.dumps(
                    {"status": True, "debug_message": "Received", "data": data, "start_time": start_time.isoformat(), "total_time_taken": total_time.seconds, "version": version}),
                status_code=200
            )
        except Exception as e_exception:
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            capture_exception(e_exception)
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debug_message": "Request Failed", "error": str(e_exception), "start_time": start_time.isoformat(), "total_time_taken": total_time.seconds, "version": version, 'code': 6}),
                status_code=200
            )

    if req_params.get('method') == "displayboard":
        try:
            start_time = datetime.datetime.now()
            req_body = {}
            try:
                req_body = req.get_json()
            except Exception as e_exception:
                capture_exception(e_exception)
                return func.HttpResponse(
                    body=json.dumps(
                        {"status": False, "debug_message": str(e_exception), "version": version, "code": 7}),
                    status_code=200
                )
            chrome_driver = create_driver(__location__=None)  # open browser
            table_data = get_display_board(
                chrome_driver, req_body["highcourt_id"])
            data = {
                "status": True,
                "data": table_data,
                "request": {"params": req_params}
            }
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            return func.HttpResponse(
                body=json.dumps(
                    {"status": True, "debug_message": "Received", "data": data, "start_time": start_time.isoformat(), "total_time_taken": total_time.seconds, "version": version}),
                status_code=200
            )
        except Exception as e_exception:
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            capture_exception(e_exception)
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debug_message": "Request Failed", "error": str(e_exception), "start_time": start_time.isoformat(), "time_time_taken": total_time.seconds, "version": version, 'code': 8}),
                status_code=200
            )

    if req_params.get("method") == "advocatecasesbyname":

        req_body = {}
        try:
            req_body = req.get_json()
        except Exception as e_exception:
            capture_exception(e_exception)
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debug_message": str(e_exception), "version": version, "code": 9}),
                status_code=200
            )

        @ fire_and_forget
        def get_highcourt_total_no_of_cases_wrapper():
            logger.info("get_highcourt_cases_by_name_wrapper")
            start_time = datetime.datetime.now()
            start = cases_per_iteration
            try:
                __location__ = f'{path}/highcourt/{req_body.get("advocate_name")}'
                chrome_driver = create_driver(__location__)
                get_no_of_cases
                get_cases_by_name
                get_no_of_cases_props = {}
                get_cases_by_name_props = {}
                if req_body.get("highcourt_id"):
                    get_no_of_cases = get_highcourt_no_of_cases
                    get_cases_by_name = get_highcourt_cases_by_name
                    get_no_of_cases_props = {
                        "driver": chrome_driver,
                        "advocate_name": req_body["advocate_name"],
                        "highcourt_id": req_body["highcourt_id"],
                        "bench_code": req_body["bench_code"],
                        "logger": logger,
                        "location": __location__
                    }
                    get_cases_by_name_props = {
                        "driver": chrome_driver,
                        "advocate_name": req_body["advocate_name"],
                        "__location__": __location__,
                        "start": None,
                        "stop": None,
                        "logger": None
                    }
                else:
                    get_no_of_cases = get_districtcourt_no_of_cases
                    get_cases_by_name = get_districtcourt_cases_by_name
                    get_no_of_cases_props = {
                        "driver": chrome_driver,
                        "advocate_name": req_body["advocate_name"],
                        "district_id": req_body["district_id"],
                        "state_id": req_body["state_id"],
                        "court_complex_id": req_body["court_complex_id"],
                        "logger": logger,
                        "location": __location__
                    }
                    get_cases_by_name_props = {
                        "driver": chrome_driver,
                        "logger": None,
                        "start": None,
                        "stop": None,
                    }

                case_details = get_no_of_cases(get_no_of_cases_props)
                total_cases = int(case_details["number_of_cases"][23:])
                if total_cases <= cases_per_iteration:
                    data = get_cases_by_name(get_cases_by_name_props)
                    data["number_of_establishments_in_court_complex"] = case_details["number_of_establishments_in_court_complex"]
                    data["number_of_cases"] = case_details["number_of_cases"]
                    logger.info(json.dumps(data))
                    end_time = datetime.datetime.now()
                    total_time = end_time - start_time
                    try:
                        requests.post(url=req_body["callback_url"], timeout=10, json={
                            "data": data, "request": {"body": req_body, "params": req_params, "start_time": start_time.isoformat(), "time": total_time.seconds, "version": version}})
                    except Exception as e_exception:
                        capture_exception(e_exception)
                        logger.info({"err_msg": "callback request failed"})
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
                                url="https://ecourtsapiservice-dev.azurewebsites.net/api/WebHandler?method=advocatecasesbynamepagination", timeout=1, json=req_body)
                        except Exception as e_exception:
                            logger.info(str(e_exception), exc_info=True)
                            end_time = datetime.datetime.now()
                            total_time = end_time - start_time
                            capture_exception(e_exception)
                            try:
                                requests.post(url=req_body["callback_url"], timeout=10, json={
                                    "error": str(e_exception), "message": "Request Failed", "request": {"body": req_body, "params": req_params, "start_time": start_time.isoformat(), "time": total_time.seconds, "code": 10}})
                            except Exception as e_exc:
                                capture_exception(e_exc)
                                logger.info(
                                    {"err_msg": "callback request failed"})

                        start = start + cases_per_iteration
                        stop = stop + cases_per_iteration
                        n = n - 1
                        iteration = iteration + 1
                chrome_driver.close()
                chrome_driver.quit()

            except Exception as e_exception:
                logger.info(str(e_exception), exc_info=True)
                tb = traceback.print_exc()
                end_time = datetime.datetime.now()
                total_time = end_time - start_time
                capture_exception(e_exception)
                try:
                    requests.post(url=req_body["callback_url"], timeout=10, json={
                        "error": str(e_exception), "traceback": tb, "request": {"body": req_body, "params": req_params, "start_time": start_time.isoformat(), "time": total_time.seconds, 'version': version, "code": 11}})
                except Exception as e_exc:
                    capture_exception(e_exc)
                    logger.info({"err_msg": "callback request failed"})

        get_highcourt_total_no_of_cases_wrapper()
        return func.HttpResponse(
            body=json.dumps(
                {"status": True, "debug_message": "Request Received and processing", "request": {"body": req_body, "params": req_params, "version": version}}),
        )

    if req_params.get("method") == "advocatecasesbynamepagination":
        req_body = {}
        try:
            req_body = req.get_json()
        except Exception as e_exception:
            capture_exception(e_exception)
            return func.HttpResponse(
                body=json.dumps(
                    {"status": False, "debug_message": str(e_exception), "version": version, "code": 12}),
                status_code=200
            )

        logger.info("url request made")

        @ fire_and_forget
        def get_highcourt_cases_by_name_wrapper():
            start_time = datetime.datetime.now()

            try:
                __location__ = f'{path}/highcourt/{req_body["advocate_name"]}/{req_body["iteration"]}'
                chrome_driver = create_driver(__location__)  # open browser
                get_no_of_cases
                get_cases_by_name
                get_no_of_cases_props = {}
                get_cases_by_name_props = {}
                if req_body.get("highcourt_id"):
                    get_no_of_cases = get_highcourt_no_of_cases
                    get_cases_by_name = get_highcourt_cases_by_name
                    get_no_of_cases_props = {
                        "driver": chrome_driver,
                        "advocate_name": req_body["advocate_name"],
                        "highcourt_id": req_body["highcourt_id"],
                        "bench_code": req_body["bench_code"],
                        "logger": logger,
                        "iteration": req_body["iteration"],
                        "location": __location__
                    }
                    get_cases_by_name_props = {
                        "driver": chrome_driver,
                        "advocate_name": req_body["advocate_name"],
                        "__location__": __location__,
                        "start": req_body["start"],
                        "stop": req_body["stop"],
                        "logger": logger
                    }
                else:
                    get_no_of_cases = get_districtcourt_no_of_cases
                    get_cases_by_name = get_districtcourt_cases_by_name
                    get_no_of_cases_props = {
                        "driver": chrome_driver,
                        "advocate_name": req_body["advocate_name"],
                        "district_id": req_body["district_id"],
                        "state_id": req_body["state_id"],
                        "court_complex_id": req_body["court_complex_id"],
                        "logger": logger,
                        "iteration": req_body["iteration"],
                        "location": __location__
                    }
                    get_cases_by_name_props = {
                        "driver": chrome_driver,
                        "logger": logger,
                        "start": req_body["start"],
                        "stop": req_body["stop"]
                    }

                case_details = get_no_of_cases(
                    get_no_of_cases_props)
                cases = get_cases_by_name(get_cases_by_name_props)
                cases["number_of_establishments_in_court_complex"] = case_details["number_of_establishments_in_court_complex"]
                cases["number_of_cases"] = case_details["number_of_cases"]
                cases_data = {"start": req_body["start"],
                              "stop": req_body["stop"], "data": cases}
                chrome_driver.close()
                chrome_driver.quit()
                end_time = datetime.datetime.now()
                total_time = end_time - start_time
                try:
                    requests.post(url=req_body["callback_url"], timeout=10, json={
                        "data": cases_data, "request": {"body": req_body, "params": req_params, "start_time": start_time.isoformat(), "time": total_time.seconds, 'version': version}})
                except Exception as e_exception:
                    capture_exception(e_exception)
                    logger.info({"err_msg": "callback request failed"})

            except Exception as e_exception:
                logger.info(str(e_exception), exc_info=True)
                tb = traceback.print_exc()
                end_time = datetime.datetime.now()
                total_time = end_time - start_time
                capture_exception(e_exception)
                try:
                    requests.post(url=req_body["callback_url"], timeout=10, json={
                        "error": str(e_exception), "traceback": tb, "request": {"body": req_body, "params": req_params, "start_time": start_time.isoformat(), "time": total_time.seconds, "version": version, "code": 13}})
                except Exception as e_exc:
                    capture_exception(e_exc)
                    logger.info({"err_msg": "callback request failed"})

        get_highcourt_cases_by_name_wrapper()

        return func.HttpResponse(
            body=json.dumps(
                {"status": True, "debug_message": "Request Received and processing", "request": {"body": req_body, "params": req_params, "version": version}}),
        )


def main(req: func.HttpRequest) -> func.HttpResponse:
    """ Main function for Azure Function """
    try:
        return main_handler(req)
    except Exception as e_exception:
        capture_exception(e_exception)
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debug_message": str(e_exception), "version": version, "code": 14}),
            status_code=200
        )
