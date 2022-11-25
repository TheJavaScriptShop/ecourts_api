import os
import cv2
import base64
import easyocr
import re

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .sel import selenium_click_xpath


__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))

# get grayscale image


def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def remove_noise(image):
    return cv2.medianBlur(image, 5)


def get_text_from_captcha(driver, img_path, retry_path, captcha_path, logger):
    logger.info("decoding captcha")
    reader = easyocr.Reader(
        ["en"], gpu=False, model_storage_directory=__location__, download_enabled=False)
    result = reader.readtext(img_path)
    match = re.search(r'\(?([0-9A-Za-z]+)\)?', result[0][1])
    if match is None:
        logger.info("retry decoding")
        selenium_click_xpath(driver, retry_path)
        get_captcha(driver, img_path, captcha_path)
        return get_text_from_captcha(driver, img_path, retry_path, captcha_path, logger)
    else:
        if (len(match.group(1)) != 6):
            logger.info("retry decoding")
            selenium_click_xpath(driver, retry_path)
            get_captcha(driver, img_path, captcha_path)
            return get_text_from_captcha(driver, img_path, retry_path, captcha_path, logger)
    logger.info("captcha decoded")
    return match.group(1)


def get_captcha(driver, img_path, captcha_path):
    captcha_element = driver.find_element(By.XPATH, captcha_path)
    # captcha_element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
    #     (By.XPATH, captcha_path)))
    img_base64 = driver.execute_script("""
    var ele = arguments[0];
    var cnv = document.createElement('canvas');
    cnv.width = ele.width + 100; cnv.height = ele.height + 100;
    cnv.getContext('2d').drawImage(ele, 0, 0);
    return cnv.toDataURL('image/jpeg').substring(22);
    """, captcha_element)

    with open(img_path, 'wb') as f:
        f.write(base64.b64decode(img_base64))
