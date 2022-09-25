import logging
import os
import json
import time

import azure.functions as func
from selenium import webdriver

from .scrappers.highcourts import get_highcourt_cases_by_name


__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))


def main(req: func.HttpRequest) -> func.HttpResponse:
    """ Main function for Azure Function """
    logging.info(req)
    logging.info('Called ECourts Service.')
    logging.info(time.ctime())
    if (req.method.lower() != "post"):
        return func.HttpResponse(
            body=json.dumps(
                {"status": False, "debugMessage": "Method not supported"}),
            status_code=200
        )

    req_body = req.get_json()
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
