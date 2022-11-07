from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, request

import base64
import os
import re
import json
import webbrowser
import traceback
import datetime
import cv2
import easyocr
import time
import torch
import logging
import threading
import requests
import sentry_sdk
from dotenv import load_dotenv

from sentry_sdk import capture_exception
from WebHandler.scrappers.highcourts import get_highcourt_no_of_cases, get_highcourt_cases_by_name
from WebHandler.scrappers.display_board import get_display_board
from WebHandler.scrappers.cause_list import get_cause_list_data
from WebHandler.scrappers.districtcourts import get_districtcourt_no_of_cases, get_districtcourt_cases_by_name

load_dotenv()


path = os.environ.get('DOWNLOAD_PATH')

sentry_sdk.init(
    dsn="https://94c7a2c09b7140a9ac611581cfb3b33a@o4504008607924224.ingest.sentry.io/4504008615460864",
    traces_sample_rate=1.0
)

version = "3.0.8"


def create_driver(__location__):
    options = Options()
    DRIVER_PATH = os.environ.get('DRIVER_PATH')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1700x800")
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

    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(DRIVER_PATH, chrome_options=options)
    driver.implicitly_wait(30)
    driver.maximize_window()
    return driver


def fire_and_forget(f):
    def wrapped():
        threading.Thread(target=f).start()

    return wrapped


app = Flask(__name__)


