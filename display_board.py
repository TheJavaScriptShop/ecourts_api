from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import time
from selenium.webdriver.chrome.options import Options

import traceback
import datetime
import time

def selenium_click_xpath(driver, xpath):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, xpath))).click()


def get_table_data_as_list(driver, xpath):
    rows = []
    table = driver.find_element(by="xpath", value=xpath)
    for row in table.find_elements(by="xpath", value='.//tr'):
        rows.append(
            [td.text for td in row.find_elements(by="xpath", value=".//td")])
    return rows

def main():
    options = Options()
    DRIVER_PATH = '/usr/local/bin/chromedriver'
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--headless")

    # Change desire location of the downloaded file
    prefs = {
        "browser.helperApps.neverAsk.saveToDisk" : "application/octet-stream;application/vnd.ms-excel;text/html;application/pdf",
        "pdfjs.disabled" : True,
        "print.always_print_silent" : True,
        "network.proxy.autoconfig_url.include_path" : True,
        "print.show_print_progress": False,
        "browser.download.show_plugins_in_list": False,
        "browser.download.folderList": 2,
        "download.default_directory": '/Users/chetnasingh/Desktop/arbito' 
    }
    
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(executable_path=DRIVER_PATH,chrome_options=options)

    driver.get('https://tshc.gov.in/')
    print("accessed website")
    # Cause list
    selenium_click_xpath(driver,'/html/body/header/div[2]/div/div/div/div/div[2]/ul/li[2]/a')
    
    # Live Status of Cause list 
    selenium_click_xpath(driver,'/html/body/form/center/div/div/div[1]/div/input[6]')
    print("live status of cause list button clicked")

    driver.implicitly_wait(1)

    cause_list = get_table_data_as_list(driver,"/html/body/div[2]/form/center/table")
    status_on_leave = 'ON LEAVE'
    status_uploaded = "UPLOADED"

    for  idx, item in enumerate(cause_list) :
        if idx > 0:
            try:
                if  item[2] == status_on_leave:
                    print("No data for this case")
                else:
                    selenium_click_xpath(driver,'/html/body/div[2]/form/center/table/tbody/tr['+str(idx)+']/td[5]/a')
                    time.sleep(2)
                    print("Downloaded data for id", item[0])
                    
            except Exception as e:
                print("Error for ID ", item, e )

        else :
            print("No data for this case")

    data = {
        "noOfRecords": len(cause_list) ,
    }

    print("done")
    print(data)

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