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
__location__ = os.environ.get('DOWNLOAD_PATH')


def create_driver():
    options = Options()
    DRIVER_PATH = os.environ.get('DRIVER_PATH')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    # options.add_argument("--headless")
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

    permitted_cases = 10
    total_cases = 0
    data = {}

    is_valid_request = True

    chrome_driver = create_driver()

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

        @ fire_and_forget
        def get_total_no_of_cases_wrapper():
            try:
                case_details = get_no_of_cases(
                    chrome_driver, body["advocateName"], body["highCourtId"], body["benchCode"])
                total_cases = int(case_details["number_of_cases"][23:])
                logger.info({"total_cases": total_cases})
                if total_cases <= permitted_cases:
                    data = get_highcourt_cases_by_name(
                        chrome_driver, __location__)
                else:
                    logger.info("entered else")
                    n = total_cases/permitted_cases
                    logger.info({"n": n})
                    start = 0
                    stop = permitted_cases
                    while (n > 0):
                        logger.info({"n inside while": n})
                        logger.info("about to request")
                        body["start"] = start
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
                        logger.info("requested")
                        start = start + permitted_cases
                        stop = stop + permitted_cases
                        n = n-1
            except Exception as e:
                logger.info(str(e))

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
        logger.info("url request made")

        @fire_and_forget
        def get_highcourt_cases_by_name_wrapper():
            try:
                case_details = get_no_of_cases(
                    chrome_driver, body["advocateName"], body["highCourtId"], body["benchCode"])
                data = get_highcourt_cases_by_name(
                    chrome_driver, __location__, body["start"], body["stop"])
            except Exception as e:
                logger.info(str(e))
        get_highcourt_cases_by_name_wrapper()
        data = {
            "status": True,
            "debugMessage": "Request Received and processing",
            "request": {"body": body, "params": params}
        }
        return jsonify({"status": True, "debugMessage": "Received", "data": data})

    # else:
    #     data = {"status": False, "debugMessage": "Method not supported"}
    #     logger.info(data)
    #     return jsonify(data)
    if not is_valid_request:
        data = {"status": False, "debugMessage": "Insufficient parameters"}
        logger.info(data)
        return jsonify(data)
    chrome_driver.close()
    chrome_driver.quit()
    return jsonify({"status": True, "debugMessage": "Received", "data": data})


if __name__ == "__main__":
    app.run(debug=True, port=4000)
