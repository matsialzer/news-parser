from datetime import datetime
import json
import re
from time import sleep
from typing import List
from bs4 import BeautifulSoup
from urllib import parse
import requests

from parsers.models import NewsLinks
from parsers.scrapers.utils import extract_dates, save_last_date
import logging

logger = logging.getLogger('parsers')
logger.setLevel('INFO')

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

LAST_NEWS_PAGE = 'https://qalampir.uz/latest'
BASE_URL = 'https://qalampir.uz'


def get_post_detail(link: str) -> dict:
    post_info = {}
    try:
        req = requests.get(link)
        soup = BeautifulSoup(req.content, 'html.parser')

        # _main_content = soup.find('div', class_='article')
        _main_content = soup.find('main', class_='article')

        # ----  title  ---- //
        title = _main_content.find('h1', class_='text')
        post_info['title'] = title.text
        # // ----  title  ----

        # ----  main image  ---- //
        main_image = None
        main_img_tag = _main_content.find('img', class_='mainImg')
        if main_img_tag:
            main_image = encoder_utf_8(main_img_tag['src'])

        # img_layout = _main_content.find('div', class_='source_post')
        # if img_layout:
        #     _img = img_layout.find('img')
        #     if _img:
        #         try:
        #             main_image = encoder_utf_8(_img['src'])
        #         except:
        #             pass
        post_info['main_image'] = main_image
        # // ----  main image  ----

        # ----  video  ---- //
        video = None
        _iframe_block = soup.find('div', class_='iframe-block')
        if _iframe_block:
            _iframe = _iframe_block.find('iframe')
            try:
                if _iframe:
                    video = encoder_utf_8(_iframe['src'])
            except:
                pass
        post_info['video'] = video

        if not post_info.get('main_image'):
            yt_img_base_url = "https://img.youtube.com/vi/{}/maxresdefault.jpg"
            if post_info.get('video'):
                if "youtube.com" in post_info['video']:
                    yt_video_id = post_info['video'].split('/')[-1]
                    yt_image = yt_img_base_url.format(yt_video_id)
                    post_info['main_image'] = yt_image
        # // ----  video  ----

        # ----  texts & summary & images  ---- //
        # _body = _main_content.find('div', class_='richtextbox')
        _body = _main_content.find('div', class_='content-main-titles')
        _all_p = _body.find_all('p')
        text = ""
        summary = ""
        images = []
        if _all_p:
            for p in _all_p:
                img = p.find('img')
                if img:
                    img_url = encoder_utf_8(img['src'])
                    if not main_image and not video:
                        main_image = img_url
                        post_info['main_image'] = img_url
                        continue
                    images.append(img_url)
                # if not summary:
                #     summary = p.text
                #     continue
                text += p.text + '\n'
        post_info['summary'] = summary
        post_info['text'] = text
        post_info['images'] = images
        # // ----  texts & summary & images  ----

        # ----  tags  ---- //
        tags = []
        _tags_layout = soup.find('div', class_='tags')
        if _tags_layout:
            _tags = _tags_layout.find_all('span', class_='tag')
            if _tags:
                for tag in _tags:
                    tags.append({
                        'name': tag.text.strip(),
                        'url': "#", #encoder_utf_8(BASE_URL+tag['href'])
                    })
        post_info['tags'] = tags
        # // ----  tags  ----
    except Exception as e:
        post_info['errors'] = e
    return post_info



test_link = 'https://qalampir.uz/news/anzhelina-zholi-bmtdagi-faoliyatiga-nuk-ta-k-uydi-74098'
test_link = 'https://qalampir.uz/news/-2301-74111'
test_link = 'https://qalampir.uz/news/ronalduni-ustidan-kulgan-8-yashar-k-izga-ulim-bilan-ta%D2%B3did-k-ilishdi-video-74095'
test_link = 'https://qalampir.uz/news/dune-a%D2%B3olisining-3-6-foizini-migrantlar-tashkil-k-iladi-bmt-74085'
test_link = 'https://qalampir.uz/news/yurak-yetishmovchiligini-oldindan-ayta-oladigan-moslama-yaratildi-74101'

# res = get_post_detail(test_link)
# print(res)


months = {
    'yanvar': 1,
    'fevral': 2,
    'mart': 3,
    'aprel': 4,
    'may': 5,
    'iyun': 6,
    'iyul': 7,
    'avgust': 8,
    'sentabr': 9,
    'oktabr': 10,
    'noyabr': 11,
    'dekabr': 12
}


def collect_new_links(last_date: datetime=None) -> List[str]:
    req = requests.get(LAST_NEWS_PAGE)
    links = []
    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        # _news_layout = soup.find('div', class_='block_lh')
        _news_layout = soup.find('div', class_='content-border')
        flag = True
        load_more = False
        new_last_date = None
        page = 2
        while flag:
            news_blocks = None
            if load_more:
                break
                sleep(0.3)
                next_page_url = f"https://qalampir.uz/uz/news/latest/load-more?page={page}"
                req = requests.get(next_page_url)
                if 200<= req.status_code < 300:
                    soup = BeautifulSoup(json.loads(req.content)['data'], 'html.parser')
                    news_blocks = soup.find_all('a', class_='ss_item item flex_row')
                    page += 1
                else:
                    load_more = False
                    flag = False
                    break
            else:
                # news_blocks = _news_layout.find_all('a', class_='ss_item item flex_row')
                news_blocks = _news_layout.find_all('div', class_='col-lg-4 col-md-6')
                # print(f'news blocks : {len(news_blocks)}')
            if not news_blocks:
                load_more = False
                flag = False
                break
            for news_block in news_blocks:
                try:
                    a_tag = news_block.find('a', class_='news-card')
                    url = encoder_utf_8(BASE_URL+a_tag['href'])
                    # date_block = news_block.find('span', class_='date_view flex_row')
                    # time_block = news_block.find('span', class_='date')
                    # time_block = date_block.find_all('span')[0]

                    # date_list = time_block.text.split()
                    # if len(date_list) == 1:
                    #     _date: list = list(datetime.today().timetuple()[0:3])
                    # elif len(date_list) == 3:
                    #     _date: list = [datetime.today().year, months[date_list[1].lower()], int(date_list[0])]
                    # elif len(date_list) == 4:
                    #     _date: list = [int(date_list[2]), months[date_list[1].lower()], int(date_list[0])]
                    # else:
                    #     flag = False
                    #     load_more = False
                    #     logger.error(f'date time parsing error : {date_list}')

                    # date_str = time_block.text.strip()
                    # print(date_str)
                    # time_regex = '([\d]{2}):([\d]{2})'
                    # _res_time = re.search(time_regex, date_str).groups()
                    
                    # if len(_res_time) == 2:
                    #     is_digits = all([i.isdigit() for i in _res_time])
                    #     if is_digits:
                    #         hour, minute = _res_time
                    #         _date.append(int(hour))
                    #         _date.append(int(minute))

                    # date_time = datetime(*_date)
                    yield (url)
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
                    print(e)
            break
        if new_last_date:
            save_last_date('qalampir', new_last_date.timestamp())
    return links
