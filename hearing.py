from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
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


# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def remove_noise(image):
    return cv2.medianBlur(image, 5)


def selenium_click_xpath(driver, xpath):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).click()


def selenium_send_keys_xpath(driver, xpath, text):
    WebDriverWait(driver, 40).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).send_keys(text)


def selenium_send_keys_id(driver, id, text):
    WebDriverWait(driver, 40).until(EC.element_to_be_clickable(
        (By.ID, id))).send_keys(text)


def selenium_get_text_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).text


def selenium_get_element_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).click()

def selenium_get_element_id(driver, id):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.ID, id)))

def selenium_find_element_css_selector(driver, selector):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, selector)))

def selenium_click_id(driver, id):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.ID, id))).click()
    
def selenium_click_class(driver, classname):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.CLASS_NAME, classname))).click()



def get_table_data_as_list(driver, xpath):
    rows = []
    table = driver.find_element(by="xpath", value=xpath)
    for row in table.find_elements(by="xpath", value='.//tr'):
        rows.append(
            [td.text for td in row.find_elements(by="xpath", value=".//td")])
    return rows

def main():
    options = Options()
    profile = webdriver.FirefoxProfile()
    # options.add_argument("--headless")
    # options.headless = True
    driver = webdriver.Firefox(service=Service(
        GeckoDriverManager().install()), options=options ,firefox_profile=profile)
    profile.set_preference("print.always_print_silent", True)
    profile.update_preferences()
    adv_name='S Niranjan Reddy'
    driver.get('https://tshc.gov.in/')
    print("accessed website")
    # Cause list
    selenium_click_class(driver,'data-hover')
    print("hypelink clicked")
    driver.get('https://tshc.gov.in/Hcdbs/search.do')
    print("Entered next page")
    # Daily list button
    selenium_click_xpath(driver,'/html/body/form/center/div/div/div[1]/div/input[1]')
    print("daily list button clicked")
    time.sleep(5)
    # Cause list date
    cause_list_date= Select(selenium_get_element_id(driver ,'listdate'))
    cause_list_date.select_by_value('2022-08-26')
    print("Date selected")
    # Advocate wise button
    driver.get('https://tshc.gov.in/Hcdbs/searchdates.do')
    print("entered advocate wise page")
    selenium_click_xpath(driver,'/html/body/center/form/div/div/div/input[4]')
    print("Advocate wise button clicked")
    # Advocate wise name
    driver.get('https://tshc.gov.in/Hcdbs/searchtypeinput.do')
    selenium_send_keys_xpath(driver, '/html/body/center/form/div/div/div/div/input[1]', adv_name)
    print("names sent")
    time.sleep(5)
    # Submit button of advocate wise name
    selenium_click_xpath(driver, '/html/body/center/form/div/div/div/div/input[2]')
    print("executed upto submit")
    time.sleep(5)
    # Fetching table data
    # driver.get('https://tshc.gov.in/Hcdbs/cause_list.jsp')
    time.sleep(5)
    #driver= webdriver.Firefox(GeckoDriverManager().install(),firefox_profile=profile)
    driver.get('https://tshc.gov.in/Hcdbs/cause_list.jsp')
    driver.execute_script('window.print();')
    time.sleep(10)
    # driver.quit()
    # selenium_click_xpath(driver,'/html/body/center/input')
    # print('print button clicked')
    # court_details_list= get_table_data_as_list(driver,'/html/body/table/tbody[2]')
    # print("done fetching")
    # print(court_details_list)

    # data = {
    #     "table data": court_details_list,
    #     }
    # print(data)
    # page = "scrape2.html"
    # with open(page, "w+", newline="", encoding="UTF-8") as f:
    #     f.write("<html><body><pre id='json'></pre></body></html>")
    #     f.write("<script>")
    #     f.write(
    #         f"document.getElementById('json').textContent = JSON.stringify({json.dumps(data)}, undefined, 2);")
    #     f.write("</script>")
    # webbrowser.open('file://' + os.path.realpath(page), new=2)

    driver.close()
    driver.quit()


if __name__ == "__main__":
    try:
        start = datetime.datetime.now()
        main()
    except Exception as e:
        print(traceback.format_exc())
        print(str(e))
    finally:
        end = datetime.datetime.now()
        total = end - start
        print(total.seconds)
