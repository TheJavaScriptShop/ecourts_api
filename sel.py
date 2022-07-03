import ipdb
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import base64
from pytesseract import pytesseract
from PIL import Image
import re


def selenium_click_xpath(driver, xpath):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).click()


def selenium_send_keys_xpath(driver, xpath, text):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).send_keys(text)


def selenium_get_text_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).text


def get_text_from_captcha(driver, img_path):
    img = Image.open(img_path)
    text = pytesseract.image_to_string(img)
    match = re.search(r'\(?([0-9A-Za-z]+)\)?', text)
    print(text)
    img_xpath = '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[1]/a/img'
    if match is None:
        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        #     (By.XPATH, img_xpath))).click()
        selenium_click_xpath(driver, img_xpath)
        get_captcha(driver)
        return get_text_from_captcha(driver, img_path)
    else:
        print(match.group(1))
        if (len(match.group(1)) != 6):
            # WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            #     (By.XPATH, img_xpath))).click()
            selenium_click_xpath(driver, img_xpath)
            get_captcha(driver)
            return get_text_from_captcha(driver, img_path)
    return match.group(1)


def get_captcha(driver):

    img_base64 = driver.execute_script("""
    var ele = arguments[0];
    var cnv = document.createElement('canvas');
    cnv.width = ele.width + 100; cnv.height = ele.height + 100;
    cnv.getContext('2d').drawImage(ele, 0, 0);
    return cnv.toDataURL('image/jpeg').substring(22);
    """, WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="captcha_image"]'))))

    with open(r"image.png", 'wb') as f:
        f.write(base64.b64decode(img_base64))


def main():
    options = Options()
    options.add_argument("--headless")
    options.headless = True
    driver = webdriver.Firefox(service=Service(
        GeckoDriverManager().install()), options=options)
    driver.get('https://hcservices.ecourts.gov.in/hcservices/main.php')
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="cino"]'))).send_keys("HBHC010549632021")
    is_failed_with_captach = True
    while is_failed_with_captach:
        get_captcha(driver)
        text = get_text_from_captcha(driver, r"image.png")
        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        #     (By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[2]/label"))).click()
        selenium_click_xpath(
            driver, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[2]/label")
        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        #     (By.XPATH, '//*[@id="captcha"]'))).send_keys(text)
        selenium_send_keys_xpath(driver, '//*[@id="captcha"]', text)

        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        #     (By.XPATH, '//*[@id="searchbtn"]'))).click()
        selenium_click_xpath(driver, '//*[@id="searchbtn"]')

        try:
            # failure_text = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            #     (By.XPATH, '//*[@id="errSpan"]/p'))).text
            failure_text = selenium_get_text_xpath(
                driver, '//*[@id="errSpan"]/p')
            if failure_text == 'THERE IS AN ERROR':
                is_failed_with_captach = True
        except:
            is_failed_with_captach = False
            case_title = selenium_get_text_xpath(
                driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[52]/div[2]/div[1]/div/table/tbody/tr[1]/td[2]')
            print(case_title)
    driver.close()
    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e.__str__())
