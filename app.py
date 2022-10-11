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
import ipdb
import logging
import threading
import requests

from WebHandler.scrappers.highcourts import get_highcourt_cases_by_name, get_no_of_cases

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)
path = os.environ.get('DOWNLOAD_PATH')


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

    if request.args.get('method') == "advocatecasesbyname":
        body = request.json
        params = request.args
        if not body.get("advocateName"):
            is_valid_request = False
        if not body.get("highCourtId"):
            is_valid_request = False
        if not body.get("benchCode"):
            is_valid_request = False
        if not body.get("callBackUrl"):
            is_valid_request = False
    elif request.args.get('method') == "advocatecasesbynamepagination":
        body = request.json
        params = request.args
        if not body.get("advocateName"):
            is_valid_request = False
        if not body.get("highCourtId"):
            is_valid_request = False
        if not body.get("benchCode"):
            is_valid_request = False
        if not body.get("callBackUrl"):
            is_valid_request = False
        if not body.get("start"):
            is_valid_request = False
        if not body.get("stop"):
            is_valid_request = False
    else:
        data = {"status": False, "debugMessage": "Method not supported"}
        logger.info(data)
        return jsonify(data)

    if not is_valid_request:
        data = {"status": False, "debugMessage": "Insufficient parameters"}
        logger.info(data)
        return jsonify(data)

    if request.args.get('method') == "advocatecasesbyname":
        body = request.json
        params = request.args

        @ fire_and_forget
        def get_total_no_of_cases_wrapper():
            try:
                __location__ = f'{path}/{body["advocateName"]}'
                chrome_driver = create_driver(__location__)  # open browser
                case_details = get_no_of_cases(
                    chrome_driver, body["advocateName"], body["highCourtId"], body["benchCode"])
                total_cases = int(case_details["number_of_cases"][23:])
                logger.info({"total_cases": total_cases})

                if total_cases <= cases_per_iteration:
                    data = get_highcourt_cases_by_name(
                        chrome_driver, body["advocateName"], __location__)
                    data["number_of_establishments_in_court_complex"] = case_details["number_of_establishments_in_court_complex"]
                    data["number_of_cases"] = case_details["number_of_cases"]
                    requests.post(url=body["callBackUrl"], timeout=10, json={
                        "data": data, "request": {"body": body, "params": params}})
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
                            requests.post(
                                url="http://127.0.0.1:4000?method=advocatecasesbynamepagination", timeout=1, json=body)
                        except:
                            pass
                        start = start + cases_per_iteration
                        stop = stop + cases_per_iteration
                        n = n - 1
                        iteration = iteration + 1
                chrome_driver.close()
                chrome_driver.quit()
            except Exception as e:
                logger.info(str(e))
                requests.post(url=body["callBackUrl"], timeout=10, json={
                    "error": str(e), "request": {"body": body, "params": params}})

        get_total_no_of_cases_wrapper()
        data = {
            "status": True,
            "debugMessage": "Request Received and processing",
            "request": {"body": body, "params": params}
        }
        return jsonify({"status": True, "debugMessage": "Received", "data": data})

    if request.args.get('method') == "advocatecasesbynamepagination":
        body = request.json
        params = request.args

        logger.info("url request made")

        @fire_and_forget
        def get_highcourt_cases_by_name_wrapper():
            try:
                __location__ = f'{path}/{body["advocateName"]}/{body["iteration"]}'
                chrome_driver = create_driver(__location__)  # open browser
                case_details = get_no_of_cases(
                    chrome_driver, body["advocateName"], body["highCourtId"], body["benchCode"])
                cases = get_highcourt_cases_by_name(
                    chrome_driver, body["advocateName"], __location__, body["start"], body["stop"])
                cases["number_of_establishments_in_court_complex"] = case_details["number_of_establishments_in_court_complex"]
                cases["number_of_cases"] = case_details["number_of_cases"]
                cases_data = {"start": body["start"],
                              "stop": body["stop"], "data": cases}
                requests.post(url=body["callBackUrl"], timeout=10, json={
                              "data": cases_data, "request": {"body": body, "params": params}})
                chrome_driver.close()
                chrome_driver.quit()
            except Exception as e:
                logger.info(str(e))
                requests.post(url=body["callBackUrl"], timeout=10, json={
                    "error": str(e), "request": {"body": body, "params": params}})
        get_highcourt_cases_by_name_wrapper()
        data = {
            "status": True,
            "debugMessage": "Request Received and processing",
            "request": {"body": body, "params": params}
        }
        return jsonify({"status": True, "debugMessage": "Received", "data": data})


if __name__ == "__main__":
    app.run(debug=True, port=4000)
