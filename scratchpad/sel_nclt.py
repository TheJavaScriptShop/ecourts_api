from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
# import base64
import os
import json
import webbrowser
import traceback
import datetime


def selenium_click_xpath(driver, xpath):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).click()


def selenium_send_keys_xpath(driver, xpath, text):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).send_keys(text)


def selenium_get_text_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).text


def selenium_get_element_xpath(driver, xpath):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath)))


def get_table_data_as_list(driver, xpath):
    rows = []
    table = driver.find_element(by="xpath", value=xpath)
    for row in table.find_elements(by="xpath", value='.//tr'):
        rows.append(
            [td.text for td in row.find_elements(by="xpath", value=".//td")])
    return rows


def main():
    options = Options()
    options.add_argument("--headless")
    options.headless = True
    driver = webdriver.Firefox(service=Service(
        GeckoDriverManager().install()), options=options)
    # bench = Hyd | advocate name = V Aneesh | year = 2020
    page_no = 1
    total_case_list = []
    status = True
    while status:
        driver.get(
            f"https://nclt.gov.in/advocate-name-wise-search?bench=aHlkZXJhYmFk&advocate_name=ViBBbmVlc2g=&year=MjAyMA==&page={page_no}")
        case_list = get_table_data_as_list(
            driver, '/html/body/div/div[2]/div/div/div[2]/div/div/div/div/div/div[2]/table')
        if ("Please click here" in case_list[1][0]):
            status = False
        else:
            page_no += 1
            total_case_list.extend(case_list[1:])
    data = {
        "case_list": total_case_list,
    }
    print(data)
    page = "scrape_nclt.html"
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
