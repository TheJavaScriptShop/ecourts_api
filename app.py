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

from WebHandler.scrappers.highcourts import get_highcourt_cases_by_name

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
    body = request.json
    params = request.args
    data = {}
    print(request.method)
    if request.method != 'POST':
        data = {"status": False, "debugMessage": "Method not supported"}
        logger.info(data)
        return jsonify(data)

    is_valid_request = True
    if request.args.get('method') == "advocatecasesbyname":
        if not body.get("advocateName"):
            is_valid_request = False
        if not body.get("highCourtId"):
            is_valid_request = False
        if not body.get("benchCode"):
            is_valid_request = False
        if not body.get("callBackUrl"):
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
        @ fire_and_forget
        def get_highcourt_cases_by_name_wrapper():
            try:
                chrome_driver = create_driver()
                data = get_highcourt_cases_by_name(
                    chrome_driver, body["advocateName"], body["highCourtId"], body["benchCode"], __location__)
                chrome_driver.close()
                chrome_driver.quit()
                requests.post(url=body["callBackUrl"], timeout=10, json={
                              "data": data, "request": {"body": body, "params": params}})
            except Exception as e:
                logger.info(str(e))

        get_highcourt_cases_by_name_wrapper()
        data = {
            "status": True,
            "debugMessage": "Request Received and processing",
            "request": {"body": body, "params": params}
        }

    return jsonify({"status": True, "debugMessage": "Received", "data": data})


if __name__ == "__main__":
    app.run(debug=True, port=4000)
