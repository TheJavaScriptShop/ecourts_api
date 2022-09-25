import logging
import os
import json
import time

import azure.functions as func
from selenium import webdriver

from .scrappers.highcourts import get_highcourt_cases_by_name


__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))


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
        if not req_body.get("stateCode"):
            is_valid_request = False
        if not req_body.get("benchCode"):
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
        data = get_highcourt_cases_by_name(driver, req_body.get(
            "advoc_name"), req_body.get("state_code"), req_body.get("bench_code"))
        return func.HttpResponse(json.dumps(data))
    return func.HttpResponse(
        body=json.dumps(
            {"status": False, "debugMessage": "Method not supported"}),
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
