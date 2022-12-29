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

LAST_NEWS_PAGE = "https://championat.asia/oz/"
PAGINATION_URL = 'https://championat.asia/oz/?page={}&per-page=25'
BASE_URL = "https://championat.asia"
headers = {
    "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_post_detail(link: str) -> dict:
    post_info: dict = {}

    req = session.get(link, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')
    main_div = soup.find("div", class_="news-summary-block")
    # ----  title  ---- //
    title = main_div.find("h1", class_="main-link")
    post_info['title'] = title.text.strip()
    # // ----  title  ----

    # ---- main image ---- //
    main_image = None

    if main_div:
        _main_image = main_div.find('img')
        if _main_image:
            try:
                main_image = encoder_utf_8(_main_image['src'])
            except:
                pass
    post_info['main_image'] = main_image
    # // ---- main image ----

    # --- tags ---- //
    tag_div = soup.find("div", class_="tags")
    _tags = tag_div.find_all('a')
    if _tags:
        tags = [
            {
                'name': tag.text.strip(),
                'url': BASE_URL + encoder_utf_8(tag['href'])
            }
            for tag in _tags
        ]
        post_info['tags'] = tags
    # // ----  tags  ----

    # ---- summary ---- //
    summary = None
    try:
        _summary = soup.find("div", class_="summary")
        if _summary:
            summary = _summary.text
    except:
        pass
    post_info['summary'] = summary
    # // ----  summary  ----

    description_detail = soup.find("div", class_="details")
    # ---- texts and images ---- //
    _all_p = description_detail.find_all('p')
    text = ""
    images = []
    if _all_p:
        for p in _all_p:
            img = p.find('img')
            if img:
                try:
                    images.append(encoder_utf_8(img['src']))
                except:
                    pass
            text += p.text.strip()
    post_info['text'] = text
    post_info['images'] = images
    # // ----  texts & images  ----

    # ---- video ---- // # TO DO
    main_video = None
    video_div = soup.find("div", class_="video-js")
    if video_div:
        main_video = encoder_utf_8(video_div['href'])
    post_info["main_video"] = main_video
    return post_info


link = "https://championat.asia/oz/news/instagram-messi-ronalduni-maglub-etdi-navbat-tuhumga"
# link = "https://championat.asia/oz/news/ueyn-runi-mbappe-messi-va-ronaldu-darajasiga-chiqishi-uchun-myu-yoki-realga-otishi-kerak"
# link = "https://championat.asia/oz/news/final-argentina-franciya-asosiy-tarkiblar-malum?utm_source%5B0%5D="
# link = "https://championat.asia/oz/news/jch-2022-final-argentina-franciya-33-penaltilar-seriyasi-42"
# link = "https://championat.asia/oz/news/jch-2022-xorvatiya-marokash-00-matnli-translyaciya"
# result = get_post_detail(link=link)
# print(result)


months = {
    'yan': 1,
    'fev': 2,
    'mar': 3,
    'apr': 4,
    'may': 5,
    'iyu': 6,
    'iyu': 7,
    'avg': 8,
    'sen': 9,
    'okt': 10,
    'noy': 11,
    'dek': 12
}


def collect_new_links(last_date: datetime) -> List[str]:
    req = session.get(LAST_NEWS_PAGE, headers=headers)
    links = []
    error_counter = 0
    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        _news_layout = soup.find('div', class_='news-list')
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
                    news_blocks = soup.find_all('div', class_='news-list-item')
                    page += 1
                else:
                    load_more = False
                    flag = False
                    break
            else:
                news_blocks = _news_layout.find_all('div', class_='news-list-item')
            if not news_blocks:
                load_more = False
                flag = False
                break
            for news_block in news_blocks:
                try:
                    main_link = news_block.find('a', 'main-link')
                    url = encoder_utf_8(BASE_URL+main_link['href'])
                    date_block = news_block.find('div', class_='info')

                    full_date_regex = '([\d]{2}) ([\w]{3}) ([\d]{4})'
                    _res_date = re.search(full_date_regex, date_block.text)
                    if _res_date is not None:
                        _res = _res_date.groups()
                        _date: list = [int(_res[2]), months[_res[1]], int(_res[0])]
                    else:
                        date_regex = '([\d]{2}) ([\w]{3})'
                        _res = re.search(date_regex, date_block.text).groups()
                        _date: list = [datetime.today().year, months[_res[1]], int(_res[0])]

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
            save_last_date('championat', new_last_date.timestamp())
    return links
