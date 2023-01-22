from datetime import datetime
import re
from typing import List
import requests
from urllib import parse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from parsers.models import NewsLinks
from parsers.scrapers.utils import extract_dates, save_last_date
import logging

logger = logging.getLogger('parsers')
logger.setLevel('INFO')

encoder_utf_8 = lambda x: parse.unquote(x, encoding='utf-8')

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

LAST_NEW_PAGE = "https://olamsport.com/oz/news/"
BASE_URL = "https://olamsport.com"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def get_post_detail(link: str) -> dict:
    post_info: dict = {}
    try:
        req = session.get(link, headers=headers)
        soup = BeautifulSoup(req.text, 'html.parser')
        main_div = soup.find("div", class_="news-summary-block")

        # ----  title  ---- //
        title = soup.find("h1", class_='main-link')
        post_info['title'] = title.text
        # // ----  title  ----

        # ---- main image ---- //
        main_image = None

        if main_div:
            _main_image = main_div.find('img')
            if _main_image:
                try:
                    main_image = f"{BASE_URL}{encoder_utf_8(_main_image['src'])}"
                except:
                    pass
        post_info['main_image'] = main_image
        # // ---- main image ----

        # --- tags ---- //
        _tags_block = soup.find('div', class_='tags')
        if _tags_block:
            tags_a = _tags_block.find_all('a')
            if tags_a:
                tags = [
                    {
                        'name': tag.text,
                        'url': BASE_URL + encoder_utf_8(tag['href'])
                    }
                    for tag in tags_a
                ]
                post_info['tags'] = tags
            else:
                tags = []
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
                        images.append(f"{BASE_URL}{encoder_utf_8(img['src'])}")
                    except:
                        pass
                text += p.text + '\n'
        post_info['text'] = text
        post_info['images'] = images
        # // ----  texts & images  ----

        # ---- video ---- //
        main_video = None
        video_div = soup.find_all("a", class_="tgme_widget_message_video_player js-message_video_player ready")
        if video_div:
            main_video = encoder_utf_8(video_div['href'])
        post_info["main_video"] = main_video
    except Exception as e:
        # print(f'error in olamsport parser : {e}')
        post_info['errors'] = e
    return post_info


# link = "https://olamsport.com/oz/news/xabib-jch-2022-finalida-ibragimovich-pogba-va-jokovich-bilan-uchrashdi-foto"
# link = "https://championat.asia/oz/news/final-argentina-franciya-asosiy-tarkiblar-malum"
# link = "https://championat.asia/oz/news/instagram-messi-ronalduni-maglub-etdi-navbat-tuhumga"
# link = "https://olamsport.com/oz/news/uchta-federaciyaga-rahbarlik-qilayotgan-hamyurtimiz-makron-ronaldino-ibragimovich-nusret-bilan-uchrashdi-foto"
# link = "https://olamsport.com/oz/news/faryozbek-dosmatovning-ozbekiston-chempionatidan-chetlatilish-sababi-malum-video"
# link = "https://olamsport.com/oz/news/odilxon-kamolov-jarrohlik-stoliga-yotdi-uni-hozir-bir-qarashda-tanimaysiz-video"
link = "https://olamsport.com/oz/news/charlz-oliveyra-islam-maxachevdan-qabul-qilingan-maglubiyat-sababini-ochiqladi"


# result = get_post_detail(link=link)
# print(result)

months = {
    'jan': 1,
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


def collect_new_links(last_date: datetime=None) -> List[str]:
    req = session.get(LAST_NEW_PAGE, headers=headers)
    error_counter = 0
    links = []

    if 200 <= req.status_code < 300:
        soup = BeautifulSoup(req.content, 'html.parser')
        _news_layout = soup.find('div', class_='news-list')
        flag = True
        load_more = False
        new_last_date = None
        while flag:
            news_blocks = None
            if load_more:
                load_more_link = soup.find('li', class_='next').find('a')['href']
                req = session.get(encoder_utf_8(BASE_URL + load_more_link), headers=headers)
                if 200 <= req.status_code < 300:
                    soup = BeautifulSoup(req.content, 'html.parser')
                    _news_layout = soup.find('div', class_='news-list')
                    news_blocks = _news_layout.find_all('div', class_='news-list-item')
                else:
                    load_more = False
                    flag = False
                    break
            else:
                news_blocks = _news_layout.find_all('div', class_='news-list-item')
            if not news_blocks:
                break
            for news_block in news_blocks:
                try:
                    a = news_block.find('a', class_='main-link')
                    url = encoder_utf_8(BASE_URL + a['href'])
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
                        # print(f"------{_date}")
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
                    print(f"error in olamsport collector : {e}")
                    error_counter += 1
                    if error_counter > 10:
                        flag = False
                        load_more = False
                        break
                    logger.error(e)
            break
        if new_last_date:
            save_last_date('olamsport', new_last_date.timestamp())
        return links
