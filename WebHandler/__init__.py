import logging
import os
import json
import time
import requests
import threading

import azure.functions as func
from selenium import webdriver

from .scrappers.highcourts import get_highcourt_cases_by_name


__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))


def fire_and_forget(f):
    def wrapped():
        threading.Thread(target=f).start()

    return wrapped


def main_handler(req: func.HttpRequest) -> func.HttpResponse:
    logging.info(req)
    logging.info('Called ECourts Service.')
    logging.info(time.ctime())
    if (req.method.lower() != "post"):
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": "Method not supported"}),
            status_code=200
        )

    req_body = {}
    try:
        req_body = req.get_json()
    except Exception as e_exception:
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": str(e_exception)}),
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
                {"status": False, "debugMessage": "Method not supported"}),
            status_code=200
        )

    if not is_valid_request:
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": "Insufficient parameters"}),
            status_code=200
        )

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--window-size=1700x800")

    driver = webdriver.Chrome(
        "/usr/local/bin/chromedriver", chrome_options=chrome_options)

    if req_params.get("method") == "advocatecasesbyname":
        @fire_and_forget
        def get_highcourt_cases_by_name_wrapper():
            data = get_highcourt_cases_by_name(driver, req_body.get(
                "advocateName"), req_body.get("highCourtId"), req_body.get("benchCode"))
            try:
                requests.post(url=req_body.get("callBackUrl"), timeout=10, json=json.dumps(
                    {"status": data["status"], "data": data["data"], "request": {"body": req_body, "params": req_params}}))
            except:
                pass
        get_highcourt_cases_by_name_wrapper()
        return func.HttpResponse(
            body=json.dumps(
                {"status": True, "debugMessage": "Request Received and processing", "request": {"body": req_body, "params": req_params}}),
        )
    return func.HttpResponse(
        body=json.dumps(
            {"status": False, "debugMessage": "Method not supported", "request": {"body": req_body, "params": req_params}}),
        status_code=200
    )


def main(req: func.HttpRequest) -> func.HttpResponse:
    """ Main function for Azure Function """
    try:
        return main_handler(req)
    except Exception as e_exception:
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": str(e_exception)}),
            status_code=200
        )
