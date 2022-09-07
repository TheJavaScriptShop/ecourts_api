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
import numpy as np

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
    
def selenium_find_element_xpath(driver, xpath):
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
    # Live Status of Cause list 
    selenium_click_xpath(driver,'/html/body/form/center/div/div/div[1]/div/input[6]')
    print("live status of cause list button clicked")
    time.sleep(5)
    driver.get('https://tshc.gov.in/Hcdbs/online_board.jsp')
    print("entered wise page")
    # m=get_table_data_as_list(driver,'/html/body/div[2]/form/center/table')
    table_data = get_table_data_as_list(driver,"/html/body/div[2]/form/center/table")
    print("working",table_data[2])
    time.sleep(5)
    # table_data[1].location_once_scrolled_into_view
    # driver.execute_script("arguments[0].scrollIntoView();", table_data[2])
    # time.sleep(1)
    # rows=len(selenium_find_element_xpath(driver,"/html/body/div[2]/form/center/table/tbody/tr"))
    # print(rows)
    for table in  get_table_data_as_list(driver,"/html/body/div[2]/form/center/table"):
        i=1
        j=1
        # for row in table:
        selenium_click_xpath(driver,"//*[@id='display']/tbody/tr['+str(i)+']/td[5]/a")
        i=i+1
        print("done")
        driver.get("https://tshc.gov.in/Hcdbs/upload/court['+str(j)+']_20220907.pdf")#iterate using the court number 
        driver.execute_script('window.print();')
        j=j+1
        time.sleep(10)
        #print("dataaaa",data1)
        # for data in  get_table_data_as_list(driver,".//tr"):
        #   print("printing data",data)
        print("printing table",table)
        # doubts(have to ask with Miss.Chetna)
        # m=table
        # a = m.get(1)
    # data = {
    #   "data":m
    #     },
        

    
    print("printing table",table)
    # page = "scrape3.html"
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
