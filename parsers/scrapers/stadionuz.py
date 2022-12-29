from datetime import datetime
import re
from typing import List
import requests
from urllib import parse
from bs4 import BeautifulSoup

from parsers.models import NewsLinks
from parsers.scrapers.utils import extract_dates, save_last_date
import logging

logger = logging.getLogger('parsers')
logger.setLevel('INFO')


encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

LAST_NEW_PAGE = 'https://stadion.uz/uz/news'
BASE_URL = "https://stadion.uz"


def get_post_detail(link: str) -> dict:
    post_info: dict = {}

    req = requests.get(link)
    soup = BeautifulSoup(req.text, 'html.parser')

    # ----  title  ---- //
    title = soup.find("h1", class_="newstitle").text
    post_info['title'] = title
    # // ----  title  ----

    # ----  main image  ---- //
    main_img = None
    main_img_ = soup.find("img", id="news_img")
    if main_img_:
        main_img = f'{BASE_URL}{main_img_["src"]}'
    post_info["main_img"] = main_img
    # // ----  main image  ----

    # ----  texts & images  ---- //
    news_body = soup.find("div", id="news_container")
    _all_p: object = news_body.find_all('p')
    text: str = ""
    images = []
    if _all_p:
        for p in _all_p:
            img = p.find('img')
            if img:
                images.append(img['src'])
            text += p.text + '\n'
    post_info['text'] = text
    post_info['images'] = images
    # // ----  texts & images  ----

    _tags = soup.find("div", id="middle_section").find_all("a")[:3]
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

    # ---- videos ---- // TODO
    return post_info


# link = "https://stadion.uz/uz/news/detail/361736"
# link = 'https://stadion.uz/uz/news/detail/361873'
# link = "https://stadion.uz/uz/news/detail/361864"
link = "https://stadion.uz/uz/news/detail/361858"
# link = "https://stadion.uz/uz/news/detail/361852"
# link = "https://stadion.uz/uz/news/detail/361811"
# link = "https://stadion.uz/uz/news/detail/361781"
# result = get_post_detail(link=link)
# print(result)


def collect_new_links(last_date: datetime) -> List[str]:
    # page juda betartib, newslar alohida divlarga olinmagan hammasi 1 ta umumiy divda va bir-biridan ajratib bomiydi
    new_last_date = None
    req = requests.get(LAST_NEW_PAGE)
    links = []
    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        _news_layout = soup.find('div', class_='posts news-list')
        flag = True
        load_more = False
        new_last_date = None
        while flag:
            news_blocks = None
            if load_more:
                load_more_link = _news_layout.find('a', class_='next')['href']
                req = requests.get(encoder_utf_8(BASE_URL+load_more_link))
                if 200<= req.status_code < 300:
                    soup = BeautifulSoup(req.content, 'html.parser')
                    _news_layout = soup.find('div', class_='leftContainer')
                    news_blocks = _news_layout.find_all('div', class_='nblock')
                else:
                    load_more = False
                    flag = False
                    break
            else:
                news_blocks = _news_layout.find_all('div', class_='nblock')
            if not news_blocks:
                break
            for news_block in news_blocks:
                try:
                    a = news_block.find('a', class_='nimg')
                    url = encoder_utf_8(BASE_URL+a['href'])
                
                    _date: list = extract_dates(url)
                    time_block = news_block.find('div', class_='ndt')
                    date_str = time_block.text.strip()
                    time_regex = '([\d]{2}):([\d]{2})'
                    _res_time = re.search(time_regex, date_str).groups()
                    
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
                    logger.error(e)
    if new_last_date:
        save_last_date('gazeta', new_last_date.timestamp())
    return links
