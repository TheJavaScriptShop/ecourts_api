import ipdb
import requests
from bs4 import BeautifulSoup
from lxml import etree

URL = "https://hcservices.ecourts.gov.in/hcservices/main.php"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")
dom = etree.HTML(str(soup))
print(dom)
print(dom.xpath('//*[@id="captcha_image"]')[0].text)
ipdb.set_trace()