@app.route("/", methods=["POST"])
def main():
    cases_per_iteration = int(os.environ.get('CASES_PER_ITERATION', 50))
    data = {}
    is_valid_request = True

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    logger.addHandler(sh)

    if request.args.get('method') == "advocatecasesbyname":
        body = request.json
        params = request.args
        if body.get("highCourtId"):
            if not body.get("advocateName"):
                is_valid_request = False
            if not body.get("highCourtId"):
                is_valid_request = False
            if not body.get("benchCode"):
                is_valid_request = False
            if not body.get("callBackUrl"):
                is_valid_request = False
        if body.get("districtId"):
            if not body.get("advocateName"):
                is_valid_request = False
            if not body.get("callBackUrl"):
                is_valid_request = False
            if not body.get("stateId"):
                is_valid_request = False
            if not body.get("districtId"):
                is_valid_request = False
            if not body.get("courtComplexId"):
                is_valid_request = False

    if request.args.get('method') == "advocatecauselist":
        body = request.json
        params = request.args
        if not body.get("advocateName"):
            is_valid_request = False
        if not body.get("highCourtId"):
            is_valid_request = False

    if request.args.get('method') == "displayboard":
        body = request.json
        params = request.args
        if not body.get("highCourtId"):
            is_valid_request = False

    if not is_valid_request:
        data = {"status": False, "debugMessage": "Insufficient parameters"}
        logger.info(data)
        return jsonify(data)

    if request.args.get('method') == "advocatecauselist":
        try:
            start_time = datetime.datetime.now()
            body = request.json
            params = request.args
            chrome_driver = create_driver(__location__=None)  # open browser
            data = get_cause_list_data(
                chrome_driver, body["advocateName"], body["highCourtId"])
            data = {
                "status": True,
                "data": data,
                "request": {"body": body, "params": params}
            }
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            return jsonify({"status": True, "debugMessage": "Received", "data": data, "start_time": start_time, "total_time_taken": total_time.seconds, 'version': version, 'code': '1'})
        except Exception as e_exception:
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            capture_exception(e_exception)
            return jsonify({"status": False, "debugMessage": "Request Failed", "error": str(e_exception), "start_time": start_time, "total_time_taken": total_time.seconds, 'version': version, 'code': '2'})

    if request.args.get('method') == "displayboard":
        try:
            start_time = datetime.datetime.now()
            body = request.json
            params = request.args
            chrome_driver = create_driver(__location__=None)  # open browser
            table_data = get_display_board(
                chrome_driver, body["highCourtId"])
            data = {
                "status": True,
                "data": table_data,
                "request": {"params": params}
            }
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            return jsonify({"status": True, "debugMessage": "Received", "data": data, "start_time": start_time, "total_time_taken": total_time.seconds, 'version': version, 'code': '3'})
        except Exception as e_exception:
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            capture_exception(e_exception)
            return jsonify({"status": False, "debugMessage": "Request Failed", "error": str(e_exception), "start_time": start_time, "total_time_taken": total_time.seconds, 'version': version, 'code': '4'})

    if request.args.get('method') == "advocatecasesbyname":
        body = request.json
        params = request.args
        logger = logging.getLogger("initial")
        logger.setLevel(logging.DEBUG)
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)

        if os.environ.get("APP_ENV") == "local":
            fh = logging.FileHandler('local/logger/initial.log', mode='w')
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)

        @ fire_and_forget
        def get_total_no_of_cases_wrapper():
            start_time = datetime.datetime.now()
            try:
                __location__ = f'{path}/{body["advocateName"]}'
                chrome_driver = create_driver(__location__)  # open browser
                get_no_of_cases = None
                get_cases_by_name = None
                get_no_of_cases_props = {}
                get_cases_by_name_props = {}
                if body.get("highCourtId"):
                    get_no_of_cases = get_highcourt_no_of_cases
                    get_cases_by_name = get_highcourt_cases_by_name
                    get_no_of_cases_props = {
                        "driver": chrome_driver,
                        "advocate_name": body["advocateName"],
                        "highcourt_id": body["highCourtId"],
                        "bench_code": body["benchCode"],
                        "logger": logger,
                        "location": __location__
                    }
                    get_cases_by_name_props = {
                        "driver": chrome_driver,
                        "advocate_name": body["advocateName"],
                        "__location__": __location__,
                        "start": None,
                        "stop": None,
                        "logger": logger
                    }
                else:
                    get_no_of_cases = get_districtcourt_no_of_cases
                    get_cases_by_name = get_districtcourt_cases_by_name
                    get_no_of_cases_props = {
                        "driver": chrome_driver,
                        "advocate_name": body["advocateName"],
                        "district_id": body["districtId"],
                        "state_id": body["stateId"],
                        "court_complex_id": body["courtComplexId"],
                        "logger": logger,
                        "location": __location__
                    }
                    get_cases_by_name_props = {
                        "driver": chrome_driver,
                        "logger": logger,
                        "start": None,
                        "stop": None,
                    }
                case_details = get_no_of_cases(get_no_of_cases_props)
                total_cases = int(case_details["number_of_cases"][23:])
                logger.info({"total_cases": total_cases})

                if total_cases <= cases_per_iteration:
                    data = get_cases_by_name(get_cases_by_name_props)
                    data["number_of_establishments_in_court_complex"] = case_details["number_of_establishments_in_court_complex"]
                    data["number_of_cases"] = case_details["number_of_cases"]
                    end_time = datetime.datetime.now()
                    total_time = end_time - start_time
                    logger.info(
                        {"start_time": start_time.isoformat(), "time": total_time.seconds})
                    try:
                        requests.post(url=body["callBackUrl"], timeout=10, json={
                            "data": data, "request": {"body": body, "params": params, "start_time": start_time.isoformat(), "time": total_time.seconds, 'version': version, 'code': '5'}})
                    except Exception as e_exception:
                        capture_exception(e_exception)
                        logger.info(
                            {"err_msg": "callback request failed", 'version': version, 'code': '6'})
                else:
                    n = total_cases/cases_per_iteration
                    start = 0
                    stop = cases_per_iteration
                    iteration = 1
                    while (n > 0):
                        body["start"] = start
                        body["iteration"] = iteration
                        if stop > total_cases:
                            body["stop"] = total_cases
                        else:
                            body["stop"] = stop
                        logger.info({"body": body})
                        try:
                            time.sleep(5)
                            requests.post(
                                url=f"{os.environ.get('HOST')}?method=advocatecasesbynamepagination", timeout=1, json=body)
                            logger.info("request made")
                        except Exception as e_exception:
                            end_time = datetime.datetime.now()
                            total_time = end_time - start_time
                            capture_exception(e_exception)
                            try:
                                requests.post(url=body["callBackUrl"], timeout=10, json={
                                    "error": str(e_exception), "message": "Request Failed", "request": {"body": body, "params": params, "start_time": start_time.isoformat(), "time": total_time.seconds, 'version': version, 'code': '7'}})
                            except Exception as e_exc:
                                capture_exception(e_exc)
                                logger.info(
                                    {"err_msg": "callback request failed", 'version': version, 'code': '8'})
                        start = start + cases_per_iteration
                        stop = stop + cases_per_iteration
                        n = n - 1
                        iteration = iteration + 1
                chrome_driver.close()
                chrome_driver.quit()
            except Exception as e_exception:
                logger.info(str(e_exception))
                capture_exception(e_exception)
                end_time = datetime.datetime.now()
                total_time = end_time - start_time
                capture_exception(e_exception)
                try:
                    requests.post(url=body["callBackUrl"], timeout=10, json={
                        "error": str(e_exception), "request": {"body": body, "params": params, "start_time": start_time.isoformat(), "time": total_time.seconds, 'version': version, 'code': '9'}})
                except Exception as e_exc:
                    capture_exception(e_exc)
                    logger.info({"err_msg": "callback request failed",
                                'version': version, 'code': '10'})
        get_total_no_of_cases_wrapper()
        data = {
            "status": True,
            "debugMessage": "Request Received and processing",
            "request": {"body": body, "params": params}
        }
        return jsonify({"status": True, "debugMessage": "Received", "data": data, 'version': version, 'code': '11'})

    if request.args.get('method') == "advocatecasesbynamepagination":
        body = request.json
        params = request.args

        logger = logging.getLogger(f'{body["iteration"]}')
        logger.setLevel(logging.DEBUG)
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        logger.addHandler(sh)
        if os.environ.get("APP_ENV") == "local":
            fh = logging.FileHandler(
                f'local/logger/{body["iteration"]}-{body["start"]}.log', mode='w')
            fh.setLevel(logging.DEBUG)
            logger.addHandler(fh)

        @fire_and_forget
        def get_highcourt_cases_by_name_wrapper():
            start_time = datetime.datetime.now()
            try:
                __location__ = f'{path}/{body["advocateName"]}/{body["iteration"]}'
                chrome_driver = create_driver(__location__)  # open browser
                get_no_of_cases = None
                get_cases_by_name = None
                get_no_of_cases_props = {}
                get_cases_by_name_props = {}
                if body.get("highCourtId"):
                    get_no_of_cases = get_highcourt_no_of_cases
                    get_cases_by_name = get_highcourt_cases_by_name
                    get_no_of_cases_props = {
                        "driver": chrome_driver,
                        "advocate_name": body["advocateName"],
                        "highcourt_id": body["highCourtId"],
                        "bench_code": body["benchCode"],
                        "logger": logger,
                        "iteration": body["iteration"],
                        "location": __location__
                    }
                    get_cases_by_name_props = {
                        "driver": chrome_driver,
                        "advocate_name": body["advocateName"],
                        "__location__": __location__,
                        "start": body["start"],
                        "stop": body["stop"],
                        "logger": logger
                    }
                else:
                    get_no_of_cases = get_districtcourt_no_of_cases
                    get_cases_by_name = get_districtcourt_cases_by_name
                    get_no_of_cases_props = {
                        "driver": chrome_driver,
                        "advocate_name": body["advocateName"],
                        "district_id": body["districtId"],
                        "state_id": body["stateId"],
                        "court_complex_id": body["courtComplexId"],
                        "logger": logger,
                        "iteration": body["iteration"],
                        "location": __location__
                    }
                    get_cases_by_name_props = {
                        "driver": chrome_driver,
                        "logger": logger,
                        "start": body["start"],
                        "stop": body["stop"]
                    }

                case_details = get_no_of_cases(
                    get_no_of_cases_props)
                cases = get_cases_by_name(get_cases_by_name_props)
                cases["number_of_establishments_in_court_complex"] = case_details["number_of_establishments_in_court_complex"]
                cases["number_of_cases"] = case_details["number_of_cases"]
                cases_data = {"start": body["start"],
                              "stop": body["stop"], "data": cases}
                chrome_driver.close()
                chrome_driver.quit()
                end_time = datetime.datetime.now()
                total_time = end_time - start_time
                logger.info({"start_time": start_time.isoformat(),
                            "time": total_time.seconds})
                try:
                    requests.post(url=body["callBackUrl"], timeout=10, json={
                        "data": cases_data, "request": {"body": body, "params": params, "start_time": start_time.isoformat(), "time": total_time.seconds, 'version': version, 'code': '12'}})
                except Exception as e_exception:
                    capture_exception(e_exception)
                    logger.info(
                        {"err_msg": "callback request failed", 'version': version, 'code': '13'})
            except Exception as e_exception:
                logger.info(str(e_exception))
                end_time = datetime.datetime.now()
                total_time = end_time - start_time
                capture_exception(e_exception)
                try:
                    requests.post(url=body["callBackUrl"], timeout=10, json={
                        "error": str(e_exception), "request": {"body": body, "params": params, "start_time": start_time.isoformat(), "time": total_time.seconds, 'version': version, 'code': '14'}})
                except Exception as e_exc:
                    capture_exception(e_exc)
                    logger.info(
                        {"err_msg": "callback request failed", 'version': version, 'code': '15'})
        get_highcourt_cases_by_name_wrapper()
        data = {
            "status": True,
            "debugMessage": "Request Received and processing",
            "request": {"body": body, "params": params}
        }
        return jsonify({"status": True, "debugMessage": "Received", "data": data, 'version': version, 'code': '16'})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=os.environ.get('PORT'))
