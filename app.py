from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import Select
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

from WebHandler.scrappers.highcourts import get_highcourt_cases_by_name


app = Flask(__name__)


@app.route("/", methods=["POST"])
def main():
    body = request.json
    print(body)
    options = Options()
    DRIVER_PATH = '/Users/sarvani/Downloads/chromedriver'
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1700x800")
    options.add_argument("--headless")
    __location__ = "Users/sarvani/Desktop/arbito"
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
    data = {}
    try:
        data = get_highcourt_cases_by_name(
            driver, body["advocateName"], body["highCourtId"], body["benchCode"], __location__)
    except Exception as e:
        print(str(e))

    print(data)
    json_data = json.dumps(data)
    page = "scrape.json"
    with open(page, "w+", newline="", encoding="UTF-8") as file:
        file.write(json_data)

    page = "scrape1.html"
    with open(page, "w+", newline="", encoding="UTF-8") as f:
        f.write("<html><body><pre id='json'></pre></body></html>")
        f.write("<script>")
        f.write(
            f"document.getElementById('json').textContent = JSON.stringify({json.dumps(data)}, undefined, 2);")
        f.write("</script>")
    webbrowser.open('file://' + os.path.realpath(page), new=2)

    driver.close()
    driver.quit()
    return jsonify({"status": True, "debugMessage": "Received"})


if __name__ == "__main__":
    app.run(debug=True, port=4000)
