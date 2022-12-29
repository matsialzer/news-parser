from datetime import datetime
import re
from requests.adapters import HTTPAdapter, Retry
from parsers.models import NewsLinks
from bs4 import BeautifulSoup
from urllib import parse
from typing import List
import requests

from parsers.scrapers.utils import extract_dates, save_last_date


encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

LAST_NEW_PAGE = 'https://aniq.uz/uz/yangiliklar'
PAGINATION_URL = 'https://aniq.uz/uz/yangiliklar?page={}'
BASE_URL = "https://www.aniq.uz"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_post_detail(link: str) -> dict:
    post_info: dict = {}

    req = session.get(link, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')

    # ----  title  ---- //
    title = soup.find('h1', class_='news-item_name')
    post_info['title'] = title.text.strip()
    # // ----  title  ----

    # ---- main image ---- //
    main_image = None
    main_img_div = soup.find("div", class_="news-item_img")

    if main_img_div:
        _main_image = main_img_div.find('img')
        if _main_image:
            try:
                main_image = f"{BASE_URL}{encoder_utf_8(_main_image['src'])}"
            except:
                pass
    post_info['main_image'] = main_image
    # // ---- main image ----

    # ---- texts & images ---- //
    text = ""
    images = []
    _all_p = soup.find("div", "news-item_text").find_all('p')
    if _all_p:
        for p in _all_p:
            try:
                img = p.find('img')
                if img:
                    images.append(encoder_utf_8(img['src']))
            except:
                pass
            text += p.text + '\n'
    post_info['text'] = text
    post_info['images'] = images
    # // ----  texts & images  ----

    # ----  tags  ---- //
    tags_div = soup.find("div", class_="pull-left")
    _tags = tags_div.find_all('a')
    if _tags:
        tags = [
            {
                'name': tag.text,
                'url': encoder_utf_8(tag['href'])
            }
            for tag in _tags
        ]
        post_info['tags'] = tags
    # // ----  tags  ----

    return post_info


# link = "https://aniq.uz/uz/yangiliklar/putin-minskka-etib-keldi"
link = "https://aniq.uz/uz/yangiliklar/jch-finalidagi-maglubiyatdan-sung-fransiyada-tartibsizliklar-boshlanib-ketdi"
# link = "https://aniq.uz/uz/yangiliklar/jch-2022-argentina-fransiya-uchrashuvi-asosiy-tarkiblari-malum"
# result = get_post_detail(link=link)
# print(result)


def collect_new_links(last_date: datetime) -> List[str]:
    new_last_date = None
    has_next_page = True
    links = []
    for i in range(1, 11000):
        if not has_next_page:
            break
        req = requests.get(f'https://aniq.uz/uz/yangiliklar?page={i}')
        if req.status_code == 200:
            soup = BeautifulSoup(req.text, 'html.parser')
            articles = soup.find_all('div', class_='news-list_item')
            for article in articles:
                date = article.find('div', class_='news-item_footer').text.split()
                link = article.find('a').get('href')
                if 'Bugun' in date:
                    time = date[2][:-1]
                    date = datetime.now().strftime('%d-%m-%Y')
                    date = date + ' ' + time
                    date_in_datatime = datetime.strptime(date, '%d-%m-%Y %H:%M')
                else:
                    day = date[2][:-1]
                    time = date[1]
                    date = day + ' ' + time
                    date_in_datatime = datetime.strptime(date, '%d.%m.%Y %H:%M')
                if date_in_datatime > last_date:
                    links.append(link)
                    if not new_last_date:
                        new_last_date = date_in_datatime
                else:
                    has_next_page = False
                    break

    if new_last_date:
        save_last_date('aniq', new_last_date.timestamp())
    return links
