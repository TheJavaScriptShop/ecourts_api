from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

from selenium.webdriver.common.action_chains import ActionChains





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
import os
import shutil


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
        (By.XPATH, xpath)))


def selenium_get_element_id(driver, id):
    return WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.ID, id)))


def selenium_get_element_class(driver, classname):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.CLASS_NAME, classname)))


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


def get_text_from_captcha(driver, img_path):
    reader = easyocr.Reader(["en"], gpu=False, model_storage_directory=os.path.join(
        os.getcwd()), download_enabled=False)
    result = reader.readtext(img_path)
    match = re.search(r'\(?([0-9A-Za-z]+)\)?', result[0][1])
    print(result[0][1])
    img_xpath = '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[1]/div[1]/img'
    if match is None:
        selenium_click_xpath(driver, img_xpath)
        get_captcha(driver)
        return get_text_from_captcha(driver, img_path)
    else:
        print(match.group(1))
        if (len(match.group(1)) != 6):
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


def main(advoc_name, high_court_id, bench_id):
    options = Options()
    DRIVER_PATH = '/Users/sarvani/Downloads/chromedriver'
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1700x800")

    options.add_argument("--headless")
    file_path = '/Users/sarvani/Downloads/arbito'
    prefs = {
        "browser.helperApps.neverAsk.saveToDisk" : "application/octet-stream;application/vnd.ms-excel;text/html;application/pdf",
        "pdfjs.disabled" : True,
        "print.always_print_silent" : True,
        "print.show_print_progress": False,
        "browser.download.show_plugins_in_list": False,
        "browser.download.folderList": 2,
        "download.default_directory": file_path, #Change default directory for downloads
        "download.prompt_for_download": False, #To auto download the file
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome

    }
    
    options.add_experimental_option("prefs", prefs)


    driver = webdriver.Chrome(DRIVER_PATH, chrome_options=options)

    


    action = ActionChains(driver)
    is_failed_with_captach = True
    fetched_data = False

    def wait_for_download_and_rename(newFilename):
        def chrome_downloads(drv):
            if not "chrome://downloads" in drv.current_url: 
                drv.execute_script("window.open('');") 
                drv.switch_to.window(driver.window_handles[1]) 
                drv.get("chrome://downloads/")
            return drv.execute_script("""
                return document.querySelector('downloads-manager')
                .shadowRoot.querySelector('#downloadsList')
                .items.filter(e => e.state === 'COMPLETE')
                .map(e => e.filePath || e.file_path || e.fileUrl || e.file_url);
                """)
        dld_file_paths = WebDriverWait(driver, 120, 1).until(chrome_downloads) 
        if "chrome://downloads" in driver.current_url:
            driver.close()
        driver.switch_to.window(driver.window_handles[0]) 
        dlFilename = dld_file_paths[0] 
        time_to_wait = 20 
        time_counter = 0
        while not os.path.isfile(dlFilename):
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                break
        shutil.move(dlFilename, os.path.join(file_path,newFilename))
        return

    while is_failed_with_captach:
        driver.get('https://hcservices.ecourts.gov.in/hcservices/main.php')
        driver.maximize_window()

        selenium_click_id(driver, 'leftPaneMenuCS')
        print("Successfully clicked")
        selenium_click_xpath(driver, '/html/body/div[2]/div/div/div[2]/button')
        time.sleep(2)
        print("ok clicked")
        state_code = Select(selenium_get_element_id(driver, 'sess_state_code'))
        state_code.select_by_value(high_court_id)
        time.sleep(2)
        print("Values selected")
        court_code = Select(selenium_get_element_id(
            driver, 'court_complex_code'))
        court_code.select_by_value(bench_id)
        print("court code selected")
        selenium_click_id(driver, 'CSAdvName')
        print("hypelink clicked")
        selenium_send_keys_xpath(
            driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[14]/div[2]/div[2]/input', advoc_name)
        print("names sent")
        time.sleep(3)

        get_captcha(driver)
        text = get_text_from_captcha(driver, r"image.png")
        time.sleep(3)
        selenium_click_xpath(
            driver, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/span/div/div[2]/label")
        selenium_send_keys_xpath(driver, '//*[@id="captcha"]', text)
        selenium_click_xpath(driver, '//*[@class="Gobtn"]')
        is_failed_with_captach = False
        try:
            failure_text = selenium_get_text_xpath(
                driver, '//*[@id="errSpan1"]')

            if 'THERE IS AN ERROR' in failure_text:
                print("in first")
                is_failed_with_captach = False
        except:
            try:
                failure_text_other_page = selenium_get_text_xpath(
                    driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[26]/p')
                print(failure_text_other_page)
                if 'Record Not Found' in failure_text_other_page:
                    data = {
                        "number_of_establishments_in_court_complex": 0,
                        "number_of_cases": 0,
                        "case_list": [],
                        'case_details': [],
                    }
                    fetched_data = True
                    break
                if "invalid" in failure_text_other_page.lower():
                    is_failed_with_captach = True
                else:
                    print("in second")
                    is_failed_with_captach = False
            except:
                pass

    if not fetched_data:
        try:
            # case details
            number_of_establishments_in_court_complex = selenium_get_text_xpath(
                driver, '//*[@id="showList2"]/div[1]/h3')
            print(number_of_establishments_in_court_complex)
            data = {
                "number_of_establishments_in_court_complex": number_of_establishments_in_court_complex,
                "number_of_cases": 0,
                "case_list": [],
                'case_details': [],
            }
            number_of_cases = selenium_get_text_xpath(
                driver, '//*[@id="showList2"]/div[1]/h4')
            print(number_of_cases)
            data = {
                "number_of_establishments_in_court_complex": number_of_establishments_in_court_complex,
                "number_of_cases": number_of_cases,
                "case_list": [],
                'case_details': [],
            }
            view_element = selenium_get_element_id(driver, 'dispTable')

            driver.execute_script(
                "arguments[0].scrollIntoView();", view_element)

            WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table")))
            # list of case
            case_list = get_table_data_as_list(
                driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table')
            data = {
                "number_of_establishments_in_court_complex": number_of_establishments_in_court_complex,
                "number_of_cases": number_of_cases,
                "case_list": case_list,
                'case_details': [],
            }
            navbar_1 = selenium_get_element_xpath(driver, '/html/body/div[1]/div/nav[1]')
            navbar_2 = selenium_get_element_xpath(driver, '/html/body/div[1]/div/nav[2]')
            driver.execute_script("""
                var element = arguments[0];
                element.parentNode.removeChild(element);
                """, navbar_1)

            driver.execute_script("""
                var element = arguments[0];
                element.parentNode.removeChild(element);
                """, navbar_2)
            case_details = []
            j=1
            for link in driver.find_elements(by="xpath", value='/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table/tbody/tr/td[5]'):
                print(f'case no {j}')
                print('link', link)
                time.sleep(2)
                driver.execute_script(
                    "arguments[0].scrollIntoView();", link)
                WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'someclass')))
                selenium_click_class(link, 'someclass')
                print("view clicked")
                time.sleep(2)
                # details behind the hyperlink
                # case details
                case_details_title = selenium_get_text_xpath(
                    driver, '/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[52]/div[2]/div[1]/div/table/tbody/tr[1]/td[2]')
                case_details_registration_no = selenium_get_text_xpath(
                    driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[2]/td[2]/label')
                case_details_cnr_no = selenium_get_text_xpath(
                    driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[3]/td[2]/strong')
                case_details_filing_date = selenium_get_text_xpath(
                    driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[1]/td[4]')
                case_details_registration_date = selenium_get_text_xpath(
                    driver, '//*[@id="caseBusinessDiv4"]/div/table/tbody/tr[2]/td[4]/label')
                print('case details')
                # case status
                try:
                    case_status_data = get_table_data_as_list(
                        driver, '//*[@id="caseBusinessDiv4"]/table')
                    case_status = {'status': True, 'data': case_status_data}
                    print('case status')

                except:
                    case_status = {'status': False, 'data': {}}
                # paa = petitioned and advocate
                try:
                    case_paa_data = selenium_get_text_xpath(
                        driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/span[1]')
                    case_paa = {'status': True, 'data': case_paa_data}
                    print('paa')

                except:
                    case_paa = {'status': False, 'data': {}}
                # raa = respondent and advocate
                try:
                    case_raa_data = selenium_get_text_xpath(
                        driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/span[2]')
                    case_raa = {'status': True, 'data': case_raa_data}
                    print('raa')

                except:
                    case_raa = {'status': False, 'data': {}}
                # acts
                try:
                    case_acts_data = get_table_data_as_list(
                        driver, '//*[@id="act_table"]')
                    case_acts = {'status': True, 'data': case_acts_data}
                    print('case acts')

                except:
                    case_acts = {'status': False, 'data': {}}
                # history
                try:
                    case_history_data = get_table_data_as_list(
                        driver, '//*[@id="caseHistoryDiv"]/div[2]/div[2]/table[2]')
                    case_history = {'status': True, 'data': case_history_data}
                    print('case history')

                except:
                    case_history = {'status': False, 'data': {}}
                # orders
                try:
                    case_orders_data = get_table_data_as_list(
                        driver, '//table[@class="order_table"]')
                    no_of_orders = len(case_orders_data) - 1
                    orders = selenium_get_element_xpath(driver,'//table[@class="order_table"]')
                    driver.implicitly_wait(5)
                    driver.execute_script(
                        "arguments[0].scrollIntoView();", orders)
                    driver.implicitly_wait(2)
                    print('first scroll')
                
                    i=1
                    for n in range(0,no_of_orders):
                        pdf_xpath = f'//table[@class="order_table"]/tbody/tr[{(n+2)}]/td[5]/a'
                        pdf_element = selenium_get_element_xpath(driver, pdf_xpath)
                        driver.implicitly_wait(5)
                        driver.execute_script(
                            "arguments[0].scrollIntoView();", pdf_element)
                        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
                            (By.XPATH, pdf_xpath)))
                        print('second scroll')
                        
                        driver.execute_script("arguments[0].click();", pdf_element)
                        print('clicked')

                        driver.implicitly_wait(2)
                        pdfname = case_details_title.replace("/", "-")
                        newfilename = f'{pdfname}-{i}.pdf'
                        try:
                            wait_for_download_and_rename(newfilename)
                            print(f'downloaded {i}')
                            i=i+1

                        except Exception as e:
                            print(str(e))

                    case_orders = {'status': True, 'data': case_orders_data, 'number_of_downloaded_files': i-1}
                    print("case orders")  
                except Exception as e:
                    print("error", str(e))
                    case_orders = {'status': False, 'data': {}, 'number_of_downloaded_files': 0}

                # objections
                try:
                    case_objections_data = get_table_data_as_list(
                        driver, '//*[@id="caseHistoryDiv"]/div[3]/table')
                    case_objections = {'status': True,
                                       'data': case_objections_data}
                    print('case details')
            
                except:
                    case_objections = {'status': False, 'data': {}}

                details = {
                    "title": case_details_title,
                    "registration_no": case_details_registration_no,
                    "cnr_no": case_details_cnr_no,
                    "filing_date": case_details_filing_date,
                    "registration_date": case_details_registration_date,
                    "status": case_status,
                    "paa": case_paa,
                    "raa": case_raa,
                    "acts": case_acts,
                    "history": case_history,
                    "orders": case_orders,
                    "objections": case_objections,
                }
                case_details.append(details)
                print(case_details)
                selenium_click_xpath(driver, "/html/body/div[1]/div/p/a")
                time.sleep(2)
                selenium_click_xpath(
                    driver, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[48]/input")
                view_link = selenium_get_element_id(driver, 'dispTable')

                driver.execute_script(
                    "arguments[0].scrollIntoView();", view_link)

                WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/div/div[2]/div[45]/table")))
                j = j+1


            data = {
                "number_of_establishments_in_court_complex": number_of_establishments_in_court_complex,
                "number_of_cases": number_of_cases,
                "case_list": case_list,
                'case_details': case_details,
            }
        except:
            pass

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
    try:
        start = datetime.datetime.now()

        advoc_name = 'V Aneesh'
        # sess_state_code='High Court for State of Telangana'
        # court_complex_code='Principal Bench at Hyderabad'
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
