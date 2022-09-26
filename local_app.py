from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import Select
from flask import Flask, jsonify

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


def main(advoc_name, high_court_id, bench_id):
    options = Options()
    DRIVER_PATH = '/Users/pp/Downloads/chromedriver'
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1700x800")
    options.add_argument("--headless")

    driver = webdriver.Chrome(DRIVER_PATH, chrome_options=options)
    driver.maximize_window()
    data = {}
    try:
        data = get_highcourt_cases_by_name(
            driver, advoc_name, high_court_id, bench_id)
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


if __name__ == "__main__":
    start = datetime.datetime.now()
    try:
        advoc_name = 'V Aneesh'
        high_court_id = '29'
        bench_id = '1'

        main(advoc_name, high_court_id, bench_id)
    except Exception as e:
        print(traceback.format_exc())
        print(str(e))
    finally:
        end = datetime.datetime.now()
        total = end - start
        print(total.seconds)

app = Flask(__name__)


@app.route("/", methods=["POST"])
def main():
    return jsonify({"status": True, "debugMessage": "Received"})


if __name__ == "__main__":
    app.run(debug=True, port=4000)
