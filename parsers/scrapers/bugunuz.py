from datetime import datetime
from time import sleep
from typing import List
import requests
from urllib import parse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from parsers.models import NewsLinks
import logging
import re

from parsers.scrapers.utils import save_last_date

logger = logging.getLogger('parsers')
logger.setLevel('INFO')

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
PAGINATION_URL = 'https://bugun.uz/category/yangiliklar/page/{}/'
LAST_NEWS_PAGE = 'https://bugun.uz/category/yangiliklar/?_rstr_nocache=rstr68363aa5a7f9a4ec'
BASE_URL = 'https://bugun.uz'


def get_post_detail(link: str) -> dict:
    post_info: dict = {}

    req = session.get(link, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')

    # ----  title  ---- //
    title = soup.find('div', class_='blog__header').find("h1")

    post_info['title'] = title.text
    # // ----  title  ----

    body = soup.find("div", class_="blog__body")

    # ---- images and texts ---- //
    images = []
    text = ""
    _all_p = body.find_all("p")
    _all_figures = body.find_all("figure", class_="wp-caption")
    if _all_p:
        for p in _all_p:
            text += p.text + "\n"
    post_info["text"] = text
    if _all_figures:
        for _figure in _all_figures:
            _image = _figure.find("img")
            images.append(encoder_utf_8(_image["data-src"]))
    post_info["images"] = images

    # // ---- main ----

    return post_info


# link = "https://bugun.uz/2022/12/03/pelega-otkir-respirator-infektsiya-tashxisi-qoyildi/"
# link = "https://bugun.uz/2022/11/22/jch-2022-argentina-saudiya-arabistoniga-sensatsion-tarzda-maglub-boldi-video/"
link = "https://bugun.uz/2022/11/21/stadion-uzra-parvoz-qilayotgan-talisman-ulkan-kubok-bilan-suratga-tushayotgan-muxlis-tuya-mingan-politsiyachilar-jahon-chempionati-ochilishi-suratlarda/"


# link = "https://bugun.uz/2022/12/23/saudiya-arabistoni-kompaniyasi-qoraqalpogistonda-1500-mvtlik-shamol-elektr-stantsiyasi-quradi/"
# result = get_post_detail(link=link)
# print(result)

def collect_new_links(last_date: datetime) -> List[str]:
    req = session.get(LAST_NEWS_PAGE, headers=headers)
    _date = []
    links = []
    error_counter = 0
    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        _news_layout = soup.find('div', class_='main')
        flag = True
        load_more = False
        new_last_date = None
        page = 2
        while flag:
            news_blocks = None
            if load_more:
                sleep(0.3)
                next_page_url = PAGINATION_URL.format(page)
                req = session.get(next_page_url, headers=headers)
                if 200 <= req.status_code < 300:
                    soup = BeautifulSoup(req.content, 'html.parser')
                    news_blocks = soup.find_all('div', class_='post')
                    page += 1
                else:
                    load_more = False
                    flag = False
                    break
            else:
                news_blocks = _news_layout.find_all('div', class_='post')
            if not news_blocks:
                load_more = False
                flag = False
                break
            for news_block in news_blocks:
                try:
                    main_link = news_block.find('a')
                    url = encoder_utf_8(main_link['href'])
                    date_block_div = news_block.find('div', class_='post__top')
                    date_block = date_block_div.find_all('span')[0]

                    full_date_regex = '([\d]{2}).([\d]{2}).([\d]{4})'
                    _res_date = re.search(full_date_regex, date_block.text).groups()
                    _date: list = [int(_res_date[2]), int(_res_date[1]), int(_res_date[0])]

                    time_regex = '([\d]{2}):([\d]{2})'
                    _res_time = re.search(time_regex, date_block.text).groups()

                    if len(_res_time) == 2:
                        is_digits = all([i.isdigit() for i in _res_time])

                        if is_digits:
                            hour, minute = _res_time
                            _date.append(int(hour))
                            _date.append(int(minute))
                    date_time = datetime(*_date)

                    if date_time > last_date:
                        if url not in links:
                            links.append(url)
                        if not new_last_date:
                            new_last_date = date_time
                        load_more = True
                    else:
                        load_more = False
                        flag = False
                        break
                except Exception as e:
                    error_counter += 1
                    if error_counter > 10:
                        flag = False
                        load_more = False
                        break
                    logger.error(e)

        if new_last_date:
            save_last_date('bugunuz', new_last_date.timestamp())
    return links
