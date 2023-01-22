from parsers.models import NewsLinks
from bs4 import BeautifulSoup
from datetime import datetime
from urllib import parse
from typing import List
import requests
import logging
import re

logger = logging.getLogger('parsers')
logger.setLevel('INFO')

from parsers.scrapers.utils import extract_dates, save_last_date

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

LAST_NEWS_PAGE = 'https://kun.uz/uz/news/list'
BASE_URL = 'https://kun.uz'


def get_post_detail(link: str) -> dict:
    post_info: dict = {}
    try:
        req = requests.get(link)
        soup = BeautifulSoup(req.text, 'html.parser')

        # ----  title  ---- //
        title = soup.find('div', class_='single-header__title')
        post_info['title'] = title.text
        # // ----  title  ----

        _single_content = soup.find('div', class_='single-content')

        # ----  summary  ---- //
        _summary = _single_content.find('h4')
        summary = None
        if _summary:
            summary = _summary.text
        post_info['summary'] = summary
        # // ----  summary  ----

        # ----  main image  ---- //
        main_image = None
        _main_image = _single_content.find('img')
        if _main_image:
            try:
                main_image = encoder_utf_8(_main_image['src'])
            except:
                pass
        post_info['main_image'] = main_image
        # // ----  main image  ----

        # ----  video  ---- //
        _figure = _single_content.find('figure', class_='iframe')
        video = None
        if _figure:
            _iframe = _figure.find('iframe')
            if _iframe:
                video = encoder_utf_8(_iframe['src'])
        post_info['video'] = video

        if not post_info.get('main_image'):
            yt_img_base_url = "https://img.youtube.com/vi/{}/maxresdefault.jpg"
            if post_info.get('video'):
                if "youtube.com" in post_info['video']:
                    yt_video_id = post_info['video'].split('/')[-1]
                    yt_image = yt_img_base_url.format(yt_video_id)
                    post_info['main_image'] = yt_image
        # // ----  video  ----

        # ----  texts & images  ---- //

        images = []
        _all_images = _single_content.find_all('img')
        if _all_images:
            for img in _all_images:
                img_url = img.get('src')
                if img_url:
                    if img_url != main_image:
                        images.append(encoder_utf_8(img_url))

        _all_p = _single_content.find_all('p')
        text = ""
        if _all_p:
            for p in _all_p:
                text += p.text + '\n'
        post_info['text'] = text
        post_info['images'] = images
        # // ----  texts & images  ----

        # ----  tags  ---- //
        _tags = soup.find_all('a', class_='tags-ui__link')
        if _tags:
            tags = [
                {
                    'name': tag.text,
                    'url': BASE_URL + encoder_utf_8(tag['href'])
                }
                for tag in _tags
            ]
            post_info['tags'] = tags
        # // ----  tags  ----
    except Exception as e:
        post_info['errors'] = e
    return post_info


test_link = 'https://kun.uz/uz/news/2022/12/12/ozbekistonning-energiya-inqirozi-xato-qayerda'
# test_link = 'https://kun.uz/uz/news/2022/12/11/hafta-dayjesti'
# test_link = 'https://kun.uz/uz/16388999?yrwinfo=1670905937229984-16160134128308293487-sas2-0256-sas-l7-balancer-8080-BAL-272'
# test_link = 'https://kun.uz/uz/news/2022/12/12/insoniyatga-qoyilgan-haykal-qatardagi-eng-noodatiy-yodgorlik-haqida?yrwinfo=1670900604410739-13459442102725763044-sas2-0119-sas-l7-balancer-8080-BAL-1870'
# test_link = 'https://kun.uz/uz/news/2022/12/12/ozbekneftgaz-shoxobchalarida-benzin-narxi-tushiriladi'

# res = get_post_detail(test_link)
# print(res)


def collect_new_links(last_date: datetime=None) -> List[str]:
    req = requests.get(LAST_NEWS_PAGE)
    links = []
    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        _news_layout = soup.find('div', id='news-list')
        flag = True
        load_more = False
        new_last_date = None
        while flag:
            news_blocks = None
            if load_more:
                break
                load_more_link = soup.find('a', class_='load-more__link')
                req = requests.get(encoder_utf_8(BASE_URL+load_more_link['href']))
                if 200 <= req.status_code < 300:
                    soup = BeautifulSoup(req.content, 'html.parser')
                    _news_layout = soup.find('div', id='news-list')
                    news_blocks = _news_layout.find_all('a', class_='daily-block')
                else:
                    load_more = False
                    flag = False
                    break
            else:
                news_blocks = _news_layout.find_all('a', class_='daily-block')
            if not news_blocks:
                break
            for news_block in news_blocks:
                try:
                    url = encoder_utf_8(BASE_URL+news_block['href'])

                    _date: list = extract_dates(url)
                    time_block = news_block.find('p', class_='news-date')
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
                    yield (url, date_time)
                    # if date_time > last_date:
                    #     if url not in links:
                    #         links.append(url)
                    #     if not new_last_date:
                    #         new_last_date = date_time
                    #     load_more = True
                    # else:
                    #     load_more = False
                    #     flag = False
                    #     break
                except Exception as e:
                    logger.error(e)
            break
        if new_last_date:
            save_last_date('kun', new_last_date.timestamp())
    return links