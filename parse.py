import requests
from bs4 import BeautifulSoup as BS


r = requests.get("https://www.ksma.ru/sveden/education/eduAccred/")
html = BS(r.content, "html.parser")


for el in html.select("table table-bordered table-condensed table-scroll-thead"):
    title = el.select("eduName")
    print(title[0].text)